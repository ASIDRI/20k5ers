"""5ers challenge on the test 20 trades (rule week + S/R, one position per direction, 34 instruments).

    python research/strategy/prop_t20.py [--col R_m_top_1] [--risks 0.01,0.015,0.02]

Each trade's R (net of costs) is booked on its exit day at a fixed risk per trade (fraction of the starting
balance). Challenge: step 1 +8%, step 2 +5% (both from the starting balance), failed at -10% from the starting balance
(static); the daily -5% limit is not modelled (results are booked at exits only, so intraday drawdown is
understated). A new challenge starts on the first trading day of every month 2006-2024; trades filled before the start
are not counted. No time limit; a challenge still running at the end of the data counts as unfinished.
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t17_eval import one_per_dir  # noqa: E402


def trades(col, prefixes=("t20_", "t20x_")):
    fs = [pd.read_csv(p) for pre in prefixes for p in glob.glob(str(HERE / "out" / f"{pre}*.csv"))
          if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    f["htf_sup"] = f.htf_sup.astype(str).str.lower().eq("true")
    o = one_per_dir(f.query("wk_struct == 1 & htf_sup"), "t020")
    xcol = "x_t020"
    o = o[o[col].notna() & o[xcol].notna()]
    return o[["sym", "fill", xcol, col]].rename(columns={xcol: "exit", col: "R"}).sort_values("exit")


def challenge(t, start, risk):
    eq, step, targets, i0 = 1.0, 0, (0.08, 0.05), None
    for _, r in t[t.fill >= start].iterrows():
        eq += risk * r.R
        if eq <= 0.90:
            return "breach", r.exit
        if eq >= 1 + targets[step]:
            step += 1
            if step == 2:
                return "geslaagd", r.exit
            eq = 1.0
    return "loopt", None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--col", default="R_m_top_1")
    ap.add_argument("--risks", default="0.01,0.015,0.02")
    ap.add_argument("--prefixes", default="t20_,t20x_")
    a = ap.parse_args()
    t = trades(a.col, a.prefixes.split(","))
    per_year = t.groupby(t.exit.str[:4]).R.agg(["size", "sum"])
    print(f"{len(t)} trades ({a.col}), gemiddeld {t.R.mean():+.3f}R; per jaar:\n{per_year.round(1).T.to_string()}")
    starts = pd.date_range("2006-01-01", "2024-12-01", freq="MS").strftime("%Y-%m-%d")
    for risk in map(float, a.risks.split(",")):
        res = [challenge(t, s, risk) for s in starts]
        out = pd.DataFrame(res, columns=["uitkomst", "dag"], index=starts)
        done = out[out.uitkomst != "loopt"]
        dur = (pd.to_datetime(done[done.uitkomst == "geslaagd"].dag) - pd.to_datetime(done[done.uitkomst == "geslaagd"].index)).dt.days
        print(f"\nrisico {risk*100:.1f}% per trade: geslaagd {(out.uitkomst == 'geslaagd').mean()*100:.0f}%, "
              f"breach {(out.uitkomst == 'breach').mean()*100:.0f}%, nog bezig {(out.uitkomst == 'loopt').mean()*100:.0f}%; "
              f"mediane duur tot geslaagd {dur.median():.0f} dagen")
        for lab, a_, b_ in (("2006-14", "2006", "2015"), ("2015-20", "2015", "2021"), ("2021-24", "2021", "2025")):
            g = out[(out.index >= a_) & (out.index < b_)]
            print(f"   starts {lab}: geslaagd {(g.uitkomst == 'geslaagd').mean()*100:.0f}%, breach {(g.uitkomst == 'breach').mean()*100:.0f}%")
