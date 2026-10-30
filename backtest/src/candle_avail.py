"""When is a stored candle COMPLETE, i.e. when would MT5 return it from copy_rates_from_pos(..., 1, ...)?

The CSVs in data/ohlcv do not share one time-stamp convention (checked 2026-10-28, see docs/AUDIT_PLAN.md):
  * most series are stamped at the bar's OPEN (forex D1/W1/H4 at server midnight 21:00/22:00 UTC,
    metals/indices/crypto at 00:00 UTC, oil/UK100 MN at server midnight);
  * the forex MN series are stamped with the LAST DAY of the month at 00:00 and hold the D1 bars whose
    open stamp falls in that UTC month (so the June bar ends with the server day of 1 July).
A single "stamp + duration" rule is therefore wrong: on the forex MN it hid every completed month for a
further month (the rule used from 2026-10-27 to 2026-10-28).

complete_times(times, tf, d1_times) gives, per row, the earliest moment the bar is complete:
  * open-stamped: the next bar's open (exact across weekends, DST and month lengths), capped by
    open + nominal duration;
  * month-end-labelled MN: the open of the first D1 bar stamped on/after the day after the label
    (= the close of the last D1 bar inside that month).
Duplicate rows (several series hold every row twice) are handled: "next bar" is the next DIFFERENT stamp.
"""
import pandas as pd

NOMINAL = {
    "M15": pd.Timedelta(minutes=15), "H1": pd.Timedelta(hours=1), "H4": pd.Timedelta(hours=4),
    "D1": pd.Timedelta(hours=24), "W1": pd.Timedelta(days=7), "MN": pd.Timedelta(days=31),
}


def is_month_end_labelled(times: pd.Series) -> bool:
    t = times[times >= pd.Timestamp("2005-01-01", tz=times.dt.tz)] if len(times) > 24 else times
    if t.empty:
        return False
    midnight = ((t.dt.hour == 0) & (t.dt.minute == 0)).all()
    return bool(midnight and ((t + pd.Timedelta(days=1)).dt.day == 1).mean() > 0.95)


def complete_times(times: pd.Series, tf: str, d1_times: pd.Series = None) -> pd.Series:
    nominal = NOMINAL.get(tf)
    if nominal is None or times.empty:
        return times
    uniq = times.drop_duplicates().sort_values().reset_index(drop=True)
    if tf == "MN" and is_month_end_labelled(times):
        if d1_times is not None and not d1_times.empty:
            d1 = d1_times.drop_duplicates().sort_values().reset_index(drop=True)
            probe = uniq + pd.Timedelta(days=1)
            idx = d1.searchsorted(probe, side="left")
            done = pd.Series([d1.iloc[i] if i < len(d1) else p + pd.Timedelta(days=1)
                              for i, p in zip(idx, probe)])
        else:
            done = uniq + pd.Timedelta(days=2)  # no D1 to look at: the safe side
    else:
        nxt = uniq.shift(-1)
        cap = uniq + nominal
        done = nxt.where(nxt.notna() & (nxt < cap), cap)
    done = pd.Series(pd.DatetimeIndex(done), index=uniq.index)
    pos = uniq.searchsorted(times)
    return pd.Series(done.iloc[pos].values, index=times.index, dtype=done.dtype)


def filter_completed(sim, df, symbol, tf, end_ts):
    """Rows of df (a slice of sim._load_data(symbol, tf)) that MT5 would have closed by end_ts.
    Shared by the current simulator and the unpacked old versions (audit), so all are judged alike."""
    if df.empty or tf not in NOMINAL or tf == "M15":
        return df
    cache = sim.__dict__.setdefault("_done_cache", {})
    done = cache.get((symbol, tf))
    if done is None:
        full = sim._load_data(symbol, tf)
        times = full["time"] if full["time"].dt.tz is not None else full["time"].dt.tz_localize("UTC")
        d1 = None
        if tf == "MN":
            d = sim._load_data(symbol, "D1")
            if d is not None and not d.empty:
                d1 = d["time"] if d["time"].dt.tz is not None else d["time"].dt.tz_localize("UTC")
        done = complete_times(times, tf, d1)
        cache[(symbol, tf)] = done
    return df[done.reindex(df.index) <= end_ts]
