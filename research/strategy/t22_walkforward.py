"""Test 22: walk-forward optimisation of test 20 (the test 21 grid, 34 instruments), the honest version of "optimise".

    python research/strategy/t22_walkforward.py

Every year Y from 2010 to 2025: rank all combinations (36 grid runs x filter x stop x exit = 1,152) on the trades
dated before Y - in a rolling 5-year window or in all earlier years - keeping those with at least MIN_N trades in
that window; then take the trades of year Y of (a) the best combination, (b) the top 5 together (each trade weighted
1/5). The years Y strung together are what the optimising would have earned out of sample. One position per
direction per pair inside each combination (as test 20/21).
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
from t21_select import FILTERS, EXITS, load_cfg  # noqa: E402

MIN_N = 100
YEARS = range(2010, 2026)


def combos():
    """{name: Series of R indexed by trade date} for every combination."""
    cfgs = sorted({re.match(r"g21_(r[\d.]+_l[\d.]+_b[\d.]+-[\d.]+)_", Path(p).name).group(1)
                   for p in glob.glob(str(HERE / "out" / "g21_*.csv"))})
    out = {}
    for cfg in cfgs:
        f = load_cfg(cfg)
        for fl, rule in FILTERS.items():
            o = one_per_dir(f.query(rule), "t020")
            o = o.assign(year=o.date.str[:4].astype(int))
            for sl in ("R_", "R_w_"):
                for ex in EXITS:
                    s = o[["year", f"{sl}{ex}"]].dropna()
                    out[f"{cfg}|{fl}|{sl}{ex}"] = s.rename(columns={f"{sl}{ex}": "R"})
    return out


if __name__ == "__main__":
    C = combos()
    print(f"{len(C)} combinaties")
    results = {}
    for window in ("5 jaar", "alle eerdere jaren"):
        for top in (1, 5):
            trades, picks = [], []
            for y in YEARS:
                lo = y - 5 if window == "5 jaar" else 0
                score = []
                for name, s in C.items():
                    tr = s[(s.year >= lo) & (s.year < y)].R
                    if len(tr) >= MIN_N:
                        score.append((tr.mean(), name))
                score.sort(reverse=True)
                chosen = [n for _, n in score[:top]]
                picks.append((y, chosen[0] if chosen else None))
                for n in chosen:
                    yr = C[n][C[n].year == y].R
                    trades.append(pd.DataFrame({"year": y, "R": yr.values, "w": 1 / top}))
            t = pd.concat(trades)
            x = t.R * t.w
            per_year = t.assign(x=x).groupby("year").x.sum().round(1)
            n_eff = t.w.sum()
            mean = x.sum() / n_eff
            # t-stat on the yearly sums (independent years)
            ty = per_year.mean() / per_year.std() * np.sqrt(len(per_year))
            lab = f"venster {window}, top {top}"
            results[lab] = per_year
            print(f"\n### {lab}: {n_eff:.0f} trades, gemiddeld {mean:+.3f}R per trade, "
                  f"PF {pf(t.R[t.w == t.w.max()]) if top == 1 else pf(x):.2f}, som {x.sum():+.1f}R, "
                  f"jaren positief {(per_year > 0).sum()}/{len(per_year)}, t (jaren) {ty:.2f}")
            print("  per jaar (som R):", per_year.to_dict())
            if top == 1:
                print("  gekozen per jaar:", {y: p for y, p in picks})
    pd.DataFrame(results).to_csv(HERE / "out" / "t22_walkforward.csv")
