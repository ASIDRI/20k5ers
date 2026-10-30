"""Test 21: choose one configuration of test 20 on half the instruments (even positions in alphabetical order) and
2005-2018 only; then validate that single configuration on the other half (2005-2018) and on all instruments
2019-2025. One position per direction per pair.

    python research/strategy/t21_select.py            # selection (train only) + validation of the winner
"""
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t17_eval import one_per_dir, pf  # noqa: E402

FILTERS = {"geen": "index == index", "week": "wk_struct == 1", "S/R": "htf_sup", "week+S/R": "wk_struct == 1 & htf_sup"}
EXITS = ["t020", "t027", "t065", "m_top_1"]
MIN_N = 150


def stats(x):
    x = x.dropna()
    return len(x), x.mean() if len(x) else np.nan, pf(x) if len(x) else np.nan


def load_cfg(cfg):
    fs = [pd.read_csv(p) for p in glob.glob(str(HERE / "out" / f"g21_{cfg}_*.csv")) if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["htf_sup"] = f.htf_sup.astype(str).str.lower().eq("true")
    return f


if __name__ == "__main__":
    cfgs = sorted({re.match(r"g21_(r[\d.]+_l[\d.]+_b[\d.]+-[\d.]+)_", Path(p).name).group(1)
                   for p in glob.glob(str(HERE / "out" / "g21_*.csv"))})
    syms = sorted({Path(p).name.split("_", 4)[-1][:-4] for p in glob.glob(str(HERE / "out" / f"g21_{cfgs[0]}_*.csv"))})
    A, B = set(syms[0::2]), set(syms[1::2])
    print(f"{len(cfgs)} configuraties, {len(syms)} instrumenten; A (kiezen) = {sorted(A)}")
    res, data = [], {}
    for cfg in cfgs:
        f = load_cfg(cfg)
        data[cfg] = f
        tr = f[f.sym.isin(A) & (f.date < "2019")]
        for fl, rule in FILTERS.items():
            o = one_per_dir(tr.query(rule), "t020")
            for sl in ("R_", "R_w_"):
                for ex in EXITS:
                    n, m, p = stats(o[f"{sl}{ex}"])
                    res.append(dict(cfg=cfg, filter=fl, stop="0.1 ATR" if sl == "R_" else "0.5 ATR", exit=ex,
                                    col=f"{sl}{ex}", n=n, mean=m, pf=p))
    r = pd.DataFrame(res)
    ok = r[r.n >= MIN_N].sort_values("mean", ascending=False)
    pd.set_option("display.width", 200)
    print(f"\nTOP 15 op de trainingsset (A, 2005-2018, >= {MIN_N} trades):")
    print(ok.head(15).round(3).to_string(index=False))
    print(f"\naandeel combinaties met gemiddelde > 0: {(ok['mean'] > 0).mean()*100:.0f}% van {len(ok)}")
    best = ok.iloc[0]
    f = data[best.cfg]
    rule = FILTERS[best["filter"]]
    print(f"\nGEKOZEN: {best.cfg}, filter {best['filter']}, stop {best.stop}, uitstap {best.exit}")
    pool = []
    for lab, g in (("A 2005-2018 (training)", f[f.sym.isin(A) & (f.date < "2019")]),
                   ("B 2005-2018 (validatie)", f[f.sym.isin(B) & (f.date < "2019")]),
                   ("alle 2019-2025 (validatie)", f[f.date >= "2019"])):
        o = one_per_dir(g.query(rule), "t020")
        x = o[best.col].dropna()
        if "validatie" in lab:
            pool.append(x)
        print(f"  {lab:28} n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} winnend {(x > 0).mean()*100:.0f}% "
              f"t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
    x = pd.concat(pool)
    print(f"  validatie samen              n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} "
          f"t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
    r.to_csv(HERE / "out" / "t21_grid_results.csv", index=False)
