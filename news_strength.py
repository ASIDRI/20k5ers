"""
Fundamental news score per currency and per pair, 0 to 2 (1 = neutral, above 1 = favourable), from the MT5
economic calendar.

    python news_strength.py [CSV] [--at 2025-06-01]     # prints the score of every currency and of the main pairs

Data: deploy/mql5/ExportCalendar.mq5 writes the MT5 calendar (actual, forecast, previous, importance, impact) to
<MT5 Common data folder>/Files/mt5_calendar.csv; copy it to data/calendar/mt5_calendar.csv (or pass the path).

Score (the trader's idea, 2026-10-30): per release with an actual and a forecast the surprise = actual - forecast,
scaled per indicator by the spread of its earlier surprises (z, at most 3, only after 6 earlier releases); its sign
comes from MT5's own impact field (positive / negative for the currency, so a higher unemployment rate counts against
it); weighted by importance (high 3, moderate 1) and summed over the last 6 weeks. Currency score = 1 + tanh(sum / 6),
so 0 to 2. Pair score = 1 + (score of the base - score of the quote) / 2: EURUSD above 1 when the euro news beats the
dollar news. A side that is not a currency (XAU, an index, BTC) counts as neutral (1).
Point in time: only releases up to the moment asked about.
"""
import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT = Path(__file__).resolve().parent / "data" / "calendar" / "mt5_calendar.csv"
WEIGHT = {"high": 3.0, "moderate": 1.0}
WINDOW = pd.Timedelta(days=42)
CCY = ("USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD")


def load(path=DEFAULT):
    """The export with UTC times and the signed, weighted surprise of each release (column `s`)."""
    f = pd.read_csv(path)
    f["time"] = (pd.to_datetime(f.time_server, format="%Y.%m.%d %H:%M")
                 - pd.to_timedelta(f.server_utc_offset_s, unit="s")).dt.tz_localize("UTC")
    f = f[f.actual.notna() & f.forecast.notna() & f.importance.isin(list(WEIGHT))].sort_values("time")
    raw = f.actual - f.forecast
    # spread of the earlier surprises of the same indicator (expanding, excluding this release)
    scale = raw.abs().groupby(f.event_id).transform(lambda x: x.shift(1).expanding(6).mean())
    z = (raw.abs() / scale.replace(0, np.nan)).clip(upper=3)
    sign = f.impact.map({"positive": 1.0, "negative": -1.0}).fillna(0.0)
    f["s"] = (z * sign * f.importance.map(WEIGHT)).fillna(0.0)
    return f[["time", "currency", "event", "importance", "actual", "forecast", "impact", "s"]].reset_index(drop=True)


class NewsScore:
    def __init__(self, path=DEFAULT):
        self.f = load(path)
        self.by = {c: g[["time", "s"]].reset_index(drop=True) for c, g in self.f.groupby("currency")}

    def currency(self, ccy, ts):
        """0..2 for `ccy` at UTC time `ts` (releases in the 6 weeks up to ts); 1 when there are none."""
        g = self.by.get(ccy)
        if g is None:
            return 1.0
        t = g.time.values
        a = np.searchsorted(t, np.datetime64((ts - WINDOW).tz_convert(None)), side="right")
        b = np.searchsorted(t, np.datetime64(ts.tz_convert(None)), side="right")
        return 1.0 + math.tanh(float(g.s.values[a:b].sum()) / 6.0)

    def pair(self, sym, ts):
        """0..2 for buying `sym` (base vs quote currency); a non-currency side counts as neutral."""
        u = sym.replace("_", "").upper()
        base, quote = u[:3], u[3:6]
        sb = self.currency(base, ts) if base in CCY else 1.0
        sq = self.currency(quote, ts) if quote in CCY else 1.0
        return min(2.0, max(0.0, 1.0 + (sb - sq) / 2.0))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=str(DEFAULT))
    ap.add_argument("--at", default=None)
    a = ap.parse_args()
    ns = NewsScore(a.csv)
    ts = pd.Timestamp(a.at, tz="UTC") if a.at else pd.Timestamp.now(tz="UTC")
    print(f"{len(ns.f)} releases with actual and forecast, {ns.f.time.min().date()} - {ns.f.time.max().date()}")
    print("valuta:", "  ".join(f"{c} {ns.currency(c, ts):.2f}" for c in CCY))
    for p in ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURGBP", "XAUUSD"):
        print(f"{p} {ns.pair(p, ts):.2f}")
