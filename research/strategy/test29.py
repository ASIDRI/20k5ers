"""Test 29: video 13 (trade recap EUR/JPY, EUR/USD) - previous week's high taken, then the key higher low breaks.

    python research/strategy/test29.py

Forex, 4-hour candles, 28 pairs, 2005-2025. Per week: PWH / PWL = high / low of the previous (completed) week.
Short: a 4-hour candle trades above PWH (the liquidity is taken); afterwards a 4-hour candle closes below the key
higher low = the last confirmed 4-hour swing low (2 candles each side) that formed before the highest high since the
sweep -> short at that close. Stop 0.1 daily ATR above the highest high since the sweep. Target: this week's open if
it lies below the entry, else the previous week's middle (equilibrium); only if the reward is at least the risk.
Exit at target, stop or the week's last 4-hour close. Long: the mirror at PWL. At most one trade per side per week.
Costs per symbol. Decisive: all trades; also reported: with the weekly structure (test 20's wk_struct idea: trade
direction = the side the weekly zigzag points to).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from test2 import cost_price  # noqa: E402
from t17_eval import pf  # noqa: E402
from rt import pairs  # noqa: E402

K = 2


def run(sym):
    h4 = load(sym, "H4")
    h4 = h4[h4.time >= pd.Timestamp("2005-01-01", tz="UTC")].reset_index(drop=True)
    d = load(sym, "D1")
    tr = np.r_[np.nan, np.maximum(d.high.values[1:], d.close.values[:-1]) - np.minimum(d.low.values[1:], d.close.values[:-1])]
    datr = pd.Series(pd.Series(tr).rolling(14).mean().values, index=d.time).shift(1)
    h4["wk"] = (h4.time + pd.Timedelta(hours=2)).dt.to_period("W-SAT")  # forex week: Sunday 22:00 to Friday
    o, h, l, c = (h4[k].values for k in ("open", "high", "low", "close"))
    sw_lo = np.zeros(len(h4), bool)
    sw_hi = np.zeros(len(h4), bool)
    for i in range(K, len(h4) - K):
        sw_lo[i] = l[i] == l[i - K:i + K + 1].min()
        sw_hi[i] = h[i] == h[i - K:i + K + 1].max()
    cost = cost_price(sym)
    rows = []
    weeks = list(h4.groupby("wk").indices.items())
    for (wk, idx), (_, prev) in zip(weeks[1:], weeks[:-1]):
        pwh, pwl = h[prev].max(), l[prev].min()
        wopen, eq = o[idx[0]], (pwh + pwl) / 2
        a = datr.asof(h4.time[idx[0]]) if len(datr) else np.nan
        if np.isnan(a):
            continue
        for dirn in (-1, 1):  # -1: sweep of PWH then short; +1: sweep of PWL then long
            sweep, ext_i = None, None
            for j in idx:
                if sweep is None:
                    if (h[j] > pwh) if dirn == -1 else (l[j] < pwl):
                        sweep, ext_i = j, j
                    continue
                if (h[j] > h[ext_i]) if dirn == -1 else (l[j] < l[ext_i]):
                    ext_i = j
                known = [s for s in range(idx[0] - 30, ext_i) if s + K <= j and (sw_lo[s] if dirn == -1 else sw_hi[s])]
                if not known:
                    continue
                key = l[known[-1]] if dirn == -1 else h[known[-1]]
                if (c[j] < key) if dirn == -1 else (c[j] > key):
                    entry = c[j]
                    sl = (h[ext_i] + 0.1 * a) if dirn == -1 else (l[ext_i] - 0.1 * a)
                    tp = wopen if (wopen - entry) * dirn > 0 else eq
                    risk = abs(entry - sl)
                    if risk <= 0 or (tp - entry) * dirn < risk:
                        break
                    R = None
                    for m in idx[idx > j]:
                        adv, fav = (h[m], l[m]) if dirn == -1 else (l[m], h[m])
                        if (adv >= sl) if dirn == -1 else (adv <= sl):
                            R = -1.0
                            break
                        if (fav <= tp) if dirn == -1 else (fav >= tp):
                            R = abs(tp - entry) / risk
                            break
                    if R is None:
                        R = (c[idx[-1]] - entry) * dirn / risk
                    rows.append(dict(sym=sym, week=str(wk.start_time.date()), dir=dirn, entry=entry, sl=sl, tp=tp,
                                     rr=abs(tp - entry) / risk, R=R - cost / risk, costR=cost / risk))
                    break
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = pd.concat([run(s) for s in pairs()], ignore_index=True)
    df.to_csv(HERE / "out" / "t29_weekly_sweep.csv", index=False)
    P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]
    out, pool = [], []
    for p, a_, b_ in P:
        x = df[(df.week >= a_) & (df.week < b_)].R
        pool.append(x)
        out.append(f"{p} n{len(x):5d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean()*100:.0f}%")
    x = pd.concat(pool)
    print("alle trades: " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
    print(f"mediane RR {df.rr.median():.2f}, mediane kosten {df.costR.median():.3f}R, bruto gem {(df.R + df.costR).mean():+.3f}R")
    print("short (PWH-sweep):", round(df[df.dir == -1].R.mean(), 3), " long (PWL-sweep):", round(df[df.dir == 1].R.mean(), 3))
