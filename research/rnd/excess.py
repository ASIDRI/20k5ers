"""Candidates against the BASELINE (all candles of that timeframe, same costs), not against zero.

    python research/rnd/excess.py

Costs alone make every 4h candle a loser (median 0.10 ATR per trade), so a cell only carries information if it
beats the baseline 'sig/any' of the same half. Rule (docs/RND_PLAN.md): excess t >= 3 in 2015-2020 and in
2021-2025 at least half of that excess, same sign."""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
for tf in ["weekly", "D1", "H4"]:
    f = OUT / f"{tf}_summary.csv"
    if not f.exists():
        continue
    s = pd.read_csv(f)
    base = s[(s.groep == "sig") & (s.cel == "any")].set_index("half")
    s = s[s.cel.str.split().str[0] != "any"].copy()
    s["excess"] = s.ev11 - s.half.map(base.ev11)
    s["tx"] = s.excess / (s.ev11 / s.t11).abs()
    p = s.pivot_table(index=["groep", "cel"], columns="half", values=["n", "excess", "tx"])
    p.columns = [f"{a}_{b[:3]}" for a, b in p.columns]
    door = p[(p.tx_ont.abs() >= 3) & ((p.excess_bev * p.excess_ont) > 0) & (p.excess_bev.abs() >= 0.5 * p.excess_ont.abs())]
    print(f"\n##### {tf}: basislijn ev11 na kosten {base.ev11.round(3).to_dict()}")
    print(door.round(3).to_string() if len(door) else "  geen cel met meerwaarde die bevestigd wordt")
