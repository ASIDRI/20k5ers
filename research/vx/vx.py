"""Test VX1 (docs/SYSTEM_VX.md): VectorVest translated to forex, metals and oil.

    python research/vx/vx.py            # the pre-registered system and its parts
    python research/vx/vx.py --now      # ratings, DEW and positions at the end of the data

Daily, at the close of the daily candle (complete_times): currency strength indices, ratings (RT, VAL, SAFE, VST),
DEW per index and per commodity; entries at the weekly close, exits daily when the DEW turns. A decision at the
close of day t holds from that close to the next.
"""
import argparse
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[0] / "strategy"), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402

CCY = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"]
COMMOD = ["XAUUSD", "XAGUSD", "XTI_USD"]
SLOTS, TARGET_VOL = 7, 0.10
P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def pairs():
    out = []
    for a, b in combinations(CCY, 2):
        for p in (a + b, b + a):
            try:
                load(p, "D1")
                out.append(p)
                break
            except IndexError:
                continue
    return out


def closes():
    """Closes of every instrument on the forex calendar, each known at its own candle's completion (ffill)."""
    ps = pairs()
    raw = {}
    for s in ps + COMMOD:
        d = load(s, "D1")
        d["done"] = complete_times(d["time"], "D1")
        raw[s] = d.drop_duplicates("done").set_index("done").close
    idx = pd.DatetimeIndex(sorted(set().union(*[set(raw[p].index) for p in ps])))
    df = pd.DataFrame({s: x.reindex(idx.union(x.index)).sort_index().ffill().reindex(idx) for s, x in raw.items()})
    return df, ps


def wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return x.rolling(n).apply(lambda v: (v * w).sum() / w.sum(), raw=True)


def dew(price):
    """+1 / -1 / 0: the DEW state (Up: close > WMA30 and DPO20 > 0; Down: the reverse; else unchanged)."""
    dpo = price.shift(11) - price.rolling(20).mean()
    w = wma(price, 30)
    s = pd.Series(np.where((price > w) & (dpo > 0), 1.0, np.where((price < w) & (dpo < 0), -1.0, np.nan)),
                  index=price.index)
    return s.ffill().fillna(0.0)


def ratings(logp):
    """RT, VAL, SAFE per column of a log-price frame."""
    r = logp.diff()
    sig = r.rolling(252, min_periods=126).std()
    rt = sum((logp - logp.shift(n)) / (sig * np.sqrt(n)) for n in (21, 63, 126, 252)) / 4
    val = -(logp - logp.rolling(1260, min_periods=252).mean()) / (sig * np.sqrt(252))
    safe = -r.rolling(63).std()
    return rt, val, safe


def z(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)


def build():
    px, ps = closes()
    lr = np.log(px).diff()
    idx = pd.DataFrame(0.0, index=px.index, columns=CCY)  # log strength index per currency
    for p in ps:
        idx[p[:3]] += lr[p].fillna(0) / 7
        idx[p[3:]] -= lr[p].fillna(0) / 7
    L = idx.cumsum()
    rt, val, safe = ratings(L)
    vst = (z(rt) + z(val) + z(safe)) / 3
    dew_c = pd.DataFrame({c: dew(np.exp(L[c])) for c in CCY})
    rt_m, _, _ = ratings(np.log(px[COMMOD]))
    dew_m = pd.DataFrame({s: dew(px[s]) for s in COMMOD})
    vol = lr.rolling(63).std() * np.sqrt(252)
    date = px.index.tz_convert(None) if px.index.tz is not None else px.index
    week = np.asarray((date - pd.Timestamp("2000-01-03")).days // 7)  # Monday-based week number
    weekly = np.r_[week[1:] != week[:-1], True]  # last forex day of its week (known from the calendar)
    ret = (px.shift(-1) / px - 1).fillna(0)  # from this close to the next
    cost = pd.DataFrame({s: [cost_price(s, x) / 2 / x if x == x else 0 for x in px[s].values] for s in px},
                        index=px.index)
    return dict(px=px, ps=ps, rt=rt, val=val, safe=safe, vst=vst, dew_c=dew_c, rt_m=rt_m, dew_m=dew_m, vol=vol,
                weekly=weekly, ret=ret, cost=cost, date=date)


def pair_of(a, b, ps):
    return (a + b, 1.0) if a + b in ps else (b + a, -1.0)


def simulate(D, fx=True, com=True, use_dew=True, use_vst=True):
    px, ps, ret, cost, vol = D["px"], D["ps"], D["ret"], D["cost"], D["vol"]
    cols = list(px.columns)
    w = pd.Series(0.0, index=cols)
    longs, shorts = [], []
    out = np.zeros(len(px))
    for t in range(len(px)):
        new = w.copy()
        vst, dc = D["vst"].iloc[t], D["dew_c"].iloc[t]
        if D["weekly"][t] and vst.notna().all():
            new[:] = 0.0
            longs, shorts = [], []
            if fx:
                if use_vst:
                    order = vst.sort_values(ascending=False).index
                    top, bot = list(order[:3]), list(order[::-1][:3])
                    longs = [c for c in top if not use_dew or dc[c] == 1][:2]
                    shorts = [c for c in bot if not use_dew or dc[c] == -1][:2]
                    if not use_dew:
                        longs, shorts = top[:2], bot[:2]
                else:  # DEW alone: every Up currency against every Down currency
                    longs, shorts = [c for c in CCY if dc[c] == 1], [c for c in CCY if dc[c] == -1]
                combos = [(a, b) for a in longs for b in shorts]
                for a, b in combos:
                    p, sgn = pair_of(a, b, ps)
                    if vol[p].iloc[t] > 0:
                        new[p] += sgn * TARGET_VOL / vol[p].iloc[t] / SLOTS * (4 / len(combos) if not use_vst else 1)
            if com:
                for s in COMMOD:
                    if not (px[s].iloc[t] == px[s].iloc[t]) or not vol[s].iloc[t] > 0:
                        continue
                    dm, rm = D["dew_m"][s].iloc[t], D["rt_m"][s].iloc[t]
                    sig = (dm if (dm != 0 and np.sign(rm) == dm) else 0.0) if use_dew else np.sign(rm)
                    new[s] = sig * TARGET_VOL / vol[s].iloc[t] / SLOTS
        elif use_dew:
            # daily exits: a currency whose DEW turned against, a commodity whose DEW turned against
            for c in [c for c in longs if dc[c] == -1] + [c for c in shorts if dc[c] == 1]:
                for o in (shorts if c in longs else longs):
                    p, _ = pair_of(c, o, ps)
                    new[p] = 0.0
                (longs if c in longs else shorts).remove(c)
            for s in COMMOD:
                if new[s] != 0 and np.sign(new[s]) == -D["dew_m"][s].iloc[t]:
                    new[s] = 0.0
        tc = ((new - w).abs() * cost.iloc[t].fillna(0)).sum()
        out[t] = (new * ret.iloc[t].fillna(0)).sum() - tc
        w = new
    return pd.Series(out, index=pd.Index(D["date"].strftime("%Y-%m-%d")))


def stats(r):
    eq = (1 + r).cumprod()
    vol = r.std() * np.sqrt(252)
    return (1 + r).prod() ** (252 / len(r)) - 1, vol, r.mean() * 252 / vol if vol else np.nan, (eq / eq.cummax() - 1).min()


def show(lab, r):
    cells = []
    for p, s, e in P:
        x = r[(r.index >= s) & (r.index < e)]
        a, v, sh, dd = stats(x)
        cells.append(f"{p} {a*100:+5.1f}%/j vol {v*100:4.1f}% Sharpe {sh:+.2f} maxDD {dd*100:5.1f}%")
    x = r[(r.index >= "2005") & (r.index < "2026")]
    print(f"  {lab:34} " + " | ".join(cells) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")


def now(D):
    t = len(D["px"]) - 1
    print(f"Stand op {D['date'][t].date()} (laatste gesloten dagcandle)\n")
    tab = pd.DataFrame({"VST": D["vst"].iloc[t], "RT": D["rt"].iloc[t], "VAL": D["val"].iloc[t],
                        "SAFE*100": D["safe"].iloc[t] * 100, "DEW": D["dew_c"].iloc[t]}).sort_values("VST", ascending=False)
    print(tab.round(2).to_string())
    print("\nGrondstoffen:", {s: (D["dew_m"][s].iloc[t], round(D["rt_m"][s].iloc[t], 2)) for s in COMMOD})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", action="store_true")
    a = ap.parse_args()
    D = build()
    if a.now:
        now(D)
        sys.exit()
    print("## BESLISSEND: het volledige systeem (forex + goud, zilver, olie)")
    show("VX volledig", simulate(D))
    print("\n## Delen (gerapporteerd)")
    show("alleen forex", simulate(D, com=False))
    show("alleen grondstoffen", simulate(D, fx=False))
    show("zonder DEW (alleen VST, wekelijks)", simulate(D, use_dew=False))
    show("alleen DEW (zonder VST)", simulate(D, use_vst=False))
    g = D["ret"]["XAUUSD"].fillna(0) * TARGET_VOL / D["vol"]["XAUUSD"].shift(1).bfill() / SLOTS
    show("goud kopen en houden (zelfde schaal)", pd.Series(g.values, index=pd.Index(D["date"].strftime("%Y-%m-%d"))))
