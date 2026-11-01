"""Which indicators separate winners and runners among the swing setups? (descriptive, 2026-10-31)

    python research/strategy/indicator_study.py t63_ t63x_
    python research/strategy/indicator_study.py --write t64 t63_ t63x_   # test 64: t64_ / t64x_ with rsi, poc_thru

For every filled setup of the test36b runs (`--stack` view: every setup, exact duplicates once) the indicators of the
daily candle BEFORE the fill (nothing from the fill day itself): RSI(14), MACD(12, 26, 9) histogram and its direction,
close vs SMA 50 / SMA 200 and the slope of SMA 200 (20 days), and the point of control of the leg (tick volume per
daily close, in 0.1-ATR bins from the leg start to the fill) - whether the entry lies within 0.3 ATR of it.
Everything in the trade direction (a short mirrors: RSI 100 - x, MACD and slopes negated).
Prints per bucket the number of setups, mean R_lad, win rate and runners (> 2R) on both sets.
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402


def indicators(d):
    c = d.close
    delta = c.diff()
    up, dn = delta.clip(lower=0).ewm(alpha=1 / 14).mean(), (-delta.clip(upper=0)).ewm(alpha=1 / 14).mean()
    rsi = 100 - 100 / (1 + up / dn)
    macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
    hist = macd - macd.ewm(span=9).mean()
    s50, s200 = c.rolling(50).mean(), c.rolling(200).mean()
    tr = np.maximum(d.high, c.shift()) - np.minimum(d.low, c.shift())
    atr = tr.rolling(14).mean()
    return pd.DataFrame(dict(rsi=rsi, mh=hist, mh_up=hist.diff(), c=c, s50=s50, s200=s200,
                             s200_slope=s200 - s200.shift(20), atr=atr))


def poc(d, a, b, atr):
    """Price with the most tick volume between daily candles a..b (closes binned at 0.1 ATR)."""
    w = d.iloc[a:b]
    if len(w) < 3 or not atr > 0:
        return np.nan
    bins = np.round(w.close.values / (0.1 * atr))
    vol = w.volume.values if "volume" in w else np.ones(len(w))
    s = pd.Series(vol).groupby(bins).sum()
    return float(s.idxmax() * 0.1 * atr)


def augment(prefix, out):
    """Every run file of `prefix` again as out/<out>..., with `rsi` and `poc_thru` (test 64)."""
    for path in sorted(glob.glob(str(HERE / "out" / f"{prefix}*.csv"))):
        f = pd.read_csv(path)
        f["rsi"], f["poc_thru"] = np.nan, False
        if len(f):
            d = load(f.sym.iloc[0], "D1").reset_index(drop=True)
            ind = indicators(d)
            t = d.time.dt.strftime("%Y-%m-%d").values
            for k, r in f[f.result == "gevuld"].iterrows():
                i = int(np.searchsorted(t, r.fill)) - 1
                if i < 1:
                    continue
                x = ind.iloc[i]
                p = poc(d, int(np.searchsorted(t, r.start_t)), i + 1, x.atr)
                f.loc[k, "rsi"] = x.rsi if r.dir == 1 else 100 - x.rsi
                f.loc[k, "poc_thru"] = bool(p == p and (r.entry - p) * r.dir < 0)
        f.to_csv(HERE / "out" / Path(path).name.replace(prefix, out, 1), index=False)


def table(prefix):
    f = pd.concat([pd.read_csv(p) for p in glob.glob(str(HERE / "out" / f"{prefix}*.csv"))])
    f = f[(f.result == "gevuld") & f.R_lad.notna()].drop_duplicates(["sym", "dir", "fill", "entry"]).reset_index(drop=True)
    rows = []
    for sym, g in f.groupby("sym"):
        d = load(sym, "D1").reset_index(drop=True)
        ind = indicators(d)
        t = d.time.dt.strftime("%Y-%m-%d").values
        for _, r in g.iterrows():
            i = int(np.searchsorted(t, r.fill)) - 1  # the candle before the fill
            if i < 200:
                continue
            x = ind.iloc[i]
            s = r.dir
            a = int(np.searchsorted(t, r.start_t))
            p = poc(d, a, i + 1, x.atr)
            rows.append(dict(R=r.R_lad, date=r.date, fib=r.entry_fib,
                             kern=bool(((r.ms_trend == 1) | (r.mt_done == -1)) & (not r.m_block) & (r.entry_fib >= 0.66)), rsi=x.rsi if s == 1 else 100 - x.rsi, hist=x.mh * s,
                             hist_up=x.mh_up * s, above50=(x.c - x.s50) * s > 0, above200=(x.c - x.s200) * s > 0,
                             s200_up=x.s200_slope * s > 0, ma_order=((x.s50 - x.s200) * s > 0),
                             poc_near=abs(r.entry - p) <= 0.3 * x.atr if p == p else np.nan,
                             poc_below=(r.entry - p) * s >= 0 if p == p else np.nan))
    o = pd.DataFrame(rows)
    o["rsi_b"] = pd.cut(o.rsi, [0, 30, 40, 50, 60, 100], labels=["<30", "30-40", "40-50", "50-60", ">60"]).astype(str)
    o["macd_hist"] = np.where(o["hist"] > 0, "boven 0 (mee)", "onder 0")
    o["macd_draait"] = np.where(o["hist_up"] > 0, "draait mee", "draait tegen")
    return o


def report(A, B, title, nmin):
    print(f"\n#### {title}: 37 n{len(A)} {A.R.mean():+.3f}R | holdout n{len(B)} {B.R.mean():+.3f}R")
    for ft in ("rsi_b", "macd_hist", "macd_draait", "above50", "above200", "s200_up", "ma_order", "poc_near", "poc_below"):
        print(f"\n## {ft}")
        for v in sorted(set(A[ft].map(str)) | set(B[ft].map(str))):
            a, b = A[A[ft].map(str) == v].R, B[B[ft].map(str) == v].R
            if len(a) < nmin or len(b) < nmin:
                continue
            print(f"  {v:16s} 37: n{len(a):5d} {a.mean():+.3f}R win {(a > 0).mean() * 100:3.0f}% run {(a > 2).mean() * 100:4.1f}%"
                  f" | hold: n{len(b):5d} {b.mean():+.3f}R win {(b > 0).mean() * 100:3.0f}% run {(b > 2).mean() * 100:4.1f}%")


if __name__ == "__main__":
    if sys.argv[1] == "--write":  # --write OUT PREFIX...
        for pre in sys.argv[3:]:
            augment(pre, sys.argv[2] + pre[len("t63"):])
        sys.exit()
    A, B = table(sys.argv[1]), table(sys.argv[2])
    report(A, B, "alle setups", 100)
    # does the indicator add anything beyond depth? only deep entries, and the core version (setting, no block, deep)
    report(A[A.fib >= 0.66], B[B.fib >= 0.66], "alleen diepe instap (fib >= 0,66)", 100)
    report(A[A.kern], B[B.kern], "kern: maand-setting, geen blokkade, diep", 40)
