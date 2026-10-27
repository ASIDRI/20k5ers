#!/usr/bin/env python3
"""
Leak-free headline numbers: completed candles only (HTF_NO_LOOKAHEAD=1, now the default).

    run_full      11 years continuous funded run (like quant/current) without look-ahead
    run_challenge N random challenges (same starts as random_study), step 1 and 2 at 1.8% (live settings)
    report
"""
import concurrent.futures, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = REPO / "backtest" / "output" / "replay" / "clean"
OUT.mkdir(parents=True, exist_ok=True)
os.environ["HTF_NO_LOOKAHEAD"] = "1"
spec = importlib.util.spec_from_file_location("la", str(HERE / "w5_lookahead_test.py")); la = importlib.util.module_from_spec(spec); spec.loader.exec_module(la)


def run_full():
    d = OUT / "full_2015_2025"
    if (d / "results.json").exists():
        return
    d.mkdir(parents=True, exist_ok=True)
    env, tp = la.env_tp()
    e = dict(os.environ); e.update({k: str(v) for k, v in env.items()}); e["OPT_PARAMS"] = json.dumps(tp)
    e["PYTHONUTF8"] = "1"; e["HTF_NO_LOOKAHEAD"] = "1"
    subprocess.run([sys.executable, str(HERE / "main_live_bot_backtest.py"), "--start", "2015-01-02", "--end", "2025-12-31",
                    "--balance", "50000", "--output", str(d), "--quiet"], env=e, cwd=str(REPO), capture_output=True, text=True,
                   timeout=12 * 3600)


def run_challenge(n):
    spec2 = importlib.util.spec_from_file_location("wv", str(HERE / "w5_variants.py")); wv = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(wv)
    starts = wv.rs.challenge_starts(100)[:n]
    store_p = OUT / "challenges.json"
    store = json.loads(store_p.read_text()) if store_p.exists() else {}
    todo = [s for s in starts if s not in store or store[s].get("error")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("CL_WORKERS", "2"))) as ex:
        futs = {ex.submit(wv.challenge_one, "s1_18", s): s for s in todo}
        for f in concurrent.futures.as_completed(futs):
            try:
                r = f.result()
            except Exception as e:  # noqa
                r = {"error": repr(e)}
            store = json.loads(store_p.read_text()) if store_p.exists() else {}
            store[futs[f]] = r
            store_p.write_text(json.dumps(store))


def report():
    p = OUT / "full_2015_2025" / "results.json"
    if p.exists():
        r = json.loads(p.read_text())
        print(f"11-year funded run, completed candles only: net pnl {r.get('net_pnl', 0):,.0f} | withdrawn "
              f"{r.get('fiveers_total_withdrawn', 0):,.0f} | trades {r.get('total_trades')} | win {r.get('win_rate', 0):.1f}% | "
              f"failed {r.get('account_failed')} {r.get('fail_info') or ''}")
    p = OUT / "challenges.json"
    if p.exists():
        d = json.loads(p.read_text()); v = [x for x in d.values() if not x.get("error")]
        ok = sorted(x["total"] for x in v if x.get("total")); br = sum(1 for x in v if x.get("breach"))
        print(f"challenges (steps 1+2 at 1.8%): {len(ok)}/{len(v)} passed, {br} breached, {len(v)-len(ok)-br} too slow"
              + (f", median {ok[len(ok)//2]} days" if ok else ""))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run_full":
        run_full()
    elif cmd == "run_challenge":
        run_challenge(int(sys.argv[2]))
    report()
