import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, UP = "#222", "#2e9e6b"
fig, ax = plt.subplots(figsize=(10, 6.5))
xs = [0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 22]
ys = [3, 6.5, 4.8, 8.2, 6.2, 9.6, 7.0, 8.1, 6.6, 9.0, 12.5]
ax.plot(xs, ys, color=INK, lw=1.6)
ax.hlines(6, -0.5, 25, color="#1f6fd1", lw=2)
ax.text(-0.3, 5.55, "S/R-niveau maand/week (veel tikken)", color="#1f6fd1", fontsize=9)
notes = [((7, 8.2), (2.5, 10.8), "1. Uitbraak: slot boven het niveau"),
         ((9, 6.2), (5.5, 2.6), "2. Retest houdt: hogere bodem op het niveau"),
         ((11, 9.6), (9.3, 11.8), "3. Bullish N: slot boven de vorige top"),
         ]
for xy, txt, lab in notes:
    ax.annotate(lab, xy, xytext=txt, fontsize=9, arrowprops=dict(arrowstyle="->"))
lo, hi = 6.2, 9.6
for f, lab in [(0, "0 = nieuwe top (lichaam)"), (0.618, "0,618"), (0.66, "0,66 instap"), (0.796, "0,796"),
               (1, "1 = retest-bodem (wick); SL eronder")]:
    y = hi - f * (hi - lo)
    ax.hlines(y, 11, 22, color="#888", ls="--", lw=0.8)
    ax.text(22.3, y, lab, fontsize=8, va="center")
ax.axhspan(hi - 0.796 * (hi - lo), hi - 0.618 * (hi - lo), xmin=0.46, xmax=0.87, color="#f2c94c", alpha=0.35)
ax.text(13.2, 6.85, "4. golden pocket", fontsize=9)
for f, lab in [(-0.25, "TP1 -0,25"), (-0.65, "TP2 -0,65"), (-1, "TP3 -1 / volgende S/R")]:
    y = hi - f * (hi - lo)
    ax.hlines(y, 17, 22, color=UP, ls=":", lw=1.2)
    ax.text(22.3, y, lab, fontsize=8, va="center", color=UP)
ax.annotate("5. instap", (13.5, 7.35), xytext=(14.5, 4.2), fontsize=9, arrowprops=dict(arrowstyle="->"))
ax.set_xlim(-0.5, 29); ax.set_ylim(2, 14.5); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Setup B: trendvoortzetting na uitbraak + retest van een S/R-niveau (bullish N)", fontsize=11)
fig.tight_layout()
fig.savefig("/home/user/20k5ers/docs/strategy_continuation.png", dpi=110)
print("ok")
