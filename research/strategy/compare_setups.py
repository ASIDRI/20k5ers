"""The trader's setups next to what the engine (test 18) makes of the same move: levels, fill and result of both.

    python research/strategy/compare_setups.py [--pdf docs/vergelijking_setups.pdf]

For each trade in trader_trades.TRADES the engine runs on that pair and timeframe around the trade; the engine setup
in the same direction whose fib is closest to the trader's (sum of the distances of 1 and 0, in the trader's range)
is shown. Both are then followed on the data with the same simple rules: fill at the limit, the trader's TP or -0.2
before the stop.
"""
import argparse
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
import test18 as E  # noqa: E402
from trader_trades import TRADES  # noqa: E402


def follow(d, dirn, entry, sl, tp, live):
    d = d[d.time >= pd.Timestamp(live, tz="UTC")].reset_index(drop=True)
    hit = (d.low <= entry) if dirn == 1 else (d.high >= entry)
    if not hit.any():
        return "niet gevuld", None, None
    k = int(hit.idxmax())
    for i in range(k, len(d)):
        adv, fav = (d.low[i], d.high[i]) if dirn == 1 else (d.high[i], d.low[i])
        if (adv <= sl) if dirn == 1 else (adv >= sl):
            return "-1R", str(d.time[k])[:10], str(d.time[i])[:10]
        if i > k and ((fav >= tp) if dirn == 1 else (fav <= tp)):
            return f"{abs(tp - entry) / abs(entry - sl):+.2f}R", str(d.time[k])[:10], str(d.time[i])[:10]
    return "loopt nog", str(d.time[k])[:10], None


def engine_match(sym, tf, dirn, f1, f0, live):
    span = pd.Timedelta(days=200 if tf == "D1" else 900)
    t0 = pd.Timestamp(live) - span
    df = E.run(sym, tf, str(t0.date()), str((pd.Timestamp(live) + pd.Timedelta(days=30)).date()))
    df = df[df.dir == dirn]
    if df.empty:
        return None
    rng = abs(f0 - f1)
    dist = (df.b1 - f1).abs() / rng + (df.top - f0).abs() / rng
    return df.loc[dist.idxmin()], float(dist.min())


def plot(pdf, d, name, dirn, tr, en, live):
    a = d.time.searchsorted(pd.Timestamp(live, tz="UTC")) - 70
    w = d.iloc[max(a, 0):a + 200].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11.7, 8.3))
    for i, r in w.iterrows():
        col = "#1f9bb5" if r.close >= r.open else "#0b1a33"
        ax.plot([i, i], [r.low, r.high], color=col, lw=0.7)
        ax.add_patch(plt.Rectangle((i - 0.35, min(r.open, r.close)), 0.7, max(abs(r.close - r.open), 1e-6), color=col))
    for (lab, lv), col, x0 in ((tr, "#2e7d32", 0.0), (en, "#c62828", 0.5)):
        if lv is None:
            continue
        for key, y in lv.items():
            ax.axhline(y, xmin=x0, xmax=x0 + 0.5, color=col, lw=1.0, ls="-" if key in ("instap", "SL", "TP") else ":")
            ax.text(len(w) * (x0 + 0.01), y, f"{lab} {key} {y:.5f}", fontsize=7, color=col, va="bottom")
    step = max(len(w) // 12, 1)
    ax.set_xticks(range(0, len(w), step))
    ax.set_xticklabels([str(x)[:10] for x in w.time[::step]], rotation=30, fontsize=8)
    ax.set_title(f"{name}: groen = jouw lijnen (links), rood = de motor (rechts)", fontsize=10)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="docs/vergelijking_setups.pdf")
    a = ap.parse_args()
    rows = []
    with PdfPages(a.pdf) as pdf:
        for name, sym, tf, dirn, f1, f0, entry, sl, tp, live in TRADES:
            d = load(sym, tf)
            res_t = follow(d, dirn, entry, sl, tp, live)
            rng = abs(f0 - f1)
            tr_lv = {"1": f1, "0": f0, "instap": entry, "SL": sl, "TP": tp}
            m = engine_match(sym, tf, dirn, f1, f0, live)
            row = dict(trade=name, jouw_1=f1, jouw_0=f0, jouw_instap=entry, jouw_SL=sl,
                       jouw_instap_fib=round((f0 - entry) * dirn / rng, 3), jouw_SL_fib=round((f0 - sl) * dirn / rng, 3),
                       jouw_TP_ext=round((tp - f0) * dirn / rng, 2), jouw_resultaat=res_t[0], jouw_vulling=res_t[1])
            en_lv = None
            if m is not None:
                e, dist = m
                tp_e = e.top + dirn * 0.2 * e.rng
                en_lv = {"1": e.b1, "0": e.top, "instap": e.entry, "SL": e.sl, "TP": tp_e}
                row.update(motor_1=round(e.b1, 5), motor_0=round(e.top, 5), motor_instap=round(e.entry, 5),
                           motor_SL=round(e.sl, 5), motor_SL_fib=round((e.top - e.sl) * dirn / e.rng, 3),
                           afstand=round(dist, 2), motor_status=e.result,
                           motor_vulling=e.get("fill"), motor_R_tp020=round(e.get("R_t020", np.nan), 2),
                           motor_R_beheer=round(e.get("R_m_0.2_entry_trail", np.nan), 2),
                           motor_R_jouwTP=follow(d, dirn, e.entry, e.sl, tp, live)[0])
            rows.append(row)
            plot(pdf, d, name, dirn, ("jij", tr_lv), ("motor", en_lv), live)
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(out.T.to_string())
    out.to_csv(HERE / "out" / "vergelijking_setups.csv", index=False)
