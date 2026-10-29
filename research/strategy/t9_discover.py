"""Discovery on test 9 (2015-2020 ONLY): which stop/target and which features known at the entry separate the trades.

    python research/strategy/t9_discover.py [--prefix t9_]
    python research/strategy/t9_discover.py --confirm "R_wick_t27be" "cont & (htf == 1)"   # after the rule is recorded

Without --confirm only trades with a setup date before 2021 are read, so the confirmation period stays unseen.
Numeric features are cut in terciles of the discovery period. Each cell: n, mean R (net), PF.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPLIT = "2021-01-01"
NUM = ["depth", "leg_atr", "leg_days", "retr_days", "wait_bars", "sr_dist", "hour", "body"]
CAT = ["cont", "hl", "lvl", "mn", "htf", "wk_last", "d1_ma", "dir"]


def pf(x):
    x = x.dropna()
    return x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else np.nan


def cell(x):
    x = x.dropna()
    return f"n {len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f}" if len(x) else "-"


def load(prefix):
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{prefix}*.csv")) if p.stat().st_size > 1])
    return f[f.result == "gevuld"].copy()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="t9_")
    ap.add_argument("--confirm", nargs=2, metavar=("COLUMN", "RULE"))
    ap.add_argument("--period", default="2021-2025", choices=["2021-2025", "2005-2014"])
    a = ap.parse_args()
    f = load(a.prefix)
    cols = [c for c in f.columns if c.startswith("R_")]
    if a.confirm:
        col, rule = a.confirm
        lo, hi = ("2021-01-01", "2026-01-01") if a.period == "2021-2025" else ("2005-01-01", "2015-01-01")
        for lab, g in (("discovery 2015-20", f[f.date < SPLIT]), (a.period, f[(f.date >= lo) & (f.date < hi)])):
            s = g.query(rule)
            print(f"{lab}: alles {cell(g[col])} | regel {cell(s[col])} | winnend {(s[col] > 0).mean()*100:.0f}% | "
                  f"per jaar {s.groupby(s.date.str[:4])[col].sum().round(1).to_dict()}")
        raise SystemExit
    f = f[f.date < SPLIT]
    print(f"DISCOVERY 2015-2020: {len(f)} trades\n\n--- stop/target")
    for c in cols:
        print(f"{c:15} {cell(f[c])}")
    for c in NUM:
        f[c + "_q"] = pd.qcut(f[c], 3, labels=["laag", "mid", "hoog"], duplicates="drop")
        edges = f[c].quantile([1 / 3, 2 / 3]).round(2).tolist()
        print(f"\n--- {c} (grenzen {edges})")
        for b, g in f.groupby(c + "_q", observed=True):
            print(f"  {b:5} " + " | ".join(f"{k[2:]}: {cell(g[k])}" for k in cols if k.endswith(("t0", "t27be"))))
    for c in CAT:
        print(f"\n--- {c}")
        for b, g in f.groupby(c):
            print(f"  {str(b):5} " + " | ".join(f"{k[2:]}: {cell(g[k])}" for k in cols if k.endswith(("t0", "t27be"))))
