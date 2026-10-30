"""Profile of the trader's own daily trades against the engine's candidates: where do they differ?

    python research/strategy/trader_profile.py

The trader's daily example trades (fib levels read off the screenshots) are located in the data (leg start = the
extreme in the search window, leg end = the opposite extreme after it, fill = the first touch of the entry after the
end). The same features are computed for every filled engine setup of test 19/23 (out/t23d_*.csv: legs that broke
structure, entry on the daily rejection candle) and test 20 (out/t20_*.csv, out/t20x_*.csv: big legs). For each
feature the table shows the trader's values and where they fall among the engine's setups (percentile).
Data: stored candles + Yahoo daily up to yesterday (research/strategy/out/live_data) for the trader's pairs.
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import setup_study  # noqa: E402
from candle_avail import complete_times  # noqa: E402
import test5  # noqa: E402

LIVE = HERE / "out" / "live_data"
# name, symbol, direction, fib 1, fib 0, entry, search window for the leg (from, to)
TRADER = [
    ("EURUSD long jun-25", "EURUSD", 1, 1.1395, 1.1625, 1.14765, "2025-05-25", "2025-06-13"),
    ("EURAUD short dec-25", "EURAUD", -1, 1.7905, 1.7465, 1.77675, "2025-11-15", "2025-12-10"),
    ("GBPAUD short nov-25", "GBPAUD", -1, 2.0720, 1.9990, 2.04388, "2025-10-15", "2025-11-14"),
    ("NZDCAD long okt-23", "NZDCAD", 1, 0.7965, 0.8215, 0.80537, "2023-09-10", "2023-10-11"),
    ("NZDCAD short feb-24", "NZDCAD", -1, 0.8385, 0.8150, 0.83129, "2023-12-20", "2024-02-06"),
    ("NZDCAD long jun-24", "NZDCAD", 1, 0.8085, 0.8515, 0.82460, "2024-04-10", "2024-06-12"),
    ("NZDCAD long feb-25", "NZDCAD", 1, 0.8010, 0.8205, 0.80770, "2025-01-05", "2025-01-30"),
    ("GBPNZD long mrt-26", "GBPNZD", 1, 2.2475, 2.2670, 2.25600, "2026-03-03", "2026-03-12"),
    ("GBPNZD long aug-26", "GBPNZD", 1, 2.2466, 2.3555, 2.28456, "2026-05-20", "2026-07-08"),
]
FEATS = ["leg_atr", "leg_bars", "pb_bars", "time_ratio", "leg_speed", "entry_fib", "start_lvl_atr", "zone_lvl",
         "bos", "prior_move", "m_ma", "w_ma", "w_struct", "leg_vs_range"]


class Sym:
    """Everything needed for the features of one symbol (live-extended data when present)."""

    def __init__(self, sym):
        setup_study.DATA = LIVE if list(LIVE.glob(f"{sym}_D1_*.csv")) else HERE.parents[1] / "data" / "ohlcv"
        d = setup_study.load(sym, "D1")
        self.t = d.time.values
        self.o, self.h, self.l, self.c = (d[k].values for k in ("open", "high", "low", "close"))
        tr = np.r_[self.h[0] - self.l[0], np.maximum(self.h[1:], self.c[:-1]) - np.minimum(self.l[1:], self.c[:-1])]
        self.atr = pd.Series(tr).rolling(14).mean().bfill().values
        self.lv = setup_study.Levels(sym)
        w = setup_study.load(sym, "W1")
        w["done"] = complete_times(w["time"], "W1")
        test5.REV, test5.LEG = 2.0, 4.0
        wt, _ = test5.legs(w)
        self.wd = np.array([w["done"][ci].value for ci, *_ in wt])
        self.wk = np.array([k for *_, k in wt])
        self.wp = np.array([p for _, _, p, _ in wt])
        setup_study.DATA = HERE.parents[1] / "data" / "ohlcv"

    def idx(self, day):
        return int(np.searchsorted(self.t, np.datetime64(pd.Timestamp(day).tz_localize(None))))

    def features(self, dirn, f1, f0, entry, i_s, i_e, i_f):
        rng = abs(f0 - f1)
        a = self.atr[i_e]
        ts = pd.Timestamp(self.t[i_f]).tz_localize("UTC")
        levs = [p for p, _ in self.lv.at(ts)]
        band = sorted([f0 - dirn * 0.5 * rng, f0 - dirn * 0.886 * rng])
        k = int(np.searchsorted(self.wd, ts.value, side="right")) - 1
        hs, ls = self.wp[:k + 1][self.wk[:k + 1] == "H"], self.wp[:k + 1][self.wk[:k + 1] == "L"]
        T = 0
        if len(hs) >= 2 and len(ls) >= 2:
            T = 1 if hs[-1] > hs[-2] and ls[-1] > ls[-2] else (-1 if hs[-1] < hs[-2] and ls[-1] < ls[-2] else 0)
        before = slice(max(i_s - 40, 0), i_s)
        prior_ext = self.h[before].max() if dirn == 1 else self.l[before].min()
        rng60 = self.h[max(i_e - 120, 0):i_e + 1].max() - self.l[max(i_e - 120, 0):i_e + 1].min()
        leg_bars = max(i_e - i_s, 1)
        return dict(leg_atr=rng / a, leg_bars=leg_bars, pb_bars=i_f - i_e, time_ratio=(i_f - i_e) / leg_bars,
                    leg_speed=rng / a / leg_bars, entry_fib=(f0 - entry) * dirn / rng,
                    start_lvl_atr=min((abs(p - f1) for p in levs), default=np.nan) / a,
                    zone_lvl=any(band[0] <= p <= band[1] for p in levs),
                    bos=bool((f0 - prior_ext) * dirn > 0),
                    prior_move=(self.c[i_s] - self.c[max(i_s - 60, 0)]) * dirn / a,
                    m_ma=self.lv.trend(ts, "MN") * dirn, w_ma=self.lv.trend(ts, "W1") * dirn, w_struct=T * dirn,
                    leg_vs_range=rng / rng60 if rng60 > 0 else np.nan)


def trader_rows():
    rows, cache = [], {}
    for name, sym, dirn, f1, f0, entry, w0, w1 in TRADER:
        S = cache.setdefault(sym, Sym(sym))
        a, b = S.idx(w0), S.idx(w1)
        if dirn == 1:
            i_s = a + int(np.argmin(S.l[a:b + 1]))
            i_e = i_s + int(np.argmax(S.h[i_s:b + 1]))
        else:
            i_s = a + int(np.argmax(S.h[a:b + 1]))
            i_e = i_s + int(np.argmin(S.l[i_s:b + 1]))
        hit = np.where((S.l[i_e + 1:] <= entry) if dirn == 1 else (S.h[i_e + 1:] >= entry))[0]
        if not len(hit):
            continue
        i_f = i_e + 1 + int(hit[0])
        r = dict(trade=name, sym=sym, start=str(S.t[i_s])[:10], end=str(S.t[i_e])[:10], fill=str(S.t[i_f])[:10])
        r.update(S.features(dirn, f1, f0, entry, i_s, i_e, i_f))
        rows.append(r)
    return pd.DataFrame(rows)


def engine_rows(pattern, label):
    fs = [pd.read_csv(p) for p in glob.glob(str(HERE / "out" / pattern)) if Path(p).stat().st_size > 1]
    f = pd.concat(fs)
    f = f[(f.result == "gevuld") & f.R_t020.notna()]
    rows = []
    for sym, g in f.groupby("sym"):
        S = Sym(sym)
        for _, r in g.iterrows():
            i_s, i_e, i_f = S.idx(r.start_t), S.idx(r.top_t), S.idx(r.fill)
            if not (i_s < i_e < i_f):
                continue
            x = S.features(r.dir, r.b1, r.top, r.entry, i_s, i_e, i_f)
            x.update(sym=sym, date=r.date, R=r.R_t020, src=label)
            rows.append(x)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tr = trader_rows()
    pd.set_option("display.width", 250)
    print("JOUW TRADES\n" + tr.round(2).to_string(index=False))
    eng = pd.concat([engine_rows("t23d_*.csv", "t23"), engine_rows("t20_*.csv", "t20")], ignore_index=True)
    eng.to_csv(HERE / "out" / "profile_engine.csv", index=False)
    tr.to_csv(HERE / "out" / "profile_trader.csv", index=False)
    print(f"\nMOTOR: {len(eng)} setups (t23: {(eng.src == 't23').sum()}, t20: {(eng.src == 't20').sum()})")
    print("\nper kenmerk: jouw waarden -> percentiel binnen de motor-setups")
    for c in FEATS:
        col = eng[c].astype(float)
        pct = [round((col < v).mean() * 100) for v in tr[c].astype(float)]
        print(f"  {c:14} jij {list(tr[c].astype(float).round(2))}  -> percentiel {pct}  "
              f"(motor mediaan {col.median():.2f})")
