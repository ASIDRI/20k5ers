#!/usr/bin/env python3
"""
Does the simulator's higher-timeframe look-ahead change the results?

Runs the headline configuration (frozen baseline + realistic costs + climb cap) over one-year windows twice:
HTF_NO_LOOKAHEAD=0 (as every stored result was made) and =1 (completed candles only, like the real MT5).

    uv run python3 backtest/src/w5_lookahead_test.py run     # runs missing arms (3 in parallel)
    uv run python3 backtest/src/w5_lookahead_test.py report
"""
import concurrent.futures, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = REPO / "backtest" / "output" / "replay" / "lookahead"
WINDOWS = [("2016-01-04", "2016-12-30"), ("2018-01-02", "2018-12-31"), ("2019-01-02", "2019-12-31"),
           ("2021-01-04", "2021-12-31"), ("2023-01-02", "2023-12-29")]
WORKERS = int(os.environ.get("LA_WORKERS", "3"))


def env_tp():
    spec = importlib.util.spec_from_file_location("rs", str(HERE / "w5_random_study.py"))
    rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs)
    w5 = rs.w5
    env, tp = rs.live_config()
    full = {**w5.cs.dh.BASE_ENV, **env}
    full.update(FIVEERS_MAX_SCALE="500000", FUNDED_CLIMB_RISK_PCT="1.8", BROKER_TYPE="fiveers_live")
    return full, {**w5.cs.dh.BASE_TP, **tp}


def run_one(arm):
    flag, (a, b) = arm
    d = OUT / f"nola{flag}_{a}"
    if (d / "results.json").exists():
        return arm
    d.mkdir(parents=True, exist_ok=True)
    env, tp = env_tp()
    e = dict(os.environ); e.update({k: str(v) for k, v in env.items()})
    e["OPT_PARAMS"] = json.dumps(tp); e["PYTHONUTF8"] = "1"; e["HTF_NO_LOOKAHEAD"] = str(flag)
    subprocess.run([sys.executable, str(HERE / "main_live_bot_backtest.py"), "--start", a, "--end", b,
                    "--balance", "50000", "--output", str(d), "--quiet"], env=e, cwd=str(REPO),
                   capture_output=True, text=True, timeout=4 * 3600)
    return arm


def report():
    print(f"{'window':24} {'look-ahead':>12} {'net pnl':>12} {'trades':>7} {'win%':>6} {'PF-ish':>7} {'maxDDD':>7} {'failed':>7}")
    for a, b in WINDOWS:
        for flag, name in ((0, "as before"), (1, "completed only")):
            p = OUT / f"nola{flag}_{a}" / "results.json"
            if not p.exists():
                print(f"{a}..{b[:4]:<12} {name:>12}   (missing)"); continue
            r = json.loads(p.read_text())
            print(f"{a}..{b[:7]:<12} {name:>14} {r.get('net_pnl', 0):>12,.0f} {r.get('total_trades', 0):>7} "
                  f"{r.get('win_rate', 0):>6.1f} {'':>7} {r.get('max_ddd_pct', 0) or 0:>7.2f} {str(bool(r.get('account_failed'))):>7}")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        arms = [(f, w) for w in WINDOWS for f in (0, 1)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for a in ex.map(run_one, arms):
                print("done", a, flush=True)
    report()
