"""Engine trades on recent data: the stored candles extended with Yahoo Finance daily candles up to yesterday.

    python research/strategy/live_setups.py GBPNZD --from 2026-02-11 [--engine test19|test18]

Stored D1/W1/MN files run to mid-December 2025. Yahoo daily FX candles (GBPNZD=X) are appended from the first day
after the stored data, stamped like the stored ones (22:00 UTC the evening before the trading day); weekly and
monthly candles for the new period are built from them. Today's unfinished candle is left out. Yahoo's FX candles
can differ a little from the broker's (wicks, the hour the day closes), so levels may be a few pips off.
The extended files go to the scratch directory given by --data (default: research/strategy/out/live_data) and the
engine reads them instead of data/ohlcv.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
import setup_study  # noqa: E402


def yahoo_daily(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}=X?range=2y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    day = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("Europe/London").normalize().tz_localize(None)
    y = pd.DataFrame({"day": day, "open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"]}).dropna()
    y = y[y.day < pd.Timestamp.now().normalize()]  # today's candle is not finished
    return y.drop_duplicates("day", keep="last")


def extend(sym, out):
    out.mkdir(parents=True, exist_ok=True)
    d1 = setup_study.load(sym, "D1")
    last_day = (d1.time.iloc[-1] + pd.Timedelta(hours=2)).tz_localize(None).normalize()
    y = yahoo_daily(sym)
    y = y[y.day > last_day]
    y = y[y.day.dt.dayofweek < 5]
    new = pd.DataFrame({"time": (y.day - pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": y.open, "high": y.high, "low": y.low, "close": y.close, "volume": 0})
    old = d1.assign(time=d1.time.dt.strftime("%Y-%m-%d %H:%M:%S"))[["time", "open", "high", "low", "close"]]
    old["volume"] = 0
    full = pd.concat([old, new], ignore_index=True)
    full.to_csv(out / f"{sym}_D1_live.csv", index=False)
    nd = new.assign(t=pd.to_datetime(new.time, utc=True))
    # weekly: continue the stored weekly stamps in steps of 7 days
    w = setup_study.load(sym, "W1")
    stamps = [w.time.iloc[-1] + pd.Timedelta(days=7 * k) for k in range(1, 60)]
    rows = []
    for s in stamps:
        g = nd[(nd.t >= s) & (nd.t < s + pd.Timedelta(days=7))]
        if len(g):
            rows.append(dict(time=s.strftime("%Y-%m-%d %H:%M:%S"), open=g.open.iloc[0], high=g.high.max(),
                             low=g.low.min(), close=g.close.iloc[-1], volume=0))
    wold = w.assign(time=w.time.dt.strftime("%Y-%m-%d %H:%M:%S"))[["time", "open", "high", "low", "close"]]
    wold["volume"] = 0
    pd.concat([wold, pd.DataFrame(rows)], ignore_index=True).to_csv(out / f"{sym}_W1_live.csv", index=False)
    # monthly: labelled at the month end, like the stored file
    m = setup_study.load(sym, "MN")
    nd["month"] = (nd.t + pd.Timedelta(hours=2)).dt.tz_localize(None).dt.to_period("M")
    rows = []
    for per, g in nd.groupby("month"):
        if per.to_timestamp(how="end") <= m.time.iloc[-1].tz_localize(None):
            continue
        rows.append(dict(time=str(per.to_timestamp(how="end").date()), open=g.open.iloc[0], high=g.high.max(),
                         low=g.low.min(), close=g.close.iloc[-1], volume=0))
    mold = m.assign(time=m.time.dt.strftime("%Y-%m-%d"))[["time", "open", "high", "low", "close"]]
    mold["volume"] = 0
    pd.concat([mold, pd.DataFrame(rows)], ignore_index=True).to_csv(out / f"{sym}_MN_live.csv", index=False)
    extend_h4(sym, out)
    return str(new.time.iloc[0])[:10], str(new.time.iloc[-1])[:10], len(new)


def extend_h4(sym, out):
    """4-hour candles from Yahoo 1-hour candles, in the stored 4-hour blocks (22, 2, 6, 10, 14, 18 UTC)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}=X?range=730d&interval=60m"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    y = pd.DataFrame({"t": pd.to_datetime(r["timestamp"], unit="s", utc=True), "open": q["open"], "high": q["high"],
                      "low": q["low"], "close": q["close"]}).dropna()
    y = y[y.t < pd.Timestamp.now(tz="UTC").floor("h") - pd.Timedelta(hours=1)]
    y["blk"] = (y.t - pd.Timedelta(hours=2)).dt.floor("4h") + pd.Timedelta(hours=2)
    g = y.groupby("blk").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    h4 = setup_study.load(sym, "H4")
    g = g[g.index > h4.time.iloc[-1]]
    new = pd.DataFrame({"time": g.index.strftime("%Y-%m-%d %H:%M:%S"), "open": g.open, "high": g.high, "low": g.low,
                        "close": g.close, "volume": 0})
    old = h4.assign(time=h4.time.dt.strftime("%Y-%m-%d %H:%M:%S"))[["time", "open", "high", "low", "close"]]
    old["volume"] = 0
    pd.concat([old, new], ignore_index=True).to_csv(out / f"{sym}_H4_live.csv", index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sym")
    ap.add_argument("--from", dest="start", default="2026-02-11")
    ap.add_argument("--engine", default="test19", choices=["test19", "test18"])
    ap.add_argument("--data", default=str(HERE / "out" / "live_data"))
    a = ap.parse_args()
    out = Path(a.data)
    first, last, n = extend(a.sym, out)
    print(f"Yahoo-candles toegevoegd: {n} dagen, {first} t/m {last}")
    setup_study.DATA = out
    eng = __import__(a.engine)
    eng.load = setup_study.load
    df = eng.run(a.sym, "D1", a.start, "2027-01-01")
    cols = ["dir", "start_t", "top_t", "b1", "top", "result", "fill", "entry", "sl", "R_t020", "R_t027", "R_t065",
            "R_m_0.2_top_1.0"]
    df = df[[c for c in cols if c in df]]
    df.to_csv(HERE / "out" / f"live_{a.engine}_{a.sym}.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.round(5).to_string(index=False))
