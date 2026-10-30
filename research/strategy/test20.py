"""Test 20: only the big legs (the trader's GBPNZD long Aug-Sep 2026), with the entry timing of test 19.

    python research/strategy/test20.py SYM [SYM ...] --start 2005-01-01 --end 2025-12-31 [--prefix t20_]

1. Legs: daily zigzag (test5.legs) with a turn confirmed after REV = 3 daily ATR back and a leg of at least LEG = 6
   daily ATR; fib 1 = the leg's start (wick), 0 = its end (wick). Known from the candle that confirms the turn.
2. Entry: the first daily rejection candle in the zone (long: low at or below the 0.618 level, close above its open
   in the upper 40% of its range, the close between the 0.5 and 0.786 levels), at its close. Before the first touch a
   new high moves 0 (and the zone) with it; after a touch a new high ends the setup. Void: a close beyond fib 1, or
   EXPIRY daily candles after the last re-anchor.
   (--band sets that range; --rev / --leg the zigzag; test 21 grid.)
3. Stop: beyond fib 1 by 0.1 ATR (R_*) and by 0.5 ATR (R_w_*). Exits: -0.2 (R_t020, decisive), -0.27, -0.65, and half at -0.2 with the stop to
   the old high and the rest to -1 (R_m_top_1). Costs per symbol. touch_n = earlier candles in the zone.
4. Context (the trader: "boven weekly & monthly S/R, weekly market structure bullish"): wk_struct = the weekly
   zigzag (2 weekly ATR turns) made higher highs and higher lows (lower for a short) - last two confirmed turns of
   each kind, known at the entry; htf_sup = a monthly/weekly S/R level between fib 1 and the entry (price above it
   for a long, below it for a short).
6. --tf W1 (test 20w): the same on weekly candles (zigzag in weekly ATR, expiry in weeks); the structure filter then
   uses the monthly zigzag (higher highs and lows on the monthly), S/R as before.
7. --fib body (test 30, video 12 "take the body instead of the wick"): fib 1 = the body extreme of the leg-start
   candle, 0 = the body extreme of the leg-end candle; a new high moves 0 only when a body goes beyond it. Stop stays
   beyond the body fib 1 by 0.1 ATR.
   --fib bodywick (test 30b, the trader: "body to wick, always"): fib 1 = body of the leg-start candle, 0 = wick of
   the leg end; the stop stays beyond the WICK of the leg start by 0.1 ATR.
   cont (test 31): the leg ends beyond the previous turn on the same side (higher high / lower low) = continuation.
5. A setup still waiting when the data ends is "actief" (with its zone, stop, -0.2 and the context now): for the
   scanner (scan.py).
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

REV, LEG, EXPIRY = 3.0, 6.0, 40
FIB = "wick"  # --fib body (test 30, video 12): fib 1 and 0 on the candle bodies instead of the wicks
BAND = (0.5, 0.786)  # where the close of the rejection candle must sit (fib)
SL_BUF = (0.1, 0.5)  # stop beyond fib 1 by these ATR multiples; the first is the main one (R_*), the second R_w_*
TPS = {"t020": 0.2, "t027": 0.27, "t065": 0.65}


TF = "D1"  # --tf W1 (test 20w): legs on weekly candles, context from the monthly structure
HIGHER = {"D1": "W1", "W1": "MN"}


def run(sym, start, end):
    d = load(sym, TF)
    d["done"] = complete_times(d["time"], TF)
    o, h, l, c, t = (d[k].values for k in ("open", "high", "low", "close", "time"))
    w = load(sym, HIGHER[TF])
    w["done"] = complete_times(w["time"], HIGHER[TF], load(sym, "D1")["time"] if TF == "W1" else None)
    test5.REV, test5.LEG = 2.0, 4.0
    wt, _ = test5.legs(w)
    w_done = np.array([w["done"][ci].value for ci, *_ in wt])
    w_kind = np.array([kk for *_, kk in wt])
    w_px = np.array([p for _, _, p, _ in wt])
    lv = Levels(sym)
    test5.REV, test5.LEG = REV, LEG
    turns, atr = test5.legs(d)
    cost = cost_price(sym)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    rows = []
    for k in range(1, len(turns)):
        ci, ti, p_end, kind = turns[k]
        _, si, p_start, _ = turns[k - 1]
        ready = d["done"][ci]
        if ready < t0 or ready >= t1:
            continue
        dirn = 1 if kind == "H" else -1
        top, b1 = p_end, p_start
        w1 = p_start  # wick of the leg start: the stop stays beyond it
        if FIB in ("body", "bodywick"):
            b1 = min(o[si], c[si]) if kind == "H" else max(o[si], c[si])
        if FIB == "body":
            top = max(o[ti], c[ti]) if kind == "H" else min(o[ti], c[ti])
        rng = (top - b1) * dirn
        if rng < LEG * atr[ci]:
            continue
        ext, opp = (h, l) if dirn == 1 else (l, h)
        # continuation (test 31): the leg's end beyond the previous turn on the same side (higher high for a long)
        cont = k >= 2 and (p_end - turns[k - 2][2]) * (1 if kind == "H" else -1) > 0
        row = dict(sym=sym, dir=dirn, date=str(ready.date()), start_t=str(t[si])[:10], top_t=str(t[ti])[:10], cont=cont,
                   b1=b1, top=top, rng=rng, rng_atr=rng / atr[ci])
        res, f, deadline, touched, touch_n = "verlopen", ci, ci + 1 + EXPIRY, False, 0
        entry = None
        while f + 1 < min(deadline, len(d)):
            f += 1
            if (c[f] - b1) * dirn < 0:
                res = "ongeldig"
                break
            if ((ext[f] if FIB != "body" else (max(o[f], c[f]) if dirn == 1 else min(o[f], c[f]))) - top) * dirn > 0:
                if touched:
                    res = "weggelopen"
                    break
                top = ext[f] if FIB != "body" else (max(o[f], c[f]) if dirn == 1 else min(o[f], c[f]))
                rng = (top - b1) * dirn
                row.update(top=top, rng=rng, top_t=str(t[f])[:10], reanchored=True)
                deadline = f + 1 + EXPIRY
                continue
            near = top - dirn * 0.618 * rng
            if (opp[f] - near) * dirn <= 0:
                span = h[f] - l[f]
                rej = span > 0 and ((c[f] > o[f] and c[f] - l[f] >= 0.6 * span) if dirn == 1
                                    else (c[f] < o[f] and h[f] - c[f] >= 0.6 * span))
                cf = (top - c[f]) * dirn / rng
                if rej and BAND[0] <= cf <= BAND[1]:
                    res, entry = "gevuld", c[f]
                    break
                touched = True
                touch_n += 1
        def context(i, price):
            """Weekly structure and monthly/weekly S/R between fib 1 and `price`, as known at candle i."""
            kw = int(np.searchsorted(w_done, pd.Timestamp(t[i]).tz_localize("UTC").value, side="right")) - 1
            hs, ls = w_px[:kw + 1][w_kind[:kw + 1] == "H"], w_px[:kw + 1][w_kind[:kw + 1] == "L"]
            T = 0
            if len(hs) >= 2 and len(ls) >= 2:
                T = 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)
            levs = [p for p, _ in lv.at(pd.Timestamp(t[i]).tz_localize("UTC"))]
            lo_, hi_ = sorted([b1, price])
            ts = pd.Timestamp(t[i]).tz_localize("UTC")
            return dict(wk_struct=T * dirn, htf_sup=any(lo_ <= p <= hi_ for p in levs),
                        m_ma=lv.trend(ts, "MN") * dirn)  # monthly close vs its 10-month mean, in the trade direction

        if res == "verlopen" and f + 1 >= len(d) and f + 1 < deadline:
            # the data ended while the setup was still waiting for its rejection candle: live
            res = "actief"
            row.update(zone_0618=top - dirn * 0.618 * rng, zone_0786=top - dirn * 0.786 * rng,
                       sl=(w1 if FIB == "bodywick" else b1) - dirn * SL_BUF[0] * atr[f], tp_020=top + dirn * 0.2 * rng, touch_n=touch_n,
                       nog_candles=deadline - f - 1, **context(f, top - dirn * 0.618 * rng))
        if res != "gevuld":
            rows.append(dict(row, result=res))
            continue
        row.update(**context(f, entry))
        row.update(result="gevuld", fill=str(t[f])[:10], entry=entry, touch_n=touch_n)
        for pre, buf in zip(("R_", "R_w_"), SL_BUF):
            sl = (w1 if FIB == "bodywick" else b1) - dirn * buf * atr[f]
            risk = abs(entry - sl)
            if pre == "R_":
                row.update(sl=sl, entry_fib=(top - entry) * dirn / rng, R_cost=cost / risk)
            for name, x in TPS.items():
                r, j = follow(dirn, entry, sl, top + dirn * x * rng, None, h, l, f + 1)
                row[f"{pre}{name}"] = r - cost / risk
                if pre == "R_":
                    row[f"x_{name}"] = str(t[j])[:10] if j is not None else None
            row[f"{pre}m_top_1"] = managed(dirn, entry, sl, top, rng, 0.2, "top", 1.0, h, l, f + 1) - cost / risk
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t20_")
    ap.add_argument("--rev", type=float, default=REV)
    ap.add_argument("--leg", type=float, default=LEG)
    ap.add_argument("--band", default=f"{BAND[0]},{BAND[1]}")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--fib", default="wick", choices=["wick", "body", "bodywick"])
    a = ap.parse_args()
    REV, LEG, BAND, TF, FIB = a.rev, a.leg, tuple(float(x) for x in a.band.split(",")), a.tf, a.fib
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        print(f"{s}: {len(df)} poten, {int((df.result == 'gevuld').sum()) if len(df) else 0} trades", flush=True)
