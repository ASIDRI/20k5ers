"""Test 27: trade only when the strategy's own last N closed trades summed to >= 0R (point in time).

    python research/strategy/t27_equity_filter.py [--n 20]
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t17_eval import one_per_dir, pf  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def load(patterns, rule):
    fs = [pd.read_csv(p) for pat in patterns for p in glob.glob(str(HERE / "out" / pat)) if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["htf_sup"] = f.htf_sup.astype(str).str.lower().eq("true")
    return one_per_dir(f.query(rule), "t020").sort_values("fill").reset_index(drop=True)


def equity_filter(o, col, n):
    """keep[i]: the last n trades closed before trade i's fill summed to >= 0 (fewer than n closed: keep)."""
    closed = o[o.x_t020.notna()].sort_values("x_t020")
    keep = []
    for _, t in o.iterrows():
        prev = closed[closed.x_t020 < t.fill][col].dropna().tail(n)
        keep.append(len(prev) < n or prev.sum() >= 0)
    return o[np.array(keep)]


def report(o, col, lab):
    out, pool = [], []
    for p, a, b in P:
        x = o[(o.date >= a) & (o.date < b)][col].dropna()
        pool.append(x)
        out.append(f"{p} n{len(x):4d} {x.mean():+.3f} PF {pf(x):.2f}")
    x = pd.concat(pool)
    print(f"  {lab:24} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()
    for lab, pats, col in (("(a) test 20 regel", ["t20_*.csv", "t20x_*.csv"], "R_m_top_1"),
                           ("(b) test 24 + regel", ["t24_*.csv"], "R_t020")):
        o = load(pats, "wk_struct == 1 & htf_sup")
        print(lab)
        report(o, col, "zonder filter")
        report(equity_filter(o, col, a.n), col, f"met filter (laatste {a.n})")
