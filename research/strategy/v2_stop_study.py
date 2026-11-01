"""Where should the stop go? Strategy v2 trades re-simulated with other stop rules (same entries, same targets).

    python research/strategy/v2_stop_study.py EURUSD [SYM ...] [--from 2016-01-01] [--to 2026-01-01]

For every trade: the adverse move before T1 (in the fib: 0 = the extreme, 1 = fib 1) and the result under each stop
rule. "Winners" = trades that reach T1 with the widest stop tested (beyond fib 1); a good stop keeps them and cuts the
rest early. Management as in the engine (T1 50%, stop a little in profit; T2 25%, stop to fib 0; T3 = fib -1).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import trader_strategy as T  # noqa: E402
from setup_study import load  # noqa: E402
from test2 import cost_price  # noqa: E402


LADDER = (0.5, 0.618, 0.66, 0.786, 0.886, 1.0, 1.13)


def rules(t, o, h, l, c, a):
    k, f0, rng, e = t["_k"], t["_f0"], t["_rng"], t["_entry"]
    buf = T.SL_BUF * a[k]
    fib = lambda x: f0 + x * rng + buf  # noqa: E731
    r = {"engine nu (diep: swing high, anders max(0,796, patroon))":
         (t["_hi"] if (e - f0) / rng >= T.DEEP else max(f0 + 0.796 * rng, h[k], h[k - 1])) + buf,
         "boven het patroon (+0,1 ATR)": t["_pat"] + buf,
         "boven het patroon (+0,5 ATR)": t["_pat"] + 0.5 * a[k],
         "boven het niveau + 0,5 ATR": t["_level"] + 0.5 * a[k],
         "fib 0,66": fib(0.66), "fib 0,796": fib(0.796), "fib 0,886": fib(0.886), "fib 1": fib(1.0),
         "boven de swing high (lont)": t["_hi"] + buf}
    pl = (t["_level"] - f0) / rng  # where the daily S/R lies in the fib
    nxt = [x for x in LADDER if x > pl + 0.02]
    r["volgend fib-niveau boven het dag-S/R"] = fib(nxt[0] if nxt else 1.13)
    r["twee fib-niveaus boven het dag-S/R"] = fib(nxt[1] if len(nxt) > 1 else 1.13)
    above = [p for p, _ in T.sr_levels(o, h, l, c, T.SR_TOL * a[k - 1], k) if p > t["_level"] + T.TOUCH_TOL * a[k - 1]]
    r["boven het volgende dag-S/R (+0,1 ATR)"] = (min(above) if above else f0 + rng) + buf
    if t["_band"] is not None:
        r["achter de BoS-lijn (+0,25 ATR), eerste trade"] = max(t["_band"]) + 0.25 * a[k]
    return {n: (max(v, e + 0.2 * a[k]), v < e + 0.2 * a[k]) for n, v in r.items()}  # never closer than 0.2 ATR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("syms", nargs="+")
    ap.add_argument("--from", dest="start", default="2016-01-01")
    ap.add_argument("--to", dest="end", default="2026-01-01")
    a_ = ap.parse_args()
    rows = []
    for sym in a_.syms:
        d, w, m = load(sym, "D1"), load(sym, "W1"), load(sym, "MN")
        for dirn in (-1, 1):
            sgn = -1 if dirn == 1 else 1
            o, h, l, c = (d[x].values.astype(float) for x in ("open", "high", "low", "close"))
            if sgn == -1:
                o, h, l, c = -o, -l, -h, -c
            at = T.atr(h, l, c)
            for t in T.run_view(sym, d, w, dirn, a_.start, a_.end, [], m):
                k, f0, rng, e = t["_k"], t["_f0"], t["_rng"], t["_entry"]
                t1 = f0 - T.T1 * rng
                hit = next((i for i in range(k + 1, len(h)) if l[i] <= t1), None)
                mae = (max(h[k + 1:hit + 1]) - f0) / rng if hit else np.nan  # adverse move before T1, in the fib
                cost = cost_price(sym, abs(e))
                for name, (sl, clamped) in rules(t, o, h, l, c, at).items():
                    mres = T.manage(h, l, k, e, sl, f0, rng, T.BE * at[k])
                    rows.append(dict(sym=sym, day=t["entry_day"], dir=dirn, rule=name, mae=mae,
                                     depth=(e - f0) / rng, risk_atr=(sl - e) / at[k],
                                     t1=mres["t1_i"] is not None, R=(mres["pnl"] - cost) / (sl - e), clamped=clamped))
    f = pd.DataFrame(rows)
    wide = f[f.rule == "fib 1"].set_index(["sym", "day", "dir"]).t1
    f["winner"] = [wide.get((s, dd, di), False) for s, dd, di in zip(f.sym, f.day, f.dir)]
    n = len(f.drop_duplicates(["sym", "day", "dir"]))
    print(f"{n} trades; met de wijdste stop (fib 1) halen {int(wide.sum())} T1 = 'winnaars'.")
    e1 = f[f.rule.str.startswith("engine")].drop_duplicates(["sym", "day", "dir"])
    print("tegenbeweging vóór T1 (in de fib, 0 = extreem, 1 = fib 1) bij de winnaars:",
          np.round(np.sort(e1[e1.winner].mae.values), 2))
    g = f.groupby("rule").agg(T1=("t1", "sum"), winnaars_uitgestopt=("winner", lambda x: 0),
                              R=("R", "sum"), gemR=("R", "mean"), risico_ATR=("risk_atr", "median"),
                              n=("R", "size"), stop_te_krap=("clamped", "sum"))
    g["winnaars_uitgestopt"] = [int(((f.rule == r) & f.winner & ~f.t1).sum()) for r in g.index]
    print(g.sort_values("R", ascending=False).round(2).to_string())


if __name__ == "__main__":
    main()
