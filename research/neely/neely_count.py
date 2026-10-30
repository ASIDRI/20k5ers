"""Neely test N2 (docs/NEELY_TESTS.md): count EURUSD the way Neely does, over several degrees, and trade the confirmed
patterns. Chapters 6-12 are missing from the pdf; what is used of them here is an OWN RECONSTRUCTION (marked [R]).

    python research/neely/neely_count.py [--sym EURUSD] [--tf D1|W1] [--plot docs/neely_eurusd_D1.png] [--since 2021-01-01]

The counter runs ONLINE, one closed daily candle at a time, and only ever sees the series up to that candle:

   Two counters, as the book uses several charts: daily (order of high/low from H4) and weekly (order from D1).
1. Layer 0/1 as in neely_bt: two points per candle (high and low in the order they occurred);
   monowaves; a monowave joins the count once the next point has reversed.
2. The count is ONE sequence of waves (monowaves and compacted patterns, always alternating in direction).
3. Pattern candidates: every run of 5 or 3 adjacent waves in the last WINDOW waves:
     impulse (trending)  5-3-5-3-5, impulse_check ok, no 2-4 overlap                     -> :5
     terminal            3-3-3-3-3, impulse_check ok, 2-4 overlap                        -> :3
     triangle            3-3-3-3-3, triangle_check ok (contracting or expanding)         -> :3
     zigzag              5-3-5, abc_classify zigzag                                      -> :3
     flat                3-3-5, abc_classify flat                                        -> :3
     double [R, ch. 8]   3-3-3, x smaller than both, the third beyond the end of the first,
                         first ~ third (Similarity)                                      -> :3
     triple [R, ch. 8]   3-3-3-3-3, both x smaller than their neighbours, every :3 beyond the previous one,
                         the :3's similar to each other                                  -> :3
   A monowave can be :5 when its start list (doc 5.2) holds 5/s5/L5 and :3 when it holds a 3 label; while its
   m2 is not complete both. A compacted pattern is :5 (trending impulse) or :3 (everything else).
   Every adjacent pair passes Similarity and Balance; Complexity levels of the compacted waves inside one pattern
   differ by at most 1 (doc 7.4) [R: a monowave on the daily chart can hide intraday structure, its level is open].
4. [R, ch. 6, Post-Constructive Rules, stage 1] A pattern is CONFIRMED when the price breaks its trendline against the
   last wave within the time of that last wave plus one candle, before the last wave's end is exceeded:
     impulse / terminal / triangle: the line through the ends of waves 2 and 4 (b and d);
     zigzag / flat / double: the line through the start of the first wave and the end of the second (0-B, 0-x).
   The end exceeded first, or no break in time: not this pattern (yet).
5. [R, ch. 7, Compaction] A confirmed pattern is replaced by ONE wave (start of the first, end of the last) with
   Complexity = highest Complexity inside + 1. When several confirm at once, the one with the least price x time
   goes first (doc 7.1), and the search repeats until nothing confirms.
6. Trade at the close of the candle that confirms a pattern, against its last wave:
     corrections (zigzag, flat, double, triple, terminal): T1 = the start of the pattern (full retracement);
     triangle: T1 = end of e + 75% of the widest leg;
     impulse: [R, stage 2] T1 = end of wave 4, or 61.8% of wave 5 back when wave 5 is the extension.
   Stop 0.1 ATR beyond the end of the pattern. Exits with test18.follow, costs per symbol (same engine as N1).
   Decisive: patterns with Complexity >= 2 (built from compacted patterns, not just monowaves).
"""
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from neely_core import find_monowaves, impulse_check, abc_classify, triangle_check, similar  # noqa: E402
from neely_bt import with_done, ordered_points, start_labels, SUB, SL_BUF  # noqa: E402
from test2 import cost_price  # noqa: E402
from test18 import follow  # noqa: E402

WINDOW = 30
NEED = {"impulse": "53535", "terminal": "33333", "triangle": "33333", "zigzag": "535", "flat": "335", "double": "333",
        "triple": "33333"}


@dataclass(eq=False)
class W:
    i0: int
    i1: int
    p0: float
    p1: float
    cx: int = 0
    name: str = "mono"
    st: str = "?"
    kids: tuple = ()
    known: int = 0

    up = property(lambda s: s.p1 > s.p0)
    size = property(lambda s: abs(s.p1 - s.p0))
    time = property(lambda s: s.i1 - s.i0)


class Counter:
    def __init__(self, pts):
        self.pts = np.asarray(pts, dtype=float)
        self.mono = [W(w.i0, w.i1, w.p0, w.p1) for w in find_monowaves(self.pts.tolist())[:-1]]
        for w in self.mono:
            w.known = w.i1 + 1
        self.next_mono = 0
        self.seq = []
        self.events = []
        self._opts = {}

    def opts(self, w, now):
        if w.st != "?":
            return w.st
        o = self._opts.get(id(w))
        if o is not None:
            return o
        s = start_labels(self.pts[:now + 1], w)
        if s is None or s == "any":
            return "35"
        o = ("5" if s & {"5", "s5", "L5"} else "") + ("3" if s & {"F3", "c3", "x:c3", "sL3", "L3"} else "")
        self._opts[id(w)] = o
        return o

    def kinds(self, ws, now):
        n = len(ws)
        if min(w.size for w in ws) == 0 or (ws[-1].p1 - ws[0].p0) * (1 if ws[0].up else -1) <= 0:
            return []  # [R] a compacted wave runs from start to end in the direction of its first wave
        cxs = [w.cx for w in ws if w.cx > 0]  # [R] a daily monowave can hide intraday structure: Complexity open
        if cxs and max(cxs) - min(cxs) > 1:
            return []
        if not all(similar(ws[i], ws[i + 1]) for i in range(n - 1)):
            return []
        o = [self.opts(w, now) for w in ws]
        fits = lambda name: all(c in oo for c, oo in zip(NEED[name], o))  # noqa: E731
        p = [ws[0].p0] + [w.p1 for w in ws]
        if n == 5:
            ic = impulse_check(p)
            if ic["ok"]:
                name = "impulse" if ic["kind"] == "trending" else "terminal"
                if fits(name):
                    return [(name, ic)]
            tc = triangle_check(p)
            if tc["ok"] and fits("triangle"):
                return [("triangle", tc)]
            d = 1 if ws[0].up else -1
            if fits("triple") and all(ws[i].size < ws[i - 1].size and ws[i].size < ws[i + 1].size for i in (1, 3)) and \
                    (ws[2].p1 - ws[0].p1) * d > 0 and (ws[4].p1 - ws[2].p1) * d > 0 and similar(ws[0], ws[2]) and \
                    similar(ws[2], ws[4]):
                return [("triple", {})]
            return []
        ac = abc_classify(p)
        if ac.get("family") in ("zigzag", "flat"):
            return [(ac["family"], ac)] if fits(ac["family"]) else []
        a, x, c = ws
        if fits("double") and x.size < a.size and x.size < c.size and similar(a, c) and \
                (c.p1 - a.p1) * (1 if a.up else -1) > 0:
            return [("double", {})]
        return []

    def confirm(self, ws, now):
        """Series index of the stage-1 break, or None (not yet / never)."""
        last = ws[-1]
        if len(ws) == 5:
            (x0, y0), (x1, y1) = (ws[1].i1, ws[1].p1), (ws[3].i1, ws[3].p1)
        else:
            (x0, y0), (x1, y1) = (ws[0].i0, ws[0].p0), (ws[1].i1, ws[1].p1)
        hi = now
        if hi <= last.i1:
            return None
        k = np.arange(last.i1 + 1, hi + 1)
        px = self.pts[k]
        line = y0 + (y1 - y0) * (k - x0) / (x1 - x0) if x1 != x0 else np.full(len(k), y1)
        d = 1 if last.up else -1
        brk = np.nonzero((px - line) * -d > 0)[0]
        over = np.nonzero((px - last.p1) * d > 0)[0]
        if len(brk) and (not len(over) or brk[0] < over[0]):
            return int(k[brk[0]])
        return None

    @staticmethod
    def in_time(ws, k):
        """[R, ch. 6 stage 1] the break came within the time of the last wave plus one candle (= 2 points)."""
        return k <= ws[-1].i1 + ws[-1].time + 2

    def step(self, now):
        """Take in every monowave known at series index `now`, then compact while patterns confirm."""
        while self.next_mono < len(self.mono) and self.mono[self.next_mono].known <= now:
            self.seq.append(self.mono[self.next_mono])
            self.next_mono += 1
        self.absorb()
        while True:
            best = None
            lo = max(0, len(self.seq) - WINDOW)
            for j in range(len(self.seq) - 1, lo - 1, -1):
                for n in (5, 3):
                    if j - n + 1 < lo:
                        continue
                    ws = self.seq[j - n + 1:j + 1]
                    ks = self.kinds(ws, now)
                    if not ks:
                        continue
                    k = self.confirm(ws, now)
                    if k is None:
                        continue
                    span = (max(max(w.p0, w.p1) for w in ws) - min(min(w.p0, w.p1) for w in ws)) * (ws[-1].i1 - ws[0].i0)
                    if n == 3 and best is not None and best[1] == j and best[2] == 5:
                        continue  # DETOUR (p. 4-8): the impulse ending here goes before the zigzag/flat
                    if best is None or span < best[0] or (best[1] == j and n == 5):
                        best = (span, j, n, ks[0], k)
            if best is None:
                return
            _, j, n, (name, info), k = best
            ws = self.seq[j - n + 1:j + 1]
            new = W(ws[0].i0, ws[-1].i1, ws[0].p0, ws[-1].p1, max(w.cx for w in ws) + 1, name,
                    "5" if name == "impulse" else "3", tuple(ws), k)
            self.seq[j - n + 1:j + 1] = [new]
            self.events.append((now, k, new, info))
            self.absorb()

    def absorb(self):
        """[R, doc 7.2 / ch. 12 missing waves] A wave smaller than 1/3 of BOTH neighbours in price AND in time cannot be of
        their degree and cannot form a pattern with them: it is internal to the larger move. A + w + B -> one wave in
        the direction of A (Complexity of the larger neighbour, structure open). Only once B is complete."""
        i = len(self.seq) - 2
        lo = max(1, len(self.seq) - WINDOW)
        while i >= lo:
            a, w, b = self.seq[i - 1], self.seq[i], self.seq[i + 1]
            small = lambda x, y: x.size < y.size / 3 and max(x.time, 1) < max(y.time, 1) / 3  # noqa: E731
            if small(w, a) and small(w, b):
                self.seq[i - 1:i + 2] = [W(a.i0, b.i1, a.p0, b.p1, max(a.cx, b.cx), "opgenomen", "?", (a, w, b),
                                           max(a.known, b.known))]
                i = min(i, len(self.seq) - 2)
                continue
            i -= 1

    def pending(self, now):
        """Valid patterns at the end of the count that still wait for their stage-1 break."""
        out = []
        for n in (5, 3):
            if len(self.seq) >= n:
                ws = self.seq[-n:]
                for name, _ in self.kinds(ws, now):
                    out.append((name, ws))
        return out


def target(name, ws, info, dirn):
    end = ws[-1].p1
    if name in ("zigzag", "flat", "double", "triple", "terminal"):
        return ws[0].p0
    if name == "triangle":
        return end + dirn * 0.75 * info["widest"]
    if info.get("extended") == "5":
        return end + dirn * 0.618 * ws[-1].size
    return ws[3].p1


def run(sym="EURUSD", start="2005-01-01", end="2025-12-31", cut=None, tf="D1"):
    d = with_done(sym, tf, cut)
    sub = with_done(sym, SUB[tf], cut)
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    t = d["time"].values
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().bfill().values
    pts = ordered_points(d, sub)
    cnt = Counter(pts)
    t0, t1 = pd.Timestamp(start, tz="UTC").value, pd.Timestamp(end, tz="UTC").value
    rows = []
    for f in range(len(d)):
        n0 = len(cnt.events)
        cnt.step(2 * f + 1)
        for now, k, w, info in cnt.events[n0:]:
            dirn = -1 if w.up else 1
            ws = w.kids
            row = dict(sym=sym, tf=tf, name=w.name, cx=w.cx, dir=dirn, op_tijd=Counter.in_time(ws, k), start_t=str(t[w.i0 // 2])[:10],
                       end_t=str(t[w.i1 // 2])[:10], fill=str(t[f])[:10], date=str(t[f])[:10],
                       p0=w.p0, p1=w.p1, size_atr=w.size / atr[f], bars=w.time // 2)
            if not (t0 <= pd.Timestamp(t[f]).value < t1):
                rows.append(dict(row, result="buiten"))
                continue
            entry = c[f]
            sl = w.p1 - dirn * SL_BUF * atr[f]
            tp = target(w.name, ws, info, dirn)
            if (tp - entry) * dirn <= 0 or (entry - sl) * dirn <= 0:
                rows.append(dict(row, result="geen_ruimte", entry=entry, tp1=tp))
                continue
            cost = cost_price(sym, entry)
            risk = abs(entry - sl)
            r, j = follow(dirn, entry, sl, tp, None, h, l, f + 1)
            rows.append(dict(row, result="gevuld", entry=entry, sl=sl, tp1=tp, rr1=abs(tp - entry) / risk,
                             R_cost=cost / risk, R_t1=r - cost / risk, x_t1=str(t[j])[:10] if j is not None else None))
    return pd.DataFrame(rows), cnt, d


def describe(cnt, d, last=12):
    t = d["time"].values
    lines = []
    for w in cnt.seq[-last:]:
        lines.append(f"| {str(t[w.i0 // 2])[:10]} | {str(t[w.i1 // 2])[:10]} | {w.p0:.5f} | {w.p1:.5f} | "
                     f"{'op' if w.up else 'neer'} | {w.name} | {w.cx} | :{w.st if w.st != '?' else '?'} |")
    return lines


def plot(cnt, d, path, since="2021-01-01", tf="D1"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = pd.to_datetime(d["time"].values)
    s0 = int(np.searchsorted(t, pd.Timestamp(since)))
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.fill_between(t[s0:], d["low"].values[s0:], d["high"].values[s0:], color="#bbbbbb", lw=0)
    col = {0: "#9e9e9e", 1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c", 4: "#d62728", 5: "#9467bd"}

    def draw(w, depth):
        if w.i1 // 2 < s0:
            return
        if w.cx >= 1 and depth < 2:
            for k in w.kids:
                draw(k, depth + 1)
        x = [t[max(w.i0 // 2, s0)], t[w.i1 // 2]]
        ax.plot(x, [w.p0 if w.i0 // 2 >= s0 else np.nan, w.p1], color=col.get(min(w.cx, 5)), lw=0.8 + 0.9 * w.cx)
        if w.cx >= 1 and depth == 0:
            ax.annotate(f"{w.name} ({w.cx})", (t[w.i1 // 2], w.p1), fontsize=8,
                        xytext=(0, 6 if w.up else -12), textcoords="offset points", ha="center")
    for w in cnt.seq:
        draw(w, 0)
    ax.set_title(f"EURUSD {'dag' if tf == 'D1' else 'week'}: Neely-telling (kleur = Complexity: grijs 0, blauw 1, oranje 2, groen 3, rood 4)")
    fig.tight_layout()
    fig.savefig(path, dpi=110)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sym", default="EURUSD")
    ap.add_argument("--tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--plot", default=None)
    ap.add_argument("--since", default="2021-01-01")
    a = ap.parse_args()
    df, cnt, d = run(a.sym, tf=a.tf)
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    df.to_csv(out / f"n2_{a.tf}_{a.sym}.csv", index=False)
    print(df.groupby(["cx", "result"]).size().unstack(fill_value=0))
    print("\n| van | tot | start | eind | richting | patroon | Complexity | structuur |\n|---|---|---|---|---|---|---|---|")
    print("\n".join(describe(cnt, d)))
    print("\nwacht op bevestiging:", [(n, str(d['time'].values[ws[0].i0 // 2])[:10]) for n, ws in cnt.pending(2 * len(d) - 1)])
    if a.plot:
        plot(cnt, d, a.plot, a.since, a.tf)
