"""Audit phase 1: prove the reference ("live on our data") before anything is measured with it.

    python backtest/src/audit_referee_tests.py candles [--n 300]

candles: at the live bot's own scan moments (live_clock.is_scan_bar) the simulator must return, for every
higher timeframe, exactly the candles MT5 would have CLOSED by then:
  a) no returned candle completes after 'now' (no look-ahead);
  b) the newest returned candle is the newest completed one (no needless lag);
  c) independent of the stamp rules: the newest returned D1/W1/MN close equals the last M15 close before
     the moment the candle completed (so its values were really known then), for series whose M15 matches.
Results: backtest/output/audit/referee_candles.json
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
os.environ.setdefault("HTF_NO_LOOKAHEAD", "1")

import pandas as pd  # noqa: E402
from csv_mt5_simulator import CSVMT5Simulator  # noqa: E402
from candle_avail import complete_times  # noqa: E402
import live_clock  # noqa: E402


def candles(n):
    from config import FOREX_PAIRS, METALS, OIL_ASSETS, INDICES, CRYPTO_ASSETS
    sim = CSVMT5Simulator(server="x", login=1, password="x", data_dir=str(REPO / "data" / "ohlcv"), initial_balance=1)
    rng = random.Random(7)
    symbols = [s for s in FOREX_PAIRS + METALS + OIL_ASSETS + INDICES + CRYPTO_ASSETS if sim._load_data(s, "D1") is not None]
    # scan moments 2016-2024: walk 15-minute steps and keep the live scan bars
    t = pd.Timestamp("2016-01-04", tz="UTC")
    scans = []
    while t < pd.Timestamp("2024-12-20", tz="UTC"):
        if live_clock.is_scan_bar(t.to_pydatetime()):
            scans.append(t)
        t += pd.Timedelta(minutes=15)
    picks = [(rng.choice(symbols), rng.choice(scans)) for _ in range(n)]
    out = {"checked": 0, "lookahead": [], "lag": [], "m15_mismatch": [], "m15_checked": 0}
    for sym, now in picks:
        sim._current_time = now.to_pydatetime()
        for tf in ("H4", "D1", "W1", "MN"):
            full = sim._load_data(sym, tf)
            if full is None or full.empty:
                continue
            times = full["time"] if full["time"].dt.tz is not None else full["time"].dt.tz_localize("UTC")
            d1 = None
            if tf == "MN":
                d = sim._load_data(sym, "D1")
                d1 = d["time"] if d["time"].dt.tz is not None else d["time"].dt.tz_localize("UTC")
            done = complete_times(times, tf, d1)
            got = sim.get_ohlcv(sym, tf, 5000)
            out["checked"] += 1
            if not got:
                continue
            last_t = pd.Timestamp(got[-1]["time"])
            last_t = last_t if last_t.tzinfo else last_t.tz_localize("UTC")
            last_done = done[times == last_t].max()
            if last_done > now:
                out["lookahead"].append([sym, tf, str(now), str(last_t), str(last_done)])
            newest_completed = times[done <= now].max()
            if newest_completed > last_t:
                out["lag"].append([sym, tf, str(now), str(last_t), str(newest_completed)])
            if tf in ("D1", "W1", "MN"):
                m15 = sim._load_data(sym, "M15")
                if m15 is None or m15.empty:
                    continue
                mt = m15["time"] if m15["time"].dt.tz is not None else m15["time"].dt.tz_localize("UTC")
                before = m15[mt < last_done]
                if before.empty or mt.min() > last_t:
                    continue
                c_m15 = float(before["close"].iloc[-1]); c_bar = float(got[-1]["close"])
                out["m15_checked"] += 1
                if abs(c_m15 - c_bar) / c_bar > 0.002:
                    out["m15_mismatch"].append([sym, tf, str(now), str(last_t), c_bar, c_m15])
    res = REPO / "backtest" / "output" / "audit" / "referee_candles.json"
    res.parent.mkdir(parents=True, exist_ok=True)
    res.write_text(json.dumps(out, indent=1))
    by = lambda rows: pd.Series([f"{r[0]} {r[1]}" for r in rows]).value_counts().to_dict() if rows else {}
    print(f"checked {out['checked']} (symbol, timeframe, scan) cases")
    print(f"a) look-ahead: {len(out['lookahead'])}  b) needless lag: {len(out['lag'])}")
    print(f"c) M15 cross-check: {out['m15_checked']} checked, {len(out['m15_mismatch'])} mismatches (>0.2%) {by(out['m15_mismatch'])}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("test", choices=["candles"])
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    candles(a.n)
