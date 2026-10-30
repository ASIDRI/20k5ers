"""Test 14: video 9 on its own, with its most-used entry - an inverse head and shoulders on the 4-hour chart.

    python research/strategy/test14.py SYM [SYM ...] --start 2005-01-01 --end 2025-12-31 [--prefix t14_]

Daily setup and weekly phase as test 12 (test9.zones: daily legs, zone 0.618 - 1.1; week_phase). Entry (long; mirror
for short): 4-hour swings (2 candles each side, known 2 candles later) from 10 candles before the first touch of the
zone: left shoulder L1, high H1, head L2 < L1 inside the zone, high H2, right shoulder L3 > L2. Entry at the close of
the first 4-hour candle that closes above H2 (the neckline: a higher high after a higher low). Stop beneath L3 minus
10 pips (5 for pairs that move less is not modelled). Void: a 4-hour close beyond 1.1, -0.27 traded before the entry,
or 26 daily candles. Exits: daily -0.27 (R_hs_t27), -0.68 (R_hs_t68), -0.27 with the stop to entry half way
(R_hs_t27be); net of costs. Features from test 12: cont, hl, wk_trend, wk_phase, wk_ok.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from test2 import cost_price  # noqa: E402
from test8 import pip  # noqa: E402
from test9 import zones, week_phase, follow, EXPIRY, SPAN  # noqa: E402

KH, PIPS, PRE = 2, 10, 10


def trade(z, d, sym):
    dirn = z["dir"]
    o, h, l, c, t = (d[k].values for k in ("open", "high", "low", "close", "time"))
    a = int(np.searchsorted(t, np.datetime64(z["ready"].tz_convert(None))))
    end = z["ready"] + EXPIRY * SPAN
    inv = z["top"] - dirn * 1.1 * z["rng"]
    t27, t68 = (z["top"] + dirn * x * z["rng"] for x in (0.27, 0.68))
    lo, hi = (l, h) if dirn == 1 else (-h, -l)  # mirror so that a long pattern is always searched
    zone_edge = z["zhi"] if dirn == 1 else -z["zlo"]
    touch, swings = None, []
    for i in range(a, len(d)):
        if pd.Timestamp(t[i]).tz_localize("UTC") > end:
            return dict(result="verlopen")
        if (h[i] >= t27) if dirn == 1 else (l[i] <= t27):
            return dict(result="weggelopen")
        if (c[i] < inv) if dirn == 1 else (c[i] > inv):
            return dict(result="ongeldig")
        if touch is None:
            if lo[i] <= zone_edge:
                touch = i
                swings = []
            else:
                continue
        k = i - KH  # a swing at k is known now
        if k >= max(touch - PRE, KH):
            w = slice(k - KH, k + KH + 1)
            if lo[k] == lo[w].min():
                swings.append(("L", k, lo[k]))
            if hi[k] == hi[w].max():
                swings.append(("H", k, hi[k]))
        seq = []
        for s in swings:  # alternate L/H, keeping the more extreme of two in a row
            if seq and seq[-1][0] == s[0]:
                if (s[0] == "L" and s[2] < seq[-1][2]) or (s[0] == "H" and s[2] > seq[-1][2]):
                    seq[-1] = s
            else:
                seq.append(s)
        if len(seq) < 5 or seq[-1][0] != "L":
            continue
        (_, _, l1), (_, _, h1), (_, _, l2), (_, _, h2), (_, k3, l3) = seq[-5:]
        if not (l2 < l1 and l2 <= zone_edge and l3 > l2):
            continue
        close_m = c[i] if dirn == 1 else -c[i]
        if close_m <= h2 or i <= k3:
            continue
        entry = c[i]
        sl = (l3 - PIPS * pip(sym)) if dirn == 1 else -(l3 - PIPS * pip(sym))
        risk = abs(entry - sl)
        if risk <= 0 or (t27 - entry) * dirn <= 0:
            return dict(result="ongeldig")
        cost = cost_price(sym) / risk
        kw = int(np.searchsorted(z["_wd"], pd.Timestamp(t[i]).tz_localize("UTC").value, side="right")) - 1
        res = dict(result="gevuld", entry=entry, sl=sl, fill=str(pd.Timestamp(t[i]).date()), rr1=abs(t27 - entry) / risk,
                   **(week_phase(z, kw, entry, dirn) if kw >= 0 else dict(wk_trend=0, wk_phase=0, wk_ok=False)))
        for name, tp, be in (("t27", t27, False), ("t68", t68, False), ("t27be", t27, True)):
            r, _ = follow(dirn, entry, sl, tp, be, h, l, i + 1)
            res[f"R_hs_{name}"] = r - cost
        return res
    return dict(result="open")


def run(sym, start, end):
    d = load(sym, "H4")
    rows = []
    for z in zones(sym, start, end):
        rows.append({k: v for k, v in dict(z, **trade(z, d, sym)).items() if not k.startswith("_")})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--prefix", default="t14_")
    a = ap.parse_args()
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(HERE / "out" / f"{a.prefix}{s}.csv", index=False)
        print(f"{s}: {len(df)} poten, {int((df.result == 'gevuld').sum()) if len(df) else 0} trades", flush=True)
