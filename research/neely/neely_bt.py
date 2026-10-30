"""Neely test N1 (docs/NEELY_TESTS.md): setups A and B of docs/NEELY_BOT_STRATEGIE.md, point in time on closed candles.

    python research/neely/neely_bt.py SYM [SYM ...] --tf D1 [--start 2005-01-01 --end 2025-12-31] [--prefix n1_D1_]

Layer 0 (book p. 2-6 to 2-12): one price per time unit is not enough to know the order, so every bar gives two points,
its high and its low IN THE ORDER THEY OCCURRED (book option b). The order comes from the lower timeframe (H4 inside a
day, D1 inside a week): the sub-bar holding the high against the one holding the low. Same sub-bar, or no sub-data:
a bar that closed down made its high first, a bar that closed up its low first.
Layer 1: monowaves on that series (neely_core.find_monowaves). A monowave is COMPLETE only once the next point reverses;
that point belongs to a bar, and the wave is known at that bar's close. The last (running) monowave is never used.
Every decision at bar t uses the series up to and including bar t (both its points), nothing after.

Setup A (contracting triangle, thrust): the last five complete monowaves a..e pass triangle_check (book minimum rules)
with a contracting variant, every two adjacent legs pass similar() (Similarity and Balance). Thrust direction = against
a (the side of b and d). Confirmation: a bar CLOSES beyond the end of d and beyond the b-d trendline in the thrust
direction. Void before that: a bar trades beyond the end of e, or no confirmation within the triangle's duration.
Entry at that close; stop 0.1 ATR beyond the end of e; T1 = end of e + 75% of the widest leg (decisive), T2 = 100%,
managed = half at T1, stop to entry, rest at 125%.

Setup B (resumption after a completed zigzag or flat): the last three complete monowaves a, b, c pass abc_classify
(zigzag or flat); a ~ b and b ~ c (similar()); DETOUR (book p. 4-8): if the two waves before a plus a, b, c pass
impulse_check, it is an impulse, not a correction -> skip. Trade direction = against a. Confirmation: a bar CLOSES
beyond the 0-B trendline (start of a - end of b) in the trade direction; truncated zigzag also >= 81% of the whole
zigzag back, elongated zigzag also > 61.8% of c back. Void: a bar trades beyond the end of c, or no confirmation within
the pattern's duration. Entry at that close; stop 0.1 ATR beyond the end of c; T1 = start of a (full retracement,
decisive), T2 = end of c + 161.8% of a, managed = half at T1, stop to entry, rest at T2.

Engine = the one of tests 20-33, only the strategy is new: entry at the confirming close, exits with test18.follow /
test18.managed (stop first when stop and target fall in the same bar, no time stop), costs per symbol
(research/costs.json, test2.cost_price) in R, evaluation with t17_eval (one position per direction, three periods).
A pattern still waiting for its confirmation when the data ends is "actief" (for a scanner). Context known at the entry bar:
  htf   = direction of the next timeframe up (last COMPLETED W1 / MN close vs the mean of the last 10), in the trade
          direction (+1 with, -1 against).
  lab_ok = Pre-Constructive start lists (doc section 5.2): every pattern wave whose Retracement Rule is already known
          at the entry bar (m2 complete) has the label the pattern needs in its list (A: F3 c3 c3 sL3 L3; zigzag: 5 F3
          L5; flat: F3 c3 L5). lab_n = how many waves could be checked.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "research" / "strategy"), str(ROOT / "backtest" / "src")]
from neely_core import (Monowave, find_monowaves, retracement_ratios, rule_id, condition_id,  # noqa: E402
                        impulse_check, abc_classify, triangle_check, similar)
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402
from test18 import follow, managed  # noqa: E402

SUB = {"D1": "H4", "W1": "D1"}
HIGHER = {"D1": "W1", "W1": "MN"}
SL_BUF = 0.1
MIN_DUR = 3
SIM_MIN = 1 / 3  # Similarity and Balance (p. 4-3); --sim-min lowers it (test N4: Optuna picks the threshold)
LOOSE = False  # --loose (test N4): keep expanding triangles, DETOUR impulses and setups without room to T1, as features

# doc section 5.2: start list per Rule (and Condition for Rule 4), brackets included
START = {1: {"5", "c3", "x:c3", "sL3", "s5"}, 2: {"5", "sL3", "c3", "s5"},
         3: {"F3", "c3", "s5", "5", "sL3", "L5"}, 5: {"F3", "c3", "5", "L5", "L3"},
         "4a": {"F3", "c3", "s5", "sL3"}, "4b": {"F3", "c3", "s5", "sL3", "x:c3", "L5"},
         "4c": {"c3", "F3", "x:c3"}, "4d": {"F3", "c3", "x:c3"}, "4e": {"F3", "x:c3"}}
NEED = {"A": ["F3", "c3", "c3", "sL3", "L3"], "zigzag": ["5", "F3", "L5"], "flat": ["F3", "c3", "L5"]}


def start_labels(prices, w):
    """Start list of monowave w from the prices known so far, or None while its m2 (or m0) is not complete."""
    r = retracement_ratios(prices, w)
    if r["m2_over_m1"] is None or r["m0_over_m1"] is None:
        return None
    rule = rule_id(r["m2_over_m1"])
    if rule in (6, 7):
        return "any"
    return START[f"4{condition_id(4, r['m0_over_m1'])}" if rule == 4 else rule]


def labels_fit(prices, waves, need):
    n, ok = 0, True
    for w, lab in zip(waves, need):
        s = start_labels(prices, w)
        if s is None:
            continue
        n += 1
        ok &= s == "any" or lab in s
    return ok, n


def with_done(sym, tf, cut=None):
    d = load(sym, tf)
    if cut is not None:
        d = d[d.time < cut].reset_index(drop=True)
    d1 = load(sym, "D1")["time"] if tf == "MN" else None
    if d1 is not None and cut is not None:
        d1 = d1[d1 < cut]
    d["done"] = complete_times(d["time"], tf, d1)
    return d


def ordered_points(d, sub):
    """Per bar (high, low) in the order they occurred -> series of 2 points per bar (book option b)."""
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    hi_first = c < o
    if sub is not None and len(sub):
        k = np.searchsorted(d["time"].values, sub["time"].values, side="right") - 1
        ok = (k >= 0) & (sub["time"].values < d["done"].values[np.clip(k, 0, None)])
        s = sub[ok].assign(k=k[ok]).reset_index(drop=True)
        g = s.groupby("k")
        cnt = g.size()
        ih, il = g["high"].idxmax(), g["low"].idxmin()
        multi = cnt[cnt >= 2].index
        ih, il = ih[multi].values, il[multi].values
        same = ih == il
        first = np.where(same, s["close"].values[ih] < s["open"].values[ih], ih < il)
        hi_first[multi.values] = first
    pts = np.empty(2 * len(d))
    pts[0::2] = np.where(hi_first, h, l)
    pts[1::2] = np.where(hi_first, l, h)
    return pts


def htf_trend(hd):
    """f(ts) -> +1/-1/0: last COMPLETED higher-timeframe close vs the mean of the last 10 closes."""
    done, cl = hd["done"].values, hd["close"].values

    def f(ts):
        k = int(np.searchsorted(done, ts, side="right"))
        if k < 10:
            return 0
        return 1 if cl[k - 1] > cl[k - 10:k].mean() else -1
    return f


def line_at(x0, y0, x1, y1, x):
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 != x0 else y1


def sim_pair(a, b):
    """max(price ratio, time ratio) of two waves; similar() in neely_core is sim_pair >= 1/3."""
    pr = min(a.size, b.size) / max(a.size, b.size) if max(a.size, b.size) else 0
    ti = min(a.time, b.time) / max(a.time, b.time) if max(a.time, b.time) else 0
    return max(pr, ti)


def run(sym, tf="D1", start="2005-01-01", end="2025-12-31", cut=None):
    d = with_done(sym, tf, cut)
    try:
        sub = with_done(sym, SUB[tf], cut)
    except IndexError:
        sub = None
    hd = with_done(sym, HIGHER[tf], cut)
    trend = htf_trend(hd)
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    t = d["time"].values
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().bfill().values
    pts = ordered_points(d, sub)
    waves = find_monowaves(pts.tolist())
    t0, t1 = pd.Timestamp(start, tz="UTC").value, pd.Timestamp(end, tz="UTC").value
    rows = []
    for k in range(len(waves) - 1):  # the last wave is still running
        known = (waves[k].i1 + 1) // 2  # bar whose close shows the reversal that ends wave k
        if not (t0 <= pd.Timestamp(t[known]).value < t1):
            continue
        for kind in ("A", "B"):
            n = 5 if kind == "A" else 3
            if k - n + 1 < 0:
                continue
            ws = waves[k - n + 1:k + 1]
            p = [ws[0].p0] + [w.p1 for w in ws]
            sim = min(sim_pair(ws[i], ws[i + 1]) for i in range(n - 1))
            if sim < SIM_MIN:
                continue
            dirn = -1 if ws[0].up else 1
            if kind == "A":
                tc = triangle_check(p)
                if not (tc["ok"] and (tc["variant"].startswith("contracting") or LOOSE)):
                    continue
                fam, var, detour = "triangle", tc["variant"], False
                wb, wd, end_px = ws[1], ws[3], ws[4].p1
                rng, x1, x2, xm = tc["widest"], 0.75, 1.0, 1.25
            else:
                ac = abc_classify(p)
                if ac.get("family") not in ("zigzag", "flat"):
                    continue
                detour = k >= 4 and impulse_check([waves[k - 4].p0] + [w.p1 for w in waves[k - 4:k + 1]])["ok"]
                if detour and not LOOSE:
                    continue  # DETOUR: an impulse, not a correction
                fam, var = ac["family"], ac["variant"]
                end_px, a_len, c_len = ws[2].p1, ws[0].size, ws[2].size
                rng = abs(ws[0].p0 - end_px)
                if rng == 0:
                    continue
                x1, x2 = 1.0, 1.618 * a_len / rng
                xm = x2
            i_start, i_end = ws[0].i0 // 2, ws[-1].i1 // 2
            dur = max(MIN_DUR, i_end - i_start)
            tp, tp2 = end_px + dirn * x1 * rng, end_px + dirn * x2 * rng
            row = dict(sym=sym, tf=tf, setup=kind, family=fam, variant=var, dir=dirn,
                       start_t=str(t[i_start])[:10], end_t=str(t[i_end])[:10], known=str(t[known])[:10],
                       dur=dur, end_px=end_px, sim=sim, detour=detour,
                       size_atr=(max(p) - min(p)) / atr[known])
            res, entry, f = "verlopen", None, known
            for f in range(known, min(known + dur, len(c))):
                if (l[f] - end_px if dirn == 1 else end_px - h[f]) < 0:
                    res = "ongeldig"
                    break
                x = 2 * f + 1
                if kind == "A":
                    ok = (c[f] - wd.p1) * dirn > 0 and (c[f] - line_at(wb.i1, wb.p1, wd.i1, wd.p1, x)) * dirn > 0
                else:
                    ok = (c[f] - line_at(ws[0].i0, ws[0].p0, ws[1].i1, ws[1].p1, x)) * dirn > 0
                    if var == "truncated":
                        ok &= (c[f] - (end_px + dirn * 0.81 * abs(ws[0].p0 - end_px))) * dirn >= 0
                    if var == "elongated" and fam == "zigzag":
                        ok &= (c[f] - (end_px + dirn * 0.618 * c_len)) * dirn > 0
                if ok:
                    res, entry = "gevuld", c[f]
                    break
            if res == "verlopen" and f + 1 >= len(c) and known + dur > len(c):
                res = "actief"  # still waiting for its confirmation when the data ends: for a scanner
                row.update(sl=end_px - dirn * SL_BUF * atr[f], tp1=tp, tp2=tp2, nog_candles=known + dur - len(c))
            if res != "gevuld":
                rows.append(dict(row, result=res))
                continue
            sl = end_px - dirn * SL_BUF * atr[f]
            room = (tp - entry) * dirn > 0
            if not room and not LOOSE:
                rows.append(dict(row, result="geen_ruimte", fill=str(t[f])[:10], entry=entry))
                continue
            lab_ok, lab_n = labels_fit(pts[:2 * f + 2], ws, NEED["A" if kind == "A" else fam])
            done_f = d["done"].values[f]
            cost = cost_price(sym, entry)
            risk = abs(entry - sl)
            row.update(result="gevuld", fill=str(t[f])[:10], date=str(t[f])[:10], fi=f, atr=atr[f],
                       entry=entry, sl=sl, tp1=tp, tp2=tp2,
                       rr1=abs(tp - entry) / risk, risk_atr=risk / atr[f], R_cost=cost / risk,
                       htf=trend(done_f) * dirn, lab_ok=lab_ok, lab_n=lab_n, room=room, delay=f - known,
                       inv_atr=(entry - end_px) * dirn / atr[f],
                       brk_atr=(entry - (max(wd.p1 * dirn, line_at(wb.i1, wb.p1, wd.i1, wd.p1, 2 * f + 1) * dirn) * dirn
                                         if kind == "A" else line_at(ws[0].i0, ws[0].p0, ws[1].i1, ws[1].p1, 2 * f + 1)))
                       * dirn / atr[f])
            for name, tgt in (("t1", tp), ("t2", tp2)):
                r, j = follow(dirn, entry, sl, tgt, None, h, l, f + 1)
                row[f"R_{name}"] = r - cost / risk
                row[f"x_{name}"] = str(t[j])[:10] if j is not None else None
            row["R_m"] = managed(dirn, entry, sl, end_px, rng, x1, "entry", xm, h, l, f + 1) - cost / risk
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--sim-min", type=float, default=SIM_MIN)
    ap.add_argument("--loose", action="store_true")
    a = ap.parse_args()
    SIM_MIN, LOOSE = a.sim_min, a.loose
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    for s in a.symbols:
        try:
            df = run(s, a.tf, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(out / f"{a.prefix or f'n1_{a.tf}_'}{s}.csv", index=False)
        n = int((df.result == "gevuld").sum()) if len(df) else 0
        print(f"{s} {a.tf}: {len(df)} patronen, {n} trades", flush=True)
