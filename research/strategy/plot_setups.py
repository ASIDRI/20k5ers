"""Charts of engine setups (test 36 engine output) next to the weekly picture, for the trader to review.

    python research/strategy/plot_setups.py PREFIX SYM FROM TO OUT.pdf

Left: daily candles from 40 days before the leg start to 25 days after the exit, with fib 1 / 0 / 0.618 / 0.66 /
0.786 / -0.2, the BoS (key) level the leg broke, the entry, stop, target and the weekly S/R clusters near price.
Right: weekly candles (2 years up to the fill) with the same levels and the weekly bias.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
import test5  # noqa: E402
from sr_quality import methods  # noqa: E402
from test36 import bos_bias, bias_at  # noqa: E402


def candles(ax, df):
    x = np.arange(len(df))
    up = df.close.values >= df.open.values
    ax.vlines(x, df.low, df.high, color="#555", lw=0.6)
    ax.bar(x[up], (df.close - df.open)[up], bottom=df.open[up], color="#26a69a", width=0.7)
    ax.bar(x[~up], (df.open - df.close)[~up], bottom=df.close[~up], color="#222", width=0.7)
    return x


def main(prefix, sym, a, b, out):
    f = pd.read_csv(HERE / "out" / f"{prefix}{sym}.csv")
    f = f[(f.result == "gevuld") & (f.fill >= a) & (f.fill <= b)]
    d = load(sym, "D1")
    w = load(sym, "W1")
    test5.REV = 2.0
    turns, _ = test5.legs(d)
    tp_by_top = {round(p, 6): k for k, (_, _, p, _) in enumerate(turns)}
    clus = methods(sym)[0]["cluster"]
    bb = bos_bias(sym, "W1")
    with PdfPages(out) as pdf:
        for _, r in f.iterrows():
            dirn, b1, top, entry, sl = r.dir, r.b1, r.top, r.entry, r.sl
            rng = abs(top - b1)
            fib = lambda x: top - dirn * x * rng  # noqa: E731
            ts = pd.Timestamp(r.fill, tz="UTC")
            exit_t = r.x_t020 if isinstance(r.x_t020, str) else r.fill
            dd = d[(d.time >= pd.Timestamp(r.start_t, tz="UTC") - pd.Timedelta(days=60)) &
                   (d.time <= pd.Timestamp(exit_t, tz="UTC") + pd.Timedelta(days=35))].reset_index(drop=True)
            ww = w[(w.time >= ts - pd.Timedelta(days=730)) & (w.time <= pd.Timestamp(exit_t, tz="UTC") + pd.Timedelta(days=60))].reset_index(drop=True)
            # the key level the leg broke: the previous same-side daily turn before the leg's start
            k = next((i for i, (ci, ti, p, kk) in enumerate(turns) if str(d.time[ti])[:10] == r.start_t and abs(p - r.w1) < 1e-9), None)
            key = turns[k - 1][2] if k is not None and k >= 1 else None
            levels = [p for p in clus(ts) if abs(p - entry) < 3 * rng]
            fig, (ax, ax2) = plt.subplots(1, 2, figsize=(17, 6.5), gridspec_kw={"width_ratios": [2.2, 1]})
            x = candles(ax, dd)
            ix = lambda t: int(np.searchsorted(dd.time.values, np.datetime64(pd.Timestamp(t).tz_localize(None))))  # noqa: E731
            x0 = ix(r.start_t)
            for lab, lv, col, ls in (("1", b1, "k", "--"), ("0", top, "k", "--"), ("0.618", fib(0.618), "orange", ":"),
                                     ("0.66", fib(0.66), "orange", "-"), ("0.786", fib(0.786), "teal", ":"),
                                     ("-0.2 (TP)", fib(-0.2), "green", "-")):
                ax.hlines(lv, x0, len(dd) - 1, color=col, ls=ls, lw=1)
                ax.text(len(dd) - 1, lv, f" {lab} {lv:.5f}", va="center", fontsize=8, color=col)
            ax.hlines(sl, x0, len(dd) - 1, color="red", lw=1)
            ax.text(len(dd) - 1, sl, f" SL {sl:.5f}", va="center", fontsize=8, color="red")
            if key is not None:
                ax.hlines(key, 0, len(dd) - 1, color="purple", lw=1.2)
                ax.text(0, key, " BoS (key level)", va="bottom", fontsize=8, color="purple")
            for p in levels:
                ax.hlines(p, 0, len(dd) - 1, color="royalblue", lw=2, alpha=0.35)
                ax2.hlines(p, 0, len(ww) - 1, color="royalblue", lw=2, alpha=0.35)
            fi = ix(r.fill)
            ax.plot(fi, entry, marker="^" if dirn == 1 else "v", color="blue", ms=11)
            if isinstance(r.x_t020, str):
                ax.axvline(ix(r.x_t020), color="grey", lw=0.8, ls="--")
            ax.set_xticks(x[::15])
            ax.set_xticklabels([str(t)[:10] for t in dd.time.values[::15]], rotation=30, fontsize=7)
            res = f"{r.R_t020:+.2f}R" if not pd.isna(r.R_t020) else "loopt"
            ax.set_title(f"{sym} D1 {'LONG' if dirn == 1 else 'SHORT'}  poot {r.start_t} -> {r.top_t}  instap {r.fill}"
                         f"  resultaat {res}   | weekbias {'mee' if r.hi_bias == 1 else ('tegen' if r.hi_bias == -1 else 'neutraal')}"
                         f", weekly S/R in zone {'ja' if str(r.wk_sr) == 'True' else 'nee'}", fontsize=10)
            candles(ax2, ww)
            wi = int(np.searchsorted(ww.time.values, np.datetime64(ts.tz_localize(None)))) - 1
            ax2.axvline(wi, color="blue", lw=1)
            for lv, col in ((b1, "k"), (top, "k"), (fib(0.66), "orange"), (sl, "red"), (fib(-0.2), "green")):
                ax2.hlines(lv, max(wi - 12, 0), len(ww) - 1, color=col, lw=0.8)
            ax2.set_xticks(np.arange(len(ww))[::13])
            ax2.set_xticklabels([str(t)[:7] for t in ww.time.values[::13]], rotation=30, fontsize=7)
            ax2.set_title(f"week (2 jaar); blauwe lijn = instapweek; blauwe banden = weekly S/R", fontsize=9)
            fig.tight_layout()
            pdf.savefig(fig)
            fig.savefig(str(out).replace(".pdf", f"_{r.fill}.png"), dpi=110)
            plt.close(fig)
    print(f"{len(f)} setups -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
