#!/usr/bin/env python3
"""
Parity audit: does the LIVE bot make the same decisions as the backtest that
produced the headline numbers?

w5_acceptance.py checks the frozen config keys. This audit goes further and
compares what the code actually does:

  1  EFFECTIVE strategy parameters: params/current_params.json (what live loads)
     against the parameters the backtest really ran with (file + the overlay the
     test scripts inject). Every field must match.
  2  RISK LADDER, numerically: the drawdown -> risk chain is cut out of both
     sources and run over a grid of (base risk, daily loss, total drawdown);
     the live chain with deployment defaults against the backtest chain with the
     frozen environment. Any different answer fails.
  3  STOP-LOSS after each take-profit uses the optimised sl_after_tp*_r.
  4  FRIDAY cut-off time is the same in both engines.
  5  CLOSE-ALL daily stop follows CFG_DAILY_HALT_PCT in both.
  6  DEFAULTS: every env var the backtest run sets that live also reads must have
     the same literal default in live (or be listed as a deliberate divergence).

Exit code 0 = identical, 1 = divergences. Run:
    uv run python3 backtest/src/w5_parity_audit.py
"""
import ast
import dataclasses
import importlib.util
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LIVE = REPO / "main_live_bot.py"
BT = HERE / "main_live_bot_backtest.py"

fails = []


def ok(msg):
    print(f"  OK    {msg}")


def bad(msg):
    print(f"  FAIL  {msg}")
    fails.append(msg)


def load_w5():
    spec = importlib.util.spec_from_file_location("w5c", str(HERE / "w5_common.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def backtest_env_and_tp(w5):
    """The exact env + params overlay of the 4M-dollar runs (w5_random_study.live_config)."""
    frozen = json.loads((w5.W5_DIR / "BASELINE_t65_tdd_FROZEN.json").read_text())
    env = {**w5.cs.dh.BASE_ENV, **w5.BASE_ENV, **frozen["env"]}
    tp = {**w5.cs.dh.BASE_TP, **w5.BASE_TP, **frozen["tp"]}
    return env, tp


# ── 1 ───────────────────────────────────────────────────────────────────────
def check_params(tp):
    print("\n1. Effective strategy parameters (live file vs what the backtest ran)")
    sys.path.insert(0, str(REPO))
    from params.params_loader import load_strategy_params
    live = dataclasses.asdict(load_strategy_params())
    bad_keys = []
    for k, want in sorted(tp.items()):
        if k not in live:
            continue  # not a StrategyParams field: the backtest ignores it too
        got = live[k]
        same = (abs(float(got) - float(want)) < 1e-9) if isinstance(want, (int, float)) and not isinstance(want, bool) \
            and isinstance(got, (int, float)) else got == want
        if not same:
            bad_keys.append(k)
            bad(f"param {k}: live {got!r}, backtest ran {want!r}")
    if not bad_keys:
        ok(f"all {len([k for k in tp if k in live])} overlay parameters identical")


# ── 2 ───────────────────────────────────────────────────────────────────────
_LADDER_RUNNER = r'''
import json, os, re, sys, textwrap
from pathlib import Path
REPO = Path(sys.argv[2]); mode = sys.argv[1]
sys.path.insert(0, str(REPO))
import ftmo_config
C = ftmo_config.FIVEERS_CONFIG
live_src = (REPO / "main_live_bot.py").read_text(encoding="utf-8")
bt_src = (REPO / "backtest/src/main_live_bot_backtest.py").read_text(encoding="utf-8")
ns = {"os": os, "FIVEERS_CONFIG": C}
if mode == "live":
    for name in ("_w5_tdd_emergency_pct", "_w5_tdd_warning_pct", "_w5_risk_conservative",
                 "_w5_risk_ultrasafe", "_w5_tdd_caution", "_w5_risk_cautious"):
        m = re.search(rf"^def {name}\(\):.*?(?=\n\n\n)", live_src, re.S | re.M)
        assert m, f"{name} missing in live"
        exec(m.group(0), ns)
    a = live_src.index("if daily_loss_pct >= FIVEERS_CONFIG.daily_loss_reduce_pct or total_dd_pct >=")
    b = live_src.index("# ── W5 PORT: regime-coherent risk multiplier")
    block = live_src[a:b]
else:
    a = bt_src.index("if daily_loss_pct >= FIVEERS_CONFIG.daily_loss_reduce_pct or total_dd_pct >=")
    b = bt_src.index('log.info(f"[{symbol}] Risk: {risk_pct:.3f}%')
    block = bt_src[a:b]
code = textwrap.dedent(" " * 8 + block)
out = {}
for base in (2.7, 1.8, 0.6, 0.4):
    for d in [x * 0.25 for x in range(0, 15)]:
        for t in [x * 0.25 for x in range(0, 41)]:
            l = {"base_risk": base, "daily_loss_pct": d, "total_dd_pct": t}
            exec(code, dict(ns), l)
            out[f"{base}|{d}|{t}"] = round(l["risk_pct"], 6)
print(json.dumps(out))
'''


def check_ladder(env):
    print("\n2. Risk ladder, numerically (base risk x daily loss x total drawdown grid)")
    runner = HERE.parent / "output" / "doe" / "wall5" / "_ladder_runner.py"
    runner.write_text(_LADDER_RUNNER)
    try:
        # backtest: full frozen environment; live: deployment defaults (no strategy env).
        e_bt = {k: v for k, v in os.environ.items()}
        e_bt.update({k: str(v) for k, v in env.items()})
        e_live = {k: v for k, v in os.environ.items()
                  if not k.startswith(("CFG_", "RISK_", "TDD_", "NIGHTLY_", "VOL_", "FUNDED_", "STEP2_"))}
        res = {}
        for mode, e in (("bt", e_bt), ("live", e_live)):
            p = subprocess.run([sys.executable, str(runner), mode, str(REPO)], env=e,
                               capture_output=True, text=True, cwd=str(REPO))
            if p.returncode != 0:
                bad(f"ladder runner ({mode}) crashed: {p.stderr.strip().splitlines()[-1] if p.stderr.strip() else '?'}")
                return
            res[mode] = json.loads(p.stdout.strip().splitlines()[-1])
        diffs = [(k, res["live"][k], res["bt"][k]) for k in res["bt"] if res["live"].get(k) != res["bt"][k]]
        if diffs:
            for k, lv, bv in diffs[:8]:
                base, d, t = k.split("|")
                bad(f"ladder base {base}% daily {float(d):.2f}% total {float(t):.2f}%: live {lv}%, backtest {bv}%")
            if len(diffs) > 8:
                bad(f"... and {len(diffs) - 8} more grid points differ")
        else:
            ok(f"identical on all {len(res['bt'])} grid points")
    finally:
        try:
            runner.unlink()
        except OSError:
            pass



_SL_TEST = r'''
import sys, types, io, logging
sys.path.insert(0, sys.argv[1])
import main_live_bot as m
from strategy_core import StrategyParams
class R:  # result
    def __init__(s, price=0): s.success = True; s.price = price; s.error = ""
class Pos:
    def __init__(s, t, sym, vol): s.ticket = t; s.symbol = sym; s.volume = vol
class Tick:
    def __init__(s, p): s.bid = p; s.ask = p
class FakeMT5:
    def __init__(s): s.price = 1.0; s.sl = []; s.vol = 1.0
    def get_my_positions(s): return [Pos(7, "EURUSD", s.vol)]
    def get_tick(s, sym): return Tick(s.price)
    def partial_close(s, t, v, **k): s.vol = round(s.vol - v, 2); return R(s.price)
    def modify_sl_tp(s, t, sl=None, tp=None): 
        if sl is not None: s.sl.append(sl)
        return True
    def close_position(s, t, **k): return R(s.price)
p = StrategyParams()
for k, v in dict(tp1_r_multiple=0.65, tp2_r_multiple=1.85, tp3_r_multiple=2.75, tp1_close_pct=0.25,
                 tp2_close_pct=0.6, tp3_close_pct=0.15, tp4_close_pct=0.0, tp5_close_pct=0.0,
                 sl_after_tp1_r=-0.1, sl_after_tp2_r=0.9, sl_after_tp3_r=1.7).items():
    setattr(p, k, v)
setup = types.SimpleNamespace(order_ticket=7, status="filled", direction="bullish", entry_price=1.0,
                              stop_loss=0.99, lot_size=1.0, partial_closes=0, symbol="EURUSD")
fake = FakeMT5()
bot = types.SimpleNamespace(mt5=fake, pending_setups={"EUR_USD": setup}, symbol_map={"EUR_USD": "EURUSD"},
                            params=p, _save_pending_setups=lambda: None,
                            _update_ticket_after_partial_close=lambda t, s, st, tp: t)
risk = 0.01
fake.price = 1.0 + 0.65 * risk + 1e-9
m.LiveTradingBot.manage_partial_takes(bot)
fake.price = 1.0 + 1.85 * risk + 1e-9
m.LiveTradingBot.manage_partial_takes(bot)
want = [1.0 - 0.1 * risk, 1.0 + 0.9 * risk]
got = [round(x, 6) for x in fake.sl[:2]]
want = [round(x, 6) for x in want]
if got != want:
    print(f"SLTEST FAIL stop after TP1/TP2 = {got}, backtest rule gives {want}"); sys.exit(1)
print("SLTEST OK stop after TP1 = -0.10R and after TP2 = +0.90R, exactly the backtest rule")
'''

# ── 3-5 ─────────────────────────────────────────────────────────────────────
def fn_src(path, name):
    src = path.read_text(encoding="utf-8")
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n) or ""
    return ""


def check_static():
    print("\n3. Stop-loss after each take-profit")
    live_tp = fn_src(LIVE, "manage_partial_takes")
    for k in ("sl_after_tp1_r", "sl_after_tp2_r", "sl_after_tp3_r", "sl_after_tp4_r"):
        if f"self.params, '{k}'" in live_tp:
            ok(f"live uses {k}")
        else:
            bad(f"live manage_partial_takes does not read {k}")
    if re.search(r"risk \* 0\.1\)", live_tp):
        bad("live still has a hardcoded 0.1R stop after TP1")

    # Behaviour, not just text: run the real live function against a fake MT5.
    _beh = subprocess.run([sys.executable, "-c", _SL_TEST, str(REPO)], capture_output=True, text=True,
                          env={**os.environ, "BROKER_TYPE": "fiveers_live", "MT5_LOGIN": "1",
                               "MT5_PASSWORD": "x", "MT5_SERVER": "s", "PYTHONUTF8": "1"})
    last = (_beh.stdout.strip().splitlines() or ["?"])[-1]
    if _beh.returncode == 0 and last.startswith("SLTEST OK"):
        ok(f"behaviour: {last[len('SLTEST OK '):]}")
    else:
        bad(f"behaviour test of manage_partial_takes failed: {last or _beh.stderr.strip().splitlines()[-1:]}")

    print("\n4. Friday cut-off time")
    live_f = LIVE.read_text(encoding="utf-8")
    bt_f = BT.read_text(encoding="utf-8")
    pat = "hour > 19 or (hour == 19 and minute >= 30)"
    if pat in live_f and pat in bt_f:
        ok("both engines: Friday 19:30 UTC")
    else:
        bad("Friday cut-off differs (live must be 19:30 UTC like the backtest)")
    if "now.hour > 18" in live_f:
        bad("live still has a Friday 18:30 check")

    print("\n5. Close-all daily stop")
    if "base_halt_pct = _w5_daily_halt_pct()" in live_f and 'os.getenv("CFG_DAILY_HALT_PCT"' in bt_f:
        ok("both engines: close-all stop follows CFG_DAILY_HALT_PCT")
    else:
        bad("close-all daily stop differs: live must use _w5_daily_halt_pct() like the backtest")
    if "total_dd_pct >= 7.0 and _w5_tdd_emergency_halt_enabled()" in live_f:
        ok("live TDD scan-block is gated by TDD_EMERGENCY_HALT (like the backtest)")
    else:
        bad("live blocks scans at TDD 7% regardless of TDD_EMERGENCY_HALT")


# ── 6 ───────────────────────────────────────────────────────────────────────
# Deliberate differences, each with the reason. Anything else must match.
DELIBERATE = {
    "NIGHTLY_DERISK_HOUR": "backtest 22 UTC; live runs on New York time (see acceptance note)",
    "BROKER_TYPE": "harness sets it; live reads it from the environment",
    "CFG_DAILY_WALL_PCT": "the broker enforces the real wall",
    "DDD_CLOSE_AT_TRIGGER": "simulator fill fidelity",
    "TDD_WORST_CASE": "measurement convention", "TERMINAL_ON_BREACH": "harness control",
    "SLIPPAGE_PIPS": "cost model of the simulator", "SLIPPAGE_MAP": "cost model of the simulator",
    "COST_LIMIT_ENTRIES": "cost model of the simulator", "GAP_FILLS": "simulator fidelity",
    "FIVEERS_MAX_SCALE": "simulator account ladder cap", "VOL_SIZE_ENABLE": "off in both",
    "VOL_SIZE_MULT_HIGH": "inert (VOL_SIZE_ENABLE=0)", "VOL_SIZE_MULT_LOW": "inert (VOL_SIZE_ENABLE=0)",
    "SPX500_ENABLE": "universe flag read elsewhere", "OIL_ENABLE": "universe flag read elsewhere",
    "PEG_GUARD_VOL": "live default 2.5 == backtest arm value", "EXCLUDE_SYMBOLS": "compared as a list in acceptance",
}


def literal_defaults(src, name):
    out = set()
    for m in re.finditer(rf'os\.(?:getenv|environ\.get)\(\s*["\']{name}["\']\s*,\s*["\']([^"\']*)["\']\s*\)', src):
        out.add(m.group(1))
    return out


def check_defaults(env):
    print("\n6. Environment defaults: backtest run values vs live literal defaults")
    live_src = LIVE.read_text(encoding="utf-8")
    for extra in ("broker_config.py", "weekend_gap_manager.py", "challenge_risk_manager.py"):
        pth = REPO / extra
        if pth.exists():
            live_src += "\n" + pth.read_text(encoding="utf-8")
    n_ok = n_skip = 0
    for k in sorted(env):
        if k in DELIBERATE:
            n_skip += 1
            continue
        lits = literal_defaults(live_src, k)
        if not lits:
            continue
        want = str(env[k]).strip()
        for lit in lits:
            try:
                same = abs(float(lit) - float(want)) < 1e-9
            except ValueError:
                same = lit.strip() == want
            if same:
                n_ok += 1
            else:
                bad(f"{k}: live default {lit!r}, backtest ran {want!r}")
    ok(f"{n_ok} defaults match, {n_skip} listed as deliberate divergences")


def main():
    print("=" * 74)
    print("PARITY AUDIT: live bot vs the backtest behind the headline results")
    print("=" * 74)
    w5 = load_w5()
    env, tp = backtest_env_and_tp(w5)
    check_params(tp)
    check_ladder(env)
    check_static()
    check_defaults(env)
    print("\n" + "=" * 74)
    if fails:
        print(f"PARITY: FAIL, {len(fails)} divergence(s)")
        sys.exit(1)
    print("PARITY: PASS, live decisions match the backtest on every audited point")
    sys.exit(0)


if __name__ == "__main__":
    main()
