"""S/R levels as in lesson 1 ("plotting support and resistance zones"), point in time.

levels(candles, ...) uses ONLY the candles it is given (completed MN or W1 bars up to 'now'), so the live
bot (MT5 history at start-up, then each new completed candle) and the backtest get the same levels.

Method (video 1): a level is a price where many candles turned ("taps"): swing highs and lows, wick or
body, and role flips (throw-over / deviation and back) count too. More taps = stronger. Keep few levels
(the strongest, spread out), and the ones near the current price matter most. A level counts only if it
held as support AND as resistance (min_each taps on both sides); ranked by the weaker side, then the total.
"""
import numpy as np


def _swings(h, l, n):
    hi = [i for i in range(n, len(h) - n) if h[i] == max(h[i - n:i + n + 1])]
    lo = [i for i in range(n, len(l) - n) if l[i] == min(l[i - n:i + n + 1])]
    return hi, lo


def levels(c, n_swing=2, tol_atr=0.25, min_each=2, max_levels=4, sep_atr=1.0, near_atr=None):
    """c: dict of numpy arrays open/high/low/close (oldest first). Returns [(price, support_taps, resistance_taps)].

    A tap at price p = a swing high/low candle whose wick or body edge lies within tol of p (it turned
    there; a throw-over that came back is also a swing). Candidates are those same wick and body edges. Levels are taken strongest first, at least sep_atr apart; with near_atr only
    levels within that many ATR of the last close (video: the ones near price matter)."""
    o, h, l, cl = (np.asarray(c[k], float) for k in ("open", "high", "low", "close"))
    if len(cl) < 2 * n_swing + 3:
        return []
    tr = np.maximum(h[1:], cl[:-1]) - np.minimum(l[1:], cl[:-1])
    atr = float(np.mean(tr[-60:]))
    tol = tol_atr * atr
    hi, lo = _swings(h, l, n_swing)
    cands = sorted(set([h[i] for i in hi] + [max(o[i], cl[i]) for i in hi] +
                       [l[i] for i in lo] + [min(o[i], cl[i]) for i in lo]))
    # resistance tap = a swing HIGH candle (wick or body top) that turned within tol of p;
    # support tap = a swing LOW candle (wick or body bottom). A strong level was both (role flip).
    rp = np.array([h[i] for i in hi] + [max(o[i], cl[i]) for i in hi]); ri = np.array(hi + hi)
    sp = np.array([l[i] for i in lo] + [min(o[i], cl[i]) for i in lo]); si = np.array(lo + lo)
    scored = []
    for p in cands:
        s_t = len(set(si[np.abs(sp - p) <= tol])) if len(sp) else 0
        r_t = len(set(ri[np.abs(rp - p) <= tol])) if len(rp) else 0
        scored.append((s_t, r_t, p))
    last = cl[-1]
    scored = [x for x in scored if min(x[0], x[1]) >= min_each]
    if near_atr is not None:
        scored = [x for x in scored if abs(x[2] - last) <= near_atr * atr]
    scored.sort(key=lambda x: (-min(x[0], x[1]), -(x[0] + x[1]), abs(x[2] - last)))
    out = []
    for s_t, r_t, p in scored:
        if all(abs(p - q) > sep_atr * atr for q, _, _ in out):
            out.append((float(p), int(s_t), int(r_t)))
        if len(out) >= max_levels:
            break
    return out
