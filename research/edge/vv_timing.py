"""Test V1 (docs/EDGE_SEARCH.md): VectorVest market timing (DEW, Primary Wave, Two-Week Rule) on equity indices.

    python research/edge/vv_timing.py

Daily after the close (closed candles); the position holds from that close to the next. Costs per position change.
DEW: Up when close > 30-day weighted MA and DPO(20) > 0; Down when close < WMA and DPO < 0; else the state stays.
DPO(n) = close n/2+1 days ago - SMA(n) now.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[0] / "strategy"), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def wma(c, n):
    w = np.arange(1, n + 1, dtype=float)
    return c.rolling(n).apply(lambda x: (x * w).sum() / w.sum(), raw=True)


def hold(up, dn):
    """+1 after an Up signal, -1 after a Down signal, kept until the opposite one."""
    s = pd.Series(np.where(up, 1.0, np.where(dn, -1.0, np.nan)), index=up.index)
    return s.ffill().fillna(0.0)


def signals(sym):
    d = load(sym, "D1")
    d = d[d.time.dt.dayofweek < 5].reset_index(drop=True)
    c = d.close
    dew = hold((c > wma(c, 30)) & ((c.shift(11) - c.rolling(20).mean()) > 0),
               (c < wma(c, 30)) & ((c.shift(11) - c.rolling(20).mean()) < 0))
    pw = np.sign(c - c.shift(5)).replace(0, np.nan).ffill().fillna(0)
    # Two-Week Rule on completed weekly candles, mapped to the daily candle at whose close the week is known
    w = load(sym, "W1")
    w["done"] = complete_times(w.time, "W1")
    wc = w.close
    up2, dn2 = (wc > wc.shift(1)) & (wc.shift(1) > wc.shift(2)), (wc < wc.shift(1)) & (wc.shift(1) < wc.shift(2))
    tw = hold(up2, dn2)
    dd = complete_times(d.time, "D1")
    k = np.searchsorted(w.done.values, dd.values, side="right") - 1
    tw_d = pd.Series(np.where(k >= 0, tw.values[np.clip(k, 0, None)], 0.0))
    ret = c.pct_change().shift(-1).fillna(0)  # return from this close to the next
    cost = np.array([cost_price(sym, x) for x in c]) / 2 / c.values  # one side, fraction of price
    date = d.time.dt.strftime("%Y-%m-%d")
    out = {"kopen en houden": pd.Series(1.0, index=c.index)}
    for name, pos in (("DEW", dew), ("Primary Wave", pw), ("Two-Week Rule", tw_d)):
        out[f"{name} long-only"] = pos.clip(lower=0)
        out[f"{name} long/short"] = pos
    res = {}
    for name, pos in out.items():
        r = pos * ret - pos.diff().abs().fillna(pos.abs()) * cost
        res[name] = pd.Series(r.values, index=date.values)
    return res


def stats(r):
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    ann = (1 + r).prod() ** (252 / len(r)) - 1 if len(r) else np.nan
    vol = r.std() * np.sqrt(252)
    return ann, vol, (r.mean() * 252) / vol if vol else np.nan, dd


def show(lab, res):
    print(f"\n## {lab}")
    for name, r in res.items():
        cells = []
        for p, s, e in P:
            x = r[(r.index >= s) & (r.index < e)]
            if len(x) < 100:
                cells.append(f"{p}      -")
                continue
            a, v, sh, dd = stats(x)
            cells.append(f"{p} {a*100:+5.1f}%/j Sharpe {sh:+.2f} maxDD {dd*100:5.1f}%")
        print(f"  {name:26} " + " | ".join(cells))


if __name__ == "__main__":
    spx, nas = signals("SPX500USD"), signals("NAS100USD")
    both = {k: pd.concat([spx[k], nas[k]], axis=1).mean(axis=1) for k in spx}
    show("BESLISSEND: gemiddelde van SPX500 en NAS100", both)
    for s in ("SPX500USD", "NAS100USD", "UK100_USD", "XAUUSD"):
        show(s, signals(s) if s not in ("SPX500USD", "NAS100USD") else (spx if s == "SPX500USD" else nas))
