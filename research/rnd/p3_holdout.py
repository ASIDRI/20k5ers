"""Phase P3 (pre-registered, commit ec6f967): the three per-pair rules once on 2005-2014 (stored D1 data).

    python research/rnd/p3_holdout.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "strategy")]
import systematic as S  # noqa: E402

RULES = {"R1 AUDNZD range faden (55 d)": ("AUDNZD", lambda o: -o["donch55"]),
         "R2 AUDNZD tegen 12-mnd-trend": ("AUDNZD", lambda o: -o["mom252"]),
         "R3 USDJPY 3-mnd-momentum": ("USDJPY", lambda o: o["mom63"])}

if __name__ == "__main__":
    orig = S.positions
    for name, (sym, f) in RULES.items():
        S.positions = lambda d, f=f: {"r": f(orig(d))}
        x = S.run("2005-01-01", "2015-01-01", [sym])["r"][sym]
        sh = x.mean() * 252 / (x.std() * np.sqrt(252))
        yrs = x.groupby(x.index.year).sum()
        ok = sh >= 0.3 and (yrs > 0).sum() >= 6
        print(f"{name}: Sharpe {sh:+.2f}, jaren winst {(yrs > 0).sum()}/{len(yrs)} -> {'GESLAAGD' if ok else 'VERWORPEN'}")
        print("   per jaar (%):", (yrs * 100).round(1).to_dict())
    S.positions = orig
