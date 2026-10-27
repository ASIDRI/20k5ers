#!/usr/bin/env python3
"""
Re-test every historical parameter set on the leak-free simulator (completed candles only).

Same footing for all: 1.0% risk per trade, flat $50k (no 5ers scaling), realistic costs,
no W5 extras (backtest defaults), run continues through breaches so the full year counts.

    uv run python3 backtest/src/oldparams_screen.py run 2019-01-02 2019-12-31
    uv run python3 backtest/src/oldparams_screen.py report
"""
import concurrent.futures, csv, glob, importlib.util, json, os, subprocess, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BASE = REPO / "backtest" / "output" / "oldparams"
CANDS = BASE / "cands"
WORKERS = int(os.environ.get("OP_WORKERS", "3"))


def base_env():
    spec = importlib.util.spec_from_file_location("cr", str(HERE / "w5_costs_real.py"))
    env = {"BROKER_TYPE": "fiveers_live", "HTF_NO_LOOKAHEAD": "1", "FIVEERS_SCALING_OFF": "1",
           "TERMINAL_ON_BREACH": "0", "COST_LIMIT_ENTRIES": "1"}
    try:
        cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
        env["SLIPPAGE_MAP"] = json.dumps(cr.spread_map_real(1.0))
    except Exception:
        spec = importlib.util.spec_from_file_location("rs", str(HERE / "w5_random_study.py"))
        rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs)
        env["SLIPPAGE_MAP"] = rs.live_config()[0]["SLIPPAGE_MAP"]
    return env


def run_one(job):
    key, a, b = job
    d = BASE / f"{a[:4]}" / key
    if (d / "results.json").exists():
        return job
    d.mkdir(parents=True, exist_ok=True)
    p = json.loads((CANDS / f"{key}.json").read_text())
    p["parameters"]["risk_per_trade_pct"] = 1.0
    pf = d / "params.json"; pf.write_text(json.dumps(p))
    e = dict(os.environ); e.update(ENV); e["PYTHONUTF8"] = "1"; e.pop("OPT_PARAMS", None)
    subprocess.run([sys.executable, str(HERE / "main_live_bot_backtest.py"), "--start", a, "--end", b,
                    "--balance", "50000", "--output", str(d), "--quiet", "--params-file", str(pf)],
                   env=e, cwd=str(REPO), capture_output=True, text=True)
    return job


def metrics(d):
    r = json.loads((d / "results.json").read_text())
    pos = defaultdict(float)
    for t in csv.DictReader(open(d / "trades.csv")):
        pos[str(t["ticket"]).split("_")[0]] += float(t["pnl"]) + float(t.get("swap") or 0)
    gp = sum(v for v in pos.values() if v > 0); gl = -sum(v for v in pos.values() if v <= 0)
    return {"pnl": sum(pos.values()), "trades": len(pos), "win": 100 * sum(v > 0 for v in pos.values()) / max(1, len(pos)),
            "pf": gp / gl if gl else 0, "maxddd": r.get("max_ddd_pct") or 0, "maxtdd": r.get("max_tdd_pct") or 0}


def report():
    for yd in sorted(p for p in BASE.iterdir() if p.is_dir() and p.name.isdigit()):
        rows = []
        for d in yd.iterdir():
            if (d / "results.json").exists():
                rows.append((d.name, metrics(d)))
        rows.sort(key=lambda x: -x[1]["pnl"])
        print(f"\n== {yd.name}: {len(rows)} parameter sets (1% risk, flat $50k, completed candles)")
        print(f"  {'set':12} {'P&L':>10} {'trades':>7} {'win%':>6} {'PF':>5} {'maxDDD':>7} {'maxTDD':>7}")
        for k, m in rows:
            print(f"  {k:12} {m['pnl']:>10,.0f} {m['trades']:>7} {m['win']:>6.1f} {m['pf']:>5.2f} {m['maxddd']:>7.2f} {m['maxtdd']:>7.2f}")


ENV = {}
if __name__ == "__main__":
    if sys.argv[1] == "run":
        ENV.update(base_env())
        a, b = sys.argv[2], sys.argv[3]
        keys = sys.argv[4].split(",") if len(sys.argv) > 4 else [p.stem for p in CANDS.glob("*.json")]
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for j in ex.map(run_one, [(k, a, b) for k in keys]):
                print("done", j, flush=True)
    report()
