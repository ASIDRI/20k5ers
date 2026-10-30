"""What makes the winning setups different? Found on 2015-2020, checked on 2021-2025.

    python research/strategy/winners.py

Per feature (all known when the setup is made): split into quartiles on the 2015-2020 trades, average R
per quartile in both halves. A feature only counts if the best bucket beats the rest in BOTH halves.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
SYMS = ("AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD "
        "GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY XTI_USD UK100_USD").split()

df = pd.concat(pd.read_csv(OUT / f"setups_{s}.csv") for s in SYMS)
f = df[df["result"] == "gevuld"].copy()
f["half"] = np.where(f["date"].str[:4] <= "2020", "A 2015-20", "B 2021-25")
f["win"] = f["R"] > 0
print(f"{len(f)} gevulde trades; winnaars {f.win.mean()*100:.0f}%; gem. R {f.R.mean():.3f}")
print(f"winnaars vs verliezers (medianen):")
num = ["rng_atr", "risk_atr", "bos_body_atr", "atr_ratio", "room_R", "bars_to_fib", "bars_to_fill"]
print(f.groupby("win")[num].median().round(2).T.to_string())

rows = []
for col in num:
    a = f[f.half == "A 2015-20"]
    q = a[col].quantile([0.25, 0.5, 0.75]).values
    cut = lambda x: np.digitize(x, q)  # noqa: E731
    f["_b"] = cut(f[col])
    t = f.groupby(["_b", "half"])["R"].agg(["count", "mean"]).unstack("half")
    rows.append((col, q, t))
for col in ["dir", "kind", "hl", "zone_level", "wk", "mn"]:
    t = f.groupby([col, "half"])["R"].agg(["count", "mean"]).unstack("half")
    rows.append((col, None, t))
f["cls"] = np.where(f["sym"].isin(["XTI_USD", "UK100_USD"]), "olie/index", np.where(f["sym"].str.contains("JPY"), "JPY-paren", "overige forex"))
rows.append(("cls", None, f.groupby(["cls", "half"])["R"].agg(["count", "mean"]).unstack("half")))

for col, q, t in rows:
    print(f"\n--- {col}" + (f"  (kwartielgrenzen 2015-20: {np.round(q, 2).tolist()})" if q is not None else ""))
    print(t.round(3).to_string())

print("\n--- per asset (trades / gem. R per helft; som R totaal), slechtste eerst")
pa = f.groupby(["sym", "half"])["R"].agg(["count", "mean"]).unstack("half")
pa["somR"] = f.groupby("sym")["R"].sum()
pa["beide_negatief"] = (pa[("mean", "A 2015-20")] < 0) & (pa[("mean", "B 2021-25")] < 0)
pa["beide_positief"] = (pa[("mean", "A 2015-20")] > 0) & (pa[("mean", "B 2021-25")] > 0)
print(pa.sort_values("somR").round(2).to_string())
print(f"\nin beide helften negatief: {int(pa['beide_negatief'].sum())} assets; in beide positief: {int(pa['beide_positief'].sum())}")
