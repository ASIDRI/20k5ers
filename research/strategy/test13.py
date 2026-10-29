"""Test 13: the trader's break-and-retest setups with a wide net, for taking rules out and finding what separates them.

    python research/strategy/test13.py SYM [SYM ...] --tf D1 --start 2005-01-01 --end 2025-12-31 [--prefix t13d_]

Same engine as test 11 (top = small swing, limit at 0.65, stop beyond the wick of the leg start, re-anchor on a new
high before the fill, void on a close beyond 1 or after 40 candles), but nothing is required beyond a leg of at least
1.5 ATR: every rule of test 11 becomes a column, so each can be switched off or on afterwards.
Leg start: the extreme after the most recent intact swing S that the top broke (broke = True); when the top broke
nothing, the last small swing before the top (broke = False).
Columns known when the order is placed: broke, s_fib (where S sits in the fib, wick and body: s_fib_w, s_fib_b),
pocket (S in 0.5-0.786), htf (a monthly/weekly S/R level in 0.5-0.786), rng_atr, leg_bars, speed (rng_atr per
candle), wk_trend / wk_phase / wk_ok (video 9, from the weekly zigzag), mn / wk (monthly / weekly trend in the trade
direction), ma (close vs its 50-candle mean in the trade direction). Known later: reanchored, fill_bars.
Exits: stop w (wick of the start - 0.1 ATR) or x (fib 1 - 1 ATR, wider) x targets -0.27 / -0.618 / -1 / -1.618;
-1 also with the stop to entry at the old high: R_<stop>_<target>[_be], net of costs. Also -0.2 and -0.65 (NZDCAD trades).
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
from test9 import week_phase  # noqa: E402

K, KS, ENTRY, EXPIRY, LOOKBACK = 2, 1, 0.65, 40, 120  # KS: swing size for the leg start
TPS = {"t020": 0.2, "t027": 0.27, "t065": 0.65, "t0618": 0.618, "t1": 1.0, "t1618": 1.618}


def swings(h, l, k=K):
    hi, lo = [], []
    for i in range(k, len(h) - k):
        if h[i] == h[i - k:i + k + 1].max():
            hi.append(i)
        if l[i] == l[i - k:i + k + 1].min():
            lo.append(i)
    return hi, lo


def follow(dirn, entry, sl, tp, be_px, h, l, start):
    risk, stop = abs(entry - sl), sl
    for j in range(start, len(h)):
        adv, fav = (l[j], h[j]) if dirn == 1 else (h[j], l[j])
        if (adv <= stop) if dirn == 1 else (adv >= stop):
            return (stop - entry) * dirn / risk, j
        if (fav >= tp) if dirn == 1 else (fav <= tp):
            return abs(tp - entry) / risk, j
        if be_px is not None and ((fav >= be_px) if dirn == 1 else (fav <= be_px)):
            stop = entry
    return np.nan, None


def run(sym, tf, start, end):
    d = load(sym, tf)
    d["done"] = complete_times(d["time"], tf)
    o, h, l, c, t = (d[k].values for k in ("open", "high", "low", "close", "time"))
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().bfill().values
    ma = pd.Series(c).rolling(50).mean().values
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    wt, watr = legs(w)
    wz = dict(_wk=np.array([k for *_, k in wt]), _wp=np.array([p for _, _, p, _ in wt]),
              _wa=np.array([watr[ci] for ci, *_ in wt]))
    w_done = np.array([w["done"][ci].value for ci, *_ in wt])
    lv = Levels(sym)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    hi, lo = swings(h, l)
    hi1, lo1 = swings(h, l, KS)
    cost = cost_price(sym)
    rows = []
    for dirn, tops, struct, bottoms in ((1, hi1, hi, lo1), (-1, lo1, lo, hi1)):
        ext = h if dirn == 1 else l
        opp = l if dirn == 1 else h
        busy = {}
        for i in tops:
            ready_i = i + KS
            if ready_i + 1 >= len(d):
                continue
            ready = d["done"][ready_i]
            if ready < t0 or ready >= t1:
                continue
            top = ext[i]
            j = s = None
            for s_ in sorted((x for x in struct if i - LOOKBACK <= x < i - 1), reverse=True):
                if (top - ext[s_]) * dirn <= 0:
                    continue
                seg = opp[s_ + 1:i]
                jj = s_ + 1 + int(np.argmin(seg) if dirn == 1 else np.argmax(seg))
                if jj >= i:
                    continue
                lvl_b = max(o[s_], c[s_]) if dirn == 1 else min(o[s_], c[s_])
                if jj > s_ + 1 and ((c[s_ + 1:jj] - lvl_b) * dirn > 0).any():
                    continue
                b1_ = min(o[jj], c[jj]) if dirn == 1 else max(o[jj], c[jj])
                if (top - b1_) * dirn <= 0 or (ext[s_] - b1_) * dirn <= 0:
                    continue
                j, s = jj, s_
                break
            if j is None:
                prior = [x for x in bottoms if x < i]
                if not prior:
                    continue
                j = prior[-1]
            if busy.get(j, -1) >= i:
                continue
            b1 = min(o[j], c[j]) if dirn == 1 else max(o[j], c[j])
            rng = (top - b1) * dirn
            if rng < 1.5 * atr[i]:
                continue
            fib = lambda x: (top - x) * dirn / rng  # noqa: E731
            band = sorted([top - dirn * 0.5 * rng, top - dirn * 0.786 * rng])
            s_w = fib(ext[s]) if s is not None else np.nan
            s_b = fib(max(o[s], c[s]) if dirn == 1 else min(o[s], c[s])) if s is not None else np.nan
            levs = [p for p, _ in lv.at(ready)]
            entry = top - dirn * ENTRY * rng
            stops = dict(w=opp[j] - dirn * 0.1 * atr[i], x=b1 - dirn * 1.0 * atr[i])
            if any((entry - x) * dirn <= 0 for x in stops.values()):
                continue
            kw = int(np.searchsorted(w_done, ready.value, side="right")) - 1
            row = dict(sym=sym, tf=tf, dir=dirn, date=str(ready.date()), start_t=str(t[j])[:10], top_t=str(t[i])[:10],
                       b1=b1, top=top, rng=rng, entry=entry, sl=stops["w"], broke=s is not None,
                       s_fib_w=s_w, s_fib_b=s_b, pocket=bool(0.5 <= s_w <= 0.786 or 0.5 <= s_b <= 0.786),
                       htf=any(band[0] <= p <= band[1] for p in levs), rng_atr=rng / atr[i], leg_bars=i - j,
                       speed=rng / atr[i] / max(i - j, 1), mn=lv.trend(ready, "MN") * dirn,
                       wk=lv.trend(ready, "W1") * dirn,
                       ma=int(np.sign(c[ready_i] - ma[ready_i]) * dirn) if not np.isnan(ma[ready_i]) else 0,
                       reanchored=False, **(week_phase(wz, kw, entry, dirn) if kw >= 0 else {}))
            if ((opp[i + 1:ready_i + 1] - entry) * dirn <= 0).any():
                rows.append(dict(row, result="te laat"))
                continue
            res, f = "verlopen", ready_i
            for f in range(ready_i + 1, min(ready_i + 1 + EXPIRY, len(d))):
                if (opp[f] - entry) * dirn <= 0:
                    res = "gevuld"
                    break
                if (c[f] - b1) * dirn < 0:
                    res = "ongeldig"
                    break
                if (ext[f] - top) * dirn > 0:
                    top = ext[f]
                    rng = (top - b1) * dirn
                    entry = top - dirn * ENTRY * rng
                    row.update(top=top, rng=rng, entry=entry, top_t=str(t[f])[:10], reanchored=True)
            busy[j] = f
            if res != "gevuld":
                rows.append(dict(row, result=res))
                continue
            row.update(result="gevuld", fill=str(t[f])[:10], fill_bars=f - ready_i)
            for sn, sl in stops.items():
                risk = abs(entry - sl)
                row[f"rr1_{sn}"] = abs(top + dirn * rng - entry) / risk
                hit_now = (opp[f] - sl) * dirn <= 0
                for name, x in TPS.items():
                    tp = top + dirn * x * rng
                    for be, suffix in ((None, ""), (top, "_be")):
                        if suffix and name != "t1":
                            continue
                        r = -1.0 if hit_now else follow(dirn, entry, sl, tp, be, h, l, f + 1)[0]
                        row[f"R_{sn}_{name}{suffix}"] = r - cost / risk
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default=None)
    a = ap.parse_args()
    prefix = a.prefix or f"t13{a.tf[0].lower()}_"
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{prefix}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s}: {len(df)} setups, {n} trades", flush=True)
