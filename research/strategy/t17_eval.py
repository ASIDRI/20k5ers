"""Test 17 evaluation: NZDCAD break & retest (test11 --reset-expiry), one position per direction at a time.

    python research/strategy/t17_eval.py --prefix t17_ --sym NZDCAD [--others]

A setup is taken only when no earlier taken trade in the same direction (same symbol) is still open on its fill day
(open until the exit of the decisive target). --others: the same rule on every other pair in the files (out of sample
across instruments).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def pf(x):
    return x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else np.nan


def one_per_dir(f, tp):
    keep, open_until = [], {}
    for k, t in f.sort_values(["fill", "date"]).iterrows():
        key = (t.sym, t.dir)
        if key in open_until and (open_until[key] is None or open_until[key] >= t.fill):
            continue
        keep.append(k)
        x = t[f"x_{tp}"]
        open_until[key] = x if isinstance(x, str) else None
    return f.loc[keep]


def report(f, cols, label):
    print(f"\n### {label}")
    for col in cols:
        out, pool = [], []
        for lab, a, b in P:
            x = f[(f.date >= a) & (f.date < b)][col].dropna()
            pool.append(x)
            out.append(f"{lab} n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean()*100:.0f}%")
        x = pd.concat(pool)
        print(f"  {col:9} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="t17_")
    ap.add_argument("--sym", default="NZDCAD")
    ap.add_argument("--tp", default="t020")
    ap.add_argument("--others", action="store_true")
    a = ap.parse_args()
    fs = [pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{a.prefix}*.csv")) if p.stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"]
    cols = [f"R_{a.tp}", "R_t027", "R_t065", "R_t1", "R_t1_be"]
    g = f[f.sym == a.sym]
    report(one_per_dir(g, a.tp), cols, f"{a.sym}: één positie per richting (beslissend: R_{a.tp})")
    report(g, cols, f"{a.sym}: alle setups")
    if a.others:
        o = one_per_dir(f[f.sym != a.sym], a.tp)
        report(o, cols, f"andere {o.sym.nunique()} paren samen, één positie per richting per paar")
        print("\n  per paar (R_%s, alle jaren):" % a.tp)
        print(o.groupby("sym")[f"R_{a.tp}"].agg(["size", "mean"]).round(3).sort_values("mean").to_string())
