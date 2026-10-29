"""R&D phase 2b: systematic rule families as a portfolio on daily data (30 assets), after costs.

    python research/rnd/systematic.py --start 2015-01-01 --end 2025-12-31

Each rule gives a position in {-1, 0, +1} per instrument from data up to the close of day t; it is held from that
close to the next (lag of one day, no look-ahead). Positions are scaled to equal risk (target 10%/yr volatility per
instrument from its 60-day realised volatility, measured up to t). Costs: spread + slippage of the symbol on every
change of position (research/costs.json). Portfolio = average of the instruments' returns.

Families:
  mom63 / mom126 / mom252   trend direction: sign of the return over 3 / 6 / 12 months
  donch20 / donch55         breakout: long after a close above the highest high of N days, short below the lowest
                            low; held until the opposite breakout
  pullback                  own design from the videos: only in the direction of the 12-month trend; the last
                            20-day swing (low -> high for longs); entry when price has pulled back into 0.5-0.786 of
                            it AND the day closes up (reaction); stop below the swing low; exit at the swing high
                            (fib 0) or the stop; one position at a time
  rsi2                      short-term reversion: RSI(2) < 10 above the 200-day average -> long until the close is
                            above the 5-day average (mirror for shorts)
Report per period: annual return, volatility, Sharpe, worst drawdown, share of instruments positive.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strategy"))
from setup_study import load  # noqa: E402

SYMS = ("AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD "
        "GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY XTI_USD UK100_USD").split()
COST = json.loads((HERE.parent / "costs.json").read_text())
TARGET_VOL = 0.10


def cost_frac(sym, price):
    u = sym.replace("_", "").upper()
    pips = next((v for k, v in sorted(COST.items(), key=lambda kv: -len(kv[0])) if k in u), 1.5)
    pip = 0.01 if ("JPY" in u or u.startswith("XTI")) else (1.0 if u.startswith("UK100") else 0.0001)
    return pips * pip / price  # one side, as a fraction of price


def rsi(c, n):
    d = c.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def positions(d):
    c, h, l = d["close"], d["high"], d["low"]
    out = {}
    for n in (63, 126, 252):
        out[f"mom{n}"] = np.sign(c / c.shift(n) - 1).fillna(0)
    for n in (20, 55):
        hi, lo = h.rolling(n).max().shift(1), l.rolling(n).min().shift(1)
        sig = pd.Series(np.where(c > hi, 1, np.where(c < lo, -1, np.nan)), index=c.index)
        out[f"donch{n}"] = sig.ffill().fillna(0)
    # pullback in the 12-month trend (own design from the videos)
    trend = np.sign(c / c.shift(252) - 1).fillna(0).values
    hh, ll = h.rolling(20).max().values, l.rolling(20).min().values
    cv, ov, hv, lv = c.values, d["open"].values, h.values, l.values
    pos = np.zeros(len(c))
    cur, stop, tgt = 0, np.nan, np.nan
    for t in range(252, len(c)):
        if cur != 0:  # manage: exit at the stop or the target on today's range (stop first)
            if (cur == 1 and lv[t] <= stop) or (cur == -1 and hv[t] >= stop) or \
               (cur == 1 and hv[t] >= tgt) or (cur == -1 and lv[t] <= tgt):
                cur = 0
        if cur == 0 and trend[t] != 0:
            lo_, hi_ = ll[t - 1], hh[t - 1]
            rng = hi_ - lo_
            if rng > 0:
                if trend[t] == 1:
                    z_hi, z_lo = hi_ - 0.5 * rng, hi_ - 0.786 * rng
                    if lv[t] <= z_hi and cv[t] >= z_lo and cv[t] > ov[t] and lv[t] > lo_:
                        cur, stop, tgt = 1, lo_, hi_
                else:
                    z_lo, z_hi = lo_ + 0.5 * rng, lo_ + 0.786 * rng
                    if hv[t] >= z_lo and cv[t] <= z_hi and cv[t] < ov[t] and hv[t] < hi_:
                        cur, stop, tgt = -1, hi_, lo_
        pos[t] = cur
    out["pullback"] = pd.Series(pos, index=c.index)
    r2, sma200, sma5 = rsi(c, 2), c.rolling(200).mean(), c.rolling(5).mean()
    pos = np.zeros(len(c))
    cur = 0
    for t in range(200, len(c)):
        if cur == 1 and cv[t] > sma5.iloc[t]:
            cur = 0
        elif cur == -1 and cv[t] < sma5.iloc[t]:
            cur = 0
        if cur == 0:
            if r2.iloc[t] < 10 and cv[t] > sma200.iloc[t]:
                cur = 1
            elif r2.iloc[t] > 90 and cv[t] < sma200.iloc[t]:
                cur = -1
        pos[t] = cur
    out["rsi2"] = pd.Series(pos, index=c.index)
    return out


def d1_from_m15(sym):
    """Daily candles built from the symbol's own M15 data (server day: UTC+2), for series whose stored D1/W1/MN
    come from another source (gold, silver, NAS100: checked 2026-10-28)."""
    f = sorted((HERE.parents[1] / "data" / "ohlcv").glob(f"{sym}_M15_*.csv"))[-1]
    m = pd.read_csv(f)
    m.columns = [c.lower() for c in m.columns]
    t = pd.to_datetime(m[[c for c in m.columns if c in ("time", "timestamp", "date", "datetime")][0]], utc=True)
    m = m.assign(time=t).drop_duplicates("time").set_index("time").sort_index()
    g = m.groupby((m.index + pd.Timedelta(hours=2)).floor("D"))
    d = pd.DataFrame(dict(open=g["open"].first(), high=g["high"].max(), low=g["low"].min(), close=g["close"].last()))
    return d[g.size() >= 20]  # skip near-empty days (holidays, weekend stubs)


def run(start, end, syms, from_m15=()):
    rets = {}
    for s in syms:
        d = d1_from_m15(s) if s in from_m15 else load(s, "D1").set_index("time")
        d = d[~d.index.duplicated()]
        c = d["close"]
        r = c.pct_change()
        vol = r.rolling(60).std() * np.sqrt(252)
        scale = (TARGET_VOL / vol).clip(upper=5).shift(0)
        cf = cost_frac(s, c)
        for name, p in positions(d).items():
            w = (p * scale).fillna(0)
            pnl = w.shift(1) * r - (w.diff().abs() * cf).fillna(0)
            rets.setdefault(name, {})[s] = pnl
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    res = {}
    for name, per in rets.items():
        df = pd.DataFrame(per)
        df = df[(df.index >= t0) & (df.index < t1)]
        res[name] = df
    return res


def stats(port):
    ann = port.mean() * 252
    vol = port.std() * np.sqrt(252)
    eq = (1 + port.fillna(0)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    return ann, vol, ann / vol if vol else np.nan, dd


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", default=",".join(SYMS))
    ap.add_argument("--split", default="2021-01-01", help="periods: start..split and split..end")
    ap.add_argument("--from-m15", default="", help="comma list: build D1 from the symbol's M15 data")
    a = ap.parse_args()
    res = run(a.start, a.end, a.symbols.split(","), set(filter(None, a.from_m15.split(","))))
    sp = pd.Timestamp(a.split, tz="UTC")
    rows = []
    for name, df in res.items():
        for lab, part in (("periode 1", df[df.index < sp]), ("periode 2", df[df.index >= sp])):
            port = part.mean(axis=1, skipna=True)
            ann, vol, sh, dd = stats(port)
            pos_share = (part.sum() > 0).mean()
            rows.append(dict(regel=name, periode=lab, jaarrend=round(ann * 100, 2), vol=round(vol * 100, 2),
                             sharpe=round(sh, 2), maxDD=round(dd * 100, 1), assets_pos=f"{pos_share*100:.0f}%"))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(t.pivot_table(index="regel", columns="periode", values=["jaarrend", "sharpe", "maxDD"], aggfunc="first").to_string())
    print(t[["regel", "periode", "assets_pos"]].pivot(index="regel", columns="periode", values="assets_pos").to_string())
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    t.to_csv(out / f"systematic_{a.start[:4]}_{a.end[:4]}.csv", index=False)
    reg = HERE / "registry.csv"
    pd.DataFrame(dict(fase="2b-systematisch", groep="regel", cel=sorted(res), datum=pd.Timestamp.now().isoformat()[:16])).to_csv(
        reg, mode="a", header=not reg.exists(), index=False)
