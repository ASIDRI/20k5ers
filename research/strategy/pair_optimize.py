"""Per-pair optimisation of setup 1 (+ setup 2) with a walk-forward check (trader 2026-11-26: "optimaliseren per pair,
naar de 60% win rate").

    python research/strategy/pair_optimize.py run      # the grid -> research/strategy/out/pairopt/trades.csv (~2 h)
    python research/strategy/pair_optimize.py report   # choice on 2016-2020, result on 2021-2025

The grid switches rules that the trader's setups taught us, per instrument:
  wick     BREAK_WICK (a weekly BoS must also close beyond the swing wick)
  fakes    0 off / 1 fake-BoS trigger / 2 trigger + setup-2 retest
  revert   REVERT_WEEKS 0 / 6 (+ weekly WMA 10)
  pbfib    PULLBACK_FIB off / on (PB_MIN 0.8)
  rej      REJ_N 1 / 2 (rejection wicks at the daily S/R)
  zone     ZONE lower bound 0.45 / 0.55
The engine is causal (v2_guard.py), so one run 2016-2025 per config can be split by entry date: the choice uses only
2016-2020, the score that counts is 2021-2025 (never used for the choice). The 29 exotics and later data stay held out.
"""
import itertools
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
OUT = HERE / "out" / "pairopt"
SPLIT = "2021-01-01"
GRID = list(itertools.product((True, False), (0, 1, 2), (0, 6), (False, True), (1, 2), (0.45, 0.55)))


def cfg_name(c):
    wick, fakes, rev, pb, rej, zone = c
    return f"w{int(wick)}f{fakes}r{rev}p{int(pb)}j{rej}z{int(zone * 100)}"


def one(args):
    sym, c = args
    import trader_strategy as T
    from setup_study import load
    wick, fakes, rev, pb, rej, zone = c
    T.USE_PROFILES = False
    T.BREAK_WICK, T.FAKE_TRIGGER, T.FAKE_RETEST = wick, fakes >= 1, fakes == 2
    T.REVERT_WEEKS, T.REVERT_CONFIRM = rev, ("wma" if rev else None)
    T.PULLBACK_FIB, T.PB_LEFT, T.PB_MIN = pb, 1, 0.8
    T.REJ_N, T.ZONE = rej, (zone, 1.0)
    T.LQD, T.LQ_GRAB = False, False
    d, w = load(sym, "D1"), load(sym, "W1")
    try:
        m = load(sym, "MN")
    except Exception:
        m = None
    tr = []
    for dirn in (-1, 1):
        tr += T.run_view(sym, d, w, dirn, "2016-01-01", "2026-01-01", [], m)
    return [(sym, cfg_name(c), t["setup"], t["entry_day"], t["dir"], t["R"], bool(t["t1_day"])) for t in tr]


def run():
    syms = [f[6:-4] for f in sorted(os.listdir(HERE / "out")) if f.startswith("v2n37_")]
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [(s, c) for s in syms for c in GRID]
    rows = []
    with ProcessPoolExecutor(4) as ex:
        for n, r in enumerate(ex.map(one, tasks, chunksize=4)):
            rows += r
            if n % 100 == 0:
                print(f"  {n}/{len(tasks)}", flush=True)
    pd.DataFrame(rows, columns=["sym", "cfg", "setup", "day", "dir", "R", "t1"]).to_csv(OUT / "trades.csv", index=False)


def stats(x):
    r = x.R
    n = len(r)
    return dict(n=n, win=x.t1.mean() if n else np.nan, R=r.sum(), mean=r.mean() if n else np.nan)


def report(min_n=6, min_win=0.55):
    df = pd.read_csv(OUT / "trades.csv")
    df["is_"] = df.day < SPLIT
    syms = sorted(df.sym.unique())
    allc = [cfg_name(c) for c in GRID]
    # per pair: best config on 2016-2020 (most R with >= min_n trades and T1 win >= min_win)
    pick, rows = {}, []
    for s in syms:
        g = df[(df.sym == s) & df.is_]
        best, bestR = None, -1e9
        for cn in allc:
            x = g[g.cfg == cn]
            st = stats(x)
            if st["n"] >= min_n and st["win"] >= min_win and st["R"] > bestR:
                best, bestR = cn, st["R"]
        pick[s] = best
        if best is None:
            rows.append(dict(sym=s, cfg="(geen)", n_is=0, win_is=np.nan, R_is=0, n_oos=0, win_oos=np.nan, R_oos=0))
            continue
        a = stats(g[g.cfg == best])
        b = stats(df[(df.sym == s) & ~df.is_ & (df.cfg == best)])
        rows.append(dict(sym=s, cfg=best, n_is=a["n"], win_is=a["win"], R_is=a["R"], n_oos=b["n"], win_oos=b["win"],
                         R_oos=b["R"]))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(t.round(2).to_string(index=False))
    sel = t[t.cfg != "(geen)"]
    oos = df[~df.is_ & df.apply(lambda r: pick.get(r.sym) == r.cfg, axis=1)]
    print(f"\nPer paar gekozen op 2016-2020 (>= {min_n} trades, T1 >= {min_win:.0%}): {len(sel)} van {len(syms)} paren")
    print(f"  2016-2020 (keuze):  {int(sel.n_is.sum())} trades, R {sel.R_is.sum():+.1f}")
    print(f"  2021-2025 (test):   {len(oos)} trades, T1 {oos.t1.mean():.0%}, R {oos.R.sum():+.1f}, "
          f"gem {oos.R.mean():+.3f}, t {oos.R.mean() / oos.R.std() * np.sqrt(len(oos)):.2f}")
    # references on 2021-2025: one config for every pair (best on 2016-2020 over all pairs) and the current profiles
    tot = df[df.is_].groupby("cfg").R.sum()
    glob = tot.idxmax()
    go = df[~df.is_ & (df.cfg == glob)]
    print(f"  ter vergelijking, 1 instelling voor alle paren (beste op 2016-2020: {glob}): 2021-2025 {len(go)} trades, "
          f"T1 {go.t1.mean():.0%}, R {go.R.sum():+.1f}")
    cur = df[~df.is_ & (((df.sym == "EURUSD") & (df.cfg == "w1f0r6p1j2z45")) | ((df.sym != "EURUSD") & (df.cfg == "w0f2r6p0j2z45")))]
    print(f"  ter vergelijking, huidige profielen: 2021-2025 {len(cur)} trades, T1 {cur.t1.mean():.0%}, R {cur.R.sum():+.1f}")
    return t, pick


if __name__ == "__main__":
    run() if sys.argv[1:] == ["run"] else report()
