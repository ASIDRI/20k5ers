"""Audit phase 1: prove the reference ("live on our data") before anything is measured with it.

    python backtest/src/audit_referee_tests.py candles [--n 300]
    python backtest/src/audit_referee_tests.py broker
    python backtest/src/audit_referee_tests.py clock

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


def broker():
    """Known scenarios on hand-made M15 bars. PASS = what MT5 does; KNOWN = where the fake broker is
    knowingly kinder than MT5 (each one listed, so its effect can be measured and closed)."""
    import tempfile
    from datetime import datetime, timedelta, timezone
    os.environ.update({"GAP_FILLS": "1", "SLIPPAGE_PIPS": "0", "COST_LIMIT_ENTRIES": "0", "SLIPPAGE_MAP": "{}"})
    t0 = datetime(2023, 3, 6, 8, 0, tzinfo=timezone.utc)

    def fresh(bars):
        sim = CSVMT5Simulator(server="x", login=1, password="x", data_dir=tempfile.mkdtemp(), initial_balance=50000)
        sim._m15_indexed["EUR_USD"] = {pd.Timestamp(t0 + timedelta(minutes=15 * i)): dict(
            open=o, high=h, low=l, close=c, volume=1) for i, (o, h, l, c) in enumerate(bars)}
        sim.set_current_time(t0)
        return sim

    def step(sim, i):
        sim.set_current_time(t0 + timedelta(minutes=15 * i))
        hits = sim.check_sl_tp_hits()
        for h in hits:
            sim.close_position(h["ticket"], close_price=h["price"])
        return sim.check_pending_order_fills(), hits

    res = []

    def check(name, ok, known=False, detail=""):
        res.append(("PASS" if ok else ("KNOWN" if known else "FAIL"), name, detail))

    # 1 buy limit below market: not filled while price stays above, filled at the limit when touched
    sim = fresh([(1.1000, 1.1010, 1.0995, 1.1005), (1.1005, 1.1008, 1.0985, 1.0990)])
    r = sim.place_pending_order("EUR_USD", direction="bullish", price=1.0990, sl=1.0950, tp=1.1100, volume=1)
    f0, _ = step(sim, 0)
    f1, _ = step(sim, 1)
    pos = sim._positions.get(r.order_id)
    check("buy limit waits, then fills at its price", not f0 and f1 and pos and abs(pos.price_open - 1.0990) < 1e-9)
    # 2 buy stop through a gap: fills at the (worse) open
    sim = fresh([(1.1000, 1.1004, 1.0996, 1.1002), (1.1030, 1.1040, 1.1025, 1.1035)])
    r = sim.place_pending_order("EUR_USD", direction="bullish", price=1.1010, sl=1.0950, tp=1.1100, volume=1)
    step(sim, 0); step(sim, 1)
    pos = sim._positions.get(r.order_id)
    check("buy stop gapped through fills at the open", pos is not None and abs(pos.price_open - 1.1030) < 1e-9,
          detail=f"fill {pos.price_open if pos else None}")
    # 3 SL and TP inside the same bar: the stop is assumed first (the safe side)
    sim = fresh([(1.1000, 1.1002, 1.0998, 1.1000), (1.1000, 1.1100, 1.0900, 1.1000)])
    r = sim.place_market_order("EUR_USD", direction="bullish", volume=1, sl=1.0950, tp=1.1050)
    _, hits = step(sim, 1)
    check("SL and TP in one bar -> SL", bool(hits) and hits[0]["type"] == "sl")
    # 4 a bar that fills the order AND goes through the stop: MT5 can stop the trade in that same bar
    sim = fresh([(1.1000, 1.1002, 1.0998, 1.1000), (1.1000, 1.1001, 1.0900, 1.0920), (1.0920, 1.0930, 1.0915, 1.0925)])
    r = sim.place_pending_order("EUR_USD", direction="bullish", price=1.0990, sl=1.0950, tp=1.1100, volume=1)
    step(sim, 0)
    f1, h1 = step(sim, 1)
    stopped_same_bar = r.order_id not in sim._positions
    check("fill bar that also crosses the SL stops the trade in that bar", stopped_same_bar, known=True,
          detail="the stop is only checked from the next bar on; real price may have hit the SL after the fill")
    # 5 buy limit ABOVE the market with an explicit type: MT5 rejects it (invalid price)
    sim = fresh([(1.1000, 1.1002, 1.0998, 1.1000), (1.1000, 1.1002, 1.0998, 1.1000)])
    r = sim.place_pending_order("EUR_USD", order_type="buy_limit", price=1.1050, sl=1.0950, tp=1.1100, volume=1)
    check("buy limit above the market is rejected", not r.success, known=True,
          detail="accepted and filled at 1.1050 on the next bar (the live client never sends this: it picks LIMIT/STOP from the tick)")
    # 6 sell TP reached by the bid only: a sell closes on the ASK, so it needs bid <= TP - spread
    sim = fresh([(1.1000, 1.1002, 1.0998, 1.1000), (1.1000, 1.1001, 1.0950, 1.0960)])
    r = sim.place_market_order("EUR_USD", direction="bearish", volume=1, sl=1.1050, tp=1.0950)
    _, hits = step(sim, 1)
    check("sell TP needs the ask to reach it", not hits, known=True,
          detail="TP taken when the bid low touches it: optimistic by one spread on sell TPs and sell stops")
    for st, name, det in res:
        print(f"[{st:5}] {name}" + (f"  ({det})" if det and st != "PASS" else ""))
    out = REPO / "backtest" / "output" / "audit" / "referee_broker.json"
    out.write_text(json.dumps(res, indent=1))
    return res


def clock():
    """The live clock (New York + 7 h, with US DST) against the data: every forex D1 candle must open at
    server midnight, and the live scan times must fall right after it (00:15, Monday 01:00)."""
    sim = CSVMT5Simulator(server="x", login=1, password="x", data_dir=str(REPO / "data" / "ohlcv"), initial_balance=1)
    bad, n = [], 0
    for sym in ("EUR_USD", "GBP_JPY", "AUD_CAD", "XTI_USD", "UK100_USD"):
        d = sim._load_data(sym, "D1")
        t = d["time"] if d["time"].dt.tz is not None else d["time"].dt.tz_localize("UTC")
        t = t[(t >= pd.Timestamp("2016-01-01", tz="UTC")) & (t < pd.Timestamp("2025-01-01", tz="UTC"))].drop_duplicates()
        for ts in t:
            n += 1
            srv = live_clock.server_time(ts.to_pydatetime())
            if (srv.hour, srv.minute) != (0, 0):
                bad.append([sym, str(ts), str(srv)])
    scans = 0
    wrong = []
    tt = pd.Timestamp("2016-01-04", tz="UTC")
    while tt < pd.Timestamp("2024-12-31", tz="UTC"):
        if live_clock.is_scan_bar(tt.to_pydatetime()):
            scans += 1
            srv = live_clock.server_time(tt.to_pydatetime())
            want = (1, 0) if srv.weekday() == 0 else (0, 15)
            if (srv.hour, srv.minute) != want or srv.weekday() > 4:
                wrong.append(str(tt))
        tt += pd.Timedelta(minutes=15)
    print(f"D1 opens checked: {n}, not at server midnight: {len(bad)} {bad[:5]}")
    print(f"scan moments 2016-2024: {scans} (weekdays: ~{9*261}), at a wrong server time: {len(wrong)}")
    (REPO / "backtest" / "output" / "audit" / "referee_clock.json").write_text(
        json.dumps({"d1_checked": n, "d1_not_at_server_midnight": bad, "scans": scans, "wrong_scans": wrong}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("test", choices=["candles", "broker", "clock"])
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    if a.test == "candles":
        candles(a.n)
    elif a.test == "clock":
        clock()
    else:
        broker()
