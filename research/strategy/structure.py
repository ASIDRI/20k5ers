"""First cut of the video method (bullish side) on one series, for the visual: swings, KEY, BOS, fib, entry/SL/TP.
Swings are only used once confirmed (n bars later), so nothing here looks ahead."""
import pandas as pd

N_SWING, FORCE, FORCE_N = 2, 1.5, 10


def load(sym, tf):
    d = pd.read_csv(f"/home/user/20k5ers/data/ohlcv/{sym}_{tf}_2003_2025.csv", parse_dates=["time"])
    d.columns = [c.lower() for c in d.columns]
    return d.drop_duplicates("time").reset_index(drop=True)


def setups(d):
    n = N_SWING
    body = (d.close - d.open).abs()
    out = []
    highs, lows = [], []  # confirmed swing indices
    state = None
    for i in range(n * 2, len(d)):
        c = i - n  # candle confirmed as swing now
        if d.high[c] == d.high[c - n:c + n + 1].max():
            highs.append(c)
        if d.low[c] == d.low[c - n:c + n + 1].min():
            lows.append(c)
        if state is None:
            # bearish structure: last two highs and last two lows descending, last low after last high
            if len(highs) >= 2 and len(lows) >= 2 and d.high[highs[-1]] < d.high[highs[-2]] \
                    and d.low[lows[-1]] < d.low[lows[-2]] and lows[-1] > highs[-1]:
                key_i = highs[-1]
                key = max(d.open[key_i], d.close[key_i])  # KEY on the body
                avg = body[i - FORCE_N:i].mean()
                if d.close[i] > key and body[i] >= FORCE * avg and d.close[i] > d.open[i]:
                    ll_i = int(d.low[key_i:i + 1].idxmin())
                    state = dict(key_i=key_i, key=key, bos_i=i, ll_i=ll_i, ll=d.low[ll_i])
        elif "hi_i" not in state:
            if d.close[i] < state["ll"]:
                state = None
                continue
            nh = [h for h in highs if h >= state["bos_i"]]
            if nh:  # impulse high confirmed: draw the fib (1 = LL wick, 0 = high body)
                h = nh[0]
                state.update(hi_i=h, f0=max(d.open[h], d.close[h]), fib_i=i)
                rng = state["f0"] - state["ll"]
                state.update(entry=state["f0"] - 0.66 * rng, z1=state["f0"] - 0.618 * rng, z2=state["f0"] - 0.796 * rng,
                             sl=state["ll"], tp1=state["f0"] + 0.25 * rng, tp2=state["f0"] + 0.65 * rng, tp3=state["f0"] + rng)
        else:
            s = state
            if "fill_i" not in s:
                if d.close[i] < s["ll"]:
                    state = None
                    continue
                if d.high[i] > s["tp1"]:  # ran away without a pullback: no trade
                    out.append(dict(s, result="geen terugval"))
                    state = None
                    continue
                if d.low[i] <= s["entry"]:
                    s["fill_i"] = i
            if "fill_i" in s:
                if d.low[i] <= s["sl"]:
                    out.append(dict(s, exit_i=i, result="SL"))
                    state = None
                elif d.high[i] >= s["tp1"]:
                    out.append(dict(s, exit_i=i, result="TP1"))
                    state = None
    return out
