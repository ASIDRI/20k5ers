"""Test 5: the trader's corrections (2026-10-29) on the dossier.

    python research/strategy/test5.py SYM [SYM ...] --start 2015-03-01 [--prefix t5_]

1. Legs, not small swings: a zigzag on WEEKLY candles; a turn is confirmed once price comes back REV x weekly ATR
   from the extreme (known only from that week on). A leg = the move between two confirmed turns, at least
   LEG x weekly ATR. The direction of the setup is the direction of the last completed leg (the big move), not of
   the last two small swings.
2. Fib over that leg: 1 = the leg's start (wick), 0 = its end (wick). Zone 0.618 - 1.1: price may wick below 1
   (a sweep of the low) and still be valid.
3. Entry: the first DAILY candle in the zone that rejects (long: low in the zone, close in the upper half of its range
   and above its open; mirror for short). Stop: just beyond the 1.1 level (0.2 daily ATR), since the low may be swept
   (SL_MODE "extreme": just beyond the lowest low since the zone was entered, for comparison).
   Void when a daily candle closes beyond 1.1, when -0.25 trades first, or after EXPIRY weeks.
4. Win = -0.25 reached before the stop. Exits reported: (a) all at -0.25, (b) half at -0.25 + stop to entry + rest at
   -0.65 or the next S/R level, (c) ladder -0.25/-0.5/-0.618/-1.
Tags: 'cont' = the leg broke the previous leg's extreme (continuation, bullish N / bearish V), else reversal;
'lvl' = a monthly/weekly S/R level inside the zone; 'mn' = monthly trend in the trade direction.
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
from test2 import cost_price, manage, ladder  # noqa: E402

REV, LEG, EXPIRY_W = 2.0, 4.0, 26
SL_MODE = "fib110"  # "fib110": stop just beyond the 1.1 level (the low may be swept); "extreme": just beyond the zone low so far


def legs(w):
    """Zigzag turns on weekly candles, point in time: [(confirm_index, turn_index, price, kind)] kind 'H' or 'L'."""
    h, l, c = w.high.values, w.low.values, w.close.values
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().bfill().values
    turns, d, ext_i = [], 0, 0
    for i in range(1, len(w)):
        if d >= 0 and h[i] >= h[ext_i]:
            ext_i = i if d == 1 or h[i] >= h[ext_i] else ext_i
        if d <= 0 and l[i] <= l[ext_i]:
            ext_i = i if d == -1 or l[i] <= l[ext_i] else ext_i
        if d == 0:
            d = 1 if c[i] > c[0] else -1
            ext_i = i
            continue
        if d == 1:
            if h[i] > h[ext_i]:
                ext_i = i
            elif h[ext_i] - l[i] >= REV * atr[i]:
                turns.append((i, ext_i, h[ext_i], "H"))
                d, ext_i = -1, i
        else:
            if l[i] < l[ext_i]:
                ext_i = i
            elif h[i] - l[ext_i] >= REV * atr[i]:
                turns.append((i, ext_i, l[ext_i], "L"))
                d, ext_i = 1, i
    return turns, atr


def zones(sym, start, end):
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    lv = Levels(sym)
    turns, atr = legs(w)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    out = []
    for k in range(2, len(turns)):
        ci, ti, p_end, kind = turns[k]
        _, si, p_start, _ = turns[k - 1]
        _, _, p_prev, _ = turns[k - 2]  # previous leg's end, same side as this leg's end
        ready = w["done"][ci]
        if ready < t0 or ready >= t1:
            continue
        rng = abs(p_end - p_start)
        if rng < LEG * atr[ci]:
            continue
        dirn = 1 if kind == "H" else -1
        top, ext = p_end, p_start
        z_lo, z_hi = sorted([top - dirn * 0.618 * rng, top - dirn * 1.1 * rng])
        levs = lv.at(ready)
        nxt = [p for p, _ in levs if (p - (top + dirn * 0.25 * rng)) * dirn > 0 and (p - (top + dirn * 0.65 * rng)) * dirn < 0]
        out.append(dict(sym=sym, dir=dirn, date=str(ready.date()), ready=ready, start_t=w["time"][si], top_t=w["time"][ti],
                        ext=ext, top=top, rng=rng, z1=top - dirn * 0.618 * rng, z2=top - dirn * 1.1 * rng,
                        zlo=z_lo, zhi=z_hi, tp1=top + dirn * 0.25 * rng,
                        tp2=(min(nxt) if dirn == 1 else max(nxt)) if nxt else top + dirn * 0.65 * rng,
                        cont=bool((p_end - p_prev) * dirn > 0),
                        lvl=any(z_lo <= p <= z_hi for p, _ in levs),
                        mn=lv.trend(ready, "MN") * dirn))
    return out


def trade(z, d):
    dirn = z["dir"]
    a = int(np.searchsorted(d["time"].values, np.datetime64(z["ready"].tz_convert(None))))
    end = z["ready"] + pd.Timedelta(weeks=EXPIRY_W)
    o, h, l, c, t, atr = (d[k].values for k in ("open", "high", "low", "close", "time", "atr"))
    inv = z["top"] - dirn * 1.1 * z["rng"]  # 1.1 level
    extreme = None
    for i in range(a, len(d)):
        if pd.Timestamp(t[i]).tz_localize("UTC") > end:
            return dict(result="verlopen")
        if (h[i] >= z["tp1"]) if dirn == 1 else (l[i] <= z["tp1"]):
            return dict(result="weggelopen")
        if (c[i] < inv) if dirn == 1 else (c[i] > inv):
            return dict(result="ongeldig")
        inside = (l[i] <= z["zhi"]) if dirn == 1 else (h[i] >= z["zlo"])
        if not inside and extreme is None:
            continue
        e = l[i] if dirn == 1 else h[i]
        extreme = e if extreme is None else (min(extreme, e) if dirn == 1 else max(extreme, e))
        rngc = h[i] - l[i]
        if rngc <= 0:
            continue
        react = (c[i] > o[i] and (c[i] - l[i]) / rngc >= 0.5) if dirn == 1 else (c[i] < o[i] and (h[i] - c[i]) / rngc >= 0.5)
        if react and inside:
            entry = c[i]
            base = inv if SL_MODE == "fib110" else extreme
            sl = base - dirn * 0.2 * atr[i]
            risk = abs(entry - sl)
            if risk <= 0 or (z["tp1"] - entry) * dirn <= 0:
                return dict(result="ongeldig")
            zz = dict(z, tp1=z["tp1"], tp2=z["tp2"])
            m = manage(dirn, entry, sl, risk, zz, h, l, i + 1)
            return dict(result="gevuld", entry=entry, sl=sl, risk=risk, rr1=abs(z["tp1"] - entry) / risk,
                        fill=str(pd.Timestamp(t[i]).date()), R_c=ladder(dirn, entry, sl, risk, zz, h, l, i + 1), **m)
    return dict(result="open")


def run(sym, start, end):
    d = load(sym, "D1")
    tr = np.r_[np.nan, np.maximum(d.high.values[1:], d.close.values[:-1]) - np.minimum(d.low.values[1:], d.close.values[:-1])]
    d["atr"] = pd.Series(tr).rolling(14).mean().values
    cp = cost_price(sym)
    rows = []
    for z in zones(sym, start, end):
        r = trade(z, d)
        z = dict(z, **r)
        if r["result"] == "gevuld":
            z["R_cost"] = cp / r["risk"]
            z["win"] = bool(r["tp1_hit"])
            z["Rnet_a"] = (r["rr1"] if r["tp1_hit"] else -1.0) - z["R_cost"]
            z["Rnet"] = r["R"] - z["R_cost"]
            z["Rnet_c"] = r["R_c"] - z["R_cost"]
        rows.append(z)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2015-03-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t5_")
    ap.add_argument("--split", default="2021-01-01")
    ap.add_argument("--sl", default="fib110", choices=["fib110", "extreme"])
    a = ap.parse_args()
    SL_MODE = a.sl
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
    for half, g in f.groupby("half"):
        be = 1 / (1 + g.rr1.mean())
        print(f"{half}: trades {len(g)}, winnend {g.win.mean()*100:.1f}% (break-even {be*100:.1f}%), "
              f"a {g.Rnet_a.mean():+.3f}R PF {pf(g.Rnet_a):.2f} | b {g.Rnet.mean():+.3f}R PF {pf(g.Rnet):.2f} | "
              f"c {g.Rnet_c.mean():+.3f}R PF {pf(g.Rnet_c):.2f}")
    for col in ["cont", "lvl", "mn", "dir"]:
        print(f"\n--- {col}")
        print(f.groupby([col, "half"]).agg(n=("win", "size"), winnend=("win", "mean"), a=("Rnet_a", "mean"),
                                           b=("Rnet", "mean"), c=("Rnet_c", "mean")).round(3).to_string())
