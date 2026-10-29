"""The prop-firm basket measured on the real 15-minute path (no intraday assumption).

    python research/rnd/prop_m15.py --strategies trend_long,mom126_ls,buyhold --vols 0.05,0.06,0.08,0.10 --cap 3

Daily, after the server-day close: target weights per instrument from systematic.py rules (data up to that close),
each instrument at equal risk, the portfolio scaled to a target annual volatility (60-day realised volatility of the
portfolio, known at that close), gross leverage capped. The weights are held through the next server day; equity is
marked every 15 minutes at the WORST price of each bar (low for longs, high for shorts) and summed over instruments.
Costs: spread + slippage on every weight change. The 5ers rules are applied to that equity: breach when the intraday
low is 10% under the start or 5% under the day's start (max of equity and balance at server midnight).
Challenge (step 1 +8%, step 2 +5%) and funded (80% of profit paid every +W, lost at -10%) from every 5th start date.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "strategy")]
import systematic as S  # noqa: E402

BASKET = ["SPX500_USD", "NAS100_USD", "UK100_USD", "XAU_USD", "XAG_USD"]


def m15(sym):
    f = sorted((HERE.parents[1] / "data" / "ohlcv").glob(f"{sym}_M15_*.csv"))[-1]
    m = pd.read_csv(f)
    m.columns = [c.lower() for c in m.columns]
    t = pd.to_datetime(m[[c for c in m.columns if c in ("time", "timestamp", "date", "datetime")][0]], utc=True)
    m = m.assign(time=t).drop_duplicates("time").set_index("time").sort_index()
    m["day"] = (m.index + pd.Timedelta(hours=2)).floor("D")
    return m


def daily_paths(strategy, target_vol, cap, basket):
    """Per server day: close-to-close portfolio return and the worst intraday portfolio return vs the day's start."""
    rule = {"trend_long": lambda o: o["mom252"].clip(lower=0), "mom126_ls": lambda o: o["mom126"],
            "buyhold": lambda o: pd.Series(1.0, index=o["mom252"].index),
            "pullback_long": lambda o: o["pullback"].clip(lower=0), "donch55": lambda o: o["donch55"]}[strategy]
    W, R, ADV, COSTF = {}, {}, {}, {}
    for s in basket:
        mm = m15(s)
        d = S.d1_from_m15(s)
        d.index = pd.DatetimeIndex(d.index)
        pos = rule(S.positions(d))
        r = d["close"].pct_change()
        vol = r.rolling(60).std() * np.sqrt(252)
        W[s] = (pos * (0.10 / vol)).clip(-5, 5)  # equal risk per instrument, decided at that day's close
        R[s] = r
        COSTF[s] = S.cost_frac(s, d["close"])
        prev = d["close"].shift(1)
        # adverse intraday move vs the previous close, for a long and for a short position
        g = mm.groupby("day")
        lo, hi = g["low"].min(), g["high"].max()
        ADV[s] = pd.DataFrame({"long": lo.reindex(d.index) / prev - 1, "short": hi.reindex(d.index) / prev - 1})
    Wd = pd.DataFrame(W).fillna(0) / len(basket)
    Rd = pd.DataFrame(R)
    port_raw = (Wd.shift(1) * Rd).sum(axis=1)
    pvol = port_raw.rolling(60).std() * np.sqrt(252)
    k = (target_vol / pvol).clip(upper=10).shift(0)
    Wt = Wd.mul(k, axis=0)
    gross = Wt.abs().sum(axis=1)
    Wt = Wt.div((gross / cap).clip(lower=1), axis=0)  # cap gross leverage
    Wh = Wt.shift(1).fillna(0)  # held during the day
    cost = (Wt.diff().abs() * pd.DataFrame(COSTF)).sum(axis=1).shift(1).fillna(0)
    ret = (Wh * Rd).sum(axis=1) - cost
    # worst intraday: per instrument its adverse extreme (conservative: all instruments at their worst together)
    worst = pd.Series(0.0, index=Wh.index)
    for s in basket:
        a = ADV[s].reindex(Wh.index)
        w = Wh[s]
        worst += np.where(w > 0, w * a["long"].fillna(0), np.where(w < 0, w * a["short"].fillna(0), 0.0))
    worst = np.minimum(worst - cost, ret)
    df = pd.DataFrame({"ret": ret, "worst": worst, "gross": Wh.abs().sum(axis=1)}).dropna()
    return df[df.index >= df.index[0] + pd.Timedelta(days=380)]  # warm-up for 252-day rules + vol


def run_path(ret, worst, start, w_payout, horizon):
    eq, i = 1.0, start
    for target in (0.08, 0.05):
        eq = 1.0
        while True:
            if i >= len(ret):
                return "einde", i - start, 0.0
            low = eq * (1 + worst[i])
            if low <= 0.90 or low <= eq * 0.95:
                return "breach", i - start, 0.0
            eq *= 1 + ret[i]
            i += 1
            if eq >= 1 + target:
                break
    days = i - start
    paid, eq = 0.0, 1.0
    for j in range(i, min(i + horizon, len(ret))):
        low = eq * (1 + worst[j])
        if low <= 0.90 or low <= eq * 0.95:
            break
        eq *= 1 + ret[j]
        if eq >= 1 + w_payout:
            paid += 0.8 * (eq - 1)
            eq = 1.0
    return "geslaagd", days, paid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategies", default="trend_long,mom126_ls,buyhold,pullback_long")
    ap.add_argument("--vols", default="0.05,0.06,0.08,0.10")
    ap.add_argument("--cap", type=float, default=3.0, help="maximum gross leverage")
    ap.add_argument("--fee", type=float, default=0.005)
    ap.add_argument("--withdraw", type=float, default=0.04)
    ap.add_argument("--horizon", type=int, default=504)
    ap.add_argument("--basket", default=",".join(BASKET))
    a = ap.parse_args()
    basket = a.basket.split(",")
    rows = []
    for st in a.strategies.split(","):
        for v in map(float, a.vols.split(",")):
            df = daily_paths(st, v, a.cap, basket)
            ret, worst = df["ret"].values, df["worst"].values
            res = [run_path(ret, worst, s, a.withdraw, a.horizon) for s in range(0, len(ret) - 60, 5)]
            done = [x for x in res if x[0] != "einde"]
            ok = [x for x in done if x[0] == "geslaagd"]
            ratio = (-df["worst"] / df["ret"].clip(upper=-1e-9).abs())[df["ret"] < -0.002]
            rows.append(dict(strategie=st, vol=v, starts=len(done), geslaagd=round(len(ok) / max(1, len(done)) * 100, 1),
                             breach=round(sum(x[0] == "breach" for x in done) / max(1, len(done)) * 100, 1),
                             dagen_med=int(np.median([x[1] for x in ok])) if ok else None,
                             uitbet_funded=round(np.mean([x[2] for x in ok]) * 100, 2) if ok else 0,
                             EV=round((np.mean([x[2] for x in done]) - a.fee) * 100, 2),
                             jaarrend=round(df["ret"].mean() * 252 * 100, 1), maxdag=round(df["worst"].min() * 100, 2),
                             intraday_factor_med=round(ratio.median(), 2), hefboom_gem=round(df["gross"].mean(), 2)))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print(f"echte 15-min-pad, hefboomplafond {a.cap}, fee {a.fee*100:.1f}%, uitbetaling bij +{a.withdraw*100:.0f}%")
    print(t.to_string(index=False))
    t.to_csv(HERE / "out" / "prop_m15.csv", index=False)
