"""Test 24: only enter after a confirmed reaction in the golden pocket / 0.786 (the trader, 2026-10-30).

    python research/strategy/test24.py SYM [SYM ...] --start 2005-01-01 --end 2025-12-31 [--prefix t24_]

"Alleen een positie openen nadat er reactie is in goldenpocket of 0-786 die wijst op een bounce en continuation.
Soms valt de prijs ook onder de 1/1, dan is het belangrijk dat het daar liquiditeit heeft genomen van een eerdere low.
En dan opnieuw kijken op de 4u chart naar confirmation dat het toch nog een bullish N wordt."

1. Daily legs as test 20 (zigzag: turn after 3 daily ATR, leg >= 6 ATR; fib 1 = start, 0 = end, wicks).
2. Watch on 4-hour candles from the candle after the daily confirmation. Before the zone is touched, a new high moves
   0 with it. Zone touched = a 4-hour low at or below the 0.618 level.
3. Below fib 1: allowed only when price takes the liquidity of an earlier daily low - the highest daily swing low
   (2 candles each side) below fib 1 in the 120 days before the leg start (`liq`); the setup is void if price goes
   more than 1 daily ATR below `liq`, or below fib 1 - 0.1 ATR when there is no such low. swept = price went below
   `liq`.
4. Confirmation (the start of the N's second leg): after the lowest 4-hour low since the touch (L*), a 4-hour candle
   closes above the last confirmed 4-hour swing high (2 candles each side) that formed before L* and after the touch
   minus 10 candles. Entry at that close; only if the reward to -0.2 is at least 1.5 times the risk. When below fib 1
   without a sweep yet, no entry.
5. Stop: beneath L* by 0.1 daily ATR. Exits: -0.2 (R_t020, decisive), -0.27, -0.65, and half at -0.2 with the stop to
   the old high, rest to -1 (R_m_top_1). Void after a new high once touched, or 40 trading days after the last
   re-anchor.
Features at the entry (for "when does the confirmation work"): swept, l_fib (depth of L* in the fib), conf_bars
(4-hour candles from the touch to the confirmation), entry_fib, rr, and the context of test 20 (wk_struct, htf_sup,
m_ma).
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

REV, LEG, EXPIRY_D, K4, MIN_RR = 3.0, 6.0, 40, 2, 1.5
TPS = {"t020": 0.2, "t027": 0.27, "t065": 0.65}


def run(sym, start, end):
    d = load(sym, "D1")
    d["done"] = complete_times(d["time"], "D1")
    dh, dl = d.high.values, d.low.values
    h4 = load(sym, "H4")
    t4 = h4.time.values
    o4, hh, ll, c4 = (h4[k].values for k in ("open", "high", "low", "close"))
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    test5.REV, test5.LEG = 2.0, 4.0
    wt, _ = test5.legs(w)
    w_done = np.array([w["done"][ci].value for ci, *_ in wt])
    w_kind = np.array([kk for *_, kk in wt])
    w_px = np.array([p for _, _, p, _ in wt])
    lv = Levels(sym)
    test5.REV, test5.LEG = REV, LEG
    turns, atr = test5.legs(d)
    sw_lo = [i for i in range(2, len(d) - 2) if dl[i] == dl[i - 2:i + 3].min()]
    sw_hi = [i for i in range(2, len(d) - 2) if dh[i] == dh[i - 2:i + 3].max()]
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
        rng = (top - b1) * dirn
        A = atr[ci]
        if rng < LEG * A:
            continue
        # liquidity: the nearest earlier daily swing low below fib 1 (high for a short), known before the leg started
        cand = [dl[i] for i in sw_lo if si - 120 <= i < si - 2 and dl[i] < b1] if dirn == 1 else \
               [dh[i] for i in sw_hi if si - 120 <= i < si - 2 and dh[i] > b1]
        liq = (max(cand) if dirn == 1 else min(cand)) if cand else None
        floor = (liq - dirn * A) if liq is not None else (b1 - dirn * 0.1 * A)
        hi, lo = (hh, ll) if dirn == 1 else (-ll, -hh)  # mirrored so the long logic serves both
        cm = c4 if dirn == 1 else -c4
        topm, b1m, floorm = top * dirn, b1 * dirn, floor * dirn
        liqm = liq * dirn if liq is not None else None
        row = dict(sym=sym, dir=dirn, date=str(ready.date()), start_t=str(d.time[si])[:10], top_t=str(d.time[ti])[:10],
                   b1=b1, top=top, rng=rng, liq=liq)
        a = int(np.searchsorted(t4, np.datetime64(ready.tz_convert(None))))
        deadline = ready + pd.Timedelta(days=EXPIRY_D * 7 / 5)
        touch, low_i, swept, res, swings = None, None, False, "verlopen", []
        f = a - 1
        while f + 1 < len(h4):
            f += 1
            if pd.Timestamp(t4[f]).tz_localize("UTC") > deadline:
                break
            if lo[f] <= floorm:
                res = "ongeldig"
                break
            if hi[f] > topm:
                if touch is not None:
                    res = "weggelopen"
                    break
                topm = hi[f]
                rng = topm - b1m
                deadline = pd.Timestamp(t4[f]).tz_localize("UTC") + pd.Timedelta(days=EXPIRY_D * 7 / 5)
                row.update(top=topm * dirn, rng=rng, reanchored=True)
                continue
            near = topm - 0.618 * rng
            if touch is None:
                if lo[f] <= near:
                    touch, low_i = f, f
                else:
                    continue
            if lo[f] < lo[low_i]:
                low_i = f
            if liqm is not None and lo[f] < liqm:
                swept = True
            s = f - K4  # a 4-hour swing high at s is known now
            if s >= touch - 10 and hi[s] == hi[s - K4:s + K4 + 1].max():
                swings.append(s)
            below1 = lo[low_i] < b1m
            if below1 and not swept:
                continue
            prev = [x for x in swings if x < low_i]
            if not prev or cm[f] <= hi[prev[-1]]:
                continue
            entry_m = cm[f]
            sl_m = lo[low_i] - 0.1 * A
            tp_m = topm + 0.2 * rng
            risk = entry_m - sl_m
            if risk <= 0 or (tp_m - entry_m) / risk < MIN_RR:
                continue
            res = "gevuld"
            break
        if res != "gevuld":
            rows.append(dict(row, result=res))
            continue
        entry, sl, top = entry_m * dirn, sl_m * dirn, topm * dirn
        risk = abs(entry - sl)
        i_d = int(np.searchsorted(d.time.values, t4[f], side="right")) - 1
        kw = int(np.searchsorted(w_done, pd.Timestamp(t4[f]).tz_localize("UTC").value, side="right")) - 1
        hs, ls = w_px[:kw + 1][w_kind[:kw + 1] == "H"], w_px[:kw + 1][w_kind[:kw + 1] == "L"]
        T = 0
        if len(hs) >= 2 and len(ls) >= 2:
            T = 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)
        ts = pd.Timestamp(t4[f]).tz_localize("UTC")
        levs = [p for p, _ in lv.at(ts)]
        lo_, hi_ = sorted([b1, entry])
        row.update(result="gevuld", fill=str(ts.date()), entry=entry, sl=sl, swept=swept,
                   l_fib=(topm - lo[low_i]) / rng, conf_bars=f - touch, entry_fib=(topm - entry_m) / rng,
                   rr=(topm + 0.2 * rng - entry_m) / risk, R_cost=cost / risk,
                   wk_struct=T * dirn, htf_sup=any(lo_ <= p <= hi_ for p in levs), m_ma=lv.trend(ts, "MN") * dirn)
        for name, x in TPS.items():
            r, j = follow(dirn, entry, sl, top + dirn * x * rng, None, hh, ll, f + 1)
            row[f"R_{name}"] = r - cost / risk
            row[f"x_{name}"] = str(t4[j])[:10] if j is not None else None
        row["R_m_top_1"] = managed(dirn, entry, sl, top, rng, 0.2, "top", 1.0, hh, ll, f + 1) - cost / risk
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t24_")
    a = ap.parse_args()
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        print(f"{s}: {len(df)} poten, {int((df.result == 'gevuld').sum()) if len(df) else 0} trades", flush=True)
