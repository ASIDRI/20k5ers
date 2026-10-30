"""Neely test N2 evaluation (EURUSD counter): one position per direction; decisive cx >= 2 & op_tijd, R_t1.

    python research/neely/n2_eval.py
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "strategy"))
from t17_eval import one_per_dir  # noqa: E402
from neely_eval import line  # noqa: E402

RULES = {"beslissend (cx >= 2, op tijd)": "cx >= 2 & op_tijd", "cx >= 2, ook te laat": "cx >= 2",
         "cx 1, op tijd": "cx == 1 & op_tijd", "cx >= 3, op tijd": "cx >= 3 & op_tijd"}

if __name__ == "__main__":
    for p in sorted((HERE / "out").glob("n2_*_EURUSD.csv")):
        f = pd.read_csv(p)
        f = f[f.result == "gevuld"].reset_index(drop=True)
        f["op_tijd"] = f.op_tijd.astype(str).str.lower().eq("true")
        print(f"\n## {p.stem}")
        for lab, rule in RULES.items():
            o = one_per_dir(f.query(rule), "t1")
            print(f"  {lab:30} {len(o):5d} trades | " + line(o, "R_t1"))
        o = one_per_dir(f.query("cx >= 2 & op_tijd"), "t1")
        print("  per patroon (beslissend):", o.groupby("name").R_t1.agg(["size", "mean"]).round(3).to_dict("index"))
