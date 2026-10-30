"""Phase P1: map the character of EURUSD, AUDNZD, USDJPY before designing anything.

    python research/rnd/pair_diag.py

Per pair, separately for 2015-2020 (discovery) and 2021-2025 (confirmation), from M15 data (duplicates removed):
  1. trend or reversion: variance ratio VR(k) of returns on H1, H4 and D1 for k = 2, 5, 10, 20
     (VR > 1: moves continue; VR < 1: moves reverse) and the lag-1 autocorrelation;
  2. time effects: mean return per hour of the day (UTC) and per weekday, in basis points, with t-values;
  3. stretch: z-score of the close vs its 20-day mean and stdev, bucketed; mean return over the next 5 days;
  4. levels: share of touches of a monthly/weekly S/R level (sr_levels, point in time) that turn (move 1 daily ATR
     away from the level in the bounce direction before 1 ATR through it), against random prices at the same
     distance from the close (baseline).
Costs per pair in basis points are printed for comparison.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "strategy")]
from setup_study import Levels  # noqa: E402
import systematic as S  # noqa: E402

PAIRS = {"EURUSD": "EUR_USD", "AUDNZD": "AUD_NZD", "USDJPY": "USD_JPY"}
SPLIT = pd.Timestamp("2021-01-01", tz="UTC")


def m15(name):
    parts = []
    for f in sorted((HERE.parents[1] / "data" / "ohlcv").glob(f"{name}_M15_*.csv")):  # all files, merged
        m = pd.read_csv(f)
        m.columns = [c.lower() for c in m.columns]
        t = pd.to_datetime(m[[c for c in m.columns if c in ("time", "timestamp", "date", "datetime")][0]], utc=True)
        parts.append(m.assign(time=t)[["time", "open", "high", "low", "close"]])
    return pd.concat(parts).drop_duplicates("time").set_index("time").sort_index()


def resample(m, rule):
    shift = pd.Timedelta(hours=2) if rule == "1D" else pd.Timedelta(0)
    g = m.groupby((m.index + shift).floor(rule))
    d = pd.DataFrame(dict(open=g["open"].first(), high=g["high"].max(), low=g["low"].min(), close=g["close"].last(), n=g.size()))
    return d[d.n >= (20 if rule == "1D" else 2)]


def vr(r, k):
    r = r.dropna()
    v1 = r.var()
    rk = r.rolling(k).sum().dropna()
    return rk.var() / (k * v1) if v1 > 0 else np.nan


def halves(x):
    return {"15-20": x[x.index < SPLIT], "21-25": x[x.index >= SPLIT]}


def tstat(x):
    x = x.dropna()
    return x.mean() / (x.std() / np.sqrt(len(x))) if len(x) > 2 else np.nan


def main():
    for pair, name in PAIRS.items():
        m = m15(name)
        m = m[m.index >= pd.Timestamp("2015-01-01", tz="UTC")]
        price = m["close"].median()
        cost_bp = S.cost_frac(pair, price) * 2 * 1e4
        print(f"\n################ {pair}  (kosten heen en terug ±{cost_bp:.1f} bp)")
        frames = {"H1": resample(m, "1h"), "H4": resample(m, "4h"), "D1": resample(m, "1D")}
        print("1. trend of terugkeer: VR(k) [>1 doorlopen, <1 terugkeren] en autocorrelatie lag 1")
        for tf, d in frames.items():
            r = np.log(d["close"]).diff()
            for lab, x in halves(r).items():
                print(f"   {tf} {lab}: " + "  ".join(f"VR{k}={vr(x, k):.2f}" for k in (2, 5, 10, 20)) + f"  ac1={x.autocorr():+.3f}")
        print("2. tijd: gemiddelde per uur (UTC) in bp, alleen |t| >= 2.5 in een periode")
        h1 = frames["H1"]
        r = np.log(h1["close"] / h1["open"]) * 1e4
        for lab, x in halves(r).items():
            g = x.groupby(x.index.hour).agg(["mean", tstat])
            sig = g[g["tstat"].abs() >= 2.5]
            print(f"   {lab}: " + (", ".join(f"{h}u {row['mean']:+.2f}bp (t {row['tstat']:+.1f})" for h, row in sig.iterrows()) or "geen"))
        d1 = frames["D1"]
        rd = np.log(d1["close"]).diff() * 1e4
        for lab, x in halves(rd).items():
            g = x.groupby(x.index.dayofweek).agg(["mean", tstat]).dropna()
            print(f"   weekdag {lab}: " + ", ".join(f"{['ma','di','wo','do','vr','za','zo'][i]} {row['mean']:+.1f}bp (t {row['tstat']:+.1f})" for i, row in g.iterrows()))
        print("3. uitrekking: z-score van het slot t.o.v. het 20-dagengemiddelde -> rendement volgende 5 dagen (bp)")
        c = d1["close"]
        z = (c - c.rolling(20).mean()) / c.rolling(20).std()
        fwd = (np.log(c.shift(-5) / c) * 1e4)
        b = pd.cut(z, [-9, -2, -1, 1, 2, 9], labels=["<-2", "-2..-1", "-1..1", "1..2", ">2"])
        for lab, idx in (("15-20", z.index < SPLIT), ("21-25", z.index >= SPLIT)):
            g = fwd[idx].groupby(b[idx], observed=True).agg(["count", "mean", tstat])
            print(f"   {lab}: " + "  ".join(f"z {k}: n={int(r_['count'])} {r_['mean']:+.0f}bp (t {r_['tstat']:+.1f})" for k, r_ in g.iterrows()))
        print("4. S/R van maand/week: aandeel aanrakingen dat keert (1 ATR weg vóór 1 ATR door) vs willekeurige prijzen")
        lv = Levels(pair)
        hi, lo, cl = d1["high"].values, d1["low"].values, d1["close"].values
        atr = (d1["high"] - d1["low"]).rolling(14).mean().values
        rng = np.random.default_rng(3)
        for lab, (a0, a1) in (("15-20", (None, SPLIT)), ("21-25", (SPLIT, None))):
            hits, base = [], []
            for i in range(30, len(d1) - 30):
                t = d1.index[i]
                if (a0 is not None and t < a0) or (a1 is not None and t >= a1):
                    continue
                levs = [p for p, _ in lv.at(t)]
                A = atr[i]
                for p in levs + [cl[i - 1] + rng.uniform(-3, 3) * A]:
                    is_base = p not in levs
                    side = 1 if cl[i - 1] > p else -1  # approaching from above: support test (bounce up)
                    touched = (lo[i] <= p) if side == 1 else (hi[i] >= p)
                    if not touched or abs(cl[i - 1] - p) > 3 * A:
                        continue
                    out = None
                    for j in range(i + 1, min(i + 30, len(d1))):
                        if (side == 1 and lo[j] <= p - A) or (side == -1 and hi[j] >= p + A):
                            out = 0; break
                        if (side == 1 and hi[j] >= p + A) or (side == -1 and lo[j] <= p - A):
                            out = 1; break
                    if out is not None:
                        (base if is_base else hits).append(out)
            print(f"   {lab}: niveau keert {np.mean(hits)*100:.1f}% (n={len(hits)}) | willekeurige prijs {np.mean(base)*100:.1f}% (n={len(base)})")


if __name__ == "__main__":
    main()
