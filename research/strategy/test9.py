"""Test 9: daily setups, 4-hour entry; several stops/targets and everything known at the entry, for a discovery round.

    python research/strategy/test9.py SYM [SYM ...] --start 2015-01-01 --end 2025-12-31 [--prefix t9_]

Setup (as test 7): legs on DAILY candles (zigzag of test5: turn after 2 daily ATR back, leg >= 4 daily ATR); fib over
the last leg (1 = start, 0 = end); zone 0.618 - 1.1 (the start may be swept). Entry: the first 4-hour rejection candle
in the zone (long: low in the zone, close above its open and in the upper half of its range; mirror for shorts), at
its close. Void: a 4-hour close beyond 1.1, -0.27 traded before the entry, or 26 daily candles after the leg.
Every entry is followed with each combination of
  stop  f110 = 1.1 level - 0.2 x 4h ATR | wick = lowest low since the zone was touched - 0.5 x 4h ATR |
        f100 = 1.0 level (leg start) - 0.2 x 4h ATR (only when the entry is above it)
  target t0 = the leg's end (0) | t27 = -0.27 | t27be = -0.27, stop to entry once half way to the target
-> columns R_<stop>_<target> (net of costs; a bar touching stop and target counts as the stop).
Features at the entry (all known then): depth (fib level of the entry), leg_atr, leg_days, retr_days, wait_bars,
cont, hl, lvl, mn, htf (weekly trend), wk_last (the last completed weekly leg points in the trade direction),
sr_dist (nearest monthly/weekly level, in daily ATR), hour, d1_ma (daily close vs its 50-day mean, in the trade
direction), body (rejection candle body / range).
Test 10 (video 8 context, also known at the entry): wk_depth = how far price has corrected the last completed weekly
leg (0 = its end, 1 = its start; NaN when that leg points against the trade); decel = the last counter-move on the
daily is smaller than the one before it (corrections getting smaller).
Test 12 (video 9): wk_trend, wk_phase (1 correction, 2 impulse, 3 pause, 4 extension, 0 no clear trend) and wk_ok
(see week_phase).
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

EXPIRY, SPAN = 26, pd.Timedelta(days=7 / 5)
STOPS, TARGETS = ("f110", "wick", "f100"), ("t0", "t27", "t27be")


def atr(d, n=14):
    tr = np.r_[d.high.values[0] - d.low.values[0],
               np.maximum(d.high.values[1:], d.close.values[:-1]) - np.minimum(d.low.values[1:], d.close.values[:-1])]
    return pd.Series(tr).rolling(n).mean().bfill().values


def zones(sym, start, end):
    d1 = load(sym, "D1")
    d1["done"] = complete_times(d1["time"], "D1")
    ma50 = d1.close.rolling(50).mean().values
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    wturns, w_atr_all = legs(w)
    w_atr = np.array([w_atr_all[ci] for ci, *_ in wturns])
    w_done = np.array([w["done"][ci].value for ci, *_ in wturns])
    w_kind = np.array([k for *_, k in wturns])
    w_px = np.array([p for _, _, p, _ in wturns])
    lv = Levels(sym)
    turns, a1 = legs(d1)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    out = []
    for k in range(4, len(turns)):
        ci, ti, p_end, kind = turns[k]
        _, si, p_start, _ = turns[k - 1]
        p_prev, p_prev_start = turns[k - 2][2], turns[k - 3][2]
        counter_last, counter_before = abs(p_start - p_prev), abs(p_prev_start - turns[k - 4][2])
        ready = d1["done"][ci]
        if ready < t0 or ready >= t1:
            continue
        rng = abs(p_end - p_start)
        if rng < 4.0 * a1[ci]:
            continue
        dirn = 1 if kind == "H" else -1
        levs = [p for p, _ in lv.at(ready)]
        z1, z2 = p_end - dirn * 0.618 * rng, p_end - dirn * 1.1 * rng
        out.append(dict(sym=sym, dir=dirn, date=str(ready.date()), ready=ready, top_t=d1["time"][ti],
                        ext=p_start, top=p_end, rng=rng, zlo=min(z1, z2), zhi=max(z1, z2), atr_d=a1[ci],
                        leg_atr=rng / a1[ci], leg_days=int(ti - si),
                        cont=bool((p_end - p_prev) * dirn > 0), hl=bool((p_start - p_prev_start) * dirn > 0),
                        lvl=any(min(z1, z2) <= p <= max(z1, z2) for p in levs),
                        mn=lv.trend(ready, "MN") * dirn, htf=lv.trend(ready, "W1") * dirn,
                        d1_ma=int(np.sign(d1.close.values[ci] - ma50[ci]) * dirn) if not np.isnan(ma50[ci]) else 0,
                        decel=bool(counter_last < counter_before),
                        _levs=levs, _wd=w_done, _wk=w_kind, _wp=w_px, _wa=w_atr))
    return out


def week_phase(z, kw, entry, dirn):
    """Video 9: weekly bias in 4 phases (uptrend; mirror for a downtrend), from the confirmed weekly zigzag turns:
    trend = last two highs and last two lows both higher (lower); 1 = correction (last turn is a high), 2 = impulse
    (last turn is a low), 3 = pause (within 0.5 weekly ATR under the previous high), 4 = extension (above it); 0 = no
    clear trend. wk_ok: a trade the video allows - with the trend in phase 2 or 4, or against it in phase 1."""
    kinds, px = z["_wk"][:kw + 1], z["_wp"][:kw + 1]
    hs, ls = px[kinds == "H"], px[kinds == "L"]
    if kw < 3 or len(hs) < 2 or len(ls) < 2:
        return dict(wk_trend=0, wk_phase=0, wk_ok=False)
    T = 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)
    if T == 0:
        return dict(wk_trend=0, wk_phase=0, wk_ok=False)
    last = kinds[-1]
    ext = hs[-1] if T == 1 else ls[-1]  # previous extreme in the trend direction
    if (last == "H") == (T == 1):
        ph = 1
    elif (entry - ext) * T > 0:
        ph = 4
    elif (ext - entry) * T < 0.5 * z["_wa"][kw]:
        ph = 3
    else:
        ph = 2
    return dict(wk_trend=T * dirn, wk_phase=ph, wk_ok=bool((ph in (2, 4) and dirn == T) or (ph == 1 and dirn == -T)))


def follow(dirn, entry, sl, tp, be, h, l, start):
    """R of one stop/target combination and the exit bar; a bar touching both counts as the stop."""
    risk = abs(entry - sl)
    stop, half = sl, entry + dirn * 0.5 * abs(tp - entry)
    for j in range(start, len(h)):
        adv, fav = (l[j], h[j]) if dirn == 1 else (h[j], l[j])
        if (adv <= stop) if dirn == 1 else (adv >= stop):
            return (stop - entry) * dirn / risk, j
        if (fav >= tp) if dirn == 1 else (fav <= tp):
            return abs(tp - entry) / risk, j
        if be and ((fav >= half) if dirn == 1 else (fav <= half)):
            stop = entry
    return np.nan, None


def trade(z, d, sym):
    dirn = z["dir"]
    o, h, l, c, t, a4 = (d[k].values for k in ("open", "high", "low", "close", "time", "atr"))
    a = int(np.searchsorted(t, np.datetime64(z["ready"].tz_convert(None))))
    end = z["ready"] + EXPIRY * SPAN
    inv = z["top"] - dirn * 1.1 * z["rng"]
    t27 = z["top"] + dirn * 0.27 * z["rng"]
    touch = None
    for i in range(a, len(d)):
        if pd.Timestamp(t[i]).tz_localize("UTC") > end:
            return dict(result="verlopen")
        if (h[i] >= t27) if dirn == 1 else (l[i] <= t27):
            return dict(result="weggelopen")
        if (c[i] < inv) if dirn == 1 else (c[i] > inv):
            return dict(result="ongeldig")
        inside = (l[i] <= z["zhi"]) if dirn == 1 else (h[i] >= z["zlo"])
        if inside and touch is None:
            touch = i
        rngc = h[i] - l[i]
        if not inside or rngc <= 0:
            continue
        react = (c[i] > o[i] and (c[i] - l[i]) / rngc >= 0.5) if dirn == 1 else (c[i] < o[i] and (h[i] - c[i]) / rngc >= 0.5)
        if not react:
            continue
        entry = c[i]
        ext = l[touch:i + 1].min() if dirn == 1 else h[touch:i + 1].max()
        stops = dict(f110=inv - dirn * 0.2 * a4[i], wick=ext - dirn * 0.5 * a4[i],
                     f100=z["ext"] - dirn * 0.2 * a4[i])
        tps = dict(t0=z["top"], t27=t27, t27be=t27)
        when = pd.Timestamp(t[i]).tz_localize("UTC").value
        kw = np.searchsorted(z["_wd"], when, side="right") - 1
        res = dict(result="gevuld", entry=entry, fill=str(pd.Timestamp(t[i]).date()), hour=pd.Timestamp(t[i]).hour,
                   depth=(z["top"] - entry) * dirn / z["rng"],
                   retr_days=(pd.Timestamp(t[i]).tz_localize("UTC") - z["top_t"]).days, wait_bars=i - a,
                   wk_last=(1 if z["_wk"][kw] == "H" else -1) * dirn if kw >= 0 else 0,
                   wk_depth=((z["_wp"][kw] - entry) * dirn / abs(z["_wp"][kw] - z["_wp"][kw - 1])
                             if kw >= 1 and (1 if z["_wk"][kw] == "H" else -1) == dirn else np.nan),
                   **week_phase(z, kw, entry, dirn),
                   sr_dist=min((abs(p - entry) for p in z["_levs"]), default=np.nan) / z["atr_d"],
                   body=abs(c[i] - o[i]) / rngc)
        cost = cost_price(sym)
        for sn, sl in stops.items():
            for tn, tp in tps.items():
                col = f"R_{sn}_{tn}"
                if (entry - sl) * dirn <= 0 or (tp - entry) * dirn <= 0:
                    res[col], res[f"x_{sn}_{tn}"] = np.nan, None
                    continue
                r, j = follow(dirn, entry, sl, tp, tn.endswith("be"), h, l, i + 1)
                res[col] = r - cost / abs(entry - sl)
                res[f"x_{sn}_{tn}"] = str(pd.Timestamp(t[j]).date()) if j is not None else None
        return res
    return dict(result="open")


def run(sym, start, end):
    d = load(sym, "H4")
    d["atr"] = atr(d)
    rows = []
    for z in zones(sym, start, end):
        r = trade(z, d, sym)
        rows.append({k: v for k, v in dict(z, **r).items() if not k.startswith("_")})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t9_")
    a = ap.parse_args()
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        print(f"{s}: {len(df)} poten, {int((df.result == 'gevuld').sum()) if len(df) else 0} trades", flush=True)
