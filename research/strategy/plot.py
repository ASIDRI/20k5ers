import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from structure import load, setups

UP, DN, INK = "#2e9e6b", "#d0503c", "#222"


def candles(ax, d, a, b):
    for i in range(a, b):
        o, h, l, c = d.open[i], d.high[i], d.low[i], d.close[i]
        col = UP if c >= o else DN
        ax.plot([i, i], [l, h], color=col, lw=0.8)
        ax.add_patch(Rectangle((i - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), color=col))


def real(ax, sym, bos_year, title):
    d = load(sym, "W1")
    s = next(x for x in setups(d) if d.time[x["bos_i"]].year == bos_year)
    a, b = max(0, s["key_i"] - 25), min(len(d), s.get("exit_i", s["bos_i"]) + 8)
    candles(ax, d, a, b)
    ax.hlines(s["key"], s["key_i"], b, color=INK, lw=1.2)
    ax.text(s["key_i"], s["key"], " KEY (lagere top, lichaam)", va="bottom", fontsize=8)
    ax.annotate("BOS: sluit krachtig boven KEY", (s["bos_i"], d.close[s["bos_i"]]), xytext=(s["bos_i"] - 22, d.close[s["bos_i"]]),
                fontsize=8, arrowprops=dict(arrowstyle="->"))
    x0 = s["hi_i"]
    ax.axhspan(s["z2"], s["z1"], xmin=0, xmax=1, color="#f2c94c", alpha=0.25)
    for lvl, lab in [(s["f0"], "fib 0"), (s["ll"], "fib 1 = SL (wick)"), (s["entry"], "instap 0,66"),
                     (s["tp1"], "TP1 -0,25"), (s["tp2"], "TP2 -0,65"), (s["tp3"], "TP3 -1")]:
        ax.hlines(lvl, x0, b, color="#888", lw=0.8, ls="--")
        ax.text(b - 0.5, lvl, lab, ha="right", va="bottom", fontsize=7)
    if "fill_i" in s:
        ax.plot(s["fill_i"], s["entry"], "o", color="#1f6fd1")
        ax.plot(s["exit_i"], s["tp1"] if s["result"] == "TP1" else s["sl"], "X", color=INK, ms=8)
    ticks = list(range(a, b, max(1, (b - a) // 6)))
    ax.set_xticks(ticks, [d.time[i].strftime("%b %y") for i in ticks], fontsize=7)
    ax.set_title(f"{title}: {sym} week, uitkomst {s['result']}", fontsize=10)


def schema(ax):
    xs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 21, 23]
    ys = [10, 7, 8.5, 5.5, 7, 4, 7.6, 9.4, 7.2, 6.3, 10.5, 12]
    ax.plot(xs, ys, color=INK, lw=1.5)
    ax.hlines(7, 4, 23, color=INK, lw=1.2); ax.text(4.2, 7.1, "KEY = laatste lagere top", fontsize=8)
    ax.annotate("BOS: candle SLUIT boven KEY, met kracht", (11.6, 7.4), xytext=(5, 11), fontsize=8, arrowprops=dict(arrowstyle="->"))
    ax.annotate("KEY-candle", (8, 7), xytext=(1, 2.8), fontsize=8, arrowprops=dict(arrowstyle="->"))
    ax.text(0, 14.8, "Dalend: lagere toppen + lagere bodems. KEY = laatste lagere top.\nAlleen een SLOT boven KEY telt; een wick of valse uitbraak niet.", fontsize=8)
    lo, hi = 4, 9.4
    for f, lab in [(0, "0 (top, lichaam)"), (0.618, "0,618"), (0.66, "0,66 instap"), (0.796, "0,796"), (1, "1 = SL onder swing low")]:
        y = hi - f * (hi - lo); ax.hlines(y, 14, 23, color="#888", ls="--", lw=0.8); ax.text(23.2, y, lab, fontsize=7, va="center")
    ax.axhspan(hi - 0.796 * (hi - lo), hi - 0.618 * (hi - lo), xmin=0.58, color="#f2c94c", alpha=0.3)
    for f, lab in [(-0.25, "TP1 -0,25"), (-0.65, "TP2 -0,65"), (-1, "TP3 -1")]:
        y = hi - f * (hi - lo); ax.hlines(y, 18, 23, color=UP, ls=":", lw=1); ax.text(23.2, y, lab, fontsize=7, va="center", color=UP)
    ax.text(14.5, 3, "zone moet samenvallen\nmet KEY of S/R (maand)", fontsize=7)
    ax.set_xlim(-0.5, 28); ax.set_ylim(2, 16); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Schema: dalende trend -> BOS -> fib -> instap", fontsize=10)


fig, axs = plt.subplots(1, 3, figsize=(18, 6))
schema(axs[0])
real(axs[1], "AUDUSD", 2017, "Voorbeeld 1")
real(axs[2], "EURUSD", 2021, "Voorbeeld 2")
fig.suptitle("Market Matrix-methode: KEY, BOS, fib-instap (gevonden door de regels zelf, zonder blik in de toekomst)", fontsize=12)
fig.tight_layout()
fig.savefig("/home/user/20k5ers/docs/strategy_visual.png", dpi=110)
print("ok")
