"""R&D phase 2: daily and 4h signals incl. liquidity, at monthly/weekly S/R levels or not.

    python research/rnd/events.py --tf D1      (or H4)

Same rules as weekly_events.py: completed candles only, levels/trends known at that moment, entry at the
next candle's open, outcomes on the following candles of the same timeframe in units of its ATR(14):
win11 (+1 before -1; a candle touching both counts as a loss), win21 (+2 before -1), fwd3/6/12 after costs.

Signals (bull; bear = mirror):
  engulf, pin, sfp   as on the weekly chart (sfp = sweep of the previous candle's low, close back above)
  sweep_prev         sweep of the previous period's low and close back above it
                     (D1: previous WEEK low; H4: previous DAY low), the classic liquidity grab
  sweep_eq           sweep of equal lows (two latest confirmed swing lows within 0.2 ATR) and close back above
  fvg                price trades back into an open bullish fair value gap of the last 20 candles and closes above
                     its bottom
  any                every candle, both directions (baseline)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "strategy"))
sys.path.insert(0, str(HERE.parents[1] / "backtest" / "src"))
from setup_study import load, Levels  # noqa: E402
from test2 import cost_price  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from weekly_events import SYMS, summarize  # noqa: E402

TOL = 0.25
HOR = {"D1": 20, "H4": 30}
PREV = {"D1": "W1", "H4": "D1"}


def events(sym, tf, start, end):
    x = load(sym, tf)
    x["done"] = complete_times(x["time"], tf)
    p = load(sym, PREV[tf])
    p["done"] = complete_times(p["time"], PREV[tf])
    lv = Levels(sym)
    o, h, l, c = (x[k].values for k in ("open", "high", "low", "close"))
    tr = np.r_[np.nan, np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().values
    pdone = p["done"].values
    cp = cost_price(sym)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    hor = HOR[tf]
    highs, lows = [], []
    rows = []
    for k in range(30, len(x) - 1):
        # swings confirmed at k (2 bars each side)
        s = k - 2
        if h[s] == h[s - 2:s + 3].max():
            highs.append(s)
        if l[s] == l[s - 2:s + 3].min():
            lows.append(s)
        done = x["done"][k]
        if done < t0 or done >= t1 or np.isnan(atr[k]):
            continue
        A = atr[k]
        rngk, body = h[k] - l[k], abs(c[k] - o[k])
        j = int(np.searchsorted(pdone, np.datetime64(done.tz_convert(None)), side="right")) - 1  # last completed prev period
        if j < 1:
            continue
        pl, ph = p["low"].values[j], p["high"].values[j]
        levs = [q for q, _ in lv.at(done)]
        for dirn in (1, -1):
            if dirn == 1:
                eq = len(lows) >= 2 and abs(l[lows[-1]] - l[lows[-2]]) <= 0.2 * A
                eqp = min(l[lows[-1]], l[lows[-2]]) if eq else None
                fvg_hit = False
                for m in range(max(2, k - 20), k - 1):
                    if l[m] > h[m - 2] and l[m + 1:k].min(initial=np.inf) > h[m - 2]:  # gap still open before k
                        if l[k] <= l[m] and c[k] > h[m - 2]:
                            fvg_hit = True
                            break
                sig = {"engulf": c[k] > o[k] and c[k - 1] < o[k - 1] and c[k] >= o[k - 1] and o[k] <= c[k - 1],
                       "pin": rngk > 0 and (min(o[k], c[k]) - l[k]) >= max(2 * body, 0.5 * rngk) and c[k] >= l[k] + 2 / 3 * rngk,
                       "sfp": l[k] < l[k - 1] and c[k] > l[k - 1],
                       "sweep_prev": l[k] < pl and c[k] > pl,
                       "sweep_eq": eq and l[k] < eqp and c[k] > eqp,
                       "fvg": fvg_hit}
                at_level = any(l[k] <= q + TOL * A and c[k] > q and l[k] >= q - 2 * A for q in levs)
            else:
                eq = len(highs) >= 2 and abs(h[highs[-1]] - h[highs[-2]]) <= 0.2 * A
                eqp = max(h[highs[-1]], h[highs[-2]]) if eq else None
                fvg_hit = False
                for m in range(max(2, k - 20), k - 1):
                    if h[m] < l[m - 2] and h[m + 1:k].max(initial=-np.inf) < l[m - 2]:
                        if h[k] >= h[m] and c[k] < l[m - 2]:
                            fvg_hit = True
                            break
                sig = {"engulf": c[k] < o[k] and c[k - 1] > o[k - 1] and c[k] <= o[k - 1] and o[k] >= c[k - 1],
                       "pin": rngk > 0 and (h[k] - max(o[k], c[k])) >= max(2 * body, 0.5 * rngk) and c[k] <= h[k] - 2 / 3 * rngk,
                       "sfp": h[k] > h[k - 1] and c[k] < h[k - 1],
                       "sweep_prev": h[k] > ph and c[k] < ph,
                       "sweep_eq": eq and h[k] > eqp and c[k] < eqp,
                       "fvg": fvg_hit}
                at_level = any(h[k] >= q - TOL * A and c[k] < q and h[k] <= q + 2 * A for q in levs)
            sig["any"] = True
            fired = [n for n, v in sig.items() if v]
            entry = o[k + 1]
            win11 = win21 = None
            for i in range(k + 1, min(k + 1 + hor, len(x))):
                up = (h[i] - entry) if dirn == 1 else (entry - l[i])
                dn = (entry - l[i]) if dirn == 1 else (h[i] - entry)
                if win11 is None:
                    win11 = 0 if dn >= A else (1 if up >= A else None)
                if win21 is None:
                    win21 = 0 if dn >= A else (1 if up >= 2 * A else None)
                if win11 is not None and win21 is not None:
                    break
            fwd = {f"fwd{n}": ((c[min(k + n, len(x) - 1)] - entry) * dirn - cp) / A for n in (3, 6, 12)}
            fwd["fwd10"] = fwd["fwd6"]  # summarize() reads fwd10 as its forward measure: here 6 candles
            for n in fired:
                rows.append(dict(sym=sym, date=str(done.date()), sig=n, dir=dirn, at_level=at_level,
                                 wk=lv.trend(done, "W1") * dirn, mn=lv.trend(done, "MN") * dirn,
                                 win11=win11, win21=win21, cost_atr=cp / A, **fwd))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", choices=["D1", "H4"], required=True)
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", default=",".join(SYMS))
    a = ap.parse_args()
    outdir = HERE / "out"
    outdir.mkdir(exist_ok=True)
    allev = []
    for s in a.symbols.split(","):
        try:
            e = events(s, a.tf, a.start, a.end)
            allev.append(e)
            print(f"{s}: {len(e)} events", flush=True)
        except Exception as ex:  # noqa
            print(f"{s}: overgeslagen ({type(ex).__name__}: {ex})", flush=True)
    ev = pd.concat(allev)
    ev.to_csv(outdir / f"{a.tf}_events.csv", index=False)
    s, piv = summarize(ev, a.tf)
    s.to_csv(outdir / f"{a.tf}_summary.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 500)
    t = s[s.groep.isin(["sig", "sig/at_level"])].pivot_table(index=["groep", "cel"], columns="half",
                                                              values=["n", "p11", "ev11", "t11", "fwd10", "t10"])
    print(t.round(3).to_string())
    print("\nKANDIDATEN (ontdek |t| >= 2; 'door' = t >= 3 en bevestiging >= helft van het effect, zelfde teken):")
    D, B = s[s.half == "ontdek 15-20"].set_index(["groep", "cel"]), s[s.half == "bevestig 21-25"].set_index(["groep", "cel"])
    for m, tt in (("ev11", "t11"), ("fwd10", "t10")):
        for idx, r in D[D[tt].abs() >= 2].iterrows():
            if idx not in B.index:
                continue
            b = B.loc[idx]
            door = abs(r[tt]) >= 3 and np.sign(b[m]) == np.sign(r[m]) and abs(b[m]) >= 0.5 * abs(r[m])
            print(f"  {m:5} {idx[0]:22} {idx[1]:20} ontdek n={int(r.n):5} {r[m]:+.3f} (t {r[tt]:+.2f}) | "
                  f"bevestig n={int(b.n):5} {b[m]:+.3f} (t {b[tt]:+.2f})  {'DOOR' if door else ''}")
    reg = HERE / "registry.csv"
    cells = s[s.half == "ontdek 15-20"][["groep", "cel"]].drop_duplicates()
    pd.DataFrame(dict(fase=f"2-{a.tf}", groep=cells.groep, cel=cells.cel, datum=pd.Timestamp.now().isoformat()[:16])).to_csv(
        reg, mode="a", header=not reg.exists(), index=False)
    print(f"\nregister: {len(cells)} cellen bijgeschreven")
