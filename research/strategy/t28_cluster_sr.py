"""Test 28: the rule of tests 20/24 with cluster S/R levels (sr_quality.py: the only definition that beat random).

    python research/strategy/t28_cluster_sr.py
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from sr_quality import methods  # noqa: E402
from t17_eval import one_per_dir, pf  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def with_cluster(patterns):
    fs = [pd.read_csv(p) for pat in patterns for p in glob.glob(str(HERE / "out" / pat)) if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["htf_sup"] = f.htf_sup.astype(str).str.lower().eq("true")
    col = {}
    for sym, g in f.groupby("sym"):
        fn = methods(sym)[0]["cluster"]
        for i, r in g.iterrows():
            lv = fn(pd.Timestamp(r.fill, tz="UTC"))
            lo, hi = sorted([r.b1, r.entry])
            col[i] = any(lo <= p <= hi for p in lv)
    f["htf_sup_c"] = pd.Series(col)
    return f


if __name__ == "__main__":
    for lab, pats, cl in (("(a) test 20", ["t20_*.csv", "t20x_*.csv"], "R_m_top_1"), ("(b) test 24", ["t24_*.csv"], "R_t020")):
        f = with_cluster(pats)
        print(lab)
        for rl, rule in (("oude S/R + week", "wk_struct == 1 & htf_sup"), ("CLUSTER S/R + week", "wk_struct == 1 & htf_sup_c"),
                         ("cluster S/R alleen", "htf_sup_c"), ("geen cluster in de poot", "~htf_sup_c")):
            o = one_per_dir(f.query(rule), "t020")
            out, pool = [], []
            for p, a, b in P:
                x = o[(o.date >= a) & (o.date < b)][cl].dropna()
                pool.append(x)
                out.append(f"{p} n{len(x):4d} {x.mean():+.3f} PF {pf(x):.2f}")
            x = pd.concat(pool)
            print(f"  {rl:24} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
