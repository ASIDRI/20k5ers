"""Neely test N3 (docs/NEELY_TESTS.md): other stops, targets and entries for the N1 signals, chosen by Optuna on
2005-2014 only, then measured unchanged on 2015-2020 and 2021-2025.

    python research/neely/n3_optuna.py [--trials 300] [--cells A_D1 B_D1 A_W1 B_W1]

Signals: the N1 setups (research/neely/out/n1_<tf>_<sym>.csv, decisive filter htf == 1 & lab_ok), so the signal
itself (pattern, confirmation at a closed candle, direction) does not change. Only the trade around it:

  s   stop buffer: the stop sits s x ATR beyond the pattern's invalidation point (end of e / end of c)    [0, 1.5]
  e   entry: 0 = market at the confirming close; > 0 = limit order e x (close - stop) back towards the
      stop, valid for the pattern's duration in candles (not filled -> no trade)                         [0, 0.6]
  k   target in R from the fill                                                                            [0.3, 5]
  be  stop to the fill once price has gone be x R in favour (from the next candle), or never               [0.3, 3] / off
  H   time stop: out at the close H candles after the fill                                                 [2, 120]

Fill and exit rules (no look-ahead, the cautious side): a limit fills at its price when a later candle trades
through it; in the fill candle only the stop counts, the target from the next candle on; stop before target in one
candle; a gap beyond the stop exits at the open; costs per symbol (test2.cost_price) in R. One position per
direction per symbol (a signal is skipped while an earlier trade in that direction is still open).
Objective on 2005-2014: t-value of R per trade (mean / sd x sqrt(n)), at least 100 trades.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from neely_bt import with_done  # noqa: E402
from test2 import cost_price  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def load_cell(setup, tf):
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"n1_{tf}_*.csv")) if p.stat().st_size > 1])
    f = f[(f.result == "gevuld") & (f.setup == setup)].copy()
    f["lab_ok"] = f.lab_ok.astype(str).str.lower().eq("true")
    f = f[(f.htf == 1) & f.lab_ok].sort_values(["sym", "fi"]).reset_index(drop=True)
    o, h, l, c, base, ends = [], [], [], [], {}, {}
    n = 0
    for sym in f.sym.unique():
        d = with_done(sym, tf)
        base[sym] = n
        n += len(d)
        ends[sym] = n - 1
        for arr, k in ((o, "open"), (h, "high"), (l, "low"), (c, "close")):
            arr.append(d[k].values)
    sig = dict(gi=np.array([base[s] + i for s, i in zip(f.sym, f.fi)], dtype=np.int64),
               end=np.array([ends[s] for s in f.sym], dtype=np.int64),
               dirn=f.dir.values.astype(np.int64), inval=f.end_px.values.astype(float), atr=f.atr.values.astype(float),
               dur=f.dur.values.astype(np.int64),
               cost=np.array([cost_price(s, e) for s, e in zip(f.sym, f.entry)], dtype=float),
               key=(pd.factorize(f.sym)[0] * 2 + (f.dir.values > 0)).astype(np.int64))
    return f, np.concatenate(o), np.concatenate(h), np.concatenate(l), np.concatenate(c), sig


@njit(cache=True)
def simulate(gi, end, dirn, inval, atr, dur, cost, key, O, H, L, C, s, e, k, be, hold, nkeys):
    n = len(gi)
    R = np.full(n, np.nan)
    busy = np.full(nkeys, -1)
    for q in range(n):
        f, d = gi[q], dirn[q]
        if busy[key[q]] >= f:
            continue
        stop0 = inval[q] - d * s * atr[q]
        risk0 = (C[f] - stop0) * d
        if risk0 <= 0:
            continue
        # entry
        g, px = -1, 0.0
        if e == 0.0:
            g, px = f, C[f]
        else:
            lim = C[f] - d * e * risk0
            for j in range(f + 1, min(f + dur[q], end[q]) + 1):
                if (L[j] - lim if d == 1 else lim - H[j]) <= 0:
                    g, px = j, lim
                    break
        if g < 0:
            continue
        risk = (px - stop0) * d
        tp = px + d * k * risk
        stop = stop0
        out, xj = np.nan, -1
        last = min(g + hold, end[q])
        armed = False
        for j in range(g if g > f else g + 1, last + 1):
            if armed:
                stop = px
            adv = L[j] if d == 1 else H[j]
            if (adv - stop) * d <= 0:
                op = O[j]
                ex = op if (j > g and (op - stop) * d < 0) else stop
                out, xj = (ex - px) * d / risk, j
                break
            if j > g:
                fav = H[j] if d == 1 else L[j]
                if (fav - tp) * d >= 0:
                    out, xj = k, j
                    break
                if be > 0 and (fav - (px + d * be * risk)) * d >= 0:
                    armed = True
            if j == last:
                out, xj = (C[j] - px) * d / risk, j
        if xj < 0:
            continue
        R[q] = out - cost[q] / risk
        busy[key[q]] = xj
    return R


def evaluate(cell, prm):
    f, O, H, L, C, sig = cell
    R = simulate(sig["gi"], sig["end"], sig["dirn"], sig["inval"], sig["atr"], sig["dur"], sig["cost"], sig["key"],
                 O, H, L, C, prm["s"], prm["e"], prm["k"], prm["be"] if prm["be_on"] else 0.0, int(prm["H"]),
                 int(sig["key"].max()) + 1)
    return pd.Series(R, index=f.date.values).dropna()


def tval(x):
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0


def pf(x):
    return x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else np.nan


def report(r):
    out = []
    for lab, a, b in P:
        x = r[(r.index >= a) & (r.index < b)]
        out.append(f"{lab} n{len(x):5d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean() * 100:.0f}%")
    oos = r[r.index >= "2015"]
    return " | ".join(out) + f" | t buiten-steekproef {tval(oos):.2f}"


if __name__ == "__main__":
    import optuna
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--cells", nargs="+", default=["A_D1", "B_D1", "A_W1", "B_W1"])
    a = ap.parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    best_all = {}
    for name in a.cells:
        setup, tf = name.split("_")
        cell = load_cell(setup, tf)

        def objective(tr):
            prm = dict(s=tr.suggest_float("s", 0.0, 1.5), e=tr.suggest_float("e", 0.0, 0.6),
                       k=tr.suggest_float("k", 0.3, 5.0), be_on=tr.suggest_categorical("be_on", [False, True]),
                       be=tr.suggest_float("be", 0.3, 3.0), H=tr.suggest_int("H", 2, 120))
            r = evaluate(cell, prm)
            x = r[r.index < "2015"]
            return tval(x) if len(x) >= 100 else -10.0

        st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
        st.optimize(objective, n_trials=a.trials)
        prm = st.best_params
        r = evaluate(cell, prm)
        best_all[name] = dict(params=prm, t_train=st.best_value)
        print(f"\n## {name}: beste op 2005-14 (t {st.best_value:.2f}): "
              + ", ".join(f"{kk}={v:.3g}" if isinstance(v, float) else f"{kk}={v}" for kk, v in prm.items()))
        print("  " + report(r))
        # reference: the N1 rule as it was (market at the close, stop 0.1 ATR, T1 not expressed in R -> k = median rr1)
        ref = dict(s=0.1, e=0.0, k=float(cell[0].rr1.median()), be_on=False, be=1.0, H=10_000)
        print(f"  N1-achtig (markt, stop 0,1 ATR, k = mediaan rr1 {ref['k']:.2f}): " + report(evaluate(cell, ref)))
    (HERE / "out" / "n3_best.json").write_text(json.dumps(best_all, indent=1))
