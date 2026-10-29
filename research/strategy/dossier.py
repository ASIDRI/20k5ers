"""Visual dossier: every setup the code found, so a trader can see what it does differently.

    python research/strategy/dossier.py --prefix viz_ --pairs EURUSD,AUDNZD,USDJPY --out docs/dossier_setups.pdf

One page per two trades, on weekly candles: S/R levels of month/week the code knew at that moment, KEY, the
breaking candle (BOS), the swing used for the fib (1 = extreme, 0 = top), the golden pocket 0.618-0.796, entry
(after a daily reaction candle in the zone), stop, -0.25 and -0.65, and the result. First page: the rules as coded.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load, Levels  # noqa: E402

UP, DN, INK = "#2e9e6b", "#d0503c", "#222"
RULES = """Zo werkt de code (test 4, structuur op de week, instap op de dag):

1. S/R-niveaus: maand en week, alleen uit candles die al gesloten waren. Een niveau = prijs waar wicks vaak
   keerden, minstens 2x als support EN 2x als resistance. (Grijze lijnen: M = maand, W = week.)
2. Trend/structuur op de week: toppen en bodems = hoger/lager dan 2 weken links en rechts, pas bevestigd 2 weken later.
   Dalend: KEY = laatste lagere top. BOS = een week sluit krachtig boven KEY (lichaam >= 1,5x gemiddelde van 10 weken).
   (Spiegelbeeld voor short.)
3. Fib na de BOS: 1 = laagste wick tussen KEY en de breuk; 0 = de eerste bevestigde top na de breuk (wick).
   Zone = 0,618-0,796 (geel). Doelen: -0,25 en -0,65 (of het volgende S/R-niveau daartussen).
4. Instap: pas als een DAGcandle in de zone een afwijzing toont (slot in de bovenste helft, groen voor long).
   SL: net onder de laagste wick in de zone (0,2 dag-ATR). Vervalt na 60 dagen, bij een slot onder fib 1,
   of als -0,25 eerst geraakt wordt.
5. Winnend = -0,25 geraakt voor de SL.

Wat de code NIET doet (en jij misschien wel): kop-schouders herkennen, de 'kracht' of 'netheid' van de structuur
beoordelen, op 4u/1u naar vertraging kijken, nieuws/sessies, DXY of correlaties, kiezen welk niveau 'telt'.
Kijk per grafiek: zou jij deze trade zo genomen hebben? Waar zou jij het anders zien?"""


def candles(ax, w, a, b):
    for i in range(a, b):
        o, h, l, c = w.open[i], w.high[i], w.low[i], w.close[i]
        col = UP if c >= o else DN
        ax.plot([i, i], [l, h], color=col, lw=0.7)
        ax.add_patch(Rectangle((i - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), color=col))


def plot_trade(ax, z, w, lv):
    t = lambda s: pd.Timestamp(s) if pd.Timestamp(s).tzinfo else pd.Timestamp(s).tz_localize("UTC")  # noqa: E731
    idx = lambda ts: int(w.time.searchsorted(t(ts), side="right")) - 1  # noqa: E731
    ki, bi, ei, ti = idx(z.key_t), idx(z.bos_t), idx(z.ext_t), idx(z.top_t)
    fi = idx(z.fill) if isinstance(z.fill, str) else None
    a = max(0, min(ki, ei) - 25)
    b = min(len(w), (fi if fi is not None else ti) + 18)
    candles(ax, w, a, b)
    for p, tf in lv.at(t(z.ready)):
        if w.low[a:b].min() - 0.02 * p <= p <= w.high[a:b].max() + 0.02 * p:
            ax.axhline(p, color="#999", lw=0.8, ls="-")
            ax.text(a, p, f" {tf} {p:.5g}", fontsize=6, color="#666", va="bottom")
    d = z.dir
    ax.hlines(z.key, ki, bi, color=INK, lw=1.4)
    ax.text(ki, z.key, " KEY", fontsize=7, va="bottom" if d == 1 else "top")
    ax.annotate("BOS", (bi, w.close[bi]), xytext=(bi - 6, w.close[bi] + d * 0.6 * (z.top - z.ext)),
                fontsize=7, arrowprops=dict(arrowstyle="->"))
    ax.plot([ei], [z.ext], "o", color="#1f6fd1", ms=4)
    ax.plot([ti], [z.top], "o", color="#1f6fd1", ms=4)
    x0 = min(ei, ti)
    ax.axhspan(min(z.z1, z.z2), max(z.z1, z.z2), xmin=(x0 - a) / max(1, b - a), color="#f2c94c", alpha=0.35)
    for lvl, lab, col in [(z.top, "0", "#888"), (z.ext, "1", "#888"), (z.tp1, "-0,25", UP), (z.tp2, "doel 2", UP)]:
        ax.hlines(lvl, x0, b - 1, color=col, ls="--", lw=0.8)
        ax.text(b - 1, lvl, f" {lab}", fontsize=7, va="center", color=col)
    if fi is not None and z.result == "gevuld":
        ax.plot([fi], [z.entry], "^" if d == 1 else "v", color="#1f6fd1", ms=9)
        ax.hlines(z.sl, fi, b - 1, color=DN, lw=1.0)
        ax.text(fi, z.sl, " SL", fontsize=7, color=DN, va="top" if d == 1 else "bottom")
        res = f"WINNEND (-0,25 voor SL), {z.Rnet:+.1f}R" if z.win else f"VERLIES, {z.Rnet:+.1f}R"
    else:
        res = f"geen trade ({z.result})"
    ticks = list(range(a, b, max(1, (b - a) // 6)))
    ax.set_xticks(ticks, [w.time[i].strftime("%b %y") for i in ticks], fontsize=7)
    ax.tick_params(axis="y", labelsize=7)
    conf = ", ".join(k for k, v in (("S/R in zone", z.lvl), ("OB", z.ob), ("FVG", z.fvg)) if v) or "geen samenloop"
    ax.set_title(f"{z.sym} {'LONG' if d == 1 else 'SHORT'}  setup {z.date}  instap {z.fill if isinstance(z.fill, str) else '-'}  |  {res}  |  {conf}",
                 fontsize=8, color=UP if (z.result == "gevuld" and z.win) else (DN if z.result == "gevuld" else "#666"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="viz_")
    ap.add_argument("--pairs", default="EURUSD,AUDNZD,USDJPY")
    ap.add_argument("--out", default=str(HERE.parents[1] / "docs" / "dossier_setups.pdf"))
    ap.add_argument("--all-zones", action="store_true", help="also the setups that never filled")
    a = ap.parse_args()
    zs = pd.concat(pd.read_csv(HERE / "out" / f"{a.prefix}test2_{s}.csv") for s in a.pairs.split(","))
    if not a.all_zones:
        zs = zs[zs.result == "gevuld"]
    zs = zs.sort_values(["sym", "date"]).reset_index(drop=True)
    with PdfPages(a.out) as pdf:
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.text(0.05, 0.95, "Dossier: alle setups die de code vond (EURUSD, AUDNZD, USDJPY, 2015-2025)", fontsize=14, va="top")
        f = zs[zs.result == "gevuld"]
        summ = f.groupby("sym").agg(trades=("win", "size"), winnend=("win", "mean"), gemR=("Rnet", "mean"))
        txt = "\n".join(f"{s}: {int(r.trades)} trades, winnend {r.winnend*100:.0f}%, gemiddeld {r.gemR:+.2f}R na kosten" for s, r in summ.iterrows())
        fig.text(0.05, 0.88, RULES, fontsize=9, va="top", family="monospace")
        fig.text(0.05, 0.12, txt, fontsize=10, va="top")
        pdf.savefig(fig); plt.close(fig)
        cache = {}
        for k in range(0, len(zs), 2):
            fig, axs = plt.subplots(2, 1, figsize=(11.7, 8.3))
            for ax, (_, z) in zip(axs, zs.iloc[k:k + 2].iterrows()):
                if z.sym not in cache:
                    w = load(z.sym, "W1")
                    cache[z.sym] = (w, Levels(z.sym))
                plot_trade(ax, z, *cache[z.sym])
            if len(zs.iloc[k:k + 2]) == 1:
                axs[1].axis("off")
            fig.tight_layout()
            pdf.savefig(fig); plt.close(fig)
    print(f"{len(zs)} setups -> {a.out}")
