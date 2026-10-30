"""Test 26: video 10 "Liquidity Pockets" - intraday on SPX500 (2015-2026) and NAS100 (2015-2022, 15-minute data).

    python research/strategy/test26.py

Every New York trading day D (times in New York time): the high PH and low PL of the previous day's noon session
(13:30-16:00) are the liquidity. On day D, from 18:00 the evening before until 15:00:
- short: price trades above PH (takes the liquidity) and a 15-minute candle then closes back below PH (it fails to
  break away) -> short at that close, stop 0.1 x the PH-PL range above the highest high since the sweep, target PL;
- long: the mirror (sweep below PL, close back above it, target PH).
The first trigger of the day only; the reward must be at least the risk. Exit at target, stop (a candle touching both
counts as the stop) or at the 16:00 close. Costs per symbol (test2.cost_price) in R.
Variant `bias`: only in the direction of the daily trend (previous day's close above / below its 20-day mean),
as the video trades "if you are bullish".
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from test2 import cost_price  # noqa: E402
from t17_eval import pf  # noqa: E402

DATA = HERE.parents[1] / "data" / "ohlcv"
SETS = {"SPX500USD": ("SPX500_USD_M15_2015_2026.csv", "2027"), "NAS100USD": ("NAS100_USD_M15_2015_2025.csv", "2023")}


def run(sym, file, until):
    d = pd.read_csv(DATA / file)
    d["time"] = pd.to_datetime(d.time, utc=True)
    d = d.drop_duplicates("time").sort_values("time")
    d = d[d.time < pd.Timestamp(until, tz="UTC")]
    d["ny"] = d.time.dt.tz_convert("America/New_York")
    d["day"] = (d.ny + pd.Timedelta(hours=6)).dt.date  # trading day: 18:00 the evening before belongs to the next day
    d["hm"] = d.ny.dt.hour * 60 + d.ny.dt.minute
    cost = cost_price(sym)
    daily = d.groupby("day").close.last()
    bias = np.sign(daily - daily.rolling(20).mean()).shift(1)
    rows, prev = [], None
    for day, g in d.groupby("day"):
        noon = g[(g.hm >= 13 * 60 + 30) & (g.hm < 16 * 60)]
        if prev is not None and len(g) > 20:
            ph, pl = prev
            rng = ph - pl
            w = g[(g.hm < 15 * 60) | (g.hm >= 18 * 60)]
            h, l, c = w.high.values, w.low.values, w.close.values
            swept_hi = swept_lo = None
            trade = None
            for i in range(len(w)):
                if swept_hi is None and h[i] > ph:
                    swept_hi = i
                if swept_lo is None and l[i] < pl:
                    swept_lo = i
                if swept_hi is not None and c[i] < ph and i >= swept_hi:
                    sl = h[swept_hi:i + 1].max() + 0.1 * rng
                    trade = (-1, c[i], sl, pl, w.time.values[i])
                    break
                if swept_lo is not None and c[i] > pl and i >= swept_lo:
                    sl = l[swept_lo:i + 1].min() - 0.1 * rng
                    trade = (1, c[i], sl, ph, w.time.values[i])
                    break
            if trade:
                dirn, entry, sl, tp, t_in = trade
                risk = abs(entry - sl)
                if risk > 0 and abs(tp - entry) >= risk and (tp - entry) * dirn > 0:
                    rest = g[(g.time > pd.Timestamp(t_in, tz="UTC")) & (g.hm < 16 * 60)]
                    R = None
                    for _, b in rest.iterrows():
                        adv, fav = (b.low, b.high) if dirn == 1 else (b.high, b.low)
                        if (adv <= sl) if dirn == 1 else (adv >= sl):
                            R = -1.0
                            break
                        if (fav >= tp) if dirn == 1 else (fav <= tp):
                            R = abs(tp - entry) / risk
                            break
                    if R is None:
                        last = rest.close.iloc[-1] if len(rest) else entry
                        R = (last - entry) * dirn / risk
                    rows.append(dict(sym=sym, day=str(day), dir=dirn, entry=entry, sl=sl, tp=tp, rr=abs(tp - entry) / risk,
                                     R=R - cost / risk, bias=bias.get(day, 0) * dirn))
        prev = (noon.high.max(), noon.low.min()) if len(noon) else prev
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = pd.concat([run(s, f, u) for s, (f, u) in SETS.items()], ignore_index=True)
    df.to_csv(HERE / "out" / "t26_liquidity_pockets.csv", index=False)
    P = [("2015-18", "2015", "2019"), ("2019-22", "2019", "2023"), ("2023-26", "2023", "2027")]
    for lab, g0 in (("alle", df), ("met dag-bias", df[df.bias == 1]), ("tegen dag-bias", df[df.bias == -1])):
        out, pool = [], []
        for p, a, b in P:
            x = g0[(g0.day >= a) & (g0.day < b)].R
            pool.append(x)
            out.append(f"{p} n{len(x):4d} {x.mean():+.3f}R PF {pf(x):.2f} win {(x > 0).mean()*100:.0f}%")
        x = pd.concat(pool)
        print(f"{lab:16} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f} | mediane RR {g0.rr.median():.2f}")
    print("\nper instrument:", df.groupby("sym").R.agg(["size", "mean"]).round(3).to_dict("index"))
