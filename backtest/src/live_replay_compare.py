#!/usr/bin/env python3
"""
Run the live bot (live_replay.py) and the backtest engine over the SAME window, same
environment and same data, then compare the trades.

    uv run python3 backtest/src/live_replay_compare.py --start 2019-03-04 --end 2019-04-30 --tag a

The environment is the one behind the headline results (frozen baseline + realistic costs + climb cap,
CHALLENGE_STEP=funded so both start funded at 1.8% below $300k).
Outputs in backtest/output/replay/<tag>/: live/ (replay) and bt/ (backtest), plus compare.json.
"""
import argparse, csv, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def load_env():
    spec = importlib.util.spec_from_file_location("rs", str(HERE / "w5_random_study.py"))
    rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs)
    w5 = rs.w5
    env, tp = rs.live_config()
    full = {**w5.cs.dh.BASE_ENV, **env}
    full.update(FIVEERS_MAX_SCALE="500000", FUNDED_CLIMB_RISK_PCT="1.8", CHALLENGE_STEP="funded",
                BROKER_TYPE="fiveers_live")
    return full, {**w5.cs.dh.BASE_TP, **tp}, w5


def read_trades(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--tag", default="run"); ap.add_argument("--set", action="append", default=[],
                    help="extra KEY=VALUE for BOTH sides (to isolate a difference)")
    ap.add_argument("--skip-live", action="store_true"); ap.add_argument("--skip-bt", action="store_true")
    a = ap.parse_args()
    out = REPO / "backtest" / "output" / "replay" / a.tag
    (out / "live").mkdir(parents=True, exist_ok=True); (out / "bt").mkdir(parents=True, exist_ok=True)
    env, tp, w5 = load_env()
    for kv in a.set:
        k, v = kv.split("=", 1); env[k] = v
    envfile = out / "env.json"; envfile.write_text(json.dumps(env, indent=1))

    if not a.skip_live:
        e = dict(os.environ); e["PYTHONUTF8"] = "1"
        subprocess.run([sys.executable, str(HERE / "live_replay.py"), "--start", a.start, "--end", a.end,
                        "--out", str(out / "live"), "--env-json", str(envfile)],
                       env=e, cwd=str(REPO), capture_output=True, text=True)
    if not a.skip_bt:
        e = dict(os.environ); e.update(env); e["OPT_PARAMS"] = json.dumps(tp); e["PYTHONUTF8"] = "1"
        subprocess.run([sys.executable, str(HERE / "main_live_bot_backtest.py"), "--start", a.start, "--end", a.end,
                        "--balance", "50000", "--output", str(out / "bt"), "--quiet"],
                       env=e, cwd=str(REPO), capture_output=True, text=True)

    L = read_trades(out / "live" / "trades.csv"); B = read_trades(out / "bt" / "trades.csv")

    def norm(sym):
        return {"UK100": "UK100USD", "XTIUSD": "XTIUSD", "XBRUSD": "XBRUSD"}.get(sym.replace("_", ""), sym.replace("_", ""))

    def key(r):
        return (norm(r["symbol"]), (r.get("open_time") or "")[:16], r.get("type", ""))

    def full(rows):
        return [r for r in rows if str(r.get("partial", "")).lower() not in ("true", "1")]
    Lf, Bf = full(L), full(B)
    lk = {key(r): r for r in Lf}; bk = {key(r): r for r in Bf}
    both = sorted(set(lk) & set(bk)); only_l = sorted(set(lk) - set(bk)); only_b = sorted(set(bk) - set(lk))
    pnl = lambda rows: round(sum(float(r["pnl"]) + float(r.get("swap") or 0) for r in rows), 2)
    res = {"window": [a.start, a.end], "live_rows": len(L), "bt_rows": len(B), "live_full": len(Lf), "bt_full": len(Bf),
           "matched": len(both), "only_live": [list(k) for k in only_l], "only_bt": [list(k) for k in only_b],
           "live_pnl": pnl(L), "bt_pnl": pnl(B)}
    (out / "compare.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k not in ("only_live", "only_bt")}, indent=1))
    print("only in live  :", res["only_live"][:15]); print("only in backtest:", res["only_bt"][:15])


if __name__ == "__main__":
    main()
