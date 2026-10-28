"""R&D phase 1: weekly candle signals, at monthly/weekly S/R levels or not. Do they predict the next weeks?

    python research/rnd/weekly_events.py --start 2015-01-01 --end 2025-12-31

Point in time: an event is a COMPLETED weekly candle; levels and trends are those known when it completed
(sr_levels via setup_study.Levels, candle_avail completion times). Entry: open of the first daily candle after
the weekly candle completed. Outcomes on the daily path, in units of the weekly ATR(14):
  win11 = +1 ATR reached before -1 ATR (same day both: loss), within 40 daily bars (else unresolved)
  win21 = +2 before -1;  fwd5/fwd10/fwd20 = return after 5/10/20 daily bars (direction of the signal)
Costs (spread + slippage, both sides) are converted to ATR and taken off ev11 and the forward returns.

Signals (bull; bear = mirror):
  engulf  bullish candle whose body engulfs the previous (bearish) body
  pin     lower wick >= 2x body and >= half the range, close in the upper third
  sfp     low below the previous week's low, close back above it (sweep and reclaim)
  any     every weekly candle (baseline), both directions
Context: at_level = the wick tested a level (low within 0.25 ATR of it or below it) and the close is above it;
trend = sign of the weekly and monthly trend in the direction of the signal.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strategy"))
sys.path.insert(0, str(HERE.parents[1] / "backtest" / "src"))
from setup_study import load, Levels  # noqa: E402
from test2 import cost_price  # noqa: E402
from candle_avail import complete_times  # noqa: E402

SYMS = ("AUDCAD AUDCHF AUDJPY AUDNZD AUDUSD CADCHF CADJPY CHFJPY EURAUD EURCAD EURCHF EURGBP EURJPY EURNZD EURUSD "
        "GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPUSD NZDCAD NZDCHF NZDJPY NZDUSD USDCAD USDCHF USDJPY XTI_USD UK100_USD").split()
TOL = 0.25
HORIZON = 40


def events(sym, start, end):
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    d = load(sym, "D1")
    lv = Levels(sym)
    o, h, l, c = (w[k].values for k in ("open", "high", "low", "close"))
    tr = np.r_[np.nan, np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().values
    dt = d["time"].values
    dh, dl, dc, do = (d[k].values for k in ("high", "low", "close", "open"))
    cp = cost_price(sym)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    rows = []
    for k in range(20, len(w)):
        done = w["done"][k]
        if done < t0 or done >= t1 or np.isnan(atr[k]):
            continue
        a = int(np.searchsorted(dt, np.datetime64(done.tz_convert(None))))
        if a >= len(d) - 2:
            continue
        entry = do[a]
        rngk = h[k] - l[k]
        body = abs(c[k] - o[k])
        levs = [p for p, _ in lv.at(done)]
        for dirn in (1, -1):
            if dirn == 1:
                sig = {"engulf": c[k] > o[k] and c[k - 1] < o[k - 1] and c[k] >= o[k - 1] and o[k] <= c[k - 1],
                       "pin": rngk > 0 and (min(o[k], c[k]) - l[k]) >= max(2 * body, 0.5 * rngk) and c[k] >= l[k] + 2 / 3 * rngk,
                       "sfp": l[k] < l[k - 1] and c[k] > l[k - 1]}
                at_level = any(l[k] <= p + TOL * atr[k] and c[k] > p and l[k] >= p - 2 * atr[k] for p in levs)
            else:
                sig = {"engulf": c[k] < o[k] and c[k - 1] > o[k - 1] and c[k] <= o[k - 1] and o[k] >= c[k - 1],
                       "pin": rngk > 0 and (h[k] - max(o[k], c[k])) >= max(2 * body, 0.5 * rngk) and c[k] <= h[k] - 2 / 3 * rngk,
                       "sfp": h[k] > h[k - 1] and c[k] < h[k - 1]}
                at_level = any(h[k] >= p - TOL * atr[k] and c[k] < p and h[k] <= p + 2 * atr[k] for p in levs)
            sig["any"] = True
            fired = [s for s, v in sig.items() if v]
            # outcome on the daily path
            A = atr[k]
            win11 = win21 = None
            for j in range(a, min(a + HORIZON, len(d))):
                up = (dh[j] - entry) * dirn if dirn == 1 else (entry - dl[j])
                dn = (entry - dl[j]) if dirn == 1 else (dh[j] - entry)
                if win11 is None:
                    if dn >= A:
                        win11 = 0
                    elif up >= A:
                        win11 = 1
                if win21 is None:
                    if dn >= A:
                        win21 = 0
                    elif up >= 2 * A:
                        win21 = 1
                if win11 is not None and win21 is not None:
                    break
            fwd = {f"fwd{n}": ((dc[min(a + n - 1, len(d) - 1)] - entry) * dirn - cp) / A for n in (5, 10, 20)}
            for s in fired:
                rows.append(dict(sym=sym, date=str(done.date()), sig=s, dir=dirn, at_level=at_level,
                                 wk=lv.trend(done, "W1") * dirn, mn=lv.trend(done, "MN") * dirn,
                                 win11=win11, win21=win21, cost_atr=cp / A, **fwd))
    return pd.DataFrame(rows)


def summarize(df, label):
    df = df.copy()
    df["half"] = np.where(df.date.str[:4] <= "2020", "ontdek 15-20", "bevestig 21-25")
    df["ev11"] = np.where(df.win11 == 1, 1.0, np.where(df.win11 == 0, -1.0, np.nan)) - df.cost_atr
    df["ev21"] = np.where(df.win21 == 1, 2.0, np.where(df.win21 == 0, -1.0, np.nan)) - df.cost_atr
    out = []
    groups = [("sig",), ("sig", "at_level"), ("sig", "at_level", "wk"), ("sig", "at_level", "mn")]
    for g in groups:
        for key, x in df.groupby(list(g) + ["half"]):
            ev = x["ev11"].dropna()
            ev2 = x["ev21"].dropna()
            out.append(dict(groep="/".join(g), cel=" ".join(str(v) for v in key[:-1]), half=key[-1], n=len(x),
                            p11=round(x["win11"].mean() * 100, 1), ev11=round(ev.mean(), 3),
                            t11=round(ev.mean() / (ev.std() / np.sqrt(len(ev))), 2) if len(ev) > 2 else np.nan,
                            ev21=round(ev2.mean(), 3), fwd10=round(x["fwd10"].mean(), 3),
                            t10=round(x["fwd10"].mean() / (x["fwd10"].std() / np.sqrt(len(x))), 2) if len(x) > 2 else np.nan))
    s = pd.DataFrame(out)
    piv = s.pivot_table(index=["groep", "cel"], columns="half", values=["n", "ev11", "t11", "ev21", "fwd10", "t10"])
    return s, piv


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--symbols", default=",".join(SYMS))
    a = ap.parse_args()
    outdir = HERE / "out"
    outdir.mkdir(exist_ok=True)
    allev = []
    for s in a.symbols.split(","):
        try:
            e = events(s, a.start, a.end)
            allev.append(e)
            print(f"{s}: {len(e)} events", flush=True)
        except Exception as ex:  # noqa
            print(f"{s}: overgeslagen ({type(ex).__name__}: {ex})", flush=True)
    ev = pd.concat(allev)
    ev.to_csv(outdir / "weekly_events.csv", index=False)
    s, piv = summarize(ev, "weekly")
    s.to_csv(outdir / "weekly_summary.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 500)
    print(piv.round(3).to_string())
    # candidates: the rule of docs/RND_PLAN.md (discovery t >= 3; confirmation same sign and >= half the effect)
    print("\nKANDIDATEN (ontdek |t| >= 2 op ev11 of fwd10; 'door' = t >= 3 en bevestiging >= helft van het effect):")
    D, B = s[s.half == "ontdek 15-20"].set_index(["groep", "cel"]), s[s.half == "bevestig 21-25"].set_index(["groep", "cel"])
    for m, t in (("ev11", "t11"), ("fwd10", "t10")):
        for idx, r in D[D[t].abs() >= 2].iterrows():
            if idx not in B.index:
                continue
            b = B.loc[idx]
            door = abs(r[t]) >= 3 and np.sign(b[m]) == np.sign(r[m]) and abs(b[m]) >= 0.5 * abs(r[m])
            print(f"  {m:5} {idx[0]:22} {idx[1]:18} ontdek n={int(r.n):4} {r[m]:+.3f} (t {r[t]:+.2f}) | "
                  f"bevestig n={int(b.n):4} {b[m]:+.3f} (t {b[t]:+.2f})  {'DOOR' if door else ''}")
    reg = HERE / "registry.csv"
    cells = s[s.half == "ontdek 15-20"][["groep", "cel"]].drop_duplicates()
    pd.DataFrame(dict(fase="1-week", groep=cells.groep, cel=cells.cel, datum=pd.Timestamp.now().isoformat()[:16])).to_csv(
        reg, mode="a", header=not reg.exists(), index=False)
    print(f"\nregister: {len(cells)} cellen bijgeschreven -> {reg}")
