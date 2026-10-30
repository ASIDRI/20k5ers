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
Context: hi_bias (bos_bias of the next higher timeframe, in the trade direction), hi_struct (zigzag 2 / 4 of the next higher timeframe: W1 for D1 legs, MN for W1 legs, HH+HL = +1 in the trade
direction), htf_sup (a monthly/weekly S/R level between fib 1 and the entry), m_ma (monthly close vs its 10-month
mean, in the trade direction), wk_sr (test 41: a weekly S/R cluster level between the wick of fib 1 and the entry).
Structural framework (video 4, test 37): bos = a --tf close during the leg beyond the previous same-side turn (the key
level: the last high for a long), i.e. the leg broke structure; shift = that previous turn was itself lower than the one
before (the leg turned a downtrend: inverse H&S), else continuation (N).
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
from sr_quality import methods as sr_methods  # noqa: E402

REV, LEG, EXPIRY, OB_BACK, SL_BUF = 2.0, 4.0, 40, 5, 0.1
ENTRY = 0.618  # --entry 0.66 (test 39, video 3: "enter around 66")
CONFIRM = False  # --confirm (test 40): after the touch, enter at the close of a daily confirmation candle (bullish, closing
# above the previous high, still at or below fib 0.382) instead of the limit
CONFL = False  # --confl (test 44): limit at the BoS (key) level or a weekly S/R cluster inside fib 0.618-0.796 (the
# first one price reaches); no such level -> no trade
BASE = False  # --base (test 45): the base / S/R zone formed before the BoS (>= 2 daily swing points within 0.5 ATR);
# on the return into it a daily rejection candle (hammer / pin bar or engulfing) confirms, entry at its close
PATTERNS = False  # --patterns (test 46): every bullish / bearish pattern of the trader's cheat sheet confirms
REANCHOR = False  # --reanchor (test 42): a new extreme beyond fib 0 before the fill moves fib 0 there (limit at ENTRY
# of the new leg, OB dropped, expiry restarts) instead of voiding the setup
SWEEP = False  # --sweep (test 38): a wick beyond fib 0 before the fill is a liquidity sweep, the fib stays; void only at a close beyond 0
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


def monthly_levels(sym, n=4):
    """The trader's monthly S/R (GBPJPY 194 / 140, 2026-10-30): price levels where monthly candles reject with the wick
    while the body stays on one side, from both sides (support and resistance). Score per candidate price (monthly
    opens, closes, highs, lows) = support rejections (low within 0.1 monthly ATR above the level or through it, body
    above) + resistance rejections (mirror), both >= 1; the n best, at least 2 monthly ATR apart, score >= 5.
    Point in time: only completed monthly candles. Returns a function ts -> [levels] (GBPJPY late 2025: 143.5, 197.0)."""
    m = load(sym, "MN")
    m["done"] = complete_times(m["time"], "MN", load(sym, "D1")["time"])
    o, h, l, c = (m[k].values for k in ("open", "high", "low", "close"))
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(12, min_periods=3).mean().bfill().values
    done = np.array([x.value for x in m["done"]])
    cache = {}

    def at(ts):
        k = int(np.searchsorted(done, ts.value, side="right"))  # completed monthly candles
        if k < 24:
            return []
        if k in cache:
            return cache[k]
        A = atr[k - 1]
        tol = 0.1 * A
        oo, hh, ll, cc = o[:k], h[:k], l[:k], c[:k]
        bl, bh = np.minimum(oo, cc), np.maximum(oo, cc)
        sc = []
        for p in np.unique(np.r_[oo, cc, hh, ll]):
            sup = int(((ll <= p + tol) & (bl >= p - tol)).sum())
            res = int(((hh >= p - tol) & (bh <= p + tol)).sum())
            if sup and res and sup + res >= 5:
                sc.append((sup + res, p))
        out = []
        for _, p in sorted(sc, reverse=True):
            if all(abs(p - q) > 2 * A for q in out):
                out.append(float(p))
            if len(out) == n:
                break
        cache[k] = out
        return out
    return at


def bos_bias(sym, tf):
    """Video 4 / 12: on tf, +1 after a close above the last confirmed swing high (zigzag 2 / 4), -1 after a close below
    the last confirmed swing low; it holds until the opposite key level breaks. (done times, state) per candle."""
    w = load(sym, tf)
    w["done"] = complete_times(w["time"], tf, load(sym, "D1")["time"] if tf == "MN" else None)
    test5.REV = 2.0
    wt, _ = test5.legs(w)
    c = w.close.values
    known = {}
    for ci, _, p, kk in wt:
        known.setdefault(ci, []).append((kk, p))
    hi = lo = None
    state, out = 0, []
    for i in range(len(w)):
        if hi is not None and c[i] > hi:
            state = 1
        elif lo is not None and c[i] < lo:
            state = -1
        out.append(state)
        for kk, p in known.get(i, []):  # turns confirmed by this candle are known from its close on
            hi, lo = (p, lo) if kk == "H" else (hi, p)
    return np.array([x.value for x in w["done"]]), np.array(out)


def bias_at(bb, ts):
    k = int(np.searchsorted(bb[0], ts.value, side="right")) - 1
    return int(bb[1][k]) if k >= 0 else 0


def trend_at(st, ts):
    done, kind, px = st
    k = int(np.searchsorted(done, ts.value, side="right")) - 1
    hs, ls = px[:k + 1][kind[:k + 1] == "H"], px[:k + 1][kind[:k + 1] == "L"]
    if len(hs) < 2 or len(ls) < 2:
        return 0
    return 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)


def rejection(o, h, l, c, f, dirn):
    """Daily confirmation in the trade direction: hammer / pin bar (wick against the trade >= half the candle, close in
    the outer 40%) or an engulfing candle."""
    O, H, L, C = (o[f], h[f], l[f], c[f]) if dirn == 1 else (-o[f], -l[f], -h[f], -c[f])
    span = H - L
    if span <= 0:
        return False
    pin = min(O, C) - L >= 0.5 * span and C - L >= 0.6 * span
    po, pc = (o[f - 1], c[f - 1]) if dirn == 1 else (-o[f - 1], -c[f - 1])
    engulf = C > O and pc < po and C > po and O <= pc
    return pin or engulf


def pattern(o, h, l, c, f, dirn):
    """Cheat-sheet patterns (the trader, 2026-10-30) ending at candle f, in the trade direction (mirrored for shorts):
    hammer, inverted hammer, dragonfly doji, spinning top, engulfing, harami, tweezers, morning star, three white
    soldiers, three inside up, three outside up. Returns the name or None."""
    if f < 3:
        return None
    m = (lambda a: a) if dirn == 1 else (lambda a: -a)
    O = [m(o[f - k]) for k in (2, 1, 0)]
    C = [m(c[f - k]) for k in (2, 1, 0)]
    H = [m(h[f - k]) if dirn == 1 else m(l[f - k]) for k in (2, 1, 0)]
    L = [m(l[f - k]) if dirn == 1 else m(h[f - k]) for k in (2, 1, 0)]
    span = [H[i] - L[i] for i in range(3)]
    body = [abs(C[i] - O[i]) for i in range(3)]
    up = [C[i] > O[i] for i in range(3)]
    if span[2] <= 0:
        return None
    lw, uw = min(O[2], C[2]) - L[2], H[2] - max(O[2], C[2])
    if lw >= 2 * body[2] and uw <= max(body[2], 0.15 * span[2]):
        return "hammer"
    if uw >= 2 * body[2] and lw <= max(body[2], 0.15 * span[2]) and C[1] < O[1]:
        return "inverted hammer"
    if body[2] <= 0.1 * span[2] and uw <= 0.1 * span[2]:
        return "dragonfly doji"
    if up[2] and body[2] <= 0.3 * span[2] and lw >= 0.25 * span[2] and uw >= 0.25 * span[2] and C[1] < O[1]:
        return "spinning top"
    if up[2] and not up[1] and C[2] > O[1] and O[2] <= C[1]:
        return "engulfing"
    if up[2] and not up[1] and body[1] > 0 and C[2] < O[1] and O[2] > C[1]:
        return "harami"
    if up[2] and not up[1] and abs(L[2] - L[1]) <= 0.05 * max(span[1], span[2]):
        return "tweezers"
    if not up[0] and body[0] >= 0.5 * span[0] and body[1] <= 0.3 * body[0] and up[2] and C[2] > (O[0] + C[0]) / 2:
        return "morning star"
    if all(up) and C[0] < C[1] < C[2]:
        return "three white soldiers"
    if not up[0] and up[1] and C[1] < O[0] and O[1] > C[0] and C[2] > O[0]:
        return "three inside up"
    if not up[0] and up[1] and C[1] > O[0] and O[1] <= C[0] and C[2] > C[1]:
        return "three outside up"
    return None


def base_zone(o, h, l, c, si, ti, key, dirn, A, top, rng):
    """The S/R zone the leg broke out of (the trader's demand / supply zone before the BoS): >= 3 daily swing points
    (highs and lows, 2 candles each side) within 0.5 ATR, from 30 candles before the leg start to the break of the key
    level, whose middle lies at fib 0.382-0.81. Returns (near edge, far edge) of the one price reaches first."""
    # the break: the last daily close in the leg beyond the most recent swing point on the same side (the trader's BoS
    # line, e.g. EURAUD 1.7591 in June 2025), else the key level
    ext = h if dirn == 1 else l
    br, sw = None, None
    for j in range(max(si - 30, 4), ti + 1):
        i = j - 2
        if ext[i] == (ext[i - 2:i + 3].max() if dirn == 1 else ext[i - 2:i + 3].min()):
            sw = ext[i]
        if j > si and sw is not None and (c[j] - sw) * dirn > 0:
            br = j
    if br is None and key is not None:
        br = next((j for j in range(si, ti + 1) if (c[j] - key) * dirn > 0), None)
    if br is None:
        return None
    pts = []
    for i in range(max(si - 30, 2), max(br, ti - 1)):  # swing points of the base, up to the extreme
        if h[i] == h[i - 2:i + 3].max():
            pts.append(h[i])
        if l[i] == l[i - 2:i + 3].min():
            pts.append(l[i])
    best = None
    for p in pts:
        m = [q for q in pts if abs(q - p) <= 0.5 * A]
        mid = float(np.mean(m))
        fb = (top - mid) * dirn / rng
        if len(m) >= 2 and 0.382 <= fb <= 0.81:
            near, far = (max(m), min(m)) if dirn == 1 else (min(m), max(m))
            if best is None or (near - best[0]) * dirn > 0:
                best = (near, far)
    return best


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
    bb = bos_bias(sym, HIGHER[tf])
    lv = Levels(sym)
    clus = sr_methods(sym)[0]["cluster"]
    mlev = monthly_levels(sym)
    wk = load(sym, "W1")
    wkt, wkh, wkl, wkc = wk.time.values, wk.high.values, wk.low.values, wk.close.values  # weekly S/R: >= 2 weekly swing points within 0.25 weekly ATR (test 41)
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
        key = turns[k - 2][2] if k >= 2 else None  # previous same-side turn: the key level
        bos = key is not None and bool(((gc[si:ti + 1] - key) * dirn > 0).any())
        shift = bos and k >= 4 and (key - turns[k - 4][2]) * dirn < 0
        gp_hi, gp_lo = top - dirn * ENTRY * rng, top - dirn * 0.786 * rng  # near / far edge of the golden pocket
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
        cands = ([key] if key is not None else []) + list(clus(ready))
        if tf == "D1" and k >= 2:  # smaller BoS levels: daily swing points (2 candles each side) since the previous
            # same-side turn that the leg closed beyond (the trader's BoS line, e.g. NZDCAD Sep 2024)
            ext = h if dirn == 1 else l
            beyond = c[si:ti + 1].max() if dirn == 1 else c[si:ti + 1].min()
            for i in range(max(turns[k - 2][1], 2), si - 1):
                if (ext[i] == (ext[i - 2:i + 3].max() if dirn == 1 else ext[i - 2:i + 3].min())) and (beyond - ext[i]) * dirn > 0:
                    cands.append(ext[i])

        def conf_level(top_, rng_):
            fibs = [((top_ - p) * dirn / rng_, p) for p in cands]
            ok = [x for x in fibs if 0.6 <= x[0] <= 0.81]
            return min(ok)[1] if ok else None
        conf = conf_level(top, rng)
        if CONFL:
            if conf is None:
                rows.append(dict(sym=sym, dir=dirn, date=str(ready.date()), result="geen confluentie"))
                continue
            entry = conf
        origin_sr = any(abs(p - w1) <= 0.5 * A or abs(p - b1) <= 0.5 * A for p in list(clus(ready)) + [q for q, _ in lv.at(ready)])
        sl = w1 - dirn * SL_BUF * A
        row = dict(sym=sym, dir=dirn, date=str(ready.date()), start_t=str(g.time.values[si])[:10],
                   top_t=str(g.time.values[ti])[:10], b1=b1, w1=w1, top=top, rng=rng, has_ob=bool(obs), ob_t=ob_t, bos=bos, shift=shift,
                   n_ob=len(obs), entry=entry, sl=sl, conf=conf is not None, origin_sr=origin_sr, entry_fib=(top - entry) * dirn / rng)
        zone = None
        if BASE:
            zone = base_zone(o, h, l, c, si, ti, key, dirn, A, top, rng) if tf == "D1" else None
            if zone is None:
                rows.append(dict(row, result="geen basis"))
                continue
            entry = zone[0]
            row.update(zone_near=zone[0], zone_far=zone[1], entry=entry)
        f = int(np.searchsorted(dt, ready.tz_convert(None).to_datetime64()))
        last = min(f + EXPIRY * DAYS[tf], len(d))
        res, touched = "verlopen", False
        top_day = g.time.values[ti] if tf == "D1" else None  # the daily candle of the leg's extreme
        while f < last:
            beyond = ((c[f] if SWEEP else (h[f] if dirn == 1 else l[f])) - top) * dirn > 0
            if beyond and ((l[f] if dirn == 1 else h[f]) - entry) * dirn > 0:
                if REANCHOR and not touched:
                    top = h[f] if dirn == 1 else l[f]
                    rng = (top - b1) * dirn
                    entry = top - dirn * ENTRY * rng
                    if CONFL:
                        entry = conf_level(top, rng)
                        if entry is None:
                            res = "weggelopen"
                            break
                    last = min(f + 1 + EXPIRY * DAYS[tf], len(d))
                    row.update(top=top, rng=rng, entry=entry, has_ob=False, reanchored=True)
                    top_day = dt[f]
                    f += 1
                    continue
                res = "weggelopen"
                break
            if BASE:
                if (c[f] - zone[1]) * dirn < -0.5 * A:  # closed clearly through the zone: it did not hold
                    res = "ongeldig"
                    break
                pat = pattern(o, h, l, c, f, dirn) if PATTERNS else ("pin/engulf" if rejection(o, h, l, c, f, dirn) else None)
                ext3 = l[f - 2:f + 1].min() if dirn == 1 else h[f - 2:f + 1].max()  # the pattern's extreme
                if pat and ((ext3 if PATTERNS else (l[f] if dirn == 1 else h[f])) - zone[0]) * dirn <= 0.1 * A \
                        and (c[f] - zone[1]) * dirn > 0 and (top - c[f]) * dirn >= 0.2 * rng:
                    res = "gevuld"
                    row["pattern"] = pat
                    break
                f += 1
                continue
            if not CONFIRM and ((l[f] if dirn == 1 else h[f]) - entry) * dirn <= 0:
                res = "gevuld"
                break
            if (c[f] - b1) * dirn < 0:
                res = "ongeldig"
                break
            if CONFIRM:
                if touched and (c[f] - o[f]) * dirn > 0 and (c[f] - (h[f - 1] if dirn == 1 else l[f - 1])) * dirn > 0 \
                        and (top - c[f]) * dirn >= 0.382 * rng:
                    res = "gevuld"
                    break
                touched = touched or ((l[f] if dirn == 1 else h[f]) - entry) * dirn <= 0
            f += 1
        if res == "verlopen" and f >= len(d):
            res = "actief"
        if res != "gevuld":
            rows.append(dict(row, result=res))
            continue
        fill = c[f] if (CONFIRM or BASE) else (entry if ((o[f] - entry) * dirn >= 0) else o[f])  # a gap through the limit: the open
        risk = abs(fill - sl)
        ts = pd.Timestamp(dt[f]).tz_localize("UTC")
        lo_, hi_ = sorted([b1, fill])
        cost = cost_price(sym, fill)
        row.update(result="gevuld", fill=str(ts.date()), entry=fill, entry_fib=(top - fill) * dirn / rng, R_cost=cost / risk,
                   hi_struct=trend_at(st, ts) * dirn, htf_sup=any(lo_ <= p <= hi_ for p, _ in lv.at(ts)),
                   m_ma=lv.trend(ts, "MN") * dirn, hi_bias=bias_at(bb, ts) * dirn,
                   wk_sr=any(min(w1, fill) <= p <= max(w1, fill) for p in clus(ts)))
        tp20 = top + dirn * 0.2 * rng
        ml = mlev(ts)
        row.update(m_block=any(min(fill, tp20) < p < max(fill, tp20) for p in ml),  # test 47: monthly S/R in the way
                   m_sup=any(min(sl, fill) <= p <= max(sl, fill) for p in ml),  # monthly S/R behind the entry
                   n_mlev=len(ml))
        if top_day is not None:  # test 43: the week of the leg's extreme swept a weekly S/R level and closed back
            wi = int(np.searchsorted(wkt, top_day, side="right")) - 1
            ext, cl = (wkh[wi], wkc[wi]) if dirn == 1 else (wkl[wi], wkc[wi])
            row["w_rej"] = any((ext - p) * dirn > 0 and (cl - p) * dirn < 0 for p in clus(ts))
        hit_sl = not (CONFIRM or BASE) and ((l[f] if dirn == 1 else h[f]) - sl) * dirn <= 0  # a confirmation entry is at the close
        for name, x in (("t020", 0.2), ("t025", 0.25), ("t065", 0.65)):
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
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--entry", type=float, default=0.618)
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--reanchor", action="store_true")
    ap.add_argument("--confl", action="store_true")
    ap.add_argument("--base", action="store_true")
    ap.add_argument("--patterns", action="store_true")
    a = ap.parse_args()
    PATTERNS = a.patterns
    SWEEP, ENTRY, CONFIRM, REANCHOR, CONFL, BASE = a.sweep, a.entry, a.confirm, a.reanchor, a.confl, a.base
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s}: {len(df)} poten, {n} trades, {int(df.get('has_ob', pd.Series(dtype=bool)).sum())} met OB", flush=True)
