"""Test E1 (docs/STRATEGY_EW.md): the trader's Elliott Wave method. Waves counted on the weekly and daily chart, trades
on the 4-hour chart. Point in time on closed candles; the same engine as tests 20-33.

    python research/ew/ew_bt.py SYM [SYM ...] [--start 2005-01-01 --end 2025-12-31] [--prefix e1_]
    python research/ew/ew_bt.py SYM [SYM ...] --now          (the count on W1 / D1 at the end of the data)

Swings: a high (low) is confirmed once price has come back K x ATR(14) from it; it is known at the close of that
candle. K: weekly 2, daily 3, 4-hour 2.

Count (weekly and daily; mirror for down), on the last confirmed swings, video "Elliott Wave Theory":
  in wave 3   swings 0-1-2: wave 2 retraced 0.382-0.786 of wave 1 (+-0.03) [37:49-38:57]            -> up
  in wave 5   swings 0-1-2-3-4: as above, 3 beyond 1 and not shorter than 1 [34:42, 03:33], wave 4 retraced
              0.236-0.382 of 3 (0.20-0.50) and stays above the top of 1 [33:44, 42:18]              -> up
  5 waves done  as "in wave 5" plus a new high beyond 3 with wave 5 >= 0.5 x wave 1                -> down
  The count ending at the last swing wins (5 done > in 5 > in 3). Void once the last close breaks its invalidation
  (start of wave 1 / top of wave 1 / top of wave 5).

Setup 1 (decisive), buy the end of the correction in the direction of the bigger count:
  4-hour impulse leg 0 -> 1 of at least 4 ATR(4h), its end confirmed; then a 4-hour close where
  - the low since point 1 has reached the 0.382 level of the leg (zone 0.382-0.786) [38:04-39:22, video 2 02:37-05:45],
  - the MACD(12,26,9) line crosses its signal line in the trade direction ("wait for this crossover") [v2 11:10-11:31],
  - the close is beyond the 0.786 level and nothing closed beyond the start of the leg,
  within the time of the leg itself ("wave 2 is mostly shorter in time than wave 1") [33:14-33:20], at least 6 candles.
  Entry at that close. Stop 0.1 ATR(4h) beyond the start of the leg [39:45-40:05].
  Exits: R_m (decisive) half at point 1 (retest of the high), stop to entry, rest at the 1.618 extension
  (0 -> 1 -> low of the correction) [40:13-40:50, v2 50%-partials and stop to entry]; R_t1 all at point 1;
  R_t2 all at 1.618; R_tight_m like R_m with the stop 0.1 ATR beyond the low of the correction (his live stops).
  Context: d1 / w1 = direction of the daily / weekly count in the trade direction (+1 with, -1 against, 0 none).

Setup 2 (second cell), fade a completed five-wave move on the 4-hour chart:
  4-hour swings 0..5 meet "5 waves done", with MACD divergence (MACD line at 5 below its value at 3, for a top)
  [v2 12:10-12:33, 54:20]. Entry at the close of the candle that confirms swing 5. Stop 0.1 ATR beyond 5.
  R_m half at the end of wave 4, stop to entry, rest at 0.618 of the whole move 0 -> 5; R_t1 all at the end of 4.

Costs per symbol (test2.cost_price), stop before target within a candle (test18).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "research" / "strategy"), str(ROOT / "backtest" / "src")]
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402
from test18 import follow, managed  # noqa: E402

K = {"W1": 2.0, "D1": 3.0, "H4": 2.0}
LEG_MIN = 4.0
ZONE = (0.382, 0.786)
MIN_WAIT = 6
SL_BUF = 0.1
# H4 series stored under another name than the daily / weekly ones
ALIAS = {"XAUUSD": "XAU_USD", "XAGUSD": "XAG_USD", "NAS100USD": "NAS100_USD", "SPX500USD": "SPX500_USD"}


def frame(sym, tf, cut=None):
    d = load(ALIAS.get(sym, sym) if tf == "H4" else sym, tf)
    if cut is not None:
        d = d[d.time < cut].reset_index(drop=True)
    d["done"] = complete_times(d["time"], tf)
    h, l, c = d.high.values, d.low.values, d.close.values
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    d["atr"] = pd.Series(tr).rolling(14).mean().bfill().values
    return d


def swings(h, l, atr, k):
    """Confirmed swings [(i_extreme, i_known, price, +1 high / -1 low)]: price came back k x ATR from the extreme.
    Everything is known at the close of candle i_known."""
    out, mode, hi_i, lo_i = [], 0, 0, 0
    for i in range(len(h)):
        if mode >= 0 and h[i] >= h[hi_i]:
            hi_i = i
        if mode <= 0 and l[i] <= l[lo_i]:
            lo_i = i
        if mode >= 0 and h[hi_i] - l[i] >= k * atr[i] and (mode == 1 or hi_i > lo_i):
            out.append((hi_i, i, h[hi_i], 1))
            mode, lo_i = -1, i
        elif mode <= 0 and h[i] - l[lo_i] >= k * atr[i] and (mode == -1 or lo_i > hi_i):
            out.append((lo_i, i, l[lo_i], -1))
            mode, hi_i = 1, i
    return out


def count(sw, close):
    """(bias, label, invalidation) from the confirmed swings `sw` and the last close."""
    if len(sw) < 3:
        return 0, "", np.nan
    last = sw[-1][3]
    best = None
    for s in (1, -1):  # s = +1: an up impulse
        x = [p * s for _, _, p, _ in sw]
        kinds = [kd * s for *_, kd in sw]
        n = len(x)

        def ok_w2(a):  # swings a, a+1, a+2 = start, end 1, end 2
            l1 = x[a + 1] - x[a]
            r2 = (x[a + 1] - x[a + 2]) / l1 if l1 > 0 else -1
            return l1 > 0 and 0.352 <= r2 <= 0.816

        def ok_w4(a):
            if not ok_w2(a):
                return False
            l1, l3 = x[a + 1] - x[a], x[a + 3] - x[a + 2]
            r4 = (x[a + 3] - x[a + 4]) / l3 if l3 > 0 else -1
            return x[a + 3] > x[a + 1] and l3 >= l1 and 0.20 <= r4 <= 0.50 and x[a + 4] > x[a + 1]

        # 5 waves done: ends at a high of the up impulse
        if last * s == 1 and n >= 6 and kinds[-6] == -1 and ok_w4(n - 6) and x[-1] > x[-3] and \
                x[-1] - x[-2] >= 0.5 * (x[-5] - x[-6]):
            cand = (3, -s, "5 golven af", sw[-1][2])
        elif last * s == -1 and n >= 5 and kinds[-5] == -1 and ok_w4(n - 5):
            cand = (2, s, "in golf 5", sw[-4][2])
        elif last * s == -1 and n >= 3 and kinds[-3] == -1 and ok_w2(n - 3):
            cand = (1, s, "in golf 3", sw[-3][2])
        else:
            continue
        if best is None or cand[0] > best[0]:
            best = cand
    if best is None:
        return 0, "", np.nan
    _, bias, label, inval = best
    # the count is void once the last close is beyond its invalidation level (against the expected move)
    if (close - inval) * bias < 0:
        return 0, "", np.nan
    return bias, label, inval


def htf_states(d, k):
    """Count state at the close of every candle of a higher timeframe."""
    sw = swings(d.high.values, d.low.values, d.atr.values, k)
    out, j = [], 0
    known = [s[1] for s in sw]
    for i in range(len(d)):
        while j < len(sw) and known[j] <= i:
            j += 1
        out.append(count(sw[:j], d.close.values[i]))
    return out


def macd(c):
    s = pd.Series(c)
    line = s.ewm(span=12, adjust=False).mean() - s.ewm(span=26, adjust=False).mean()
    return line.values, line.ewm(span=9, adjust=False).mean().values


def run(sym, start="2005-01-01", end="2025-12-31", cut=None):
    h4 = frame(sym, "H4", cut)
    d1, w1 = frame(sym, "D1", cut), frame(sym, "W1", cut)
    st = {"D1": htf_states(d1, K["D1"]), "W1": htf_states(w1, K["W1"])}
    done = {"D1": d1.done.values, "W1": w1.done.values}

    def ctx(tf, f):
        k = int(np.searchsorted(done[tf], h4.done.values[f], side="right")) - 1
        return st[tf][k] if k >= 0 else (0, "", np.nan)

    o, h, l, c, t, atr = (h4[k].values for k in ("open", "high", "low", "close", "time", "atr"))
    ml, sg = macd(c)
    sw = swings(h, l, atr, K["H4"])
    t0, t1 = pd.Timestamp(start, tz="UTC").value, pd.Timestamp(end, tz="UTC").value
    rows = []
    for q in range(1, len(sw)):
        (i0, _, p0, k0), (i1, kn, p1, k1) = sw[q - 1], sw[q]
        if not (t0 <= pd.Timestamp(t[kn]).value < t1):
            continue
        # ---------------- setup 1: correction after the leg 0 -> 1
        dirn = k1
        leg = (p1 - p0) * dirn
        if leg >= LEG_MIN * atr[kn]:
            z382, z786 = p1 - dirn * ZONE[0] * leg, p1 - dirn * ZONE[1] * leg
            wait = max(MIN_WAIT, i1 - i0)
            ext = l if dirn == 1 else h
            res, f = "verlopen", kn
            for f in range(kn, min(i1 + wait, len(c) - 1) + 1):
                if (c[f] - p0) * dirn < 0:
                    res = "ongeldig"
                    break
                if ((h[f] if dirn == 1 else l[f]) - p1) * dirn > 0:
                    res = "weggelopen"  # a new extreme beyond 1 before the entry: the move went on without us
                    break
                lowest = (ext[i1 + 1:f + 1].min() if dirn == 1 else ext[i1 + 1:f + 1].max()) if f > i1 else p1
                touched = (lowest - z382) * dirn <= 0
                cross = (ml[f] - sg[f]) * dirn > 0 and (ml[f - 1] - sg[f - 1]) * dirn <= 0
                if touched and cross and (c[f] - z786) * dirn > 0:
                    res = "gevuld"
                    break
            row = dict(sym=sym, setup=1, dir=dirn, start_t=str(t[i0])[:10], top_t=str(t[i1])[:10], leg_atr=leg / atr[kn])
            if res == "gevuld":
                entry = c[f]
                low2 = lowest
                depth = (p1 - low2) * dirn / leg
                ext2 = p1 + dirn * (1.618 - depth) * leg  # 1.618 x wave 1 from the end of wave 2
                cost = cost_price(sym, entry)
                dd, ww = ctx("D1", f), ctx("W1", f)
                row.update(result="gevuld", fill=str(t[f])[:16], date=str(t[f])[:10], entry=entry, depth=depth,
                           d1=dd[0] * dirn, d1_lab=dd[1], w1=ww[0] * dirn, w1_lab=ww[1])
                for name, sl in (("", p0 - dirn * SL_BUF * atr[f]), ("tight_", low2 - dirn * SL_BUF * atr[f])):
                    risk = (entry - sl) * dirn
                    if risk <= 0 or (p1 - entry) * dirn <= 0:
                        continue
                    row[f"R_{name}m"] = managed(dirn, entry, sl, p1, leg, 0.0, "entry", 1.618 - depth, h, l, f + 1) - cost / risk
                    if name == "":
                        row.update(sl=sl, R_cost=cost / risk, rr1=(p1 - entry) * dirn / risk)
                        for nm, tgt in (("t1", p1), ("t2", ext2)):
                            r, j = follow(dirn, entry, sl, tgt, None, h, l, f + 1)
                            row[f"R_{nm}"] = r - cost / risk
                            row[f"x_{nm}"] = str(t[j])[:16] if j is not None else None
                rows.append(row)
            else:
                rows.append(dict(row, result=res))
        # ---------------- setup 2: five waves done at swing q
        if q >= 5:
            x = [s[2] for s in sw[q - 5:q + 1]]
            s5 = k1  # +1: the five waves went up (swing q is a high) -> trade down
            b, lab, _ = count(sw[q - 5:q + 1], c[kn])
            if lab == "5 golven af" and b == -s5 and (ml[i1] - ml[sw[q - 2][0]]) * s5 < 0:
                dirn = -s5
                entry = c[kn]
                sl = p1 - dirn * SL_BUF * atr[kn]
                w4, whole = x[4], (x[5] - x[0]) * s5
                risk = (entry - sl) * dirn
                row = dict(sym=sym, setup=2, dir=dirn, start_t=str(t[sw[q - 5][0]])[:10], top_t=str(t[i1])[:10],
                           leg_atr=whole / atr[kn])
                if risk > 0 and (w4 - entry) * dirn > 0:
                    cost = cost_price(sym, entry)
                    dd, ww = ctx("D1", kn), ctx("W1", kn)
                    x2 = max(1.0, 0.618 * whole / ((p1 - w4) * s5))  # rest at 0.618 of 0 -> 5, never short of wave 4
                    r, j = follow(dirn, entry, sl, w4, None, h, l, kn + 1)
                    row.update(result="gevuld", fill=str(t[kn])[:16], date=str(t[kn])[:10], entry=entry, sl=sl,
                               R_cost=cost / risk, rr1=(w4 - entry) * dirn / risk, d1=dd[0] * dirn, d1_lab=dd[1], w1=ww[0] * dirn,
                               w1_lab=ww[1], R_t1=r - cost / risk, x_t1=str(t[j])[:16] if j is not None else None,
                               R_m=managed(dirn, entry, sl, p1, (p1 - w4) * s5, 1.0, "entry", x2,
                                           h, l, kn + 1) - cost / risk)
                else:
                    row.update(result="geen_ruimte")
                rows.append(row)
    return pd.DataFrame(rows)


def now(sym):
    out = []
    for tf in ("W1", "D1"):
        d = frame(sym, tf)
        sw = swings(d.high.values, d.low.values, d.atr.values, K[tf])
        b, lab, inv = count(sw, d.close.values[-1])
        last = ", ".join(f"{str(d.time.values[i])[:10]} {'H' if kd > 0 else 'L'} {p:.5g}" for i, _, p, kd in sw[-6:])
        out.append(f"{tf}: {lab or 'geen telling'}{' (' + ('op' if b > 0 else 'neer') + f', ongeldig voorbij {inv:.5g})' if b else ''}; "
                   f"laatste swings {last}")
    return f"{sym} | " + " | ".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="e1_")
    ap.add_argument("--now", action="store_true")
    a = ap.parse_args()
    (HERE / "out").mkdir(exist_ok=True)
    for s in a.symbols:
        try:
            if a.now:
                print(now(s), flush=True)
                continue
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        g = df[df.result == "gevuld"] if len(df) else df
        print(f"{s}: setup 1 {int((g.setup == 1).sum()) if len(g) else 0} trades, setup 2 "
              f"{int((g.setup == 2).sum()) if len(g) else 0}", flush=True)
