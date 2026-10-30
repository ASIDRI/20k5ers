"""Test 25: breakaway or not (video 11) on the confirmed trades of test 24.

    python research/strategy/t25_breakaway.py

breakaway = a daily candle inside the leg (start to end) with a body of at least 1 daily ATR that closes beyond the
previous swing high (the highest high of the 40 days before the leg start; mirror for shorts).
Rule: (breakaway and the reaction low stays inside fib 1) or (no breakaway and the reaction low took fib 1).
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from t17_eval import one_per_dir, pf  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def breakaway(f):
    out = {}
    for sym, g in f.groupby("sym"):
        d = load(sym, "D1")
        t = d.time.values
        o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
        tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
        atr = pd.Series(tr).rolling(14).mean().bfill().values
        for i, r in g.iterrows():
            s = int(np.searchsorted(t, np.datetime64(pd.Timestamp(r.start_t))))
            e = int(np.searchsorted(t, np.datetime64(pd.Timestamp(r.top_t))))
            if s < 41 or e <= s:
                out[i] = False
                continue
            key = h[s - 40:s].max() if r.dir == 1 else l[s - 40:s].min()
            body = (c[s:e + 1] - o[s:e + 1]) * r.dir
            beyond = (c[s:e + 1] - key) * r.dir > 0
            out[i] = bool((beyond & (body >= atr[s:e + 1])).any())
    return pd.Series(out)


if __name__ == "__main__":
    f = pd.concat([pd.read_csv(p) for p in glob.glob(str(HERE / "out" / "t24_*.csv")) if Path(p).stat().st_size > 1])
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["breakaway"] = breakaway(f)
    rules = {"regel video 11": "(breakaway & l_fib <= 1) | (~breakaway & l_fib > 1)",
             "breakaway, reactie binnen 1": "breakaway & l_fib <= 1",
             "geen breakaway, fib 1 genomen": "~breakaway & l_fib > 1",
             "geen breakaway, binnen 1 (vermijden volgens video)": "~breakaway & l_fib <= 1",
             "alle (test 24)": "index == index"}
    for lab, rule in rules.items():
        o = one_per_dir(f.query(rule), "t020")
        for col in ("R_t020", "R_m_top_1"):
            out, pool = [], []
            for p, a, b in P:
                x = o[(o.date >= a) & (o.date < b)][col].dropna()
                pool.append(x)
                out.append(f"{p} n{len(x):4d} {x.mean():+.3f} PF {pf(x):.2f}")
            x = pd.concat(pool)
            print(f"{lab:48} {col:10} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
