"""Test 11: break and retest at the golden pocket - the trader's own examples (EURUSD D1/W1, EURAUD D1, GBPAUD D1).

    python research/strategy/test11.py SYM [SYM ...] --tf D1 --start 2005-01-01 --end 2025-12-31 [--prefix t11d_]

On one timeframe (D1 or W1), point in time:
1. Swings: fractal highs/lows (K candles each side), known K candles after the swing.
2. Break leg (long; mirror for short): a swing high H (KS candles each side, so known one candle later) that took
   out a swing high S (K candles each side, within LOOKBACK). The leg starts at the lowest low between S and H, and
   S must not have been taken out before that low. Fib 1 = the BODY low of the leg-start candle, 0 = the WICK high
   of H; S counts as intact until a candle closes beyond its body. The broken level S (body top or wick) must sit in the pocket between the 0.5 and 0.786 levels - the retest
   of the broken level. The most recent S that qualifies is used.
   Tag 'htf': a monthly/weekly S/R level also lies between 0.5 and 0.786.
3. Order: a limit buy at the 0.65 level from the candle after H is confirmed. Stop beneath the WICK low of the
   leg-start candle minus 0.1 ATR. A new high above H before the fill moves the fib (0) and the order with it
   (as the trader redraws). Cancelled when a candle closes below fib 1 or after EXPIRY candles (with --reset-expiry
   counted from the last re-anchor, test 17). A candle that fills and touches the stop counts as a loss.
4. Exits per trade: targets -0.2 / -0.27 / -0.65 / -0.618 / -1 / -1.618 (R_t027 ... R_t1618), each also with the stop to entry
   once price trades at the old high (0) (R_..._be). A candle touching stop and target counts as the stop.
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

K, KS, ENTRY, EXPIRY, LOOKBACK = 2, 1, 0.65, 40, 120  # KS: swing size for the leg start
TPS = {"t020": 0.2, "t027": 0.27, "t065": 0.65, "t0618": 0.618, "t1": 1.0, "t1618": 1.618}
RESET_EXPIRY = False  # --reset-expiry (test 17): a re-anchored order gets EXPIRY candles again


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
    lv = Levels(sym)
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    hi, lo = swings(h, l)
    hi1, lo1 = swings(h, l, KS)
    cost = cost_price(sym)
    rows = []
    for dirn, tops, struct, bottoms in ((1, hi1, hi, lo1), (-1, lo1, lo, hi1)):
        ext = h if dirn == 1 else l  # the side of the leg end
        opp = l if dirn == 1 else h
        busy = {}  # leg start -> last candle its order was alive (a re-anchored order is not opened again)
        for i in tops:
            ready_i = i + KS
            if ready_i + 1 >= len(d):
                continue
            ready = d["done"][ready_i]
            if ready < t0 or ready >= t1:
                continue
            top = ext[i]
            # leg start: the extreme after the most recent structure point S that this move broke (long: the lowest
            # low between S and the top), S never taken out before that low, and S in the 0.5-0.786 pocket
            j = broken = None
            for s_ in sorted((x for x in struct if i - LOOKBACK <= x < i - 1), reverse=True):
                lvl_w = ext[s_]
                if (top - lvl_w) * dirn <= 0:
                    continue
                seg = opp[s_ + 1:i]
                jj = s_ + 1 + int(np.argmin(seg) if dirn == 1 else np.argmax(seg))
                if jj <= s_ + 1 - 1 or jj >= i:
                    continue
                lvl_b = max(o[s_], c[s_]) if dirn == 1 else min(o[s_], c[s_])
                if jj > s_ + 1 and ((c[s_ + 1:jj] - lvl_b) * dirn > 0).any():
                    continue  # S already broken (a close beyond its body) before the leg started
                b1_ = min(o[jj], c[jj]) if dirn == 1 else max(o[jj], c[jj])
                rng_ = (top - b1_) * dirn
                if rng_ <= 0 or (lvl_w - b1_) * dirn <= 0:
                    continue
                band_ = sorted([top - dirn * 0.5 * rng_, top - dirn * 0.786 * rng_])
                if any(band_[0] <= x <= band_[1] for x in (lvl_w, lvl_b)):
                    j, broken, band = jj, [s_], band_
                    break
            if j is None or busy.get(j, -1) >= i:
                continue
            b1 = min(o[j], c[j]) if dirn == 1 else max(o[j], c[j])
            rng = (top - b1) * dirn
            if rng < 1.5 * atr[i]:
                continue
            levs = [p for p, _ in lv.at(ready)]
            entry = top - dirn * ENTRY * rng
            sl = opp[j] - dirn * 0.1 * atr[i]
            if (entry - sl) * dirn <= 0:
                continue
            row = dict(sym=sym, tf=tf, dir=dirn, date=str(ready.date()), start_t=str(t[j])[:10], top_t=str(t[i])[:10],
                       b1=b1, top=top, rng=rng, rng_atr=rng / atr[i], entry=entry, sl=sl,
                       htf=any(band[0] <= p <= band[1] for p in levs), n_broken=len(broken))
            # pullback already at the entry before the top was known (the candle after it): no order
            if ((opp[i + 1:ready_i + 1] - entry) * dirn <= 0).any():
                rows.append(dict(row, result="te laat"))
                continue
            res, f, deadline = "verlopen", ready_i, ready_i + 1 + EXPIRY
            while f + 1 < min(deadline, len(d)):
                f += 1
                if (opp[f] - entry) * dirn <= 0:
                    res = "gevuld"
                    break
                if (c[f] - b1) * dirn < 0:
                    res = "ongeldig"
                    break
                if (ext[f] - top) * dirn > 0:  # a new high before the fill: the fib moves to it, the order follows
                    top = ext[f]
                    rng = (top - b1) * dirn
                    entry = top - dirn * ENTRY * rng
                    row.update(top=top, rng=rng, entry=entry, top_t=str(t[f])[:10], reanchored=True)
                    if RESET_EXPIRY:
                        deadline = f + 1 + EXPIRY
            busy[j] = f
            if res != "gevuld":
                rows.append(dict(row, result=res))
                continue
            risk = abs(entry - sl)
            row.update(result="gevuld", fill=str(t[f])[:10], R_cost=cost / risk, rr1=abs(top + dirn * rng - entry) / risk)
            if (opp[f] - sl) * dirn <= 0:  # the fill candle also reached the stop
                for name in TPS:
                    row[f"R_{name}"] = row[f"R_{name}_be"] = -1.0 - cost / risk
                row["exit"] = row["fill"]
                row.update({f"x_{name}": row["fill"] for name in TPS})
                rows.append(row)
                continue
            for name, x in TPS.items():
                tp = top + dirn * x * rng
                for be, suffix in ((None, ""), (top, "_be")):
                    r, k = follow(dirn, entry, sl, tp, be, h, l, f + 1)
                    row[f"R_{name}{suffix}"] = r - cost / risk
                    if not suffix:
                        row[f"x_{name}"] = str(t[k])[:10] if k is not None else None
                        if name == "t1":
                            row["exit"] = row["x_t1"]
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--reset-expiry", action="store_true")
    a = ap.parse_args()
    RESET_EXPIRY = a.reset_expiry
    prefix = a.prefix or f"t11{a.tf[0].lower()}_"
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{prefix}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s}: {len(df)} setups, {n} trades", flush=True)
