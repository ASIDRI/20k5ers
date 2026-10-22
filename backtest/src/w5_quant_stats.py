#!/usr/bin/env python3
"""
Quant statistics from full trade lists: one continuous funded account,
2015-01-02 .. 2025-12-31, $50,000 start on the 5ers ladder, live config.

Arms:  current   live config as deployed (2.7% risk while climbing)
       climb18   same, with FUNDED_CLIMB_RISK_PCT=1.8 (max 1.8% below 300k)

Outputs are kept (trades.csv, results.json) in
backtest/output/doe/wall5/quant/<arm>/ so every number can be re-derived.

Run:  uv run python3 backtest/src/w5_quant_stats.py run
      uv run python3 backtest/src/w5_quant_stats.py report
"""
import csv, importlib.util, json, math, os, subprocess, sys, concurrent.futures
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_r = importlib.util.spec_from_file_location("rs", str(HERE / "w5_random_study.py"))
rs = importlib.util.module_from_spec(_r); _r.loader.exec_module(rs)
w5 = rs.w5
QDIR = w5.W5_DIR / "quant"
START, END, BAL = "2015-01-02", "2025-12-31", 50_000.0
ARMS = {"current": {}, "climb18": {"FUNDED_CLIMB_RISK_PCT": "1.8"}}


def run_arm(arm):
    d = QDIR / arm
    if (d / "results.json").exists():
        return arm
    d.mkdir(parents=True, exist_ok=True)
    env, tp = rs.live_config(); env.update(ARMS[arm])
    e = dict(os.environ); e.update(w5.cs.dh.BASE_ENV); e.update(env)
    e["FIVEERS_MAX_SCALE"] = "500000"
    e.setdefault("BROKER_TYPE", "fiveers_live")
    e["OPT_PARAMS"] = json.dumps({**w5.cs.dh.BASE_TP, **tp})
    e["PYTHONUTF8"] = "1"
    subprocess.run([sys.executable, str(w5.cs.dh.BACKTEST), "--start", START, "--end", END,
                    "--balance", f"{BAL:.2f}", "--output", str(d), "--quiet"],
                   env=e, cwd=str(w5.cs.dh.REPO), capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=12 * 3600)
    return arm


def stats(arm):
    d = QDIR / arm
    r = json.loads((d / "results.json").read_text())
    rows = list(csv.DictReader(open(d / "trades.csv")))
    # Partial closes are separate rows; group them back into one trade per ticket.
    by_ticket = defaultdict(float); close_t = {}; open_t = {}
    for x in rows:
        t = x["ticket"].split("_partial_")[0]
        by_ticket[t] += float(x["pnl"]) + float(x.get("swap") or 0)
        close_t[t] = max(close_t.get(t, ""), x["close_time"]); open_t[t] = x["open_time"]
    pnl = [by_ticket[t] for t in sorted(by_ticket, key=lambda k: close_t[k])]
    wins = [p for p in pnl if p > 0]; losses = [p for p in pnl if p <= 0]
    gp, gl = sum(wins), -sum(losses)
    # Longest losing streak.
    streak = best = 0
    for p in pnl:
        streak = streak + 1 if p <= 0 else 0
        best = max(best, streak)
    # Daily returns relative to the funded level that day (5ers measure).
    daily = defaultdict(float)
    for x in rows:
        daily[x["close_time"][:10]] += float(x["pnl"]) + float(x.get("swap") or 0)
    levels = sorted((ev.get("time") or ev.get("date") or "", ev.get("new_level"))
                    for ev in (r.get("fiveers_scaling_log") or []))
    def level_on(day):
        lv = BAL
        for t, nl in levels:
            if t and str(t)[:10] <= day and nl:
                lv = nl
        return lv
    rets = [daily[k] / level_on(k) for k in sorted(daily)]
    n = len(rets); mu = sum(rets) / n if n else 0
    sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / (n - 1)) if n > 1 else 0
    dsd = math.sqrt(sum(min(0, x) ** 2 for x in rets) / n) if n else 0
    hold_h = []
    from datetime import datetime
    for t in by_ticket:
        try:
            a = datetime.fromisoformat(open_t[t]); b = datetime.fromisoformat(close_t[t])
            hold_h.append((b - a).total_seconds() / 3600)
        except ValueError:
            pass
    hold_h.sort()
    months = r.get("monthly_stats") or {}
    mvals = [v.get("pnl", 0) if isinstance(v, dict) else v for v in (months.values() if isinstance(months, dict) else [])]
    fi = r.get("fail_info") or {}
    return {
        "survived": not r.get("account_failed"),
        "end": (str(fi.get("time"))[:10] if r.get("account_failed") else END),
        "withdrawn": r.get("fiveers_total_withdrawn") or 0.0,
        "final_level": r.get("fiveers_final_funded_level"),
        "scale_ups": len(r.get("fiveers_scaling_log") or []),
        "trades": len(pnl),
        "win_rate": 100 * len(wins) / len(pnl) if pnl else 0,
        "profit_factor": gp / gl if gl else float("inf"),
        "avg_win": gp / len(wins) if wins else 0,
        "avg_loss": -gl / len(losses) if losses else 0,
        "payoff": (gp / len(wins)) / (gl / len(losses)) if wins and losses and gl else 0,
        "expectancy": sum(pnl) / len(pnl) if pnl else 0,
        "max_loss_streak": best,
        "trading_days": n,
        "green_days_pct": 100 * sum(1 for x in rets if x > 0) / n if n else 0,
        "best_day_pct": 100 * max(rets) if rets else 0,
        "worst_day_pct": 100 * min(rets) if rets else 0,
        "sharpe": mu / sd * math.sqrt(252) if sd else 0,
        "sortino": mu / dsd * math.sqrt(252) if dsd else 0,
        "max_ddd_pct": r.get("max_ddd_pct"), "max_tdd_pct": r.get("max_tdd_pct"),
        "green_months_pct": (100 * sum(1 for v in mvals if v > 0) / len(mvals)) if mvals else None,
        "median_hold_h": hold_h[len(hold_h) // 2] if hold_h else None,
        "ddd_halts": r.get("ddd_halts"),
    }


def report():
    out = {a: stats(a) for a in ARMS if (QDIR / a / "results.json").exists()}
    (QDIR / "quant_stats.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        (w5.DOE_DIR / "tmp").mkdir(parents=True, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            for a in ex.map(run_arm, ARMS):
                print("[quant] done", a, flush=True)
    report()
