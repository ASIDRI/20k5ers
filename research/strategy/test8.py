"""Test 8: the rules of video 8 (FTMO interview, swing trader with the same top-down method; 2026-10-29).

    python research/strategy/test8.py SYM [SYM ...] --start 2015-01-01 [--prefix t8_]

1. Daily pattern: a bullish N / bearish V on DAILY legs (zigzag of test5, --struct D1): the last leg made a higher
   high ('cont') from a higher low ('hl'), mirror for shorts, and is impulsive (>= LEG x daily ATR).
2. Fib from the leg's start (1) to its end (0); TP = -0.27 (the daily TP). Daily zone: from 0.618 down to the first
   structure = the previous leg's end (the high that was broken), kept between the 0.618 and 1 levels; 0.786 when
   that structure lies above 0.618.
3. 4-hour entry: after the first touch of the zone, wait until at least 3 four-hour candles since the touch respect
   the zone (no close beyond its far side) and at least one of them is bullish (bearish for shorts). Then a limit order
   on the body of the last bullish candle (its open); stop beneath the lowest wick since the touch plus 10 pips.
   Void: a 4-hour close beyond the zone, the TP reached before the fill, or EXPIRY daily candles after the leg.
4. Exits: (a) all at -0.27 or the stop; (b) the same, stop to entry once price is 2R (or half the way to the TP if
   that is nearer) in profit.
Tags: 'htf' = weekly trend in the trade direction, 'mn' = monthly trend, 'lvl' = monthly/weekly S/R in the zone.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load, Levels  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402
from test5 import legs  # noqa: E402

EXPIRY, TP_EXT, PIPS = 26, 0.27, 10
SPAN = pd.Timedelta(days=7 / 5)


def pip(sym):
    u = sym.replace("_", "").upper()
    return 0.01 if ("JPY" in u or u.startswith("XTI")) else (1.0 if u.startswith("UK100") else 0.0001)


def zones(sym, start, end):
    w = load(sym, "D1")
    w["done"] = complete_times(w["time"], "D1")
    lv = Levels(sym)
    turns, atr = legs(w)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    out = []
    for k in range(3, len(turns)):
        ci, ti, p_end, kind = turns[k]
        _, si, p_start, _ = turns[k - 1]
        p_prev = turns[k - 2][2]  # previous leg's end (same side as this end)
        p_prev_start = turns[k - 3][2]  # previous low for a long (high for a short)
        ready = w["done"][ci]
        if ready < t0 or ready >= t1:
            continue
        rng = abs(p_end - p_start)
        if rng < 4.0 * atr[ci]:
            continue
        dirn = 1 if kind == "H" else -1
        top, ext = p_end, p_start
        f618, f786, f1 = (top - dirn * x * rng for x in (0.618, 0.786, 1.0))
        far = p_prev if (f618 - p_prev) * dirn > 0 and (p_prev - f1) * dirn >= 0 else f786
        z_lo, z_hi = sorted([f618, far])
        levs = lv.at(ready)
        out.append(dict(sym=sym, dir=dirn, date=str(ready.date()), ready=ready, start_t=w["time"][si], top_t=w["time"][ti],
                        ext=ext, top=top, rng=rng, near=f618, far=far, zlo=z_lo, zhi=z_hi,
                        tp=top + dirn * TP_EXT * rng,
                        cont=bool((p_end - p_prev) * dirn > 0), hl=bool((p_start - p_prev_start) * dirn > 0),
                        lvl=any(z_lo <= p <= z_hi for p, _ in levs),
                        mn=lv.trend(ready, "MN") * dirn, htf=lv.trend(ready, "W1") * dirn))
    return out


def trade(z, d, sym):
    dirn = z["dir"]
    a = int(np.searchsorted(d["time"].values, np.datetime64(z["ready"].tz_convert(None))))
    end = z["ready"] + EXPIRY * SPAN
    o, h, l, c, t = (d[k].values for k in ("open", "high", "low", "close", "time"))
    beyond = (lambda x: x < z["far"]) if dirn == 1 else (lambda x: x > z["far"])
    hit = (lambda i, p: h[i] >= p) if dirn == 1 else (lambda i, p: l[i] <= p)
    touch, limit, sl = None, None, None
    for i in range(a, len(d)):
        if pd.Timestamp(t[i]).tz_localize("UTC") > end:
            return dict(result="verlopen")
        if hit(i, z["tp"]):
            return dict(result="weggelopen")
        if limit is not None and ((l[i] <= limit) if dirn == 1 else (h[i] >= limit)):
            return fill(z, d, i, limit, sl, sym)
        if beyond(c[i]):
            return dict(result="ongeldig")
        if touch is None:
            if (l[i] <= z["zhi"]) if dirn == 1 else (h[i] >= z["zlo"]):
                touch = i
            else:
                continue
        seg = range(touch, i + 1)
        bull = [j for j in seg if (c[j] - o[j]) * dirn > 0]
        if limit is None and len(seg) >= 3 and bull:
            limit = o[bull[-1]]
            ext = min(l[j] for j in seg) if dirn == 1 else max(h[j] for j in seg)
            sl = ext - dirn * PIPS * pip(sym)
            if (z["tp"] - limit) * dirn <= 0 or (limit - sl) * dirn <= 0:
                return dict(result="ongeldig")
    return dict(result="open")


def fill(z, d, i, entry, sl, sym):
    dirn, h, l, t = z["dir"], d["high"].values, d["low"].values, d["time"].values
    risk = abs(entry - sl)
    rr = abs(z["tp"] - entry) / risk
    be_at = entry + dirn * min(2.0, 0.5 * rr) * risk
    Ra = Rb = None
    stop_b, xa, xb = sl, None, None
    for j in range(i, len(h)):
        adv, fav = (l[j], h[j]) if dirn == 1 else (h[j], l[j])
        if Ra is None:
            if (adv <= sl) if dirn == 1 else (adv >= sl):
                Ra, xa = -1.0, j
            elif j > i and ((fav >= z["tp"]) if dirn == 1 else (fav <= z["tp"])):
                Ra, xa = rr, j
        if Rb is None:
            if (adv <= stop_b) if dirn == 1 else (adv >= stop_b):
                Rb, xb = (stop_b - entry) * dirn / risk, j
            elif j > i and ((fav >= z["tp"]) if dirn == 1 else (fav <= z["tp"])):
                Rb, xb = rr, j
            elif j > i and ((fav >= be_at) if dirn == 1 else (fav <= be_at)):
                stop_b = entry
        if Ra is not None and Rb is not None:
            break
    if Ra is None:
        return dict(result="open")
    cost = cost_price(sym) / risk
    day = lambda k: str(pd.Timestamp(t[k]).date()) if k is not None else None  # noqa: E731
    return dict(result="gevuld", entry=entry, sl=sl, risk=risk, rr1=rr, fill=day(i), exit_a=day(xa), exit_b=day(xb),
                win=Ra > 0, R_cost=cost, Rnet_a=Ra - cost, Rnet=(Rb if Rb is not None else 0.0) - cost)


def run(sym, start, end):
    d = load(sym, "H4")
    return pd.DataFrame([dict(z, **trade(z, d, sym)) for z in zones(sym, start, end)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t8_")
    ap.add_argument("--split", default="2021-01-01")
    a = ap.parse_args()
    out = HERE / "out"
    allz = []
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(out / f"{a.prefix}{s}.csv", index=False)
        print(f"{s}: {len(df)} poten, {int((df.result == 'gevuld').sum()) if len(df) else 0} trades", flush=True)
        allz.append(df)
    df = pd.concat(allz)
    f = df[df.result == "gevuld"].copy()
    f["half"] = np.where(f.date < a.split, "periode 1", "periode 2")
    pf = lambda x: x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else np.nan  # noqa: E731
    print(f"\n##### {len(allz)} assets: {len(df)} poten, {len(f)} trades; {df.result.value_counts().to_dict()}")
    for lab, g0 in (("alles", f), ("filter cont+hl+htf", f[f.cont & f.hl & (f.htf == 1)])):
        for half, g in g0.groupby("half"):
            print(f"{lab} {half}: trades {len(g)}, winnend {g.win.mean()*100:.1f}% (break-even {100/(1+g.rr1.median()):.1f}%, "
                  f"mediane RR {g.rr1.median():.2f}), a {g.Rnet_a.mean():+.3f}R PF {pf(g.Rnet_a):.2f} | "
                  f"b {g.Rnet.mean():+.3f}R PF {pf(g.Rnet):.2f}")
    for col in ["cont", "hl", "lvl", "mn", "htf", "dir"]:
        print(f"\n--- {col}")
        print(f.groupby([col, "half"]).agg(n=("win", "size"), winnend=("win", "mean"), a=("Rnet_a", "mean"),
                                           b=("Rnet", "mean")).round(3).to_string())
