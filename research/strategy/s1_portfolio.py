"""S1 as a portfolio: equity curve 2005-2025 and the 5ers challenge on it.

    python research/strategy/s1_portfolio.py [--prefix s1_] [--exit c] [--risks 0.005,0.01,0.015,0.02] [--trend htf]
                                             [--one-per-ccy]

S1 = test5.py trades with all three video filters (cont, lvl, mn == 1), from research/strategy/out/<prefix>*.csv
(test 7: --trend htf, the trend one timeframe above the legs). --one-per-ccy: a trade is skipped while another open
trade shares a currency with it (taken in order of fill; the same day: the order of the files).
Every trade risks a fixed fraction r of the starting balance (no compounding). Marked to market on daily closes from
the fill until the exit day; on the exit day the trade is worth its booked R (exit a or c). Costs at the fill.
Worst intraday equity = close equity minus each open trade's adverse move that day (all at once; conservative), each
trade's dip limited to its stop. The ladder's partial exits are not marked: the whole position swings until it exits
(more swing than in reality).
Challenge (5ers High Stakes): step 1 +8%, step 2 +5% on the starting balance; breach at worst equity <= 90% of the
starting balance or <= 95% of the previous close. No time limit. At a target everything is closed and the next step
starts with new trades only. Funded: payout of 80% of the profit at +W, then a fresh start; lost at a breach; HORIZON
trading days. Starts: the first trading day of every month.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402

PERIODS = [("2005-14", "2005-01-01", "2015-01-01"), ("2015-20", "2015-01-01", "2021-01-01"),
           ("2021-25", "2021-01-01", "2026-01-01")]


def trades(prefix, trend="mn"):
    f = pd.concat([pd.read_csv(p) for p in sorted((HERE / "out").glob(f"{prefix}*.csv"))])
    f = f[(f.result == "gevuld") & f.cont & f.lvl & (f[trend] == 1)].copy()
    return f.sort_values("fill", kind="stable").reset_index(drop=True)


def ccys(sym):
    return set(sym.split("_")) if "_" in sym else {sym[:3], sym[3:]}


def one_per_ccy(f, ex):
    keep, open_ = [], []  # open_: (exit day, currencies)
    for k, t in f.iterrows():
        if not isinstance(t[f"exit_{ex}"], str):
            continue
        open_ = [(x, c) for x, c in open_ if x > t.fill]
        if any(c & ccys(t.sym) for _, c in open_):
            continue
        keep.append(k)
        open_.append((t[f"exit_{ex}"], ccys(t.sym)))
    return f.loc[keep].reset_index(drop=True)


def matrix(f, ex):
    """V[trade, day]: value in R at the day's close (0 before the fill, final R after the exit); D: intraday dip."""
    d1 = {s: load(s, "D1") for s in f.sym.unique()}
    for d in d1.values():
        d["day"] = d["time"].dt.strftime("%Y-%m-%d")
    days = sorted(set().union(*[set(d["day"]) for d in d1.values()]))
    pos = {x: i for i, x in enumerate(days)}
    V = np.zeros((len(f), len(days)))
    D = np.zeros_like(V)
    keep = []
    for k, t in f.iterrows():
        exit_day = t[f"exit_{ex}"]
        if not isinstance(exit_day, str):
            continue
        keep.append(k)
        final = t.Rnet_c if ex == "c" else t.Rnet_a
        d = d1[t.sym]
        seg = d[(d.day > t.fill) & (d.day < exit_day)]
        sgn = t.dir
        adverse = seg.low.values if sgn == 1 else seg.high.values
        mtm = (seg.close.values - t.entry) * sgn / t.risk - t.R_cost
        worst = np.maximum((adverse - t.entry) * sgn / t.risk, -1.0) - t.R_cost
        a, b = pos[t.fill], pos[exit_day]
        V[k, a] = -t.R_cost
        idx = [pos[x] for x in seg.day]
        V[k, idx] = mtm
        D[k, idx] = mtm - worst
        V[k, b:] = final
        xd = d[d.day == exit_day]
        if len(xd):  # exit day: dip from the last close to the stop/target, at most to -1R
            prev = V[k, b - 1] if b > a else -t.R_cost
            adv = xd.low.values[0] if sgn == 1 else xd.high.values[0]
            worst = max((adv - t.entry) * sgn / t.risk, -1.0) - t.R_cost
            D[k, b] = max(0.0, min(prev, final) - worst)
    keep = np.array(keep)
    return f.loc[keep].reset_index(drop=True), V[keep], D[keep], np.array(days)


def phase(V, D, fill_i, s, r, target=None, end=None):
    """Run from day s with trades filled on/after s. Returns (outcome, day index where it ended, equity at that close)."""
    m = fill_i >= s
    E = 1 + r * V[m].sum(0)  # trades filled on/after s are 0 before their fill
    W = E - r * D[m].sum(0)
    end = len(E) if end is None else min(end, len(E))
    prev = 1.0
    for i in range(s, end):
        if W[i] <= 0.90 or W[i] <= prev * 0.95:
            return "breach", i, W[i]
        if target is not None and E[i] >= 1 + target:
            return "doel", i, E[i]
        prev = E[i]
    return "einde", end - 1, E[end - 1]


def challenge(V, D, fill_i, s, r):
    i = s
    for target in (0.08, 0.05):
        out, i, _ = phase(V, D, fill_i, i, r, target=target)
        if out != "doel":
            return out, i
        i += 1
    return "geslaagd", i


def funded(V, D, fill_i, s, r, w, horizon):
    paid, i, stop = 0.0, s, s + horizon
    while i < min(stop, V.shape[1]):
        out, i, eq = phase(V, D, fill_i, i, r, target=w, end=stop)
        if out == "doel":
            paid += 0.8 * (eq - 1)
            i += 1
            continue
        return paid, out == "breach"
    return paid, False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="s1_")
    ap.add_argument("--exit", default="c", choices=["a", "c"])
    ap.add_argument("--risks", default="0.005,0.01,0.015,0.02")
    ap.add_argument("--withdraw", type=float, default=0.04)
    ap.add_argument("--horizon", type=int, default=504)
    ap.add_argument("--fee", type=float, default=0.005)
    ap.add_argument("--trend", default="mn", choices=["mn", "htf"])
    ap.add_argument("--one-per-ccy", action="store_true")
    a = ap.parse_args()
    f = trades(a.prefix, a.trend)
    if a.one_per_ccy:
        f = one_per_ccy(f, a.exit)
    f, V, D, days = matrix(f, a.exit)
    fill_i = np.searchsorted(days, f.fill.values)
    R = V.sum(0)  # cumulative R, all trades
    print(f"S1 exit {a.exit}: {len(f)} trades, {f.sym.nunique()} assets, gem {f['Rnet_' + a.exit].mean():+.3f}R")
    open_n = ((np.arange(len(days))[None, :] >= fill_i[:, None]) &
              (np.arange(len(days))[None, :] < np.searchsorted(days, f[f'exit_{a.exit}'].values)[:, None])).sum(0)
    print(f"gelijktijdig open: gem {open_n.mean():.1f}, max {open_n.max()}")
    yr = pd.Series(np.diff(np.r_[0, R]), index=pd.to_datetime(days)).groupby(lambda x: x.year).sum()
    print("R per jaar: " + ", ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
    print("trades per jaar: " + ", ".join(f"{y}:{n}" for y, n in f.fill.str[:4].value_counts().sort_index().items()))
    for r in map(float, a.risks.split(",")):
        E = 1 + r * R
        Wd = E - r * D.sum(0)
        dd = (Wd / np.maximum.accumulate(E) - 1).min()
        ann = (E[-1] - 1) / (len(days) / 252)
        print(f"\n=== risico {r*100:.1f}% per trade: {ann*100:+.1f}%/jaar (enkelvoudig), max DD {dd*100:.1f}%, "
              f"slechtste jaar {yr.min()*r*100:+.1f}%")
        starts = pd.Series(range(len(days)), index=pd.to_datetime(days)).groupby(lambda x: (x.year, x.month)).first().values
        for lab, p0, p1 in PERIODS:
            ss = [s for s in starts if p0 <= days[s] < p1]
            res = [challenge(V, D, fill_i, s, r) for s in ss]
            ok = [x for x in res if x[0] == "geslaagd"]
            br = sum(x[0] == "breach" for x in res)
            dur = np.median([x[1] - s for x, s in zip(res, ss) if x[0] == "geslaagd"]) if ok else np.nan
            pays = [funded(V, D, fill_i, x[1] + 1, r, a.withdraw, a.horizon)[0] for x in ok]
            ev = len(ok) / len(res) * (np.mean(pays) if pays else 0) - a.fee
            print(f"  {lab}: starts {len(res)}, geslaagd {len(ok)/len(res)*100:.0f}%, breach {br/len(res)*100:.0f}%, "
                  f"open/einde {(len(res)-len(ok)-br)/len(res)*100:.0f}%, mediaan {dur:.0f} handelsdagen; "
                  f"funded uitbetaling gem {np.mean(pays)*100 if pays else 0:.1f}% in {a.horizon} d; EV {ev*100:+.1f}% per challenge")
