"""Replication check: the trader's EURUSD trades (docs/SETUPS_TRADER.md) against the strategy-v2 engine.

    python research/strategy/v2_replication.py

Lists each trader trade with the engine trade in the same direction within 5 trading days, every engine trade the
trader did not take (from 1 May 2018 to the last trader setup), and the trader's no-trade setups.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import trader_strategy as T  # noqa: E402
from setup_study import load  # noqa: E402

# (setup, entry day, direction, entry) - the trader's own trades
TRADER = [("1", "2018-07-10", -1, 1.17430), ("2", "2018-10-16", -1, 1.15737), ("3", "2019-02-01", -1, 1.14548),
          ("4", "2019-05-02", -1, 1.11722), ("6", "2019-08-09", -1, 1.11988), ("7", "2019-11-21", -1, 1.10578),
          ("11", "2020-06-22", 1, 1.12609), ("13", "2020-11-13", 1, 1.18339),
          ("15", "2021-05-06", 1, 1.20648)]
NO_TRADE = [("5", "2019-07-01", "2019-08-01"), ("8", "2020-01-20", "2020-02-03"), ("9", "2020-02-07", "2020-03-02"),
            ("12", "2020-10-19", "2020-11-02")]
END = "2021-05-31"


def main():
    d, w, m = load("EURUSD", "D1"), load("EURUSD", "W1"), load("EURUSD", "MN")
    tr = []
    for dirn in (-1, 1):
        tr += T.run_view("EURUSD", d, w, dirn, "2016-01-01", "2026-01-01", [], m)
    e = pd.DataFrame(tr).sort_values("entry_day")
    e = e[(e.entry_day >= "2018-05-01") & (e.entry_day <= END)]
    used, ok = set(), 0
    print("trader                      | engine")
    for sid, day, dirn, px in TRADER:
        c = e[(e.dir == dirn) & (abs(pd.to_datetime(e.entry_day) - pd.Timestamp(day)).dt.days <= 7)]
        if len(c):
            r = c.iloc[0]
            used.add(r.name)
            ok += 1
            lag = (pd.Timestamp(r.entry_day) - pd.Timestamp(day)).days
            print(f"s{sid:3s} {day} {'L' if dirn == 1 else 'S'} {px:.5f} | {r.entry_day} ({lag:+d} d) {r.entry:.5f} "
                  f"{r.pattern}, R {r.R:+.2f}")
        else:
            print(f"s{sid:3s} {day} {'L' if dirn == 1 else 'S'} {px:.5f} | -- MIST --")
    extra = e[~e.index.isin(used)]
    for sid, a, b in NO_TRADE:
        hit = extra[(extra.entry_day >= a) & (extra.entry_day <= b)]
        print(f"s{sid:3s} geen trade {a} - {b}       | {'OK' if not len(hit) else 'ENGINE TRADE ' + hit.entry_day.iloc[0]}")
    print(f"\n{ok}/{len(TRADER)} trades gevonden; extra engine-trades tot {END}:")
    for _, r in extra.iterrows():
        print(f"   {r.entry_day} {'L' if r.dir == 1 else 'S'} {r.entry:.5f} {r.pattern}, R {r.R:+.2f}")


if __name__ == "__main__":
    main()
