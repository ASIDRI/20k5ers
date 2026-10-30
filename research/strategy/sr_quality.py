"""Back to basics: do our higher-timeframe S/R levels actually hold better than a random line?

    python research/strategy/sr_quality.py

Every month end t (2005-2025), per instrument, levels are built point in time from the completed weekly (and
monthly) candles. Each level within 3 weekly ATR of the close at t is followed on daily candles for 63 days: the first
touch from the side price is on (support from above, resistance from below; touch = within 0.1 daily ATR). Then:
held = price moves 1 daily ATR away from the level (back to the side it came from) before a daily close 0.5 daily
ATR through it; broke = the opposite; neither within 20 days = undecided (left out).
Each method's levels are compared with the same levels shifted 1.5 weekly ATR up or down (random): a level only
"works" if it holds more often than its shifted twin.
Methods:
  huidig    the current method (sr_levels.levels: wick taps from both sides, weekly + monthly, Levels.at)
  swing     every weekly swing high/low (2 weeks each side) of the last 2 years
  cluster   prices where >= 2 weekly swing points of the last 2 years lie within 0.25 weekly ATR (several reactions)
  rolwissel weekly swing highs that were later broken by a weekly close (old resistance -> support) and swing lows
            later broken (old support -> resistance): the trader's "Breaker" / "KEY"
  body      prices where >= 3 weekly opens/closes of the last 2 years lie within 0.15 weekly ATR (body levels)
  maand     monthly swing highs/lows (2 months each side) of the last 10 years
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load, Levels  # noqa: E402
from candle_avail import complete_times  # noqa: E402

RNG = np.random.default_rng(7)


def atr(h, l, c, n=14):
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    return pd.Series(tr).rolling(n).mean().bfill().values


def swings(h, l, n=2):
    hi = [i for i in range(n, len(h) - n) if h[i] == h[i - n:i + n + 1].max()]
    lo = [i for i in range(n, len(l) - n) if l[i] == l[i - n:i + n + 1].min()]
    return hi, lo


def clusters(prices, tol, k):
    prices = np.sort(np.asarray(prices))
    out = []
    for p in prices:
        n = np.sum(np.abs(prices - p) <= tol)
        if n >= k and all(abs(p - q) > tol for q in out):
            out.append(float(np.mean(prices[np.abs(prices - p) <= tol])))
    return out


def methods(sym):
    """{method: function(t) -> list of levels known at t}."""
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    m = load(sym, "MN")
    m["done"] = complete_times(m["time"], "MN", load(sym, "D1")["time"])
    wo, wh, wl, wc = (w[k].values for k in ("open", "high", "low", "close"))
    watr = atr(wh, wl, wc)
    mh, ml = m.high.values, m.low.values
    lv = Levels(sym)
    whi, wlo = swings(wh, wl)
    mhi, mlo = swings(mh, ml)

    def known_w(t):
        return int((w["done"] <= t).sum())

    def f_huidig(t):
        return [p for p, _ in lv.at(t)]

    def f_swing(t):
        k = known_w(t)
        return [wh[i] for i in whi if k - 104 <= i < k - 2] + [wl[i] for i in wlo if k - 104 <= i < k - 2]

    def f_cluster(t):
        k = known_w(t)
        return clusters(f_swing(t), 0.25 * watr[k - 1], 2) if k > 10 else []

    def f_rolwissel(t):
        k = known_w(t)
        out = []
        for i in whi:
            if k - 104 <= i < k - 2 and (wc[i + 1:k] > wh[i]).any():
                out.append(wh[i])
        for i in wlo:
            if k - 104 <= i < k - 2 and (wc[i + 1:k] < wl[i]).any():
                out.append(wl[i])
        return out

    def f_body(t):
        k = known_w(t)
        if k < 20:
            return []
        ends = np.r_[wo[max(k - 104, 0):k], wc[max(k - 104, 0):k]]
        return clusters(ends, 0.15 * watr[k - 1], 3)

    def f_maand(t):
        k = int((m["done"] <= t).sum())
        return [mh[i] for i in mhi if k - 120 <= i < k - 2] + [ml[i] for i in mlo if k - 120 <= i < k - 2]

    return dict(huidig=f_huidig, swing=f_swing, cluster=f_cluster, rolwissel=f_rolwissel, body=f_body,
                maand=f_maand), (w, watr)


def test_level(p, side, h, l, c, a, start, horizon=63, decide=20):
    """side +1: price above the level (support test). Returns 'held', 'broke', None (no touch / undecided)."""
    end = min(start + horizon, len(c))
    for i in range(start, end):
        touch = (l[i] <= p + 0.1 * a[i]) if side == 1 else (h[i] >= p - 0.1 * a[i])
        if not touch:
            continue
        for j in range(i, min(i + decide, len(c))):
            if (c[j] - p) * side <= -0.5 * a[j]:
                return "broke"
            if ((h[j] - p) if side == 1 else (p - l[j])) >= 1.0 * a[j]:
                return "held"
        return None
    return None


if __name__ == "__main__":
    syms = [p.name[3:-4] for p in sorted((HERE / "out").glob("s1_*.csv"))]
    res = []
    for sym in syms:
        d = load(sym, "D1")
        h, l, c = d.high.values, d.low.values, d.close.values
        a = atr(h, l, c)
        meth, (w, watr) = methods(sym)
        for t in pd.date_range("2005-01-31", "2025-09-30", freq="ME", tz="UTC"):
            i0 = int(np.searchsorted(d.time.values, np.datetime64(t.tz_convert(None))))
            if i0 < 30 or i0 >= len(c) - 5:
                continue
            kw = int((w["done"] <= t).sum()) - 1
            wa = watr[kw]
            last = c[i0 - 1]
            for name, fn in meth.items():
                for p in fn(t):
                    if abs(p - last) > 3 * wa or abs(p - last) < 0.2 * a[i0]:
                        continue
                    for kind, q in (("echt", p), ("verschoven", p + RNG.choice([-1, 1]) * 1.5 * wa)):
                        side = 1 if last > q else -1
                        out = test_level(q, side, h, l, c, a, i0)
                        if out:
                            res.append(dict(sym=sym, t=str(t.date()), method=name, kind=kind, held=out == "held"))
        print(sym, len(res), flush=True)
    r = pd.DataFrame(res)
    r.to_csv(HERE / "out" / "sr_quality.csv", index=False)
    r["period"] = np.where(r.t < "2015", "2005-14", np.where(r.t < "2021", "2015-20", "2021-25"))
    tab = r.groupby(["method", "kind"]).held.agg(["size", "mean"]).unstack()
    print("\nHOUDT STAND bij de eerste aanraking (aandeel), echt vs. 1,5 week-ATR verschoven:")
    print(tab.round(3).to_string())
    print("\nverschil echt - verschoven per periode (procentpunt):")
    per = r.groupby(["method", "period", "kind"]).held.mean().unstack()
    print(((per["echt"] - per["verschoven"]) * 100).round(1).unstack().to_string())
