"""Which monthly/weekly trend definition fits the test 20 trades best? (descriptive; the trades are already known)

    python research/strategy/t20_trend.py

All filled test 20 setups (big daily legs, 34 instruments, 2005-2025). Per trade, known at the fill (completed
candles only), each +1 = with the trade, -1 = against, 0 = undecided:
  w_struct  weekly zigzag (2 ATR) higher highs and higher lows (= test 20's wk_struct)
  m_struct  the same on monthly candles
  w_ma      last weekly close above / below the mean of the last 10 weekly closes
  m_ma      last monthly close above / below the mean of the last 10 monthly closes
Each definition (and combinations) as a filter "with the trend", one position per direction per pair, three periods.
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load, Levels  # noqa: E402
from candle_avail import complete_times  # noqa: E402
import test5  # noqa: E402
from t17_eval import one_per_dir, pf  # noqa: E402

P = [("2005-14", "2005", "2015"), ("2015-20", "2015", "2021"), ("2021-25", "2021", "2026")]


def m_structure(sym):
    m = load(sym, "MN")
    m["done"] = complete_times(m["time"], "MN", load(sym, "D1")["time"])
    test5.REV, test5.LEG = 2.0, 4.0
    turns, _ = test5.legs(m)
    return (np.array([m["done"][ci].value for ci, *_ in turns]), np.array([k for *_, k in turns]),
            np.array([p for _, _, p, _ in turns]))


def struct_at(done, kind, px, ts):
    k = int(np.searchsorted(done, ts.value, side="right")) - 1
    hs, ls = px[:k + 1][kind[:k + 1] == "H"], px[:k + 1][kind[:k + 1] == "L"]
    if len(hs) < 2 or len(ls) < 2:
        return 0
    return 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)


if __name__ == "__main__":
    fs = [pd.read_csv(p) for p in glob.glob(str(HERE / "out" / "t20_*.csv")) + glob.glob(str(HERE / "out" / "t20x_*.csv"))
          if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[f.result == "gevuld"].reset_index(drop=True)
    cols = {k: [] for k in ("m_struct", "w_ma", "m_ma")}
    for sym, g in f.groupby("sym"):
        lv, ms = Levels(sym), m_structure(sym)
        for i, r in g.iterrows():
            ts = pd.Timestamp(r.fill, tz="UTC")
            cols["m_struct"].append((i, struct_at(*ms, ts) * r.dir))
            cols["w_ma"].append((i, lv.trend(ts, "W1") * r.dir))
            cols["m_ma"].append((i, lv.trend(ts, "MN") * r.dir))
    for k, v in cols.items():
        f[k] = pd.Series(dict(v))
    f["w_struct"] = f.wk_struct
    rules = {"geen trendfilter": "index == index",
             "weekstructuur (HH/HL)": "w_struct == 1",
             "maandstructuur (HH/HL)": "m_struct == 1",
             "week boven/onder 10-weeks gem.": "w_ma == 1",
             "maand boven/onder 10-maands gem.": "m_ma == 1",
             "week + maand gemiddelde eens": "w_ma == 1 & m_ma == 1",
             "week- en maandstructuur eens": "w_struct == 1 & m_struct == 1",
             "weekstructuur + maandgemiddelde": "w_struct == 1 & m_ma == 1",
             "tegen de maandtrend (gemiddelde)": "m_ma == -1"}
    pd.set_option("display.width", 220)
    for col in ("R_m_top_1", "R_t020"):
        print(f"\n### {col} (één positie per richting)")
        for lab, rule in rules.items():
            o = one_per_dir(f.query(rule), "t020")
            out, pool = [], []
            for p, a, b in P:
                x = o[(o.date >= a) & (o.date < b)][col].dropna()
                pool.append(x)
                out.append(f"{p} {x.mean():+.3f} (n{len(x)})")
            x = pd.concat(pool)
            print(f"  {lab:34} " + " | ".join(out) + f" | samen {x.mean():+.3f} PF {pf(x):.2f} t {x.mean() / x.std() * np.sqrt(len(x)):.2f}")
