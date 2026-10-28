"""Audit phase 2: per version, its OWN backtest as it was (A), the same with completed candles only (B),
and its LIVE bot in the replay (C: fake MT5 that serves completed candles only, M15 fills, 5ers measurement).

    python backtest/src/audit_run.py queue --versions V3,V4,V5,V6,V7 --years 2023 --workers 4
    python backtest/src/audit_run.py table

Start it detached and without any time limit:
    backtest/run_job.sh audit2023 .venv/bin/python backtest/src/audit_run.py queue --versions V3,V4,V5,V6,V7 --years 2023

A run is the version's backtest/src/main_live_bot_backtest.py, started inside its unpacked code
(backtest/output/audit/<V>/code, see audit_versions.py) with its own params and default balance.
B differs from A only by AUDIT_CANDLES=exact (the shared referee, candle_avail.py).
C runs the version's main_live_bot.py through live_replay.py --code-root, with the version's default backtest
balance; an operator restart the next day after a bot halt, and trading continues after a 5ers breach so the
whole year is compared (both are reported in summary.json).
Each run writes backtest/output/audit/<V>/runs/<year>_<A|B>/ (results.json, trades.csv, run.log).
Runs that already have results.json are skipped, so the queue can be restarted after a reboot.
"""
import argparse
import json
import os
import subprocess
import sys
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "backtest" / "output" / "audit"
PY = str(ROOT / ".venv" / "bin" / "python")


def run_dir(v, year, mode):
    return AUDIT / v / "runs" / f"{year}_{mode}"


def default_balance(code):
    s = (code / "backtest" / "src" / "main_live_bot_backtest.py").read_text(errors="replace")
    m = re.search(r"'--balance', type=float, default=([0-9.]+)", s)
    return m.group(1) if m else "50000"


def done_file(v, year, mode):
    return run_dir(v, year, mode) / ("summary.json" if mode == "C" else "results.json")


def start(v, year, mode):
    code = (AUDIT / v / "code") if v != "V10" else ROOT
    out = run_dir(v, year, mode)
    out.mkdir(parents=True, exist_ok=True)
    if mode == "C":
        cmd = [PY, "-u", str(ROOT / "backtest" / "src" / "live_replay.py"), "--start", f"{year}-01-01",
               "--end", f"{year}-12-31", "--balance", default_balance(code), "--out", str(out),
               "--code-root", str(code), "--env-json", str(ROOT / "backtest" / "output" / "replay" / "live_env.json"),
               "--restart-after-halt", "--no-stop-on-breach"]
        env = dict(os.environ, PYTHONUTF8="1", HTF_NO_LOOKAHEAD="1")
        (out / "cmd.json").write_text(json.dumps({"cwd": str(ROOT), "cmd": cmd}, indent=1))
        log = open(out / "run.log", "w")
        return subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    env = dict(os.environ, PYTHONUTF8="1")
    env.pop("AUDIT_CANDLES", None)
    if mode == "B":
        env["AUDIT_CANDLES"] = "exact"
    cmd = [PY, "-u", "backtest/src/main_live_bot_backtest.py", "--start", f"{year}-01-01", "--end", f"{year}-12-31",
           "--output", str(out)]
    (out / "cmd.json").write_text(json.dumps({"cwd": str(code), "cmd": cmd, "AUDIT_CANDLES": env.get("AUDIT_CANDLES")}, indent=1))
    log = open(out / "run.log", "w")
    return subprocess.Popen(cmd, cwd=code, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)


def queue(versions, years, workers, modes):
    jobs = [(v, y, m) for y in years for v in versions for m in modes
            if not done_file(v, y, m).exists()]
    running = []
    print(f"{len(jobs)} runs to do, {workers} at a time", flush=True)
    while jobs or running:
        while jobs and len(running) < workers:
            j = jobs.pop(0)
            running.append((j, start(*j)))
            print(f"started {j}", flush=True)
        time.sleep(30)
        for j, p in list(running):
            if p.poll() is not None:
                running.remove((j, p))
                ok = done_file(*j).exists()
                print(f"finished {j} exit={p.returncode} results={'yes' if ok else 'NO'}", flush=True)
    table()


def table():
    rows = []
    for vdir in sorted(AUDIT.glob("V*"), key=lambda p: int(p.name[1:])):
        for r in sorted((vdir / "runs").glob("*_*")) if (vdir / "runs").exists() else []:
            f = r / "results.json"
            if (r / "summary.json").exists():
                c = json.loads((r / "summary.json").read_text())
                b = float(re.search(r'"--balance", "([0-9.]+)"', (r / "cmd.json").read_text()).group(1))
                d = {"initial_balance": b, "return_pct": round(100 * (c.get("trading_pnl") or 0) / b, 1),
                     "total_trades": c.get("trades"), "win_rate": c.get("win_rate"),
                     "max_ddd_pct": c.get("max_daily_dd_pct"), "max_tdd_pct": c.get("max_total_dd_pct")}
            elif f.exists():
                d = json.loads(f.read_text())
            else:
                continue
            rows.append((vdir.name, r.name, d.get("initial_balance"), d.get("return_pct"), d.get("total_trades"),
                         d.get("win_rate"), d.get("max_ddd_pct"), d.get("max_tdd_pct")))
    print(f"{'versie':6} {'run':8} {'start':>9} {'rend.%':>8} {'trades':>6} {'win%':>5} {'maxDag%':>7} {'maxTot%':>7}")
    for v, r, b, ret, n, wr, ddd, tdd in rows:
        print(f"{v:6} {r:8} {b or 0:9.0f} {ret if ret is not None else float('nan'):8.1f} {n or 0:6} {wr or 0:5.1f} "
              f"{ddd if ddd is not None else float('nan'):7.2f} {tdd if tdd is not None else float('nan'):7.2f}")
    (AUDIT / "phase2_table.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["queue", "table"])
    ap.add_argument("--versions", default="V3,V4,V5,V6,V7")
    ap.add_argument("--years", default="2023")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--modes", default="A,B,C")
    a = ap.parse_args()
    if a.cmd == "queue":
        queue(a.versions.split(","), a.years.split(","), a.workers, a.modes.split(","))
    else:
        table()
