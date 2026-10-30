"""S/R levels as in lesson 1 ("plotting support and resistance zones"), point in time.

levels(candles, ...) uses ONLY the candles it is given (completed MN or W1 bars up to 'now'), so the live
bot (MT5 history at start-up, then each new completed candle) and the backtest get the same levels.

Method (video 1): a level is a price where many candles turned ("taps") with their WICK, from both sides. More taps = stronger. Keep few levels
(the strongest, spread out), and the ones near the current price matter most. A level counts only if it
held as support AND as resistance (min_each taps on both sides); ranked by the weaker side, then the total.
"""
import numpy as np


def _swings(h, l, n):
    hi = [i for i in range(n, len(h) - n) if h[i] == max(h[i - n:i + n + 1])]
    lo = [i for i in range(n, len(l) - n) if l[i] == min(l[i - n:i + n + 1])]
    return hi, lo


def levels(c, tol_atr=0.25, min_each=2, max_levels=4, sep_atr=1.0, near_atr=None):
    """c: dict of numpy arrays open/high/low/close (oldest first). Returns [(price, support_taps, resistance_taps)].

    WICKS, as in the video: a resistance tap at p = a candle whose high (wick) reaches p (within tol) while
    its body stays below p; a support tap = a candle whose low reaches p while its body stays above p.
    Every candle counts, not only swing points (the video counts every touch: "tap, tap, tap").
    A level counts only if it held as support AND as resistance (min_each on both sides); ranked by the
    weaker side, then the total; at least sep_atr apart; with near_atr only levels near the last close."""
    o, h, l, cl = (np.asarray(c[k], float) for k in ("open", "high", "low", "close"))
    if len(cl) < 10:
        return []
    tr = np.maximum(h[1:], cl[:-1]) - np.minimum(l[1:], cl[:-1])
    atr = float(np.mean(tr[-60:]))
    tol = tol_atr * atr
    btop, bbot = np.maximum(o, cl), np.minimum(o, cl)
    cands = np.unique(np.round(np.concatenate([h, l]), 6))
    scored = []
    for p in cands:
        r_t = int(np.sum((h >= p - tol) & (h <= p + tol) & (btop < p)))
        s_t = int(np.sum((l <= p + tol) & (l >= p - tol) & (bbot > p)))
        if min(s_t, r_t) >= min_each:
            scored.append((s_t, r_t, float(p)))
    last = cl[-1]
    if near_atr is not None:
        scored = [x for x in scored if abs(x[2] - last) <= near_atr * atr]
    scored.sort(key=lambda x: (-min(x[0], x[1]), -(x[0] + x[1]), abs(x[2] - last)))
    out = []
    for s_t, r_t, p in scored:
        if all(abs(p - q) > sep_atr * atr for q, _, _ in out):
            out.append((p, s_t, r_t))
        if len(out) >= max_levels:
            break
    return out
