import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd
from matplotlib.patches import Rectangle
from sr_levels import levels
fig, axs = plt.subplots(1, 2, figsize=(16, 6))
for ax, tf, start in [(axs[0], "MN", "2003-01-01"), (axs[1], "W1", "2019-05-01")]:
    d = pd.read_csv(f"/home/user/20k5ers/data/ohlcv/EURUSD_{tf}_2003_2025.csv", parse_dates=["time"]); d.columns = [c.lower() for c in d.columns]
    full = d[d.time < "2023-07-01"].reset_index(drop=True)
    lv = levels(full, near_atr=8, max_levels=5)
    v = full[full.time >= start].reset_index(drop=True)
    for i, r in v.iterrows():
        col = "#2e9e6b" if r.close >= r.open else "#d0503c"
        ax.plot([i, i], [r.low, r.high], color=col, lw=0.7)
        ax.add_patch(Rectangle((i - 0.35, min(r.open, r.close)), 0.7, abs(r.close - r.open) or 1e-9, color=col))
    for p, st, rt in lv:
        ax.axhline(p, color="#222", lw=1.2); ax.text(0, p, f" bot {p:.4f} (S {st} / R {rt})", va="bottom", fontsize=8)
    vid = [1.18765, 1.08646, 0.99578] + ([1.14389] if tf == "W1" else [])
    for p in vid:
        ax.axhline(p, color="#1f6fd1", lw=1.2, ls="--"); ax.text(len(v) - 1, p, f"video {p} ", ha="right", va="top", fontsize=8, color="#1f6fd1")
    ticks = list(range(0, len(v), max(1, len(v) // 8)))
    ax.set_xticks(ticks, [v.time[i].strftime("%Y" if tf == "MN" else "%b %y") for i in ticks], fontsize=8)
    ax.set_title(f"EURUSD {'maand' if tf == 'MN' else 'week'}: niveaus van de bot (zwart, data tot juli 2023) en van de video (blauw)", fontsize=10)
fig.tight_layout(); fig.savefig("/home/user/20k5ers/docs/sr_levels_check.png", dpi=105); print("ok")
