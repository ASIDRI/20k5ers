"""Dossier of the test 17 trades (one position per direction) for the trader to mark: would you take it, yes or no?

    python research/strategy/dossier_t17.py --sym NZDCAD --from 2023-01-01 --out docs/dossier_nzdcad.pdf

One page per trade: daily candles, the fib of the leg (1, 0.786, 0.65, 0.618, 0.5, 0, -0.2, -0.27), entry, stop,
target -0.2, fill and exit, and the result in R.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from t17_eval import one_per_dir  # noqa: E402

FIB = {1: "1", 0.786: "0.786", 0.65: "0.65", 0.618: "0.618", 0.5: "0.5", 0: "0", -0.2: "-0.2", -0.27: "-0.27"}


def page(pdf, d, t, n, total):
    dirn = t.dir
    b1, top = t.b1, t.top
    rng = (top - b1) * dirn
    a = d.time.searchsorted(pd.Timestamp(t.start_t, tz="UTC")) - 25
    x_end = t.x_t020 if isinstance(t.x_t020, str) else t.fill
    b = d.time.searchsorted(pd.Timestamp(x_end, tz="UTC")) + 15
    w = d.iloc[max(a, 0):min(b, len(d))].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11.7, 8.3))
    for i, r in w.iterrows():
        col = "#1f9bb5" if r.close >= r.open else "#0b1a33"
        ax.plot([i, i], [r.low, r.high], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((i - 0.35, min(r.open, r.close)), 0.7, max(abs(r.close - r.open), 1e-6), color=col))
    for lvl, lab in FIB.items():
        y = top - dirn * lvl * rng
        ax.axhline(y, color="#e07b00" if lvl in (0.618, 0.65) else ("#c0392b" if lvl < 0 else "#888"),
                   ls="--", lw=0.7)
        ax.text(len(w) - 0.5, y, f" {lab}", va="center", fontsize=8)
    tp = top + dirn * 0.2 * rng
    for y, lab, col in ((t.entry, "instap", "#2a6df4"), (t.sl, "SL", "#555"), (tp, "TP -0.2", "#1f9bb5")):
        ax.axhline(y, color=col, lw=1.2)
        ax.text(0, y, f"{lab} {y:.5f} ", va="bottom", fontsize=8, color=col)
    for day, mark, col in ((t.fill, "^" if dirn == 1 else "v", "#2a6df4"), (x_end, "x", "black")):
        k = w.time.searchsorted(pd.Timestamp(day, tz="UTC"))
        if 0 <= k < len(w):
            ax.plot(k, w.low[k] if mark != "x" else w.close[k], mark, color=col, ms=10)
    step = max(len(w) // 12, 1)
    ax.set_xticks(range(0, len(w), step))
    ax.set_xticklabels([str(x)[:10] for x in w.time[::step]], rotation=30, fontsize=8)
    res = f"{t.R_t020:+.2f}R" if pd.notna(t.R_t020) else "open"
    ax.set_title(f"{n}/{total}  {t.sym} D1  {'LONG' if dirn == 1 else 'SHORT'}  poot {t.start_t} -> {t.top_t}  "
                 f"vulling {t.fill}  uit {x_end}  resultaat (TP -0.2) {res}\n"
                 f"Zou jij deze nemen? Ja / Nee - waarom?", fontsize=10)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sym", default="NZDCAD")
    ap.add_argument("--prefix", default="t17_")
    ap.add_argument("--from", dest="start", default="2023-01-01")
    ap.add_argument("--out", default="docs/dossier_nzdcad.pdf")
    a = ap.parse_args()
    f = pd.read_csv(HERE / "out" / f"{a.prefix}{a.sym}.csv")
    f = one_per_dir(f[f.result == "gevuld"], "t020")
    f = f[f.date >= a.start].sort_values("fill")
    d = load(a.sym, "D1")
    with PdfPages(a.out) as pdf:
        for n, (_, t) in enumerate(f.iterrows(), 1):
            page(pdf, d, t, n, len(f))
    print(f"{len(f)} trades -> {a.out}")
