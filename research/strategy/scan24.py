"""Scanner for test 24 (4-hour confirmation in the golden pocket / 0.786) on the 28 forex pairs, up to now.
Fib 1 on the body of the start candle, 0 on the wick of the end (test 32). Test 32 was rejected (the tight stop under
the 4-hour reaction low); kept for watching the 4-hour timing. Journal: docs/scan/journal24_bw.csv.

    python research/strategy/scan24.py [--since 2026-01-01]

Daily and 4-hour candles: stored + Yahoo (live_setups.extend). Writes docs/scan/scan24_<today>.md: setups waiting
(with the 4-hour level whose close confirms) and the trades since --since, with the
context of test 20 (rule week + S/R, monthly trend). Appends new trades to docs/scan/journal24.csv.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import setup_study  # noqa: E402
from live_setups import extend  # noqa: E402
from scan import pairs, fmt, DOCS  # noqa: E402

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
    import test24
    test24.load = setup_study.load
    test24.FIB = "bodywick"
    df = pd.concat([test24.run(s, "2025-06-01", "2027-01-01") for s in syms], ignore_index=True)
    df["regel"] = (df.get("wk_struct") == 1) & (df.get("htf_sup").astype(str).str.lower() == "true")
    df["cont"] = df.cont.astype(str).str.lower() == "true"
    df["maand"] = df.get("m_ma").map({1: "mee", -1: "tegen", 0: "?"}).fillna("-")
    df["richting"] = df.dir.map({1: "LONG", -1: "SHORT"})
    today = str(pd.Timestamp.now().date())
    act = df[df.result == "actief"].sort_values(["aangeraakt", "sym"], ascending=[False, True])
    tr = df[(df.result == "gevuld") & (df.fill >= a.since)].sort_values("fill")
    L = [f"# Scan test 24 - {today} (fib body -> wick, 28 forexparen, dag + 4 uur t/m nu)", "",
         "Instap pas na bevestiging: na de laagste 4u-low in de zone een 4u-slot boven de laatste 4u-swingtop.",
         "Test 32 (verworpen): de krappe stop onder de 4u-reactie-low werkt niet; zie scan_<datum>.md voor de dagversie.",
         "Onder de wick van de startcandle alleen na een sweep van de liquiditeit (eerdere dag-low). SL onder de reactie-low.", "",
         "## Wachtende setups", "",
         "| paar | richting | cont | zone 0,618 | zone 0,786 | fib 1 | liquiditeit | aangeraakt | laagste | bevestiging: 4u-slot voorbij |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in act.iterrows():
        f_ = lambda v: fmt(v, r.sym) if v is not None and not pd.isna(v) else "-"  # noqa: E731
        L.append(f"| {r.sym} | {r.richting} | {'ja' if r.cont else 'nee'} | {f_(r.zone_0618)} | {f_(r.zone_0786)} | "
                 f"{f_(r.fib1)} | {f_(r.liq)} | {'ja' if r.aangeraakt else 'nee'} | {f_(r.laagste)} | {f_(r.bevestig_boven)} |")
    L += ["", f"## Trades sinds {a.since}", "",
          "| paar | richting | cont | regel | maandtrend | instap (4u) | instap | SL | TP -0,2 | RR | -0,2 | beheer |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    res = lambda v: "loopt" if pd.isna(v) else f"{v:+.2f}R"  # noqa: E731
    for _, r in tr.iterrows():
        tp = r.top + r.dir * 0.2 * r.rng
        L.append(f"| {r.sym} | {r.richting} | {'ja' if r.cont else 'nee'} | {'ja' if r.regel else 'nee'} | {r.maand} | "
                 f"{r.fill} | {fmt(r.entry, r.sym)} | {fmt(r.sl, r.sym)} | {fmt(tp, r.sym)} | {r.rr:.1f} | {res(r.R_t020)} | "
                 f"{res(r.R_m_top_1)} |")
    for lab, g in (("cont + regel", tr[tr.cont & tr.regel]), ("alle", tr), ("regel", tr[tr.regel]), ("regel + maandtrend mee", tr[tr.regel & (tr.maand == "mee")])):
        x = g.R_t020.dropna()
        L.append(f"- {lab}: {len(g)} trades, {len(x)} afgesloten, {x.sum():+.2f}R op -0,2 ({(x > 0).sum()} winnaars)")
    L += ["", "Koersen na half december 2025 van Yahoo Finance; kunnen enkele pips afwijken van de broker."]
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / f"scan24_{today}.md").write_text("\n".join(L) + "\n")
    j = DOCS / "journal24_bw.csv"
    keep = ["sym", "richting", "cont", "regel", "maand", "start_t", "top_t", "fill", "entry", "sl", "rr", "R_t020",
            "R_m_top_1"]
    new = tr[keep].assign(gezien=today)
    if j.exists():
        old = pd.read_csv(j)
        key = ["sym", "richting", "start_t", "fill"]
        new = pd.concat([old, new[~new.set_index(key).index.isin(old.set_index(key).index)]], ignore_index=True)
    new.to_csv(j, index=False)
    print("\n".join(L))
