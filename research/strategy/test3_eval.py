"""Test 3: apply the pre-registered criteria (docs/STRATEGY_FROM_VIDEOS.md, commit 06b114b) to the
out-of-sample runs 2005-2014. Group: setups against BOTH the weekly and the monthly trend (wk == -1, mn == -1).
Pass only if: mean >= +0.10R with >= 300 trades, profit factor >= 1.2, profitable in >= 6 of 10 years.
Costs as in test 2 (test 1 had none: they are applied here the same way, per trade on its risk)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test2 import cost_price  # noqa: E402

SYMS = ("AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD "
        "GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY").split()


def judge(name, f, rcol):
    g = f[(f.wk == -1) & (f.mn == -1)]
    n = len(g)
    mean = g[rcol].mean()
    pf = g.loc[g[rcol] > 0, rcol].sum() / -g.loc[g[rcol] < 0, rcol].sum()
    yrs = g.assign(y=g.date.str[:4]).groupby("y")[rcol].sum()
    ok = [mean >= 0.10 and n >= 300, pf >= 1.2, int((yrs > 0).sum()) >= 6]
    print(f"\n=== {name}: tegen week+maand, 2005-2014, na kosten")
    print(f"trades {n}, gemiddeld {mean:+.3f}R, profit factor {pf:.2f}, jaren winst {int((yrs > 0).sum())}/{len(yrs)}")
    print("per jaar (som R):", yrs.round(1).to_dict())
    print(f"criteria: [1] gem>=+0,10R & >=300: {ok[0]}  [2] PF>=1,2: {ok[1]}  [3] >=6/10 jaar: {ok[2]}"
          f"  ->  {'GESLAAGD' if all(ok) else 'VERWORPEN'}")
    a = f.groupby(np.where((f.wk == -1) & (f.mn == -1), "tegen", "rest"))[rcol].agg(["count", "mean"]).round(3)
    print("ter vergelijking:", a.to_dict("index"))


t2 = pd.concat(pd.read_csv(HERE / "out" / f"oos_test2_{s}.csv") for s in SYMS)
judge("test 2 (zone + 4u-reactie)", t2[t2.result == "gevuld"], "Rnet")

t1 = pd.concat(pd.read_csv(HERE / "out" / f"oos_setups_{s}.csv") for s in SYMS)
t1 = t1[t1.result == "gevuld"].copy()
t1["Rnet"] = t1["R"] - t1.apply(lambda r: cost_price(r["sym"]) / r["risk"], axis=1)
judge("test 1 (daggrafiek, limiet op 0,66)", t1, "Rnet")
