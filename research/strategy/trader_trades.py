"""The trader's own example trades, recalculated on the data: fill, then how far price ran (in fib units) before the
stop, and what each management style would have made.

    python research/strategy/trader_trades.py

Levels as read from the trader's TradingView screenshots (2026-10-29); fib 1 and 0 approximate (read off the chart).
The order is live from `live` (the candle after the leg's end). Data ends mid-December 2025.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402

TRADES = [  # name, symbol, tf, direction, fib 1, fib 0, entry, stop, the trader's TP, order live from
    ("EURUSD D1 long jun-25", "EURUSD", "D1", 1, 1.1395, 1.1625, 1.14765, 1.13551, 1.18745, "2025-06-13"),
    ("EURUSD W1 long jul-25", "EURUSD", "W1", 1, 1.11727, 1.1830, 1.13929, 1.11137, 1.20229, "2025-07-07"),
    ("EURAUD D1 short dec-25", "EURAUD", "D1", -1, 1.7905, 1.7465, 1.77675, 1.82566, 1.68188, "2025-12-09"),
    ("GBPAUD D1 short nov-25", "GBPAUD", "D1", -1, 2.0720, 1.9990, 2.04388, 2.08676, 1.87332, "2025-11-13"),
    ("AUDCAD W1 long sep-25", "AUDCAD", "W1", 1, 0.8985, 0.9220, 0.90695, 0.89453, 0.96500, "2025-09-08"),
    ("NZDCAD D1 long okt-23", "NZDCAD", "D1", 1, 0.7965, 0.8215, 0.80537, 0.79273, 0.83927, "2023-10-11"),
    ("NZDCAD D1 short feb-24", "NZDCAD", "D1", -1, 0.8385, 0.8150, 0.83129, 0.83972, 0.80758, "2024-02-06"),
    ("NZDCAD D1 long jun-24", "NZDCAD", "D1", 1, 0.8085, 0.8515, 0.81410, 0.80700, 0.86094, "2024-06-12"),
]
EXT = (0.2, 0.27, 0.65, 1.0, 1.618)


def run():
    rows = []
    for name, sym, tf, dirn, f1, f0, entry, sl, tp, live in TRADES:
        d = load(sym, tf)
        d = d[d.time >= pd.Timestamp(live, tz="UTC")].reset_index(drop=True)
        rng = abs(f0 - f1)
        risk = abs(entry - sl)
        fib_entry = (f0 - entry) * dirn / rng
        hit = (d.low <= entry) if dirn == 1 else (d.high >= entry)
        if not hit.any():
            rows.append(dict(trade=name, fib_instap=round(fib_entry, 3), RR_tp=round(abs(tp - entry) / risk, 2),
                             gevuld="nee (data tot " + str(d.time.iloc[-1])[:10] + ")"))
            continue
        k = int(hit.idxmax())
        fav = d.high.values if dirn == 1 else -d.low.values
        adv = d.low.values if dirn == 1 else -d.high.values
        stop_m = sl if dirn == 1 else -sl
        out = dict(trade=name, fib_instap=round(fib_entry, 3), RR_tp=round(abs(tp - entry) / risk, 2),
                   gevuld=str(d.time[k])[:10])
        # path after the fill: first stop touch, and the furthest fib extension reached before it
        stop_i = next((i for i in range(k, len(d)) if adv[i] <= stop_m), None)
        end = stop_i if stop_i is not None else len(d)
        best = fav[k:end + (0 if stop_i is None else 1)].max() if end > k else fav[k]
        best_px = best if dirn == 1 else -best
        out["verst_fib"] = round((best_px - f0) * dirn / rng, 2)  # 0.2 = reached -0.2
        out["MFE_R"] = round((best_px - entry) * dirn / risk, 2)
        out["SL_geraakt"] = str(d.time[stop_i])[:10] if stop_i is not None else "nee"
        tp_m = tp if dirn == 1 else -tp
        tp_i = next((i for i in range(k, end) if fav[i] >= tp_m), None)
        out["TP_trader"] = (f"{abs(tp - entry) / risk:+.2f}R op {str(d.time[tp_i])[:10]}" if tp_i is not None
                            else ("-1R" if stop_i is not None else "loopt nog"))
        for x in EXT:
            lvl = f0 + dirn * x * rng
            lm = lvl if dirn == 1 else -lvl
            i_x = next((i for i in range(k, end) if fav[i] >= lm), None)
            out[f"-{x}"] = "ja" if i_x is not None else "nee"
        rows.append(out)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    print(run().to_string(index=False))
