"""Setup after a fake weekly BoS (trader 2026-11-04, USDJPY Sep-Oct 2026): the attempt week closes beyond the weekly
BoS line against the trend, the next week closes back. Then price moves on away from the line, pulls back to it, and a
daily candle tests the line with a wick and closes back on the trend side: entry at that close.

    python research/strategy/fake_bos_retest_study.py

Point-in-time: the fake is known at the close of the reclaim week; daily candles after that only. In the short view
(longs on negated prices, as in trader_strategy.py). Stop beyond the pullback extreme + SL_ATR daily ATR. Exits: the
engine's ladder on the move since the reclaim (f1 = the line, f0 = the extreme since the reclaim) or a fixed 2R.
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]

AWAY = 1.0      # price first moves at least this many daily ATR away from the line
TOUCH = 0.25    # the test candle's wick comes within this many daily ATR of the line (or through it)
WEEKS = 10      # the pullback must come within this many weeks after the reclaim
SL_ATR = 0.5    # stop beyond the pullback extreme (last 5 days) + this many daily ATR


def run(sym, sl_atr=SL_ATR):
    import trader_strategy as T
    from setup_study import load
    from candle_avail import complete_times
    T.apply_profile(sym)
    d, w = load(sym, "D1"), load(sym, "W1")
    out = []
    for dirn in (-1, 1):
        sg = 1 if dirn == -1 else -1

        def px(df):
            o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
            return (o, h, l, c) if sg == 1 else (-o, -l, -h, -c)
        st, ev, wa, fakes = T.weekly_structure(*px(w))
        wdone = complete_times(w["time"], "W1").values
        ddone = complete_times(d["time"], "D1").values
        o, h, l, c = px(d)
        a = T.atr(h, l, c)
        days = [T.day_label(x) for x in d.time]
        for i0, i1, dd, line in fakes:
            if dd != 1 or st[i1] != -1:  # an attempt against a bearish (in this view) trend that failed
                continue
            k0 = int(np.searchsorted(ddone, wdone[i1], "right"))  # first day after the reclaim week closed
            k1 = min(len(c), int(np.searchsorted(ddone, wdone[min(i1 + WEEKS, len(wdone) - 1)], "right")))
            away = False
            for k in range(k0, k1):
                if c[k] > line:  # a daily close back beyond the line: the setup is off
                    break
                if not away:
                    away = line - np.min(l[k0:k + 1]) >= AWAY * a[k]
                    continue
                if h[k] >= line - TOUCH * a[k - 1] and c[k] < line and h[k] - max(o[k], c[k]) >= 0.1 * a[k - 1]:
                    if not "2016-01-01" <= days[k] < "2026-01-01":
                        break
                    e = c[k]
                    sl = np.max(h[k - 4:k + 1]) + sl_atr * a[k]
                    risk = sl - e
                    f0 = float(np.min(l[k0:k + 1]))
                    rng = line - f0
                    cost = T.cost_price(sym, abs(e))
                    mres = T.manage(h, l, k, e, sl, f0, rng, T.BE * a[k])
                    r_lad = (mres["pnl"] - cost) / risk
                    r2 = None
                    for i in range(k + 1, len(c)):
                        if h[i] >= sl:
                            r2 = -1.0; break
                        if l[i] <= e - 2 * risk:
                            r2 = 2.0; break
                    r2 = (r2 if r2 is not None else (e - c[-1]) / risk) - cost / risk
                    out.append(dict(sym=sym, dir=dirn, fake_week=T.week_label(w.time.iloc[i0]), entry_day=days[k],
                                    line=line * sg, entry=e * sg, sl=sl * sg, R_ladder=round(r_lad, 2), R_2R=round(r2, 2)))
                    break
    return out


def main():
    syms = [f[6:-4] for f in sorted(os.listdir(HERE / "out")) if f.startswith("v2n37_")]
    for sl_atr in (0.1, 0.5, 1.0):
        with ProcessPoolExecutor(4) as ex:
            res = [t for ts in ex.map(run, syms, [sl_atr] * len(syms)) for t in ts]
        df = pd.DataFrame(res)
        print(f"\nstop = pullback extreme + {sl_atr} ATR: {len(df)} trades")
        for col in ("R_ladder", "R_2R"):
            r = df[col]
            h1, h2 = df[df.entry_day < "2021"][col].sum(), df[df.entry_day >= "2021"][col].sum()
            print(f"  {col}: win {np.mean(r > 0):.0%}, R {r.sum():+.1f} (2016-20 {h1:+.1f}, 2021-25 {h2:+.1f}), "
                  f"gem {r.mean():+.3f}, t {r.mean() / r.std() * np.sqrt(len(r)):.2f}")
        if sl_atr == 0.5:
            print(df.sort_values("entry_day").to_string(index=False))


if __name__ == "__main__":
    main()
