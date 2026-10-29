"""Phase P2 (pre-registered in docs/RND_RESULTS.md, commit 78663eb): AUDNZD hourly reversion.

    python research/rnd/p2_audnzd.py [--pair AUDNZD]

H1 candles from the merged M15 data. On each closed hour: z = (close - mean N) / stdev N. |z| >= 2 -> trade against
the stretch at the next hour's open; exit when an hour closes back on the other side of its mean, after 24 hours (at
that close), or at the stop (2 x hourly ATR from entry, checked first on each bar). One position at a time per variant.
Costs (spread + slippage, both sides) per trade. Variant 'sr': only when a monthly/weekly S/R level (known at that
moment) lies within 0.5 daily ATR of the close.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "strategy")]
from setup_study import Levels  # noqa: E402
import systematic as S  # noqa: E402
from pair_diag import m15, resample, PAIRS  # noqa: E402

SPLIT = pd.Timestamp("2021-01-01", tz="UTC")


def run(pair, N, use_sr, z_in=2.0, stop_atr=2.0, max_h=24, tf="1h"):
    m = m15(PAIRS.get(pair, pair))
    h = resample(m, tf)
    h = h[h.index >= pd.Timestamp("2015-01-01", tz="UTC")]
    d = resample(m, "1D")
    datr = (d["high"] - d["low"]).rolling(14).mean()
    o, hi, lo, c = (h[k].values for k in ("open", "high", "low", "close"))
    mean = h["close"].rolling(N).mean().values
    sd = h["close"].rolling(N).std().values
    tr = np.r_[np.nan, np.maximum(hi[1:], c[:-1]) - np.minimum(lo[1:], c[:-1])]
    atr = pd.Series(tr).rolling(24).mean().values
    cost = S.cost_frac(pair, np.nanmedian(c)) * 2  # fraction of price, both sides
    lv = Levels(pair) if use_sr else None
    dates = h.index
    # daily ATR known at hour t: the last completed server day before t
    d_end = d.index + pd.Timedelta(days=1) - pd.Timedelta(hours=2)
    trades = []
    i = N + 25
    while i < len(h) - 1:
        z = (c[i] - mean[i]) / sd[i] if sd[i] > 0 else 0
        if abs(z) < z_in or np.isnan(atr[i]):
            i += 1
            continue
        if use_sr:
            k = int(np.searchsorted(d_end.values, dates[i].to_datetime64(), side="right")) - 1
            A = datr.iloc[k] if k >= 0 else np.nan
            levs = [p for p, _ in lv.at(dates[i])]
            if np.isnan(A) or not any(abs(c[i] - p) <= 0.5 * A for p in levs):
                i += 1
                continue
        dirn = -1 if z > 0 else 1
        entry = o[i + 1]
        stop = entry - dirn * stop_atr * atr[i]
        exit_px, j = None, i + 1
        while j < len(h):
            if (dirn == 1 and lo[j] <= stop) or (dirn == -1 and hi[j] >= stop):
                exit_px = stop
                break
            if (dirn == 1 and c[j] >= mean[j]) or (dirn == -1 and c[j] <= mean[j]) or j - i >= max_h:
                exit_px = c[j]
                break
            j += 1
        if exit_px is None:
            break
        pnl = (exit_px - entry) / entry * dirn - cost
        risk = stop_atr * atr[i] / entry
        trades.append(dict(time=dates[i], bp=pnl * 1e4, R=pnl / risk, hours=j - i))
        i = j + 1
    return pd.DataFrame(trades)


def report(t, label):
    out = []
    for lab, g in (("15-20", t[t.time < SPLIT]), ("21-25", t[t.time >= SPLIT])):
        n = len(g)
        tt = g.bp.mean() / (g.bp.std() / np.sqrt(n)) if n > 2 else np.nan
        pf = g.bp[g.bp > 0].sum() / -g.bp[g.bp < 0].sum() if (g.bp < 0).any() else np.nan
        out.append(f"{lab}: n={n} gem {g.bp.mean():+.2f}bp ({g.R.mean():+.3f}R) t {tt:+.2f} PF {pf:.2f} winst {(g.bp > 0).mean()*100:.0f}%")
    print(f"{label:22} " + " | ".join(out))
    return t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="AUDNZD")
    ap.add_argument("--tf", default="1h", help="1h (P2) or 4h (P2b)")
    ap.add_argument("--z", default="2.0")
    ap.add_argument("--max-bars", type=int, default=24)
    a = ap.parse_args()
    res = {}
    for N in (20, 50):
        for z in map(float, a.z.split(",")):
            for sr in (False, True):
                lab = f"{a.pair} {a.tf} N{N} z{z}{' +S/R' if sr else ''}"
                t = run(a.pair, N, sr, z_in=z, max_h=a.max_bars, tf=a.tf)
                res[lab] = report(t, lab)
    for lab, t in res.items():
        y = t.assign(y=t.time.dt.year).groupby("y").bp.sum().round(0).to_dict()
        print(f"  {lab} som bp per jaar: {y}")
