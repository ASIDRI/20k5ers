"""Test 23 columns (R_struct, x_struct, tp_struct, sl_major, rr_struct, wk_struct, htf_sup): the trader's small-leg
trade (GBPNZD March 2026) - stop beneath the major low (20 candles), target the next intact swing high above the leg.

Test 19: entry timing (the trader, 2026-10-29: "timing wanneer je erin gaat"). Same legs and exits as test 18, but
no blind limit order: wait for a DAILY rejection candle in the zone (long: low at or below the 0.618 level, close
above its open, close in the upper 40% of its range, and the close itself in the zone between the 0.5 and 0.786
levels), enter at its close. Stop as test 18 (beyond the wick of the
leg start); R_tight_t020 = stop beneath the rejection candle - 0.1 ATR instead. touch_n = earlier candles that
touched the zone (0 = first touch); at_lvl = the rejection low within 0.3 ATR of the broken level S or a
monthly/weekly level. Re-anchoring on a new high only before the first touch; after a touch a new high ends it.

Test 18: test 11 (with --reset-expiry behaviour) plus the trader's trade management, for every trade:
  half off at TP1 (-0.2 or -0.27), then the stop into profit (to the entry, or to the old high = fib 0), the rest to
  -0.65 / -1 / -1.618 or trailed under each new swing (2 candles each side): R_m_<tp1>_<lock>_<tp2>;
  and the whole position to the first monthly/weekly S/R level beyond -0.2 (R_lvl; -1 when none).

Based on test 11: break and retest at the golden pocket - the trader's own examples (EURUSD D1/W1, EURAUD D1, GBPAUD D1).

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
import test5  # noqa: E402

K, KS, ENTRY, EXPIRY, LOOKBACK = 2, 1, 0.65, 40, 120  # KS: swing size for the leg start
TPS = {"t020": 0.2, "t027": 0.27, "t065": 0.65, "t0618": 0.618, "t1": 1.0, "t1618": 1.618}
RESET_EXPIRY = True  # test 18: a re-anchored order gets EXPIRY candles again


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


def managed(dirn, entry, sl, top, rng, tp1x, lock, tp2x, h, l, start):
    """Half off at TP1, stop to `lock` (entry or top), rest to TP2 (fib extension) or trailed under swings."""
    risk = abs(entry - sl)
    tp1 = top + dirn * tp1x * rng
    tp2 = None if tp2x == "trail" else top + dirn * tp2x * rng
    stop, half = sl, None
    for j in range(start, len(h)):
        adv, fav = (l[j], h[j]) if dirn == 1 else (h[j], l[j])
        if (adv <= stop) if dirn == 1 else (adv >= stop):
            rest = (stop - entry) * dirn / risk
            return rest if half is None else half + 0.5 * rest
        if half is None and ((fav >= tp1) if dirn == 1 else (fav <= tp1)):
            half = 0.5 * abs(tp1 - entry) / risk
            stop = entry if lock == "entry" else top
        if half is not None:
            if tp2 is not None and ((fav >= tp2) if dirn == 1 else (fav <= tp2)):
                return half + 0.5 * abs(tp2 - entry) / risk
            if tp2 is None and j >= 4:
                sw = l[j - 2] if dirn == 1 else h[j - 2]
                win = l[j - 4:j + 1] if dirn == 1 else h[j - 4:j + 1]
                if (sw == win.min()) if dirn == 1 else (sw == win.max()):
                    stop = max(stop, sw) if dirn == 1 else min(stop, sw)
    return np.nan


def run(sym, tf, start, end):
    d = load(sym, tf)
    d["done"] = complete_times(d["time"], tf)
    o, h, l, c, t = (d[k].values for k in ("open", "high", "low", "close", "time"))
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().bfill().values
    lv = Levels(sym)
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    test5.REV, test5.LEG = 2.0, 4.0
    wt, _ = test5.legs(w)
    w_done = np.array([w["done"][ci].value for ci, *_ in wt])
    w_kind = np.array([kk for *_, kk in wt])
    w_px = np.array([p for _, _, p, _ in wt])
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
            res, f, deadline, touch_n, touched = "verlopen", ready_i, ready_i + 1 + EXPIRY, 0, False
            near = top - dirn * 0.618 * rng
            s_lvl = ext[broken[0]]
            while f + 1 < min(deadline, len(d)):
                f += 1
                if (c[f] - b1) * dirn < 0:
                    res = "ongeldig"
                    break
                if (ext[f] - top) * dirn > 0:
                    if touched:
                        res = "weggelopen"
                        break
                    top = ext[f]
                    rng = (top - b1) * dirn
                    near = top - dirn * 0.618 * rng
                    row.update(top=top, rng=rng, top_t=str(t[f])[:10], reanchored=True)
                    deadline = f + 1 + EXPIRY
                    continue
                if (opp[f] - near) * dirn <= 0:
                    span = h[f] - l[f]
                    rej = span > 0 and ((c[f] > o[f] and (c[f] - l[f]) >= 0.6 * span) if dirn == 1
                                        else (c[f] < o[f] and (h[f] - c[f]) >= 0.6 * span))
                    cf = (top - c[f]) * dirn / rng  # where the close sits in the fib
                    if rej and 0.5 <= cf <= 0.786:
                        res = "gevuld"
                        entry = c[f]
                        break
                    touched = True
                    touch_n += 1
            busy[j] = f
            if res != "gevuld":
                rows.append(dict(row, result=res))
                continue
            risk = abs(entry - sl)
            lv_near = [s_lvl] + levs
            row.update(result="gevuld", fill=str(t[f])[:10], R_cost=cost / risk, entry=entry,
                       rr1=abs(top + dirn * rng - entry) / risk, touch_n=touch_n, entry_fib=(top - entry) * dirn / rng,
                       at_lvl=any(abs(opp[f] - p) <= 0.3 * atr[f] for p in lv_near))
            sl_t = opp[f] - dirn * 0.1 * atr[f]
            r_t, _ = follow(dirn, entry, sl_t, top + dirn * 0.2 * rng, None, h, l, f + 1)
            row["R_tight_t020"] = r_t - cost / abs(entry - sl_t)
            # test 23: stop beneath the major low (lowest low of the 20 candles before the entry), target the next
            # structure (the nearest earlier swing high above the top that is still intact)
            sl_m = (l[max(f - 20, 0):f].min() if dirn == 1 else h[max(f - 20, 0):f].max()) - dirn * 0.1 * atr[f]
            above = [ext[x] for x in hi if x < i and (ext[x] - top) * dirn > 0
                     and not ((ext[x + 1:f + 1] - ext[x]) * dirn > 0).any()] if dirn == 1 else \
                    [ext[x] for x in lo if x < i and (ext[x] - top) * dirn > 0
                     and not ((ext[x + 1:f + 1] - ext[x]) * dirn > 0).any()]
            kw = int(np.searchsorted(w_done, pd.Timestamp(t[f]).tz_localize("UTC").value, side="right")) - 1
            hs, ls = w_px[:kw + 1][w_kind[:kw + 1] == "H"], w_px[:kw + 1][w_kind[:kw + 1] == "L"]
            T = 0
            if len(hs) >= 2 and len(ls) >= 2:
                T = 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)
            lo_, hi_ = sorted([b1, entry])
            row.update(wk_struct=T * dirn, htf_sup=any(lo_ <= p <= hi_ for p in levs))
            if above and (entry - sl_m) * dirn > 0:
                tp_s = min(above) if dirn == 1 else max(above)
                r_s, j_s = follow(dirn, entry, sl_m, tp_s, None, h, l, f + 1)
                row.update(R_struct=r_s - cost / abs(entry - sl_m), tp_struct=tp_s, sl_major=sl_m,
                           rr_struct=abs(tp_s - entry) / abs(entry - sl_m),
                           x_struct=str(t[j_s])[:10] if j_s is not None else None)
            if False:  # entry at the close: the entry candle cannot have reached the stop
                for name in TPS:
                    row[f"R_{name}"] = row[f"R_{name}_be"] = -1.0 - cost / risk
                for tp1x in (0.2, 0.27):
                    for lock in ("entry", "top"):
                        for tp2x in (0.65, 1.0, 1.618, "trail"):
                            row[f"R_m_{tp1x}_{lock}_{tp2x}"] = -1.0 - cost / risk
                row["R_lvl"] = -1.0 - cost / risk
                row["exit"] = row["fill"]
                row.update({f"x_{name}": row["fill"] for name in TPS})
                rows.append(row)
                continue
            for tp1x in (0.2, 0.27):
                for lock in ("entry", "top"):
                    for tp2x in (0.65, 1.0, 1.618, "trail"):
                        r = managed(dirn, entry, sl, top, rng, tp1x, lock, tp2x, h, l, f + 1)
                        row[f"R_m_{tp1x}_{lock}_{tp2x}"] = r - cost / risk
            beyond = [p for p in levs if (p - (top + dirn * 0.2 * rng)) * dirn > 0]
            lvl_tp = (min(beyond) if dirn == 1 else max(beyond)) if beyond else None
            if lvl_tp is not None:
                r, _ = follow(dirn, entry, sl, lvl_tp, None, h, l, f + 1)
                row["R_lvl"], row["lvl_ext"] = r - cost / risk, (lvl_tp - top) * dirn / rng
            else:
                row["R_lvl"], row["lvl_ext"] = np.nan, np.nan
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
    RESET_EXPIRY = True
    prefix = a.prefix or f"t23{a.tf[0].lower()}_"
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{prefix}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s}: {len(df)} setups, {n} trades", flush=True)
