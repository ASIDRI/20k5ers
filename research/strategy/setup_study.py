"""Setup study: every setup of the cycle on one asset, how often it worked.

    python research/strategy/setup_study.py EURUSD XTIUSD --start 2010-01-01

Point in time throughout: daily candles one by one; swings used only once confirmed (N_SWING bars later);
monthly/weekly S/R levels (sr_levels.levels, wick taps) recomputed from the MN/W1 candles that were
COMPLETE at that day (candle_avail.complete_times). Outcomes on daily bars; a bar touching both SL and
target counts as SL (the safe side).

Setups (long, and the mirror short):
  rev_level  structure flips up (daily close above KEY = last lower high, with force) and the low before it
             touched a support level (month/week)                       -> inverse H&S / reversal at S/R
  rev_free   the same flip without a level at the low                    -> reference
  cont_level trend up, close above the last swing high (bullish N), with an S/R level above as target
  cont_open  the same, no level above within reach (open space)
Trade: fib 1 = swing low (wick), 0 = new high (wick); limit at 0.66; SL just below the swing low;
half at -0.25, SL to entry, rest at -0.65 (or at the next level if that comes first); order cancelled if
-0.25 is reached first or the swing low breaks.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "backtest" / "src"))
from sr_levels import levels  # noqa: E402
from candle_avail import complete_times  # noqa: E402

DATA = HERE.parents[1] / "data" / "ohlcv"
N_SWING, FORCE, FORCE_N = 2, 1.5, 10
LEVEL_TOL_ATR = 0.5   # swing extreme "at" a level: within this many DAILY ATR
SL_BUF_ATR = 0.1
FIB_MODE = "confirmed"  # "confirmed": fib drawn once the impulse top is a confirmed swing (as in the video);
                        # "break": on the breaking bar's extreme right away


def load(sym, tf):
    f = sorted(DATA.glob(f"{sym}_{tf}_*.csv"))[0]
    d = pd.read_csv(f)
    d.columns = [c.lower() for c in d.columns]
    tcol = [c for c in d.columns if c in ("time", "timestamp", "date", "datetime")][0]
    d["time"] = pd.to_datetime(d[tcol], utc=True)
    return d.drop_duplicates("time").sort_values("time").reset_index(drop=True)


class Levels:
    """Monthly + weekly levels as known at time t (only completed candles), cached per completed set."""
    def __init__(self, sym):
        self.tf = {}
        d1 = load(sym, "D1")["time"]
        for tf in ("MN", "W1"):
            d = load(sym, tf)
            d["done"] = complete_times(d["time"], tf, d1 if tf == "MN" else None)
            self.tf[tf] = d
        self.cache = {}

    def at(self, t):
        out = []
        for tf in ("MN", "W1"):
            d = self.tf[tf]
            k = int((d["done"] <= t).sum())
            key = (tf, k)
            if key not in self.cache:
                sub = d.iloc[:k]
                self.cache[key] = [(p, tf) for p, _, _ in levels(sub, max_levels=8)] if k > 30 else []
            out += self.cache[key]
        return out


def study(sym, start, end):
    d = load(sym, "D1")
    lv = Levels(sym)
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    body = np.abs(c - o)
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().values
    highs, lows = [], []
    trend = None
    pending, open_tr, done, waiting = [], [], [], []

    def make(w, top):
        dirn, ext, levs = w["dir"], w["ext"], w["levs"]
        rng = abs(top - ext)
        if rng <= 0:
            return
        entry = top - dirn * 0.66 * rng
        sl = ext - dirn * SL_BUF_ATR * w["atr"]
        tp1 = top + dirn * 0.25 * rng
        tp2 = top + dirn * 0.65 * rng
        nxt = [p for p, _ in levs if (p - tp1) * dirn > 0 and (p - tp2) * dirn < 0]
        if nxt:  # the next S/R before -0.65 is the final target
            tp2 = min(nxt) if dirn == 1 else max(nxt)
        pending[:] = [p for p in pending if p["dir"] != dirn]  # newest setup replaces the older one
        pending.append(dict(sym=sym, kind=w["kind"], dir=dirn, date=w["date"], entry=entry, sl=sl,
                            tp1=tp1, tp2=tp2, risk=abs(entry - sl)))
    i0 = int(np.searchsorted(d["time"].values, np.datetime64(pd.Timestamp(start).tz_localize(None))))
    for i in range(max(i0, 60), len(d)):
        t = d["time"][i]
        if t >= pd.Timestamp(end, tz="UTC"):
            break
        # 1) manage open trades and pending orders on bar i (they were set up before this bar)
        for tr_ in list(open_tr):
            long = tr_["dir"] == 1
            adv, fav = (l[i], h[i]) if long else (h[i], l[i])
            hit_sl = adv <= tr_["sl"] if long else adv >= tr_["sl"]
            if hit_sl:
                tr_["R"] += tr_["left"] * ((tr_["sl"] - tr_["entry"]) / tr_["risk"] * tr_["dir"])
                tr_["exit"] = str(t.date()); open_tr.remove(tr_); done.append(tr_); continue
            if not tr_["tp1_hit"] and ((fav >= tr_["tp1"]) if long else (fav <= tr_["tp1"])):
                tr_["R"] += 0.5 * abs(tr_["tp1"] - tr_["entry"]) / tr_["risk"]
                tr_["left"] = 0.5; tr_["tp1_hit"] = True; tr_["sl"] = tr_["entry"]
            if tr_["tp1_hit"] and ((fav >= tr_["tp2"]) if long else (fav <= tr_["tp2"])):
                tr_["R"] += 0.5 * abs(tr_["tp2"] - tr_["entry"]) / tr_["risk"]
                tr_["exit"] = str(t.date()); open_tr.remove(tr_); done.append(tr_)
        for p in list(pending):
            long = p["dir"] == 1
            if (h[i] >= p["tp1"]) if long else (l[i] <= p["tp1"]):
                p["result"] = "weggelopen"; pending.remove(p); done.append(p); continue
            if (l[i] <= p["sl"]) if long else (h[i] >= p["sl"]):
                p["result"] = "ongeldig"; pending.remove(p); done.append(p); continue
            if (l[i] <= p["entry"]) if long else (h[i] >= p["entry"]):
                p.update(result="gevuld", R=0.0, left=1.0, tp1_hit=False, fill=str(t.date()))
                pending.remove(p); open_tr.append(p)
        # 2) swings confirmed by bar i
        k = i - N_SWING
        if h[k] == h[k - N_SWING:k + N_SWING + 1].max():
            highs.append(k)
        if l[k] == l[k - N_SWING:k + N_SWING + 1].min():
            lows.append(k)
        for w in list(waiting):  # impulse top confirmed -> draw the fib now
            dirn = w["dir"]
            if (c[i] < w["ext"]) if dirn == 1 else (c[i] > w["ext"]):
                waiting.remove(w); continue
            sw = [x for x in (highs if dirn == 1 else lows) if x >= w["bos_i"]]
            if sw:
                waiting.remove(w)
                top = h[sw[0]] if dirn == 1 else l[sw[0]]
                make(w, top)
        if len(highs) < 2 or len(lows) < 2 or np.isnan(atr[i]):
            continue
        forceful = body[i] >= FORCE * body[i - FORCE_N:i].mean()
        levs = lv.at(t)
        # 3) structure events on the close of bar i
        for dirn in (1, -1):
            if dirn == 1:
                lh = [x for x in highs if x < i]
                key_i = lh[-1]
                key = h[key_i]
                broke = c[i] > key and c[i - 1] <= key and c[i] > o[i] and forceful
                sw_i = int(l[key_i:i + 1].argmin()) + key_i  # the low of the leg into the break
            else:
                ll = [x for x in lows if x < i]
                key_i = ll[-1]
                key = l[key_i]
                broke = c[i] < key and c[i - 1] >= key and c[i] < o[i] and forceful
                sw_i = int(h[key_i:i + 1].argmax()) + key_i
            if not broke:
                continue
            ext = l[sw_i] if dirn == 1 else h[sw_i]
            if trend == -dirn or trend is None:
                at_level = any(abs(ext - p) <= LEVEL_TOL_ATR * atr[i] for p, _ in levs)
                kind = "rev_level" if at_level else "rev_free"
            else:
                ahead = [p for p, _ in levs if (p - c[i]) * dirn > 0]
                kind = "cont_level" if ahead else "cont_open"
            trend = dirn
            w = dict(dir=dirn, ext=ext, levs=levs, atr=atr[i], kind=kind, date=str(t.date()), bos_i=i)
            if FIB_MODE == "break":
                make(w, h[i] if dirn == 1 else l[i])
            else:
                waiting[:] = [x for x in waiting if x["dir"] != dirn] + [w]
    for p in pending + open_tr:
        p.setdefault("result", "open")
        done.append(p)
    return pd.DataFrame(done)


def report(df, sym):
    df = df.copy()
    df["year"] = df["date"].str[:4]
    f = df[df["result"] == "gevuld"]
    print(f"\n=== {sym}: {len(df)} setups, {len(f)} gevuld ({(df['result']=='weggelopen').sum()} weggelopen zonder terugval)")
    rows = []
    for kind, g in f.groupby("kind"):
        win = (g["R"] > 0).mean() * 100
        rows.append((kind, len(g), round((g["tp1_hit"]).mean() * 100), round(win), round(g["R"].mean(), 2), round(g["R"].sum(), 1)))
    print(f"{'soort':11} {'trades':>6} {'TP1%':>5} {'winst%':>6} {'gem.R':>6} {'som R':>6}")
    for r in rows:
        print(f"{r[0]:11} {r[1]:6} {r[2]:5} {r[3]:6} {r[4]:6} {r[5]:6}")
    by = f.groupby("year")["R"].agg(["count", "sum"]).round(1)
    print("per jaar (trades, som R):", ", ".join(f"{y}: {int(r['count'])}/{r['sum']}" for y, r in by.iterrows()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--fib", default="confirmed", choices=["confirmed", "break"])
    a = ap.parse_args()
    FIB_MODE = a.fib
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    for s in a.symbols:
        df = study(s, a.start, a.end)
        df.to_csv(out / f"setups_{s}.csv", index=False)
        report(df, s)
