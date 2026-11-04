"""Daily liquidity grabs (trader 2026-11-04): a daily swing high H1, a lower daily swing high H2, later a daily candle
trades above H2 and closes back below it (the grab, the high stays below H1). Short at the close of the grab (if it
is red) or of the first red candle within ENTRY_WAIT days; stop above the grab high + buffer; exit at a fixed R target
or the stop. Split by the weekly structure at the entry (point-in-time): continuation (the grab is against the weekly
trend's pullback: short in a bearish weekly structure) or counter-trend. Longs mirrored (negated prices).

    python research/strategy/daily_lq_study.py EURUSD [--grid]
"""
import argparse
import itertools
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import trader_strategy as T  # noqa: E402
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402


def trades(sym, N=2, GAP=3, WAIT=3, BUF=0.1, TGT=2.0, LOOK=60, start="2015-01-01", end="2026-01-01"):
    T.apply_profile(sym)
    d, w = load(sym, "D1"), load(sym, "W1")
    ddone, wdone = complete_times(d["time"], "D1").values, complete_times(w["time"], "W1").values
    days = np.array([T.day_label(x) for x in d.time])
    out = []
    for dirn in (-1, 1):
        sg = 1 if dirn == -1 else -1

        def px(df):
            o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
            return (o, h, l, c) if sg == 1 else (-o, -l, -h, -c)
        st = T.weekly_structure(*px(w))[0]
        o, h, l, c = px(d)
        a = T.atr(h, l, c)
        sh = [i for i in range(N, len(h) - N) if h[i] == np.max(h[i - N:i + N + 1])]  # known at i + N
        busy = -1
        for b, i2 in enumerate(sh):
            prev = [i for i in sh[:b] if 0 < i2 - i <= LOOK and h[i] > h[i2] and np.max(h[i + 1:i2]) <= h[i]]
            if not prev:
                continue
            i1 = prev[-1]
            for g in range(i2 + N + 1, min(len(c), i2 + LOOK)):
                if g - i2 < GAP:
                    continue
                if c[g - 1] > h[i2] or np.max(h[i2 + 1:g]) > h[i2]:  # already broken or grabbed before
                    break
                if not (h[g] > h[i2] and c[g] < h[i2] and h[g] < h[i1]):
                    continue
                k = next((q for q in range(g, min(len(c), g + WAIT + 1)) if c[q] < o[q] and c[q] < h[i2]
                          and np.max(h[g:q + 1]) < h[i1] and np.all(c[g:q + 1] < h[i2])), None)
                if k is None or k <= busy or not (start <= days[k] < end):
                    break
                e = c[k]
                sl = np.max(h[g:k + 1]) + BUF * a[k]
                risk = sl - e
                if risk <= 0:
                    break
                wi = int(np.searchsorted(wdone, ddone[k], "right")) - 1
                ctx = "continuation" if st[wi] == -1 else ("tegen trend" if st[wi] == 1 else "geen")
                r, ex = None, None
                for q in range(k + 1, len(c)):
                    if h[q] >= sl:
                        r, ex = -1.0, q; break
                    if l[q] <= e - TGT * risk:
                        r, ex = TGT, q; break
                if r is None:
                    r, ex = (e - c[-1]) / risk, len(c) - 1
                r -= T.cost_price(sym, abs(e)) / risk
                out.append(dict(sym=sym, dir=dirn, day=days[k], ctx=ctx, entry=e * sg, sl=sl * sg,
                                H1=h[i1] * sg, H2=h[i2] * sg, R=round(r, 2)))
                busy = ex
                break
    return pd.DataFrame(out)


def summary(df, label):
    for ctx in ("continuation", "tegen trend"):
        for dn, dv in (("shorts", -1), ("longs", 1)):
            x = df[(df.ctx == ctx) & (df.dir == dv)]
            if len(x) < 2:
                print(f"  {label:28s} {ctx:12s} {dn:6s}: {len(x)} trades"); continue
            r = x.R
            print(f"  {label:28s} {ctx:12s} {dn:6s}: {len(r):3d} tr win {np.mean(r > 0):4.0%} R {r.sum():+6.1f} "
                  f"gem {r.mean():+.2f} (15-19 {x[x.day < '2020'].R.sum():+5.1f}, 20-25 {x[x.day >= '2020'].R.sum():+5.1f}) "
                  f"t {r.mean() / r.std() * np.sqrt(len(r)):+.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sym")
    ap.add_argument("--grid", action="store_true")
    a = ap.parse_args()
    if not a.grid:
        summary(trades(a.sym), "standaard")
        return
    for N, GAP, BUF, TGT in itertools.product((2, 3), (3, 10), (0.1, 0.5), (2.0, 3.0)):
        summary(trades(a.sym, N=N, GAP=GAP, BUF=BUF, TGT=TGT), f"N{N} gap{GAP} buf{BUF} tgt{TGT}")


if __name__ == "__main__":
    main()
