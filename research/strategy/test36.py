"""Test 36 (from scratch, video 12 "Forex HTF Analysis"): daily order block in the golden pocket.

    python research/strategy/test36.py SYM [SYM ...] [--tf D1|W1] [--prefix t36_]

1. Legs: zigzag on --tf candles (turn after 2 ATR, leg >= 4 ATR). Fib 1 = body of the start candle, 0 = wick of the
   extreme (body -> wick).
2. Order block: inside the leg a daily fair value gap in the leg's direction (long: low[j+1] > high[j-1], candle j
   bullish); OB = the last opposite candle (bearish for a long) in the 5 candles before j; zone = its body. Only OBs
   whose body reaches into the golden pocket (0.618-0.786); the first price reaches (highest for a long).
3. Entry: limit at the top of the OB body, but no higher than 0.618 (long; short mirrored), first touch after the leg
   is confirmed; without an OB the limit is at 0.618 (has_ob False). Void at a new extreme before the fill, a daily close
   beyond fib 1, or after 40 --tf candles.
4. Stop: 0.1 ATR (--tf) beyond the wick of fib 1. If the fill candle also reaches the stop: -1R.
5. Exits: half at -0.25, stop to the old top, rest at -0.65 (R_m); full at -0.25 (R_t025) or -0.65 (R_t065).
Context: hi_struct (zigzag 2 / 4 of the next higher timeframe: W1 for D1 legs, MN for W1 legs, HH+HL = +1 in the trade
direction), htf_sup (a monthly/weekly S/R level between fib 1 and the entry), m_ma (monthly close vs its 10-month
mean, in the trade direction).
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
import test5  # noqa: E402
from test18 import follow, managed  # noqa: E402

REV, LEG, EXPIRY, OB_BACK, SL_BUF = 2.0, 4.0, 40, 5, 0.1
HIGHER = {"D1": "W1", "W1": "MN"}
DAYS = {"D1": 1, "W1": 5}  # daily candles per --tf candle (for the expiry)


def structure(sym, tf):
    """Zigzag 2 / 4 on tf: (done times, kinds, prices) of the turns, point in time."""
    w = load(sym, tf)
    w["done"] = complete_times(w["time"], tf, load(sym, "D1")["time"] if tf == "MN" else None)
    test5.REV = 2.0
    wt, _ = test5.legs(w)
    return (np.array([w["done"][ci].value for ci, *_ in wt]), np.array([k for *_, k in wt]),
            np.array([p for _, _, p, _ in wt]))


def trend_at(st, ts):
    done, kind, px = st
    k = int(np.searchsorted(done, ts.value, side="right")) - 1
    hs, ls = px[:k + 1][kind[:k + 1] == "H"], px[:k + 1][kind[:k + 1] == "L"]
    if len(hs) < 2 or len(ls) < 2:
        return 0
    return 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)


def run(sym, tf, start, end):
    d = load(sym, "D1")
    d["done"] = complete_times(d["time"], "D1")
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    dt = d.time.values
    g = d if tf == "D1" else load(sym, tf)
    if tf != "D1":
        g["done"] = complete_times(g["time"], tf)
    go, gc = g.open.values, g.close.values
    st = structure(sym, HIGHER[tf])
    lv = Levels(sym)
    test5.REV = REV
    turns, atr = test5.legs(g)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    rows = []
    for k in range(1, len(turns)):
        ci, ti, p_end, kind = turns[k]
        _, si, p_start, _ = turns[k - 1]
        ready = g["done"][ci]
        if ready < t0 or ready >= t1:
            continue
        dirn = 1 if kind == "H" else -1
        A = atr[ci]
        top, w1 = p_end, p_start
        b1 = min(go[si], gc[si]) if dirn == 1 else max(go[si], gc[si])
        rng = (top - b1) * dirn
        if rng < LEG * A:
            continue
        gp_hi, gp_lo = top - dirn * 0.618 * rng, top - dirn * 0.786 * rng  # near / far edge of the golden pocket
        # daily candles of the leg: from the start candle to the end of the extreme candle
        a = int(np.searchsorted(dt, g.time.values[si]))
        b = int(np.searchsorted(dt, g["done"][ti].tz_convert(None).to_datetime64())) if tf != "D1" else ti + 1
        obs = []
        for j in range(max(a + 1, 1), min(b, len(d) - 1)):
            fvg = (l[j + 1] > h[j - 1] and c[j] > o[j]) if dirn == 1 else (h[j + 1] < l[j - 1] and c[j] < o[j])
            if not fvg:
                continue
            for m in range(j - 1, max(j - 1 - OB_BACK, a - 1), -1):
                if (c[m] < o[m]) if dirn == 1 else (c[m] > o[m]):
                    near, far = (max(o[m], c[m]), min(o[m], c[m])) if dirn == 1 else (min(o[m], c[m]), max(o[m], c[m]))
                    # body reaches into the golden pocket: near edge beyond 0.786 and far edge before 0.618
                    if (near - gp_lo) * dirn >= 0 and (far - gp_hi) * dirn <= 0:
                        obs.append((near, far, str(dt[m])[:10]))
                    break
        if obs:
            near, far, ob_t = max(obs, key=lambda x: x[0] * dirn)
            entry = min(near * dirn, gp_hi * dirn) * dirn
        else:
            entry, ob_t = gp_hi, None
        sl = w1 - dirn * SL_BUF * A
        row = dict(sym=sym, dir=dirn, date=str(ready.date()), start_t=str(g.time.values[si])[:10],
                   top_t=str(g.time.values[ti])[:10], b1=b1, w1=w1, top=top, rng=rng, has_ob=bool(obs), ob_t=ob_t,
                   n_ob=len(obs), entry=entry, sl=sl, entry_fib=(top - entry) * dirn / rng)
        f = int(np.searchsorted(dt, ready.tz_convert(None).to_datetime64()))
        last = min(f + EXPIRY * DAYS[tf], len(d))
        res = "verlopen"
        while f < last:
            if ((h[f] if dirn == 1 else l[f]) - top) * dirn > 0 and ((l[f] if dirn == 1 else h[f]) - entry) * dirn > 0:
                res = "weggelopen"
                break
            if ((l[f] if dirn == 1 else h[f]) - entry) * dirn <= 0:
                res = "gevuld"
                break
            if (c[f] - b1) * dirn < 0:
                res = "ongeldig"
                break
            f += 1
        if res == "verlopen" and f >= len(d):
            res = "actief"
        if res != "gevuld":
            rows.append(dict(row, result=res))
            continue
        fill = entry if ((o[f] - entry) * dirn >= 0) else o[f]  # a gap through the limit fills at the open
        risk = abs(fill - sl)
        ts = pd.Timestamp(dt[f]).tz_localize("UTC")
        lo_, hi_ = sorted([b1, fill])
        cost = cost_price(sym, fill)
        row.update(result="gevuld", fill=str(ts.date()), entry=fill, R_cost=cost / risk,
                   hi_struct=trend_at(st, ts) * dirn, htf_sup=any(lo_ <= p <= hi_ for p, _ in lv.at(ts)),
                   m_ma=lv.trend(ts, "MN") * dirn)
        hit_sl = ((l[f] if dirn == 1 else h[f]) - sl) * dirn <= 0
        for name, x in (("t025", 0.25), ("t065", 0.65)):
            r, j = (-1.0, f) if hit_sl else follow(dirn, fill, sl, top + dirn * x * rng, None, h, l, f + 1)
            row[f"R_{name}"] = r - cost / risk
            row[f"x_{name}"] = str(dt[j])[:10] if j is not None else None
        row["R_m"] = (-1.0 if hit_sl else managed(dirn, fill, sl, top, rng, 0.25, "top", 0.65, h, l, f + 1)) - cost / risk
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t36_")
    a = ap.parse_args()
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s}: {len(df)} poten, {n} trades, {int(df.get('has_ob', pd.Series(dtype=bool)).sum())} met OB", flush=True)
