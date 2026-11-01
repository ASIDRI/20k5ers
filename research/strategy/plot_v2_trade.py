"""Daily chart of one strategy-v2 trade, with the fib, the levels, entry, stop and targets.

    python research/strategy/plot_v2_trade.py EURUSD 2018-06-26 --from 2018-05-14 --to 2018-08-24 [--compare 2018-07-10:1.1743:1.18589:2018-08-22:note]

Reads the engine's trades from research/strategy/out/v2_<SYM>.csv (trader_strategy.py). --compare draws a second
entry (date:entry:stop), e.g. the trader's own trade, for comparison. Output: docs/setups_trader/v2_<SYM>_<date>.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from trader_strategy import day_label, T1, T2  # noqa: E402

UP, DOWN, INK, MUTED, GRID = "#1595b8", "#0b1530", "#1f2937", "#6b7280", "#e5e7eb"
STOP, TARGET, ENGINE, TRADER = "#c0392b", "#1e8449", "#d35400", "#7d3c98"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sym")
    ap.add_argument("day")
    ap.add_argument("--from", dest="start")
    ap.add_argument("--to", dest="end")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--levels", default="", help="extra horizontal lines: price:label,price:label")
    a = ap.parse_args()
    t = pd.read_csv(HERE / "out" / f"v2_{a.sym}.csv")
    tr = t[t.entry_day == a.day].iloc[0]
    d = load(a.sym, "D1")
    d["day"] = [day_label(x) for x in d.time]
    d = d[(d.day >= a.start) & (d.day <= a.end)].reset_index(drop=True)
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(15, 7.5), dpi=130)
    fig.patch.set_facecolor("white")
    for i, r in d.iterrows():
        col = UP if r.close >= r.open else DOWN
        ax.plot([i, i], [r.low, r.high], color=col, lw=1)
        ax.add_patch(plt.Rectangle((i - 0.32, min(r.open, r.close)), 0.64, max(abs(r.close - r.open), 1e-5),
                                   color=col, lw=0))
    f1, f0, dirn = tr.fib1, tr.fib0, int(tr.dir)
    rng = f1 - f0
    right = len(d) + 0.5
    for lev, name in ((1, "1"), (0.796, "0.796"), (0.66, "0.66"), (0.618, "0.618"), (0.5, "0.5"), (0, "0"),
                      (-T1, f"-{T1}"), (-T2, f"-{T2}")):
        p = f0 + lev * rng
        ax.axhline(p, color=MUTED, lw=0.7, ls=(0, (4, 4)), zorder=0)
        ax.text(-0.8, p, f"{name} ", va="center", ha="right", fontsize=8, color=MUTED)
    lines = [(float(tr.level), f"dag-S/R engine {tr.level:.5f}", ENGINE)]
    for item in filter(None, a.levels.split(",")):
        p, name = item.split(":")
        lines.append((float(p), name, INK))
    for p, name, col in lines:
        ax.axhline(p, color=col, lw=1.2, zorder=1)
        ax.text(len(d) - 1, p, f"{name} ", va="bottom", ha="right", fontsize=9, color=col)
    def idx(day):
        m = d.index[d.day >= day]
        return int(m[0]) if len(m) else len(d) - 1

    def trade_box(k0, k1, entry, sl, col, label, up):
        t1 = f0 - T1 * rng
        w = k1 - k0 + 0.6
        ax.add_patch(plt.Rectangle((k0 - 0.3, min(entry, sl)), w, abs(sl - entry), color=STOP, alpha=0.12, lw=0))
        ax.add_patch(plt.Rectangle((k0 - 0.3, min(entry, t1)), w, abs(entry - t1), color=TARGET, alpha=0.10, lw=0))
        ax.plot([k0 - 0.3, k1 + 0.3], [entry, entry], color=col, lw=2)
        ax.plot([k0 - 0.3, k1 + 0.3], [sl, sl], color=STOP, lw=1.4)
        ax.plot([k0 - 0.3, k1 + 0.3], [t1, t1], color=TARGET, lw=1.4)
        lx, ha = (k1 + 0.6, "left") if up else (k0 - 0.6, "right")
        ax.text(lx, sl, f"stop {sl:.5f}", va="center", ha=ha, fontsize=8, color=STOP,
                bbox=dict(fc="white", ec="none", pad=0.5))
        ax.text(lx, t1, f"T1 {t1:.5f}", va="center", ha=ha, fontsize=8, color=TARGET,
                bbox=dict(fc="white", ec="none", pad=0.5))
        ty = entry + (0.55 if up else -0.62) * rng
        ax.annotate(label, (k0, entry), xytext=(k0 - 12, ty), arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
                    fontsize=9, color=col, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=0.8))

    k = idx(a.day)
    ke = idx(tr.exit_day) if isinstance(tr.exit_day, str) and tr.exit_day else len(d) - 1
    hit1 = isinstance(tr.t1_day, str) and tr.t1_day
    res = f"R {tr.R:+.2f}" + ("" if hit1 else ", T1 niet geraakt")
    trade_box(k, ke, tr.entry, tr.sl, ENGINE, f"engine short {a.day} ({tr.pattern})\ninstap {tr.entry:.5f}, "
              f"stop geraakt {tr.exit_day} -> {res}", up=False)
    if a.compare:
        cday, centry, csl, cend, cnote = (a.compare.split(":") + ["", ""])[:5]
        trade_box(idx(cday), idx(cend) if cend else len(d) - 1, float(centry), float(csl), TRADER,
                  f"trader short {cday}\ninstap {float(centry):.5f} {cnote}", up=True)
    step = max(1, len(d) // 14)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([pd.Timestamp(s).strftime("%d %b") for s in d.day[::step]], fontsize=9, color=INK)
    ax.tick_params(axis="y", labelsize=9, colors=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(-3, len(d) + 8)
    ax.set_title(f"{a.sym} dag - strategie v2: fib {f1:.5f} -> {f0:.5f}, triggerweek {tr.trigger_week}",
                 loc="left", fontsize=12, color=INK)
    out = HERE.parents[1] / "docs" / "setups_trader" / f"v2_{a.sym}_{a.day}.png"
    fig.tight_layout()
    fig.savefig(out)
    print(out)


if __name__ == "__main__":
    main()
