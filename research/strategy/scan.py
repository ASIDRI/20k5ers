"""Scanner: test 20 on the 28 forex pairs up to yesterday (stored candles + Yahoo daily), for forward testing.

    python research/strategy/scan.py [--since 2026-01-01]

Writes docs/scan/scan_<today>.md (active setups and the trades since --since) and appends trades it has not seen
before to docs/scan/journal.csv (first-seen date per trade), so that results are measured going forward.
Rule shown as "regel": weekly structure in the trade direction and a monthly/weekly S/R level between fib 1 and the
entry (test 20, pre-registered); setups without it are listed too, marked. Management per test 20: half at -0.2,
stop to the old high, rest to -1 (R_m_top_1); full at -0.2 (R_t020).
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import setup_study  # noqa: E402
from live_setups import extend  # noqa: E402
from rt import CCY  # noqa: E402

DOCS = HERE.parents[1] / "docs" / "scan"


def pairs():
    out = []
    for i, a in enumerate(CCY):
        for b in CCY[i + 1:]:
            for p in (a + b, b + a):
                if list(setup_study.DATA.glob(f"{p}_D1_*.csv")):
                    out.append(p)
                    break
    return out


def fmt(x, sym):
    return f"{x:.3f}" if "JPY" in sym else f"{x:.5f}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-01-01")
    a = ap.parse_args()
    live = HERE / "out" / "live_data"
    syms = pairs()
    for s in syms:
        extend(s, live)
        time.sleep(0.5)
    setup_study.DATA = live
    import test20
    test20.load = setup_study.load
    rows = []
    for s in syms:
        rows.append(test20.run(s, "2025-06-01", "2027-01-01"))
    df = pd.concat(rows, ignore_index=True)
    df["regel"] = (df.get("wk_struct") == 1) & (df.get("htf_sup").astype(str).str.lower() == "true")
    df["maand"] = df.get("m_ma").map({1: "mee", -1: "tegen", 0: "?"}).fillna("?")
    df["richting"] = df.dir.map({1: "LONG", -1: "SHORT"})
    today = str(pd.Timestamp.now().date())
    DOCS.mkdir(parents=True, exist_ok=True)
    act = df[df.result == "actief"].sort_values(["regel", "sym"], ascending=[False, True])
    tr = df[(df.result == "gevuld") & (df.fill >= a.since)].sort_values("fill")
    lines = [f"# Scan {today} (test 20, 28 forexparen, dagdata t/m gisteren)", "",
             "Regel = weekstructuur in de handelsrichting + maand/week-S/R tussen fib 1 en de instap.",
             "Instap: wachten op een dag-afwijzingscandle met wick tot 0,618 en slot tussen 0,5 en 0,786.", "",
             "## Actieve setups (zone getekend, wachten op de afwijzingscandle)", "",
             "| paar | richting | regel | maandtrend | fib 1 | fib 0 | zone 0,618 | zone 0,786 | SL | TP -0,2 | aanrakingen | nog candles |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in act.iterrows():
        lines.append(f"| {r.sym} | {r.richting} | {'ja' if r.regel else 'nee'} | {r.maand} | {fmt(r.b1, r.sym)} | {fmt(r.top, r.sym)} | "
                     f"{fmt(r.zone_0618, r.sym)} | {fmt(r.zone_0786, r.sym)} | {fmt(r.sl, r.sym)} | "
                     f"{fmt(r.tp_020, r.sym)} | {int(r.touch_n)} | {int(r.nog_candles)} |")
    lines += ["", f"## Trades sinds {a.since}", "",
              "| paar | richting | regel | maandtrend | poot | instap (dag) | instap | SL | TP -0,2 | -0,2 | beheer |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in tr.iterrows():
        tp = r.top + r.dir * 0.2 * r.rng
        res = lambda v: "loopt" if pd.isna(v) else f"{v:+.2f}R"  # noqa: E731
        lines.append(f"| {r.sym} | {r.richting} | {'ja' if r.regel else 'nee'} | {r.maand} | {r.start_t} -> {r.top_t} | {r.fill} | "
                     f"{fmt(r.entry, r.sym)} | {fmt(r.sl, r.sym)} | {fmt(tp, r.sym)} | {res(r.R_t020)} | "
                     f"{res(r.R_m_top_1)} |")
    sel = tr[tr.regel]
    sums = []
    for lab, g in (("regel = ja", sel), ("maandtrend mee", tr[tr.maand == "mee"]),
                   ("regel = ja + maandtrend mee", sel[sel.maand == "mee"]), ("alle", tr)):
        a20, am = g.R_t020.dropna(), g.R_m_top_1.dropna()
        sums.append(f"{lab}: {len(g)} trades; volledig op -0,2: {len(a20)} afgesloten, {a20.sum():+.2f}R "
                    f"({(a20 > 0).sum()} winnaars); beheer: {len(am)} afgesloten, {am.sum():+.2f}R")
    lines += [""] + [f"- {x}" for x in sums] + ["(lopende trades niet meegeteld)",
              "", "Koersen na half december 2025 van Yahoo Finance; kunnen enkele pips afwijken van de broker."]
    (DOCS / f"scan_{today}.md").write_text("\n".join(lines) + "\n")
    j = DOCS / "journal.csv"
    keep = ["sym", "richting", "regel", "maand", "start_t", "top_t", "b1", "top", "fill", "entry", "sl", "R_t020", "R_m_top_1"]
    new = tr[keep].assign(gezien=today)
    if j.exists():
        old = pd.read_csv(j)
        key = ["sym", "richting", "start_t", "fill"]
        new = new[~new.set_index(key).index.isin(old.set_index(key).index)]
        old = old.set_index(key)
        upd = tr[keep].set_index(key)
        old.update(upd[["R_t020", "R_m_top_1"]])
        new = pd.concat([old.reset_index(), new], ignore_index=True)
    new.to_csv(j, index=False)
    print("\n".join(lines))
