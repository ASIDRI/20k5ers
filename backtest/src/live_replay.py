#!/usr/bin/env python3
"""
LIVE REPLAY: run the real, unmodified main_live_bot.py against recorded prices.

Nothing in main_live_bot.py is changed or copied. This harness:

  * runs in a throw-away working directory, so the live bot's state files are untouched;
  * gives the bot a fake MetaTrader (csv_mt5_simulator, the same broker model the
    backtest uses: spreads, slippage, gaps, commission, 5ers scaling);
  * gives the bot a fake clock (datetime.now / time.time / time.sleep), so one
    pass of the bot's own `run()` loop equals one 15-minute bar;
  * replaces the bot's DDD-protection THREAD by a call made once per bar (and
    after every stop-loss hit), because a real thread cannot follow a fake clock;
  * plays the BROKER's part: it fills pending orders and triggers stop-losses
    and take-profits on each bar, in the same order as the backtest engine.

Everything the bot DECIDES (scan, signals, sizing, risk ladder, stops after TP,
nightly de-risk, Friday close, halts) is the live code.

    uv run python3 backtest/src/live_replay.py --start 2019-03-01 --end 2019-04-30 --out /tmp/replay1

Outputs in --out: trades.csv, summary.json, replay.log
"""
import argparse
import csv
import json
import os
import sys
import tempfile
import threading
import time as _real_time
from datetime import datetime as _RealDT, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


class StepDone(BaseException):
    """Raised inside the fake sleep to leave the DDD worker's endless loop."""


class Clock:
    now = _RealDT(2015, 1, 1, tzinfo=timezone.utc)


def make_fake_datetime():
    class FakeDT(_RealDT):
        @classmethod
        def now(cls, tz=None):
            t = Clock.now
            return t.astimezone(tz) if tz else t.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return Clock.now.replace(tzinfo=None)

        @classmethod
        def today(cls):
            return Clock.now.replace(tzinfo=None)
    return FakeDT


class FakeThread:
    """Captures the DDD worker instead of starting a real thread."""
    targets = []

    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
        self._target = target
        self.daemon = daemon
        self.name = name
        FakeThread.targets.append(target)

    def start(self):
        pass

    def is_alive(self):
        return True

    def join(self, timeout=None):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--balance", type=float, default=50000.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--env-json", default=None, help="JSON file with extra env (broker/simulator costs and live settings)")
    ap.add_argument("--data-dir", default=str(REPO / "data" / "ohlcv"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    if os.getenv("REPLAY_TRACE"):
        import faulthandler
        faulthandler.dump_traceback_later(int(os.getenv("REPLAY_TRACE")), exit=True)

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="live_replay_"))

    # Environment: dummy credentials, live broker type, then the caller's settings.
    os.environ.update({"BROKER_TYPE": "fiveers_live", "MT5_LOGIN": "1", "MT5_PASSWORD": "x",
                       "MT5_SERVER": "replay", "PYTHONUTF8": "1"})
    if args.env_json:
        os.environ.update({k: str(v) for k, v in json.loads(Path(args.env_json).read_text()).items()})
    os.environ["W5_CLOCK_PROBE_S"] = "0"  # the bot's server-clock probe waits on real ticks; offline it reports "not measurable"
    os.environ.pop("OPT_PARAMS", None)  # the live bot never gets the backtest's parameter overlay

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(HERE))
    os.chdir(work)  # state files (challenge_state.json, pending_setups.json, ...) land here

    # The fake MetaTrader5 module only has to exist for imports on a Linux machine.
    import types
    sys.modules.setdefault("MetaTrader5", types.ModuleType("MetaTrader5"))

    import main_live_bot as live
    import logging
    logging.getLogger("tradr").setLevel(logging.INFO if args.verbose else logging.WARNING)
    for h in logging.getLogger("tradr").handlers:
        if isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename"):
            h.setLevel(logging.INFO if args.verbose else logging.ERROR)
    fh = logging.FileHandler(out / "replay.log", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logging.getLogger("tradr").addHandler(fh)
    logging.getLogger("tradr").setLevel(logging.INFO)

    from csv_mt5_simulator import CSVMT5Simulator

    start = _RealDT.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = _RealDT.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    sim = CSVMT5Simulator(server="replay", login=1, password="x", data_dir=args.data_dir,
                          initial_balance=args.balance)
    sim.connect()
    sim.set_date_filter(start, end)
    from config import FOREX_PAIRS, METALS, OIL_ASSETS, INDICES, CRYPTO_ASSETS
    excluded = set()
    if os.getenv("OIL_ENABLE", "1").strip().lower() not in ("1", "true", "yes", "on"):
        excluded = {"XBR_USD", "XTI_USD"}
    env_excl = os.getenv("EXCLUDE_SYMBOLS", "").replace(" ", "")
    if env_excl:
        excluded |= {s for s in env_excl.split(",") if s}
    all_symbols = [s for s in FOREX_PAIRS + METALS + OIL_ASSETS + INDICES + CRYPTO_ASSETS if s not in excluded]
    sim.load_m15_data(all_symbols, start_date=start, end_date=end)
    # The live bot talks to its broker in 5ers names (EURUSD, UK100, XTIUSD); the simulator stores
    # prices under OANDA names (EUR_USD). Give the fake broker both, like a real MT5 would answer.
    from symbol_mapping import get_broker_symbol
    from broker_config import get_broker_config
    _btype = get_broker_config().broker_type.value
    ALIAS = {}
    for oanda in list(sim._m15_indexed.keys()):
        b = get_broker_symbol(oanda, _btype)
        if b != oanda:
            ALIAS[b] = oanda
            sim._m15_indexed.setdefault(b, sim._m15_indexed[oanda])
    _orig_load = sim._load_data
    sim._load_data = lambda sym, tf: _orig_load(ALIAS.get(sym, sym), tf)
    timeline = sim.get_m15_timeline(start, end)
    timeline = [t.to_pydatetime() if hasattr(t, "to_pydatetime") else t for t in timeline]
    timeline = [t if t.tzinfo else t.replace(tzinfo=timezone.utc) for t in timeline]

    # ── the fake MetaTrader the bot sees ───────────────────────────────────────
    class Facade:
        """The simulator, plus the few calls only the real MT5Client has."""
        def __init__(self, s):
            object.__setattr__(self, "_s", s)

        def __getattr__(self, name):
            return getattr(self._s, name)

        def __setattr__(self, name, value):
            setattr(self._s, name, value)

        def get_high_impact_news(self, hours_ahead=2.0, hours_behind=0.5):
            return []  # no calendar offline: the bot falls back to its fixed schedule, like the backtest

        def check_heartbeat(self):
            return True

        def is_connected(self):
            return True

        def execute_trade(self, symbol, direction, volume, sl, tp, deviation=20):
            return self._s.place_market_order(symbol, direction=direction, volume=volume, sl=sl, tp=tp)

        def modify_pending_order(self, ticket, price=None, sl=None, tp=None):
            o = self._s._pending_orders.get(ticket)
            if o is None:
                return False
            if price is not None:
                o.price = price
            if sl is not None:
                o.sl = sl
            if tp is not None:
                o.tp = tp
            return True

    fake = Facade(sim)

    # ── patch clock and threads, then build the REAL bot ───────────────────────
    FakeDT = make_fake_datetime()
    repo_mods = []
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None) or ""
        if f.startswith(str(REPO)) and "/backtest/" not in f and ".venv" not in f:
            repo_mods.append(mod)
    for mod in repo_mods:
        if getattr(mod, "datetime", None) is _RealDT:
            mod.datetime = FakeDT

    state = {"i": -1, "ddd": False, "bars": 0, "sl_hits": 0}
    threading.Thread = FakeThread  # DDD worker is driven by us, not by a real thread

    def fake_time():
        return Clock.now.timestamp()

    def fake_sleep(secs):
        if state["ddd"]:
            raise StepDone()
        if secs >= 10:
            advance()
        # short sleeps (0.1 / 0.5 / 1 s) between orders are no-ops

    _real_time.time = fake_time
    _real_time.sleep = fake_sleep

    bot = live.LiveTradingBot(immediate_scan=False)
    bot.mt5 = fake

    # Debug aid only: write the traceback of any scan error to scan_errors.log (the bot logs just the message).
    _orig_scan = bot.scan_symbol

    def _scan_logged(sym, *a, **k):
        try:
            return _orig_scan(sym, *a, **k)
        except Exception:
            import traceback
            with open(out / "scan_errors.log", "a", encoding="utf-8") as ef:
                ef.write(f"{Clock.now} {sym}\n{traceback.format_exc()}\n")
            raise
    bot.scan_symbol = _scan_logged

    def run_ddd_step():
        """One pass of the bot's own DDD protection worker."""
        if not FakeThread.targets:
            return
        state["ddd"] = True
        try:
            FakeThread.targets[-1]()
        except StepDone:
            pass
        except Exception as e:  # noqa
            live.log.error(f"[replay] DDD step error: {type(e).__name__}: {e}")
        finally:
            state["ddd"] = False

    def broker_events():
        """What the broker does on this bar: triggers stop-losses/TPs and fills orders."""
        hits = sim.check_sl_tp_hits()

        def prio(h):
            pos = sim._positions.get(h["ticket"])
            if pos is None:
                return 9e9
            bar = sim.get_m15_bar(pos.symbol, Clock.now)
            op = bar["open"] if bar else pos.price_open
            return abs(h["price"] - op)

        sl_hits = sorted([h for h in hits if h["type"] == "sl"], key=prio)
        tp_hits = [h for h in hits if h["type"] != "sl"]
        for h in sl_hits:
            if h["ticket"] in sim._positions:
                sim.close_position(h["ticket"], close_price=h["price"])
                state["sl_hits"] += 1
                run_ddd_step()  # the live thread would look at equity after every hit
        for h in tp_hits:
            if h["ticket"] in sim._positions:
                sim.close_position(h["ticket"], close_price=h["price"])
        sim.check_pending_order_fills()
        sim.update_all_position_profits()

    def advance():
        state["i"] += 1
        if state["i"] >= len(timeline):
            raise KeyboardInterrupt()
        t = timeline[state["i"]]
        Clock.now = t
        sim.set_current_time(t)
        state["bars"] += 1
        wd = t.weekday()
        if wd == 5 or (wd == 6 and t.hour < 22):
            return  # market closed: the bot's own loop still ticks, the broker does nothing
        broker_events()
        run_ddd_step()
        # In reality the bot's 10-second loop notices a fill or a closed position within seconds,
        # long before its 5-minute orphan check. One loop pass per 15-minute bar would reverse that
        # order, so give the bot those two checks right after the broker has acted.
        for fn in (bot.check_pending_orders, bot.check_position_updates):
            try:
                fn()
            except Exception as e:  # noqa
                live.log.error(f"[replay] {fn.__name__} error: {type(e).__name__}: {e}")

    # Start on the first bar, then let the bot's own run() loop take over.
    advance()
    live.running = True
    try:
        bot.run()
    except KeyboardInterrupt:
        pass

    for pos in list(sim.get_my_positions()):
        sim.close_position(pos.ticket)

    closed = sim.get_closed_trades()
    acct = sim.get_account_info()
    fields = ["ticket", "symbol", "type", "volume", "open_price", "close_price", "open_time", "close_time",
              "pnl", "swap", "sl", "tp", "partial"]
    with open(out / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for t in closed:
            w.writerow({k: t.get(k) for k in fields})
    try:
        _stale = [sym for sym, st in bot.pending_setups.items() if st.status == "filled"
                  and bot.symbol_map.get(sym, sym) not in {p.symbol for p in sim.get_my_positions()}]
        _diag = {"setups": {k: v.status for k, v in bot.pending_setups.items()},
                 "stale_filled_setups": _stale,
                 "risk_manager_open_positions": len(bot.risk_manager.state.open_positions),
                 "challenge_mode": live.CHALLENGE_MODE}
    except Exception as _e:  # noqa
        _diag = {"diag_error": repr(_e)}
    summary = {"diag": _diag,
        "start": args.start, "end": args.end, "bars": state["bars"], "trades_rows": len(closed),
        "final_balance": acct.get("balance"), "withdrawn": getattr(sim, "_total_withdrawn", 0.0),
        "funded_level": getattr(sim, "_funded_level", None), "work_dir": str(work),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
