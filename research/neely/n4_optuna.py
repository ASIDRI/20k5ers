"""Neely test N4 (docs/NEELY_TESTS.md): Optuna on the signals AND the trade, on 2005-2014 only; then 2015-2025 and the
31 holdout instruments of test 33.

    python research/neely/n4_optuna.py [--trials 500] [--tfs D1 W1] [--holdout PREFIX]

Signals: the loose N1 run (neely_bt.py --loose --sim-min 0.2 --prefix n4_<tf>_), every confirmed pattern with its
features. Optuna chooses which of them to trade (thresholds on the features) and how (stops, entry, target, as in N3):

  setups      A (triangle thrust) / B (zigzag-flat resumption) / both
  tri         contracting triangles only / also expanding
  fam         zigzag / flat / both
  detour      also B-patterns the DETOUR test calls an impulse
  sim         Similarity threshold (book 1/3)                                  [0.2, 0.6]
  htf         higher timeframe with the trade / not against it / any
  lab         Pre-Constructive start lists must fit (lab_ok)
  size        pattern size (high-low) >= size x ATR                           [0, 5]
  delay       confirmation at most `delay` candles after the pattern ended   [0, 20]
  brk         confirming close at least brk x ATR beyond the line            [0, 1]
  inv         confirming close at most inv x ATR from the invalidation point [0.5, 6]
  s, e, k, be, H   stop buffer, limit entry, target in R, stop to entry, time stop (n3_optuna)
Objective on signals before 2015: t-value of R per trade, at least 150 trades.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from neely_bt import with_done  # noqa: E402
from n3_optuna import simulate, tval, pf  # noqa: E402
from test2 import cost_price  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def load(prefix, tf):
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{prefix}{tf}_*.csv")) if p.stat().st_size > 1])
    f = f[f.result == "gevuld"].copy()
    for c in ("lab_ok", "detour"):
        f[c] = f[c].astype(str).str.lower().eq("true")
    f = f.sort_values(["sym", "fi", "setup"]).reset_index(drop=True)
    o, h, l, c, base, ends, n = [], [], [], [], {}, {}, 0
    for sym in f.sym.unique():
        d = with_done(sym, tf)
        base[sym], n = n, n + len(d)
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


def mask(f, prm):
    m = np.ones(len(f), bool)
    if prm["setups"] != "AB":
        m &= f.setup.values == prm["setups"]
    isA = f.setup.values == "A"
    if prm["tri"] == "contracting":
        m &= ~isA | f.variant.str.startswith("contracting").values
    if prm["fam"] != "both":
        m &= isA | (f.family.values == prm["fam"])
    if not prm["detour"]:
        m &= ~f.detour.values
    m &= f.sim.values >= prm["sim"]
    m &= {"mee": f.htf.values == 1, "niet_tegen": f.htf.values >= 0, "alle": np.ones(len(f), bool)}[prm["htf"]]
    if prm["lab"]:
        m &= f.lab_ok.values
    m &= f.size_atr.values >= prm["size"]
    m &= f.delay.values <= prm["delay"]
    m &= f.brk_atr.values >= prm["brk"]
    m &= f.inv_atr.values <= prm["inv"]
    return m


def evaluate(data, prm):
    f, O, H, L, C, sig = data
    m = mask(f, prm)
    if m.sum() == 0:
        return pd.Series(dtype=float)
    s = {k: v[m] for k, v in sig.items()}
    R = simulate(s["gi"], s["end"], s["dirn"], s["inval"], s["atr"], s["dur"], s["cost"], s["key"], O, H, L, C,
                 prm["s"], prm["e"], prm["k"], prm["be"] if prm["be_on"] else 0.0, int(prm["H"]), int(sig["key"].max()) + 1)
    return pd.Series(R, index=f.date.values[m]).dropna()


def suggest(tr):
    return dict(setups=tr.suggest_categorical("setups", ["A", "B", "AB"]),
                tri=tr.suggest_categorical("tri", ["contracting", "all"]),
                fam=tr.suggest_categorical("fam", ["zigzag", "flat", "both"]),
                detour=tr.suggest_categorical("detour", [False, True]),
                sim=tr.suggest_float("sim", 0.2, 0.6),
                htf=tr.suggest_categorical("htf", ["mee", "niet_tegen", "alle"]),
                lab=tr.suggest_categorical("lab", [False, True]),
                size=tr.suggest_float("size", 0.0, 5.0), delay=tr.suggest_int("delay", 0, 20),
                brk=tr.suggest_float("brk", 0.0, 1.0), inv=tr.suggest_float("inv", 0.5, 6.0),
                s=tr.suggest_float("s", 0.0, 1.5), e=tr.suggest_float("e", 0.0, 0.6), k=tr.suggest_float("k", 0.3, 5.0),
                be_on=tr.suggest_categorical("be_on", [False, True]), be=tr.suggest_float("be", 0.3, 3.0),
                H=tr.suggest_int("H", 2, 120))


def periods(r):
    out = []
    for lab, a, b in P:
        x = r[(r.index >= a) & (r.index < b)]
        out.append(f"{lab} n{len(x):5d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean() * 100:.0f}%")
    return " | ".join(out)


if __name__ == "__main__":
    import optuna
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=500)
    ap.add_argument("--tfs", nargs="+", default=["D1", "W1"])
    ap.add_argument("--holdout", default=None, help="prefix of the holdout run (n4h_): evaluate the stored best")
    a = ap.parse_args()
    store = HERE / "out" / "n4_best.json"
    if a.holdout:
        best = json.loads(store.read_text())
        for tf in a.tfs:
            r = evaluate(load(a.holdout, tf), best[tf])
            print(f"## holdout {tf}: {periods(r)} | t {tval(r):.2f}")
        sys.exit()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    best = {}
    for tf in a.tfs:
        data = load("n4_", tf)

        def objective(tr):
            r = evaluate(data, suggest(tr))
            x = r[r.index < "2015"]
            return tval(x) if len(x) >= 150 else -10.0

        st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
        st.optimize(objective, n_trials=a.trials)
        prm = st.best_params
        best[tf] = prm
        r = evaluate(data, prm)
        oos = r[r.index >= "2015"]
        print(f"\n## {tf}: {len(data[0])} signalen; beste op 2005-14 t {st.best_value:.2f}")
        print("  " + ", ".join(f"{k}={v:.3g}" if isinstance(v, float) else f"{k}={v}" for k, v in prm.items()))
        print(f"  {periods(r)} | t buiten-steekproef (2015-25) {tval(oos):.2f}")
    store.write_text(json.dumps(best, indent=1))
