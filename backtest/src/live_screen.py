#!/usr/bin/env python3
"""
Test parameter sets with the REAL live bot (live_replay.py): same code as on MT5, completed candles only.

Every set runs at 1.0% base risk on a flat $50k account (no 5ers scaling), through breaches, so the
numbers measure the edge per trade, not survival luck. The live bot's own protections stay on, except the permanent total-drawdown stop (--validated-halts).

    uv run python3 backtest/src/live_screen.py run 2019-01-02 2019-12-31 [key1,key2,...]
    uv run python3 backtest/src/live_screen.py report
"""
import concurrent.futures, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BASE = REPO / "backtest" / "output" / "live_screen"
CANDS = REPO / "backtest" / "output" / "oldparams" / "cands"
WORKERS = int(os.environ.get("LS_WORKERS", "4"))
ENV_SRC = os.environ.get("LS_ENV", "")


def run_one(job):
    key, a, b = job
    d = BASE / a[:4] / key
    if (d / "summary.json").exists():
        return job
    d.mkdir(parents=True, exist_ok=True)
    p = json.loads((CANDS / f"{key}.json").read_text())
    p = p.get("parameters", p); p["risk_per_trade_pct"] = 1.0
    (d / "params.json").write_text(json.dumps(p))
    env = json.loads(Path(ENV_SRC).read_text())
    env.update({"FIVEERS_SCALING_OFF": "1", "HTF_NO_LOOKAHEAD": "1", "CHALLENGE_STEP": "funded"})
    (d / "env.json").write_text(json.dumps(env))
    subprocess.run([sys.executable, str(HERE / "live_replay.py"), "--start", a, "--end", b, "--out", str(d),
                    "--env-json", str(d / "env.json"), "--params-json", str(d / "params.json"), "--no-stop-on-breach", "--validated-halts"],
                   cwd=str(REPO), capture_output=True, text=True, timeout=6 * 3600)
    return job


def report():
    for yd in sorted(p for p in BASE.iterdir() if p.is_dir()):
        rows = []
        for d in yd.iterdir():
            f = d / "summary.json"
            if f.exists():
                rows.append((d.name, json.loads(f.read_text())))
        rows.sort(key=lambda x: -(x[1].get("trading_pnl") or 0))
        print(f"\n== {yd.name}: {len(rows)} sets, real live bot, 1% risk, flat $50k, completed candles")
        print(f"  {'set':12} {'P&L':>10} {'trades':>7} {'win%':>6} {'PF':>6} {'maxDDD':>7} {'maxTDD':>7} {'halted':>7}")
        for k, s in rows:
            print(f"  {k:12} {s.get('trading_pnl', 0):>10,.0f} {s.get('trades', 0):>7} {s.get('win_rate', 0):>6.1f} "
                  f"{(s.get('profit_factor') or 0):>6.2f} {s.get('max_daily_dd_pct', 0):>7.2f} {s.get('max_total_dd_pct', 0):>7.2f} "
                  f"{str(s.get('bot_halted')):>7}")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        a, b = sys.argv[2], sys.argv[3]
        keys = sys.argv[4].split(",") if len(sys.argv) > 4 else sorted(p.stem for p in CANDS.glob("*.json"))
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for j in ex.map(run_one, [(k, a, b) for k in keys]):
                print("done", j, flush=True)
    report()
