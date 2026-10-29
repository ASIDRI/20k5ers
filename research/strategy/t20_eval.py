"""Test 20 evaluation: one position per direction per pair; the pre-registered rule and the parts of it.

    python research/strategy/t20_eval.py [--prefix t20_]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t17_eval import one_per_dir, pf  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]
RULES = {"regel (weekstructuur mee + boven/onder week/maand-S/R)": "wk_struct == 1 & htf_sup",
         "alleen weekstructuur mee": "wk_struct == 1", "alleen S/R": "htf_sup", "alle grote poten": "index == index"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="t20_")
    a = ap.parse_args()
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{a.prefix}*.csv")) if p.stat().st_size > 1])
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["htf_sup"] = f.htf_sup.astype(str).str.lower().eq("true")
    for lab, rule in RULES.items():
        o = one_per_dir(f.query(rule), "t020")
        print(f"\n### {lab}: {len(o)} trades ({len(o) / 21 / f.sym.nunique():.1f} per paar per jaar)")
        for col in ("R_t020", "R_t027", "R_t065", "R_m_top_1"):
            out, pool = [], []
            for p, s, e in P:
                x = o[(o.date >= s) & (o.date < e)][col].dropna()
                pool.append(x)
                out.append(f"{p} n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean()*100:.0f}%")
            x = pd.concat(pool)
            print(f"  {col:10} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
