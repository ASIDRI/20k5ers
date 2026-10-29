"""VectorVest-style trend for forex: Relative Timing (RT) and a market-timing stand-in (currency strength).

    python research/strategy/rt.py            # test 15: the pre-registered rules (docs/STRATEGY_FROM_VIDEOS.md)

VectorVest's RT and MTI formulas are not public; this is an approximation, on completed daily/weekly candles only:
- rt5 = close / close 5 trading days earlier (> 1 = up: "after 5 trading days the price is higher");
- rt = 3-day EMA of the geometric mean of close / close n days earlier, n = 5, 10, 20 (> 1 = up);
- rtw = the same on weekly candles, n = 1, 2, 4 weeks;
- mti: forex has no single market, so the market-timing part becomes currency strength: per currency the mean log rt
  over the 28 pairs of EUR GBP AUD NZD USD CAD CHF JPY (as base +, as quote -); for a pair, strength(base) -
  strength(quote) (> 0 = up);
- dew (Daily Early Warning, test 16): the currency strength turns in the trade direction today (mti higher than
  yesterday for a long) while rt5 already points that way.
All four are taken in the trade direction (+1 agrees, -1 against). A setup dated D uses the last candles completed
before D 00:00 UTC.
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402

CCY = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"]


def pairs():
    out = []
    for a, b in combinations(CCY, 2):
        for p in (a + b, b + a):
            try:
                load(p, "D1")
                out.append(p)
                break
            except IndexError:
                continue
    return out


def series(sym):
    d = load(sym, "D1")
    d["done"] = complete_times(d["time"], "D1")
    c = d.close
    gm = np.exp(sum(np.log(c / c.shift(n)) for n in (5, 10, 20)) / 3)
    d["rt5"] = c / c.shift(5)
    d["rt"] = gm.ewm(span=3, adjust=False).mean()
    w = load(sym, "W1")
    w["done"] = complete_times(w["time"], "W1")
    cw = w.close
    w["rtw"] = np.exp(sum(np.log(cw / cw.shift(n)) for n in (1, 2, 4)) / 3)
    d = pd.merge_asof(d.sort_values("done"), w[["done", "rtw"]].sort_values("done"), on="done")
    return d[["time", "done", "close", "rt5", "rt", "rtw"]]


def table():
    """Daily table per pair with rt5, rt, rtw and mti, indexed by completion time."""
    ps = pairs()
    s = {p: series(p) for p in ps}
    days = sorted(set().union(*[set(x.done) for x in s.values()]))
    idx = pd.DatetimeIndex(days)
    lr = pd.DataFrame({p: np.log(x.set_index("done").rt).reindex(idx).ffill() for p, x in s.items()})
    stren = pd.DataFrame(0.0, index=idx, columns=CCY)
    for p in ps:
        stren[p[:3]] += lr[p] / 7
        stren[p[3:]] -= lr[p] / 7
    out = {}
    for p, x in s.items():
        x = x.set_index("done").reindex(idx).ffill()
        x["mti"] = stren[p[:3]] - stren[p[3:]]
        x["dew"] = np.sign(x.mti.diff()) * (np.sign(x.mti.diff()) == np.sign(x.rt5 - 1))
        out[p] = x
    return out


def attach(trades, tab):
    """Add vv_rt5, vv_rt, vv_rtw, vv_mti (+1 / -1 in the trade direction, 0 unknown) to a trades table."""
    cols = {k: [] for k in ("vv_rt5", "vv_rt", "vv_rtw", "vv_mti", "vv_dew")}
    for _, t in trades.iterrows():
        x = tab.get(t.sym)
        k = -1 if x is None else int(x.index.searchsorted(pd.Timestamp(t.date, tz="UTC"))) - 1
        if k < 0:
            for v in cols.values():
                v.append(0)
            continue
        r = x.iloc[k]
        for name, val, ref in (("vv_rt5", r.rt5, 1), ("vv_rt", r.rt, 1), ("vv_rtw", r.rtw, 1), ("vv_mti", r.mti, 0),
                               ("vv_dew", r.dew, 0)):
            cols[name].append(0 if pd.isna(val) else int(np.sign(val - ref) * t.dir))
    return trades.assign(**cols)


def standalone_dew(tab):
    """DEW on its own: long the day after a dew up, short after a dew down, else flat; costs per change."""
    rows = []
    for p, x in tab.items():
        pos = x.dew.fillna(0)
        ret = x.close.pct_change().shift(-1)
        cost = cost_price(p) / x.close / 2 * pos.diff().abs().fillna(0)
        rows.append(pd.DataFrame({"sym": p, "pnl": pos * ret - cost, "pos": pos}, index=x.index))
    return pd.concat(rows)


def standalone(tab):
    """VectorVest-style on its own: long when rt5, rt, rtw and mti all point up, short when all down, else flat;
    the position is set at the daily close and held to the next close; costs on every change of position."""
    rows = []
    for p, x in tab.items():
        sig = np.sign(x.rt5 - 1) + np.sign(x.rt - 1) + np.sign(x.rtw - 1) + np.sign(x.mti)
        pos = pd.Series(np.where(sig == 4, 1, np.where(sig == -4, -1, 0)), index=x.index)
        ret = x.close.pct_change().shift(-1)  # next day's move
        cost = cost_price(p) / x.close / 2 * pos.diff().abs().fillna(0)  # half the round trip per side
        rows.append(pd.DataFrame({"sym": p, "pnl": pos * ret - cost, "pos": pos}, index=x.index))
    return pd.concat(rows)


if __name__ == "__main__":
    import t9_discover as T9
    import t13_discover as T13
    P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]
    tab = table()
    print(f"{len(tab)} paren")
    vv = "vv_rt5 == 1 & vv_rt == 1 & vv_rtw == 1 & vv_mti == 1"
    for lab, f, base, col in (("jouw setups (test 13, D1)", T13.load("D1"), "broke & pocket", "R_w_t1"),
                              ("video 9 (test 12)", T9.load("t12_"), "wk_ok & cont & hl", "R_f110_t27be")):
        f = attach(f.query(base).copy(), tab)
        print(f"\n### {lab}: {base}")
        for name, rule in (("zonder VV", "index == index"), ("met VV (alle 4 mee)", vv), ("met DEW mee", "vv_dew == 1")):
            out, pooled = [], []
            for p, a, b in P:
                x = f[(f.date >= a) & (f.date < b)].query(rule)[col].dropna()
                pooled.append(x)
                out.append(f"{p} {T13.cell(x)}")
            x = pd.concat(pooled)
            print(f"  {name:22} " + " | ".join(out) + f" | t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
        for c in ("vv_rt5", "vv_rt", "vv_rtw", "vv_mti", "vv_dew"):
            g = f.groupby(c)[col].mean().round(3).to_dict()
            print(f"  {c}: {g}")
    for lab, s in (("VectorVest-stijl op zich (alle 4 mee: long/short, anders vlak)", standalone(tab).dropna()),
                   ("DEW op zich (dag na het signaal)", standalone_dew(tab).dropna())):
        print(f"\n### {lab}, per dag, na kosten")
        for p, a, b in P:
            g = s[(s.index >= a) & (s.index < b)]
            daily = g.groupby(level=0).pnl.mean()
            print(f"  {p}: in de markt {g.pos.ne(0).mean()*100:.0f}% van de dagen, gem {daily.mean()*1e4:+.2f}bp/dag, "
                  f"per jaar {daily.mean()*252*100:+.2f}%, Sharpe {daily.mean()/daily.std()*np.sqrt(252):+.2f}")
