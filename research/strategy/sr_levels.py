"""S/R levels as in lesson 1 ("plotting support and resistance zones"), point in time.

levels(candles, ...) uses ONLY the candles it is given (completed MN or W1 bars up to 'now'), so the live
bot (MT5 history at start-up, then each new completed candle) and the backtest get the same levels.

Method (video 1): a level is a price where many candles turned ("taps"): swing highs and lows, wick or
body, and role flips (throw-over / deviation and back) count too. More taps = stronger. Keep few levels
(the strongest, spread out), and the ones near the current price matter most.
"""
import numpy as np


def _swings(h, l, n):
    hi = [i for i in range(n, len(h) - n) if h[i] == max(h[i - n:i + n + 1])]
    lo = [i for i in range(n, len(l) - n) if l[i] == min(l[i - n:i + n + 1])]
    return hi, lo


def levels(c, n_swing=2, tol_atr=0.25, min_taps=3, max_levels=4, sep_atr=1.0, near_atr=None):
    """c: dict of numpy arrays open/high/low/close (oldest first). Returns [(price, taps)].

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
    # a tap = a distinct swing candle (wick or body edge) that turned within tol of p
    pts = np.array([h[i] for i in hi] + [l[i] for i in lo] + [max(o[i], cl[i]) for i in hi] + [min(o[i], cl[i]) for i in lo])
    idx = np.array(hi + lo + hi + lo)
    scored = [(len(set(idx[np.abs(pts - p) <= tol])), p) for p in cands]
    last = cl[-1]
    if near_atr is not None:
        scored = [x for x in scored if abs(x[1] - last) <= near_atr * atr]
    scored.sort(key=lambda x: (-x[0], abs(x[1] - last)))
    out = []
    for taps, p in scored:
        if taps < min_taps:
            break
        if all(abs(p - q) > sep_atr * atr for q, _ in out):
            out.append((float(p), int(taps)))
        if len(out) >= max_levels:
            break
    return out
