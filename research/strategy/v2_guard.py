"""Look-ahead guard for the research backtest (trader_strategy.py). Run it after EVERY engine change, before results
are reported.

    python research/strategy/v2_guard.py                      # 8 instruments x 15 random cut days
    python research/strategy/v2_guard.py --syms EURUSD --cuts 40
    python research/strategy/v2_guard.py --all                 # all 37 instruments

The rule it checks: a trade that the backtest opens on day X must be known from the data up to and including day X.
For random cut days the engine is run on the data cut at that day's close (daily candles up to it, the weekly candles
closed by then plus the still-forming week, the months closed by then) and every trade with entry day <= the cut day
must be the same (direction, entry day, entry, stop) as in the run on all data. A trade only in the full run means
the backtest used later data to open it; a trade only in the cut run means later data made the backtest skip it
(the 2026-11-04 setup-4 error: 746 skipped trades, 18% win, -415.8R). Exit code 1 on any difference.

The cut days are drawn at random (fixed seed) and cover every year; the full daily replay (v2_lookahead_check.py)
checks every day of a period and stays for deeper checks.
"""
import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]

WARMUP, END = "2016-01-01", "2030-01-01"
DEFAULT_SYMS = ["EURUSD", "GBPJPY", "USDJPY", "AUDCAD", "GBPCAD", "XAUUSD", "NAS100USD", "EURCHF"]


def truncate(d, w, m, i):
    """The data a live bot has at the close of daily candle i: daily up to i, closed weeks plus the forming week built
    from its closed days, closed months."""
    from candle_avail import complete_times
    ddone = complete_times(d["time"], "D1").values
    wdone = complete_times(w["time"], "W1").values
    cut = ddone[i]
    dd = d.iloc[:i + 1]
    wk = w[wdone <= cut]
    nxt = w[wdone > cut].head(1)
    if len(nxt):
        part = dd[dd["time"] >= nxt["time"].iloc[0]]
        if len(part):
            row = nxt.copy()
            row["open"], row["high"] = part["open"].iloc[0], part["high"].max()
            row["low"], row["close"] = part["low"].min(), part["close"].iloc[-1]
            wk = pd.concat([wk, row])
    mm = None
    if m is not None:
        mdone = complete_times(m["time"], "MN", d["time"]).values
        mm = m[mdone <= cut].reset_index(drop=True)
    return dd, wk.reset_index(drop=True), mm


def key(t):
    return (int(t["dir"]), t["entry_day"], round(float(t["entry"]), 5), round(float(t["sl"]), 5), t.get("setup", ""))


def engine(path=None):
    """The engine module; path = another engine file (e.g. an old version) to check instead of trader_strategy.py."""
    if path:
        import importlib.util
        if "trader_strategy" not in sys.modules or getattr(sys.modules["trader_strategy"], "__file__", "") != path:
            spec = importlib.util.spec_from_file_location("trader_strategy", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["trader_strategy"] = mod
            spec.loader.exec_module(mod)
    import trader_strategy as T
    return T


def run(sym, d, w, m):
    import trader_strategy as T
    out = []
    for dirn in (-1, 1):
        out += T.run_view(sym, d, w, dirn, WARMUP, END, [], m)
    return out


def check(args):
    sym, cuts, path = args
    T = engine(path)
    from setup_study import load
    d, w = load(sym, "D1"), load(sym, "W1")
    try:
        m = load(sym, "MN")
    except Exception:
        m = None
    full = run(sym, d, w, m)
    days = np.array([T.day_label(x) for x in d.time])
    bad = []
    for cday in cuts:
        idx = np.where(days <= cday)[0]
        if not len(idx):
            continue
        i = int(idx[-1])
        dd, wk, mm = truncate(d, w, m, i)
        live = run(sym, dd, wk, mm)
        fk = {key(t) for t in full if t["entry_day"] <= days[i]}
        lk = {key(t) for t in live if t["entry_day"] <= days[i]}
        for k in sorted(fk - lk):
            bad.append((sym, days[i], "alleen in de backtest (gebruikt latere data om te openen)", k))
        for k in sorted(lk - fk):
            bad.append((sym, days[i], "alleen live (latere data liet de backtest hem overslaan)", k))
    return sym, len(cuts), bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--syms", default=",".join(DEFAULT_SYMS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--cuts", type=int, default=15)
    ap.add_argument("--from", dest="start", default="2016-03-01")
    ap.add_argument("--to", dest="end", default="2025-12-01")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--engine", default=None, help="check another engine file (e.g. an old version)")
    a = ap.parse_args()
    syms = ([f[6:-4] for f in sorted(os.listdir(HERE / "out")) if f.startswith("v2n37_")] if a.all
            else a.syms.split(","))
    rng = np.random.default_rng(a.seed)
    span = pd.bdate_range(a.start, a.end)
    tasks = []
    for s in syms:
        cuts = sorted(pd.DatetimeIndex(rng.choice(span, size=a.cuts, replace=False)).strftime("%Y-%m-%d"))
        tasks.append((s, cuts, os.path.abspath(a.engine) if a.engine else None))
    total, bad = 0, []
    with ProcessPoolExecutor(a.jobs) as ex:
        for sym, n, b in ex.map(check, tasks):
            total += n
            bad += b
            print(f"  {sym}: {n} snijdagen, {len(b)} verschillen", flush=True)
    print(f"\nGUARD: {len(syms)} instrumenten, {total} snijdagen")
    if bad:
        for sym, day, why, k in bad:
            print(f" VERSCHIL {sym} (snijdag {day}): {why} {k}")
        print("GUARD FAALT: de backtest gebruikt toekomstige data. Niet rapporteren voor dit is opgelost.")
        sys.exit(1)
    print("GUARD OK: elke trade is op zijn instapdag al bekend; geen trade wordt door latere data overgeslagen.")


if __name__ == "__main__":
    main()
