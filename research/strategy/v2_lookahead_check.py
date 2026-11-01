"""No-look-ahead check for strategy v2: replay day by day as a live bot on MT5 would see the data.

    python research/strategy/v2_lookahead_check.py EURUSD --from 2018-05-01 --to 2020-04-01

For every trading day the engine gets ONLY the daily candles up to and including that day's close, and the weekly
candles that had closed by then plus the still-forming current week (its open / high / low / close so far, built from
those daily candles, as MT5 shows it). Every trade the engine opens on that day in this truncated run must be the
same trade (direction, entry, stop) as in the full backtest, and every full-backtest trade must appear on its own
entry day. Any difference means the backtest used information from the future.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import trader_strategy as T  # noqa: E402
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402


def key(t):
    return (int(t["dir"]), t["entry_day"], round(float(t["entry"]), 5), round(float(t["sl"]), 5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sym")
    ap.add_argument("--from", dest="start", default="2018-05-01")
    ap.add_argument("--to", dest="end", default="2020-04-01")
    ap.add_argument("--warmup", default="2016-01-01")
    a = ap.parse_args()
    d, w = load(a.sym, "D1"), load(a.sym, "W1")
    full = []
    for dirn in (-1, 1):
        full += T.run_view(a.sym, d, w, dirn, a.warmup, "2030-01-01", [])
    full = {key(t) for t in full if a.start <= t["entry_day"] < a.end}
    ddone = complete_times(d["time"], "D1").values
    wdone = complete_times(w["time"], "W1").values
    days = [i for i in range(len(d)) if a.start <= T.day_label(d["time"].iloc[i]) < a.end]
    seen, bad = set(), []
    for n, i in enumerate(days):
        cut = ddone[i]
        dd = d.iloc[:i + 1]
        wk = w[wdone <= cut]
        nxt = w[wdone > cut].head(1)
        if len(nxt):  # the forming week: only the days of it that have closed
            ws = nxt["time"].iloc[0]
            part = dd[dd["time"] >= ws]
            if len(part):
                row = nxt.copy()
                row["open"], row["high"] = part["open"].iloc[0], part["high"].max()
                row["low"], row["close"] = part["low"].min(), part["close"].iloc[-1]
                wk = pd.concat([wk, row])
        trades = []
        for dirn in (-1, 1):
            trades += T.run_view(a.sym, dd, wk.reset_index(drop=True), dirn, a.warmup, "2030-01-01", [])
        today = T.day_label(d["time"].iloc[i])
        for t in trades:
            if t["entry_day"] == today:
                kk = key(t)
                seen.add(kk)
                if kk not in full:
                    bad.append(("alleen live (niet in de backtest)", kk))
        if n % 100 == 0:
            print(f"  {today} ({n + 1}/{len(days)})", flush=True)
    for kk in sorted(full - seen):
        bad.append(("alleen in de backtest (live niet genomen)", kk))
    print(f"\n{a.sym} {a.start} - {a.end}: {len(days)} dagen nagespeeld, {len(full)} backtest-trades, "
          f"{len(seen)} live gevonden")
    if bad:
        for why, kk in bad:
            print(" VERSCHIL:", why, kk)
    else:
        print(" GEEN verschil: elke trade is op zijn instapdag al bekend met dezelfde instap en stop.")


if __name__ == "__main__":
    main()
