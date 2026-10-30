"""Neely test N1 evaluation: one position per direction per symbol, per setup and timeframe; the decisive rule and parts.
Same periods, bar and one-position rule as tests 17-33 (t17_eval).

    python research/neely/neely_eval.py [--prefix n1_]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "strategy"))
from t17_eval import one_per_dir, pf, P  # noqa: E402

RULES = {"beslissend (htf mee + labels)": "htf == 1 & lab_ok",
         "alleen htf mee": "htf == 1", "alleen labels": "lab_ok", "alle patronen": "index == index",
         "beslissend, kosten <= 0,1R": "htf == 1 & lab_ok & R_cost <= 0.1"}


def line(o, col):
    out, pool = [], []
    for lab, s, e in P:
        y = o[(o.date >= s) & (o.date < e)][col].dropna()
        pool.append(y)
        out.append(f"{lab} n{len(y):5d} {y.mean():+.3f}R PF {pf(y):.2f} win {(y > 0).mean() * 100:.0f}%")
    y = pd.concat(pool)
    return " | ".join(out) + f" | t {y.mean() / y.std() * np.sqrt(len(y)):.2f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="n1_")
    a = ap.parse_args()
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{a.prefix}*.csv")) if p.stat().st_size > 1])
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["lab_ok"] = f.lab_ok.astype(str).str.lower().eq("true")
    for (tf, setup), g in f.groupby(["tf", "setup"]):
        print(f"\n## Setup {setup} op {tf} ({g.sym.nunique()} instrumenten)")
        for lab, rule in RULES.items():
            o = one_per_dir(g.query(rule), "t1")
            print(f"### {lab}: {len(o)} trades")
            for col in ("R_t1", "R_t2", "R_m"):
                print(f"  {col:5} " + line(o, col))
