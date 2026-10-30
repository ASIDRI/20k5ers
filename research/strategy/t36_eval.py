"""Test 36 evaluation: one position per direction per instrument; the pre-registered rule and its parts.

    python research/strategy/t36_eval.py [--prefix t36_]
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
RULES = {"test 45: basis-zone + dagbevestiging + weekbias": "hi_bias == 1",
         "basis-zone + dagbevestiging + weekbias + grote BoS": "hi_bias == 1 & bos",
"test 44: BoS + confluentie-instap + weekbias": "bos & hi_bias == 1",
         "BoS + confluentie-instap": "bos", "BoS + confluentie + weekbias + fib 1 op HTF-S/R": "bos & hi_bias == 1 & origin_sr",
         "BoS + confluentie + fib 1 op HTF-S/R": "bos & origin_sr",
"test 43: BoS + weekly S/R + weekbias, zonder week-sweep op de top": "bos & wk_sr & hi_bias == 1 & ~w_rej",
         "BoS + weekly S/R, zonder week-sweep": "bos & wk_sr & ~w_rej", "met week-sweep op de top": "bos & wk_sr & w_rej",
"test 41: dagpoot + BoS + weekly S/R in de zone (screenshots)": "bos & wk_sr",
         "test 41 + weekbias": "bos & wk_sr & hi_bias == 1", "BoS zonder weekly S/R": "bos & ~wk_sr",
"test 40: piramide (S/R + maand- en weekstructuur + fib + OB + dagbevestiging)": "htf_sup & hi_struct == 1 & bos & has_ob",
         "piramide zonder maandstructuur": "htf_sup & bos & has_ob", "piramide zonder OB": "htf_sup & hi_struct == 1 & bos",
"test 39: weekbias + structuurbreuk (dag)": "hi_bias == 1 & bos",
         "weekbias + breuk + OB": "hi_bias == 1 & bos & has_ob", "weekbias + breuk + S/R": "hi_bias == 1 & bos & htf_sup",
         "weekbias + breuk, omkeer": "hi_bias == 1 & shift", "weekbias + breuk, voortzetting": "hi_bias == 1 & bos & ~shift",
         "weekbias, alle poten": "hi_bias == 1", "tegen de weekbias, breuk": "hi_bias == -1 & bos",
"test 37: OB + structuurbreuk (video 4)": "has_ob & bos", "OB + breuk, omkeer (inv. H&S)": "has_ob & shift",
         "OB + breuk, voortzetting (N)": "has_ob & bos & ~shift", "OB + breuk + S/R": "has_ob & bos & htf_sup",
         "structuurbreuk zonder OB-eis": "bos", "OB zonder breuk": "has_ob & ~bos",
"regel: OB in golden pocket + hogere structuur + S/R": "has_ob & hi_struct == 1 & htf_sup",
         "OB + hogere structuur": "has_ob & hi_struct == 1", "OB + S/R": "has_ob & htf_sup",
         "OB + hogere structuur + maandtrend": "has_ob & hi_struct == 1 & m_ma == 1",
         "alleen OB": "has_ob", "zonder OB (limiet 0,618) + structuur + S/R": "~has_ob & hi_struct == 1 & htf_sup",
         "zonder OB": "~has_ob", "alle": "index == index"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="t36_")
    a = ap.parse_args()
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{a.prefix}*.csv")) if p.stat().st_size > 1])
    f = f[f.result == "gevuld"].reset_index(drop=True)
    for k in ("htf_sup", "has_ob", "bos", "shift", "wk_sr", "w_rej", "origin_sr"):
        if k not in f:
            f[k] = False
        f[k] = f[k].astype(str).str.lower().eq("true")
    for lab, rule in RULES.items():
        o = one_per_dir(f.query(rule), "t065")
        print(f"\n### {lab}: {len(o)} trades ({len(o) / 21:.0f} per jaar, {len(o) / 21 / 52:.1f} per week)")
        for col in ("R_m", "R_t020", "R_t025"):
            out, pool = [], []
            for p, s, e in P:
                x = o[(o.date >= s) & (o.date < e)][col].dropna()
                pool.append(x)
                out.append(f"{p} n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean()*100:.0f}%")
            x = pd.concat(pool)
            print(f"  {col:7} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
