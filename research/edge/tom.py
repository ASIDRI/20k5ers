"""Test X1 (docs/EDGE_SEARCH.md): turn-of-month in equity indices.

    python research/edge/tom.py

Buy at the close of trading day -2 of a month, sell at the close of trading day +3 of the next month (held on days
-1, +1, +2, +3). Trading days = daily candles Monday-Friday. Costs per symbol (test2.cost_price).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[0] / "strategy"), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from test2 import cost_price  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def tom(sym):
    d = load(sym, "D1")
    d = d[d.time.dt.dayofweek < 5].reset_index(drop=True)
    c = d.close.values
    day = d.time.dt.tz_convert(None) if d.time.dt.tz is not None else d.time
    # forex server-day candles open at 21/22 UTC: their trading day is the next calendar day
    date = (day + pd.Timedelta(hours=3)).dt.normalize() if (d.time.dt.hour >= 20).mean() > 0.5 else day.dt.normalize()
    ym = date.dt.year * 12 + date.dt.month
    last = (ym.shift(-1) != ym).values  # last trading day of its month (known from the calendar)
    # position in the month: -1 = last day, -2 = the one before; +1 = first day of the month, ...
    pos = np.zeros(len(d), int)
    first = (ym != ym.shift(1)).values
    k = 0
    for i in range(len(d)):
        k = 1 if first[i] else k + 1
        pos[i] = k
    rev = np.zeros(len(d), int)
    k = 0
    for i in range(len(d) - 1, -1, -1):
        k = 1 if last[i] else k + 1
        rev[i] = -k
    ret = pd.Series(c).pct_change().values
    is_tom = (rev == -1) | ((pos >= 1) & (pos <= 3))
    days = pd.DataFrame(dict(date=date.dt.strftime("%Y-%m-%d"), ret=ret, tom=is_tom))
    trades = []
    for i in np.nonzero(rev == -2)[0]:
        j = next((j for j in range(i + 1, min(i + 8, len(d))) if pos[j] == 3), None)
        if j is None:
            continue
        cost = cost_price(sym, c[i])
        trades.append(dict(date=str(date[i].date()), ret=(c[j] - c[i] - cost) / c[i], gross=(c[j] - c[i]) / c[i]))
    return days.iloc[1:], pd.DataFrame(trades)


def welch(a, b):
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def report(lab, days, trades):
    print(f"\n## {lab}")
    for p, s, e in P + [("2005-25", "2005", "2026")]:
        dd = days[(days.date >= s) & (days.date < e)]
        tt = trades[(trades.date >= s) & (trades.date < e)]
        if len(tt) < 5:
            continue
        a, b = dd[dd.tom].ret.dropna(), dd[~dd.tom].ret.dropna()
        share = a.sum() / dd.ret.sum() if dd.ret.sum() else np.nan
        print(f"  {p}: trades n{len(tt):3d} netto {tt.ret.mean()*100:+.3f}% (win {(tt.ret > 0).mean()*100:.0f}%, "
              f"t {tt.ret.mean() / tt.ret.std() * np.sqrt(len(tt)):.2f}) | dag TOM {a.mean()*100:+.3f}% vs rest "
              f"{b.mean()*100:+.3f}%, t {welch(a, b):.2f} | TOM-dagen {a.size / (a.size + b.size)*100:.0f}% van de dagen, "
              f"{share*100:.0f}% van het rendement")


if __name__ == "__main__":
    res = {s: tom(s) for s in ("SPX500USD", "NAS100USD")}
    # decisive: per trade the average of the two indices; per day both indices pooled
    t2 = res["SPX500USD"][1].merge(res["NAS100USD"][1], on="date", suffixes=("_s", "_n"))
    t2 = t2.assign(ret=(t2.ret_s + t2.ret_n) / 2)
    d2 = pd.concat([res["SPX500USD"][0], res["NAS100USD"][0]])
    report("BESLISSEND: SPX500 + NAS100", d2, t2)
    for s in ("SPX500USD", "NAS100USD", "UK100_USD", "XAUUSD", "EURUSD"):
        report(s, *(res[s] if s in res else tom(s)))
