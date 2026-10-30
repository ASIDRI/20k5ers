"""Test E1 evaluation: one position per direction per symbol; decisive rule and parts (same bar as tests 17-33).

    python research/ew/ew_eval.py [--prefix e1_]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "strategy"))
from t17_eval import one_per_dir, pf, P  # noqa: E402

RULES = {1: {"beslissend: dag mee, week niet tegen": "d1 == 1 & w1 >= 0", "dag mee": "d1 == 1",
             "week mee": "w1 == 1", "dag en week mee": "d1 == 1 & w1 == 1", "zonder dag/week": "index == index"},
         2: {"alle (beslissend)": "index == index", "dag mee": "d1 == 1", "dag niet tegen": "d1 >= 0"}}
COLS = {1: ("R_m", "R_t1", "R_t2", "R_tight_m"), 2: ("R_m", "R_t1")}


def line(o, col):
    out, pool = [], []
    for lab, s, e in P:
        y = o[(o.date >= s) & (o.date < e)][col].dropna()
        pool.append(y)
        out.append(f"{lab} n{len(y):4d} {y.mean():+.3f}R PF {pf(y):.2f} win {(y > 0).mean() * 100:.0f}%")
    y = pd.concat(pool)
    return " | ".join(out) + f" | t {y.mean() / y.std() * np.sqrt(len(y)):.2f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="e1_")
    a = ap.parse_args()
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{a.prefix}*.csv")) if p.stat().st_size > 1])
    f = f[f.result == "gevuld"].reset_index(drop=True)
    for setup in (1, 2):
        g = f[f.setup == setup]
        print(f"\n## Setup {setup} ({g.sym.nunique()} instrumenten)")
        for lab, rule in RULES[setup].items():
            o = one_per_dir(g.query(rule), "t1")
            print(f"### {lab}: {len(o)} trades")
            for col in COLS[setup]:
                print(f"  {col:9} " + line(o, col))
