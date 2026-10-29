"""Test 18 evaluation: every exit / management variant, discovery 2015-2020 only unless --confirm.

    python research/strategy/t18_eval.py --tf D1
    python research/strategy/t18_eval.py --tf D1 --confirm R_m_0.2_top_trail [--one]

--one: one position per direction per pair (open until the exit of the full -0.2 target, as test 17).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from t17_eval import one_per_dir, pf

HERE = Path(__file__).resolve().parent
P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def cell(x):
    x = x.dropna()
    return f"n{len(x):5d} {x.mean():+.3f}R PF {pf(x):.2f}" if len(x) else "-"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", default="D1")
    ap.add_argument("--confirm", default=None)
    ap.add_argument("--one", action="store_true")
    a = ap.parse_args()
    fs = [pd.read_csv(p) for p in sorted((HERE / "out").glob(f"t18{a.tf[0].lower()}_*.csv")) if p.stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    if a.one:
        f = one_per_dir(f, "t020")
    if a.confirm:
        pool = []
        for lab, s, e in P:
            x = f[(f.date >= s) & (f.date < e)][a.confirm].dropna()
            print(f"{lab}: {cell(x)} winnend {(x > 0).mean()*100:.0f}%")
            if lab != "2015-20":
                pool.append(x)
        x = pd.concat(pool)
        print(f"2005-14 + 2021-25 samen: {cell(x)} t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
        raise SystemExit
    g = f[(f.date >= "2015") & (f.date < "2021")]
    cols = sorted([c for c in g.columns if c.startswith("R_") and c != "R_cost"], key=lambda c: -g[c].mean())
    print(f"DISCOVERY 2015-2020 {a.tf}{' (één positie per richting)' if a.one else ''}: {len(g)} trades")
    for c in cols:
        print(f"  {c:22} {cell(g[c])}")
