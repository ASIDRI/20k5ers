"""Test 13 discovery (2015-2020 ONLY): take the trader's rules out one at a time, and see which features separate.

    python research/strategy/t13_discover.py --tf D1 [--col R_w_t1]
    python research/strategy/t13_discover.py --tf D1 --confirm R_w_t1 "broke & pocket & ..." [--period 2005-2014]

Without --confirm only setups dated before 2021 are read. Numeric features in terciles of the discovery period.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPLIT = "2021-01-01"
NUM = ["rng_atr", "leg_bars", "speed", "s_fib_w", "fill_bars"]
CAT = ["broke", "pocket", "htf", "reanchored", "wk_trend", "wk_phase", "wk_ok", "mn", "wk", "ma", "dir"]
# the trader's rules (test 11) and each one taken out
ABLATE = {"test 11 (alle regels)": "broke & pocket",
          "zonder pocket-eis": "broke",
          "zonder break-eis": "index == index",
          "zonder herverankeren": "broke & pocket & ~reanchored",
          "+ maand/week S/R in pocket": "broke & pocket & htf"}


def pf(x):
    x = x.dropna()
    return x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else np.nan


def cell(x):
    x = x.dropna()
    return f"n {len(x):5d} {x.mean():+.3f}R PF {pf(x):.2f}" if len(x) else "-"


def load(tf):
    fs = [pd.read_csv(p) for p in sorted((HERE / "out").glob(f"t13{tf[0].lower()}_*.csv")) if p.stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].copy().reset_index(drop=True)
    for b in ("broke", "pocket", "htf", "reanchored", "wk_ok"):
        f[b] = f[b].astype(str).str.lower().eq("true")
    return f


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--col", default="R_w_t1")
    ap.add_argument("--confirm", nargs=2, metavar=("COLUMN", "RULE"))
    ap.add_argument("--period", default="2021-2025", choices=["2021-2025", "2005-2014"])
    a = ap.parse_args()
    f = load(a.tf)
    if a.confirm:
        col, rule = a.confirm
        lo, hi = ("2021-01-01", "2026-01-01") if a.period == "2021-2025" else ("2005-01-01", "2015-01-01")
        for lab, g in (("discovery 2015-20", f[(f.date >= "2015-01-01") & (f.date < SPLIT)]),
                       (a.period, f[(f.date >= lo) & (f.date < hi)])):
            s = g.query(rule)
            x = s[col].dropna()
            print(f"{lab}: alles {cell(g[col])} | regel {cell(x)} | winnend {(x > 0).mean()*100:.0f}% | "
                  f"t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
        raise SystemExit
    f = f[(f.date >= "2015-01-01") & (f.date < SPLIT)]
    cols = [c for c in f.columns if c.startswith("R_")]
    print(f"DISCOVERY 2015-2020 {a.tf}: {len(f)} trades\n\n--- regels uit/aan ({a.col}; daarnaast R_w_t027, R_x_t1)")
    for lab, rule in ABLATE.items():
        g = f.query(rule)
        print(f"  {lab:28} {cell(g[a.col])} | t027 {cell(g['R_w_t027'])} | x_t1 {cell(g['R_x_t1'])}")
    print("\n--- stop/doel (test 11-regels)")
    g = f.query("broke & pocket")
    for c in cols:
        print(f"  {c:12} {cell(g[c])}")
    base = f.query("broke")
    print(f"\n--- kenmerken binnen 'broke' ({a.col})")
    for c in NUM:
        q = pd.qcut(base[c], 3, duplicates="drop")
        for b, g in base.groupby(q, observed=True):
            print(f"  {c:10} {str(b):22} {cell(g[a.col])}")
    for c in CAT:
        for b, g in base.groupby(c):
            print(f"  {c:10} {str(b):22} {cell(g[a.col])}")
