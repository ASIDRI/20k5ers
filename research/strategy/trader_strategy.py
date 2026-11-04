"""Strategy v2: the trader's top-down method as documented step by step in docs/SETUPS_TRADER.md (setups 1-10).

    python research/strategy/trader_strategy.py EURUSD [SYM ...] [--from 2018-05-01] [--to 2020-04-01] [--prefix v2_] [-v]

The previous engine (swing setups, tests 36-64) is archived in research/strategy/archive/strategy_v1_test36b.py.

LOOK-AHEAD RULE (after the setup-4 error of 2026-11-04): after EVERY change run
    python research/strategy/v2_guard.py            (and --all before a result is reported)
It cuts the data at random days and checks that every trade is known on its entry day and that no trade is skipped
because of later data. Every setup must decide in date order: a trade may only block trades that come AFTER it
(collect candidates first, sort by entry day, then apply the blocking). Results of study scripts that do not run
through this engine are not reported as results until the setup is built here and the guard passes.

Everything is written for a short and mirrored for a long (the long runs on negated prices). Point in time: a weekly
candle is used only after it has closed, a daily decision is taken at the daily close.

1. Weekly structure (setup 5 / 10 criteria): major weekly swings = zigzag with a reversal of W_REV weekly ATR. Bearish
   BoS = a weekly body close at least W_BREAK ATR below the body-low of the last major swing low AND below that swing's
   wick (BREAK_WICK; this replaced the efficiency filter W_ER, which could not tell the fake BoS of June 2019 from the
   real one of 1 June 2020); confirmed when the next week does not close back above the line (acceptance). The structure stays bearish until a confirmed bullish BoS (mirrored).
2. Weekly trigger in a bearish structure: a bearish engulfing week, body over body (open >= previous close minus
   ENG_TOL weekly ATR, close below the previous green open); or (setup 4) a close below the open of a
   green week two back after a small-bodied week (default on, --no-eng2). After a trade a new trigger week is needed,
   starting after the trade has closed; a trigger stays armed until it gives a trade. The first trigger after a weekly
   BoS needs no daily BoS: its fib starts at the highest body of the trigger week, and only the weekly BoS line it
   retests (body-low of the last weekly fractal swing low broken before the trigger week) and the daily S/R levels
   within FLIP_BAND daily ATR of it count (setup 1: 1.17503 and 1.17273).
3. Daily: daily swings = zigzag with a reversal of D_REV daily ATR. Daily BoS = the first daily close below the
   body-low of the last daily swing low, from the start of the trigger week on. Fib 1 = the highest body between that
   swing low and the BoS candle; fib 0 = the lowest low since (moves down with new lows; fib 1 is kept while no
   trade came, setup 6). A daily close above fib 1 voids the fib (new BoS needed).
4. Entry: a daily S/R level inside fib ZONE (wick reactions in the last SR_LB days within SR_TOL daily ATR: a sell =
   a high at the level with the body below, a bounce = a low at the level with the body above; >= SR_MIN reactions,
   at least one of each). At least REJ_N rejection wicks at the level in the last REJ_BACK days (high at or above the
   level, close below, upper wick >= the tolerance) with at least one bearish candle, and no daily close above the
   level (plus the tolerance) in that window; entry close >= MIN_DEPTH deep.
   The day's high reaches the level, the close is below it, and a bearish pattern: shooting
   star / doji / inverted hammer (upper wick >= STAR_WICK x body and >= 40% of the range), a bearish engulfing (body
   over body), or a bearish candle after a day that tested the level and closed below it (tweezer). Entry at the close.
5. Stop: entry depth >= DEEP -> above the swing-high wick; else above max(fib 0.796, the pattern's high); plus
   SL_BUF daily ATR.
6. Monthly S/R (lesson 1 method, research/strategy/sr_levels.py: wick taps from both sides) from ALL monthly candles
   closed so far, redrawn every MN_REFRESH months (1 January / 1 July). For now context only: logged, and per trade
   the next monthly level in the trade direction (m_sr_next) and whether one lies before T2 (m_sr_before_t2).
7. Management (setup 6): T1 = fib -0.2 (50%), stop then a little in profit (entry - BE daily ATR); T2 = fib -0.58
   (20%), stop then to fib 0; T3 = fib -1 (15%), stop then to -0.5; T4 = fib -1.618 (15%) (setup 13). R_5050: 50% at T1, 50% at T2 (stop after T1 a
   little in profit). A bar that reaches the stop and a target counts as the stop. Costs from test2.cost_price.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "backtest" / "src")]
from setup_study import load  # noqa: E402
from candle_avail import complete_times  # noqa: E402
from test2 import cost_price  # noqa: E402
import sr_levels as sr_mod  # noqa: E402  (the monthly S/R method of lesson 1)

W_REV, W_BREAK, W_ER, ENG_TOL = 1.5, 0.25, 0.0, 0.05
STRUCT_SWINGS = True  # a weekly swing counts for the structure only after the move from it made a BoS (setup 14)
EQ_TOL = 0.1  # weekly ATR: two weekly extremes this close are equal highs / lows
BREAK_WICK = True  # the BoS close must also be beyond the swing wick (replaces the efficiency filter, 2026-11-01)
WEEK_OPEN_PREV_CLOSE = True  # weekly open = previous weekly close, as on the trader's FOREXCOM charts
D_REV = 1.5
ZONE = (0.45, 1.0)
SR_LB, SR_TOL, SR_MIN = 250, 0.1, 3
TOUCH_TOL = 0.1  # daily ATR: how close a wick must come to the level at entry
STAR_WICK = 1.5
SL_BUF, DEEP, BE = 0.1, 0.66, 0.1
BEST_ONLY = False  # only the strongest daily S/R level inside the fib zone
NO_CLOSE_ABOVE = True  # no daily close above the level during the test (setup 1, 26 Jun 2018)
REJ_N, REJ_BACK = 2, 5  # at least REJ_N daily rejection wicks at the level in the last REJ_BACK days (setups 1-4, 6, 7)
BOS_CLUSTER = "confirm"  # daily BoS: "confirm" (breaks count from the swing's confirmation), "cluster", "old"
REARM = True  # a newer weekly trigger replaces an armed one that has no active fib
BOS_TRIGGER = True  # the confirmed weekly BoS arms the first trade itself (setup 11)
FLIP_BAND = 0.35  # daily ATR around the weekly break line: the levels of the first trade after a weekly BoS (setup 1)
MIN_DEPTH = 0.25  # entry close at least this deep in the fib (the trader's entries: 0.31 - 0.83)
T1, T2, T3 = 0.2, 0.58, 1.0
# (fib extension, part closed there, stop afterwards: "be" = a little in profit, or a fib level) - the trader:
# 50% at -0.2 (stop a little in profit), a part at -0.58 (stop to fib 0), a part at -1 (stop to -0.5, setup 13),
# the rest at -1.618 (TP4, setup 13)
TARGETS = ((T1, 0.5, "be"), (T2, 0.2, 0.0), (T3, 0.15, 0.5), (1.618, 0.15, 0.5))
MN_TOL, MN_MIN_EACH, MN_SEP, MN_REFRESH = 0.15, 2, 0.75, 6  # monthly S/R (wick taps both sides), redrawn every 6 months
FAKE_TRIGGER = False  # the week that closes back after a fake counter-trend weekly BoS is a trigger (trader 2026-11-04)
# Rules per ticker (trader 2026-11-04): EURUSD stays on version C; the other instruments without the wick rule and with
# the fake-BoS trigger (37 instruments: +98.5R, t 2.1). run_view applies the profile of its symbol.
USE_PROFILES = True
PROFILES = {"EURUSD": dict(BREAK_WICK=True, FAKE_TRIGGER=False, FAKE_RETEST=False, REVERT_WEEKS=6, REVERT_CONFIRM="wma",
                       PULLBACK_FIB=True, PB_LEFT=1, PB_MIN=0.8, LQD=True, LQD_CTX="both", LQD_FIB=False)}
DEFAULT_PROFILE = dict(BREAK_WICK=False, FAKE_TRIGGER=True, FAKE_RETEST=True, REVERT_WEEKS=6, REVERT_CONFIRM="wma",
                       PULLBACK_FIB=False, LQD=False, LQD_CTX="trend", LQD_FIB=True)
REVERT_WEEKS = 0  # a confirmed weekly BoS is undone by a weekly close back over its line within this many weeks (0: off)
REVERT_CONFIRM = None  # None / "wma" (close vs weekly WMA 10) / "dpo" (weekly DPO 10) / "rsi" (weekly RSI 14 vs 50):
# the undo also needs this indicator to point back to the old trend
REVERT_TOL = 0.0  # ... by at least this many weekly ATR
LQD = False  # setup 4: daily liquidity grab, entry at the close of the grab candle (daily_lq)
LQD_N, LQD_GAP, LQD_LOOK, LQD_BUF, LQD_TGT, LQD_CTX = 2, 3, 60, 0.5, 3.0, "trend"
LQD_SR = True  # setup 4 only with a daily S/R at the grabbed high (within 0.25 daily ATR)
LQD_FIB = False  # setup 4 exits with the fib ladder (TARGETS) on the leg grab high -> low since H2
LQD_LADDER = None  # setup 4 exits: ((R level, part, new stop in R or None), ...); None = all at LQD_TGT
LQ_GRAB = False  # setup 3: liquidity grab of a lower weekly swing high, no weekly BoS needed (lq_triggers)
LQ_GAP1, LQ_GAP2, LQ_LOOK, LQ_MAXW, LQ_RED, LQ_WEEKS = 3, 3, 52, 52, 3, 6
LQ_ENTRY_LEVEL = None  # setup 3 exact: entry candle wicks to >= this fib depth and closes below it, star / engulfing,
# no daily S/R needed (None: the normal daily-S/R entry)
LQ_TAPS = 1  # weeks that trade above H2 and close below it, up to and including the red week ("3 week tap")
LQ_STOP_HI = False  # setup 3: stop always above the swing-high wick of the fib (+ SL_BUF ATR)
LQ_TARGETS = None  # setup 3: own target ladder (None: TARGETS)
FAKE_RETEST = False  # setup 2: retest of the line after a fake weekly BoS (fake_retest)
RT_AWAY, RT_TOUCH, RT_WEEKS, RT_SL = 1.0, 0.25, 10, 1.0


def apply_profile(sym):
    globals().update(PROFILES.get(sym, DEFAULT_PROFILE))


DEW_FILTER = None  # None / "both" / "wma" / "dpo": daily trend at the entry close, close vs WMA 30 and DPO 20 vs 0
DEW_WMA, DEW_DPO = 30, 20
MONTHLY_FILTER = False  # no trade against the monthly structure (trader 2026-11-04, GBPJPY)
VOID_SPENT = True  # a weekly trigger whose fib was voided (close beyond fib 1) is used up (engine short 21 May 2020)
FRACTAL_FIB = False  # tested, worse (6/9 trades, +7R): fib 1 moves to the newest 3-candle swing after the daily BoS once price makes a new extreme (setup 14)
SWING_LEFT = 3  # the swing on the BoS candle goes beyond the previous SWING_LEFT candles (setup 14: 3 days; setup 2: 1)
TWEEZER_ANY = False  # setup 14: the second test may be either colour if it has a wick through the level and closes back
PULLBACK_FIB = False  # fib 1 from the last swing (higher low) after the extreme of the leg, before the BoS (setup 15)
ATR_REF = None  # daily ATR of the current view (set by run_view, used by start_fib)
PB_MIN = 0.0  # minimum size of that pullback in daily ATR
PB_LEFT = 1  # that swing is at least as extreme as the PB_LEFT candles before it
LAST_SWING_FIB = False  # False / True / "bos": only when the swing is the BoS candle itself; fib 1 from the last 3-candle swing before / at the BoS candle (setup 14)
ENG2 = True  # --no-eng2 to switch off (setup 4: close below the open of a green week two back, after a small week)


def atr(h, l, c, n=14):
    pc = np.r_[c[0], c[:-1]]
    return pd.Series(np.maximum(h, pc) - np.minimum(l, pc)).rolling(n, min_periods=1).mean().values


def zigzag(h, l, a, rev):
    """[(extreme index, +1 high / -1 low, index at which it is confirmed)]: a turn of rev x ATR from the extreme."""
    out, mode, hi, lo = [], 0, 0, 0
    for i in range(1, len(h)):
        if mode == 0:
            if h[i] > h[hi]:
                hi = i
            if l[i] < l[lo]:
                lo = i
            if hi < i and h[hi] - l[i] >= rev * a[i]:
                out.append((hi, 1, i)); mode, lo = -1, i
            elif lo < i and h[i] - l[lo] >= rev * a[i]:
                out.append((lo, -1, i)); mode, hi = 1, i
        elif mode == 1:
            if h[i] >= h[hi]:
                hi = i
            elif h[hi] - l[i] >= rev * a[i]:
                out.append((hi, 1, i)); mode, lo = -1, i
        else:
            if l[i] <= l[lo]:
                lo = i
            elif h[i] - l[lo] >= rev * a[i]:
                out.append((lo, -1, i)); mode, hi = 1, i
    return out


def weekly_structure(o, h, l, c):
    """State after each completed week in this (short) view: -1 bearish, +1 bullish, 0 unknown; and BoS events."""
    a = atr(h, l, c)
    mv = pd.Series(np.abs(np.diff(c, prepend=c[0])))
    er = (np.abs(c - np.r_[np.full(10, np.nan), c[:-10]]) / mv.rolling(10).sum().values)
    sw = zigzag(h, l, a, W_REV)
    state, s, pend, events, p = np.zeros(len(c), int), 0, None, [], 0
    conf = np.zeros(len(c))  # direction the indicator of REVERT_CONFIRM points to (+1 / -1) at the close of week i
    if REVERT_CONFIRM == "wma":
        wts = np.arange(1, 11, dtype=float)
        ind = c - np.r_[np.full(9, np.nan), np.convolve(c, wts[::-1] / wts.sum(), "valid")]
        conf = np.sign(np.nan_to_num(ind))
    elif REVERT_CONFIRM == "dpo":
        sm = pd.Series(c).rolling(10).mean().values
        conf = np.sign(np.nan_to_num(c - np.r_[np.full(6, np.nan), sm[:-6]]))
    elif REVERT_CONFIRM == "rsi":
        dc = np.diff(c, prepend=c[0])
        up = pd.Series(np.maximum(dc, 0)).ewm(alpha=1 / 14).mean().values
        dn = pd.Series(np.maximum(-dc, 0)).ewm(alpha=1 / 14).mean().values
        conf = np.sign(100 - 100 / (1 + up / np.maximum(dn, 1e-12)) - 50)
    live = None  # the last confirmed BoS while it can still be undone (REVERT_WEEKS)
    fakes = []  # (attempt week, week that closed back, direction of the attempt, line): a fake weekly BoS
    last = {1: None, -1: None}
    prev = {1: None, -1: None}  # last confirmed swing of each kind (valid or not)
    waiting = []  # (swing index, kind, level the move from it must take out) - swings that have not made a BoS yet
    for i in range(len(c)):
        while p < len(sw) and sw[p][2] <= i:
            k_, kind, _ = sw[p]; p += 1
            if not STRUCT_SWINGS:
                last[kind] = k_
            else:  # the trader (setup 14): a swing low counts only once the move from it made a higher high (a BoS)
                ref = prev[-kind]  # the previous opposite swing; a low needs a high above it, a high a low below it
                # ... unless that previous swing was an equal high / equal low (two weeks in a row at the same
                # extreme): a strong turn (2020: equal lows 16 / 23 March, so the high of 30 March counts)
                eq = ref is not None and any(
                    0 <= j < len(c) and j != ref and abs((l[j] - l[ref]) if kind == 1 else (h[j] - h[ref])) <= EQ_TOL * a[ref]
                    for j in (ref - 1, ref + 1))
                if ref is None or eq:
                    last[kind] = k_
                else:
                    waiting.append((k_, kind, h[ref] if kind == -1 else l[ref]))
            prev[kind] = k_
        if STRUCT_SWINGS:
            for item in list(waiting):
                k_, kind, lvl = item
                if (kind == -1 and np.max(h[k_:i + 1]) > lvl) or (kind == 1 and np.min(l[k_:i + 1]) < lvl):
                    if last[kind] is None or k_ > last[kind]:
                        last[kind] = k_
                    waiting.remove(item)
        if live is not None:  # a confirmed BoS closes back over its line within REVERT_WEEKS weeks: undone (NQ 2026)
            d0, line0, i00, ic, old_s = live
            if i - ic > REVERT_WEEKS or s != d0:
                live = None
            elif (line0 - c[i]) * d0 > REVERT_TOL * a[i] and (not REVERT_CONFIRM or conf[i] * old_s > 0):
                s, live = old_s, None
                fakes.append((i00, i, d0, line0))
                state[i] = s
                continue
        if pend is not None:
            d, line, i0 = pend
            if (c[i] - line) * d > 0:
                old_s = s
                s = d; events.append((i0, i, d, line))
                if REVERT_WEEKS:
                    live = (d, line, i0, i, old_s)
            else:
                fakes.append((i0, i, d, line))
            pend = None
        else:
            for d, k in ((-1, last[-1]), (1, last[1])):
                if s == d or k is None:
                    continue
                line = min(o[k], c[k]) if d == -1 else max(o[k], c[k])
                wick = l[k] if d == -1 else h[k]
                if ((c[i] - line) * d > W_BREAK * a[i] and er[i] >= W_ER
                        and (not BREAK_WICK or (c[i] - wick) * d > 0)):
                    pend = (d, line, i)
                    break
        state[i] = s
    return state, events, a, fakes


def day_label(t):
    """Trading day of a daily candle (stamped 21:00 / 22:00 UTC the evening before)."""
    return str((pd.Timestamp(t) + pd.Timedelta(hours=3)).date())


def week_label(t):
    """Monday of a weekly candle (stamped Friday 21:00 / 22:00 UTC before the week)."""
    return str((pd.Timestamp(t) + pd.Timedelta(hours=3) + pd.Timedelta(days=2)).date())


def weekly_triggers(o, h, l, c, a, state):
    """Bearish trigger weeks in a bearish structure: (index, kind)."""
    out = []
    for j in range(2, len(c)):
        if state[j] != -1 or c[j] >= o[j]:
            continue
        # FOREXCOM opens the week at the previous close (trader 2026-11-01: week of 14 Jan 2019 open = previous close
        # 1.14685; 24 Sep 2018 open 1.17492); our data's weekly open is the first quote after the weekend gap.
        # So the open condition is checked against the previous close, with ENG_TOL for brokers that gap.
        wopen = c[j - 1] if WEEK_OPEN_PREV_CLOSE else o[j]
        if c[j - 1] > o[j - 1] and wopen >= c[j - 1] - ENG_TOL * a[j] and c[j] < o[j - 1]:
            out.append((j, "engulfing"))
        elif (ENG2 and c[j - 2] > o[j - 2] and abs(c[j - 1] - o[j - 1]) <= 0.3 * (h[j - 1] - l[j - 1])
              and c[j] < o[j - 2]):
            out.append((j, "engulfing 2 weken terug"))
    return out


def sr_levels(o, h, l, c, tol, k):
    """Daily S/R levels known at the close of day k-1: [(price, reactions)], strongest first, >= 2 x tol apart.
    A sell = a high at the level (within tol) with the body below; a bounce = a low at the level with the body above."""
    s = max(0, k - SR_LB)
    H, L = h[s:k], l[s:k]
    bt, bb = np.maximum(o[s:k], c[s:k]), np.minimum(o[s:k], c[s:k])
    cand = np.unique(np.r_[H, L])
    sells = ((np.abs(H[None, :] - cand[:, None]) <= tol) & (bt[None, :] < cand[:, None])).sum(1)
    buys = ((np.abs(L[None, :] - cand[:, None]) <= tol) & (bb[None, :] > cand[:, None])).sum(1)
    ok = (sells >= 1) & (buys >= 1) & (sells + buys >= SR_MIN)
    lv, score = cand[ok], (sells + buys)[ok]
    keep = []
    for i in np.argsort(-score, kind="stable"):
        if all(abs(lv[i] - q) > 2 * tol for q, _ in keep):
            keep.append((float(lv[i]), int(score[i])))
    return keep


def pattern(o, h, l, c, k, p, tol, etol):
    body, up, rg = abs(c[k] - o[k]), h[k] - max(o[k], c[k]), h[k] - l[k]
    if rg > 0 and up >= STAR_WICK * body and up >= 0.4 * rg:
        return "shooting star / doji"
    if c[k] < o[k] and c[k - 1] > o[k - 1] and o[k] >= c[k - 1] - etol and c[k] < o[k - 1]:
        return "bearish engulfing"
    if (c[k] < o[k] or (TWEEZER_ANY and up >= tol)) and h[k - 1] >= p - tol and c[k - 1] < p:
        return "tweezer / bearish na test"
    return None


def manage(h, l, k, entry, sl, f0, rng, be):
    """Exits from the day after the entry (in the short view). Ladder TARGETS: (fib extension, part closed, where the
    stop goes after it). A bar that reaches the stop and a target counts as the stop. Also the 50/50 variant
    (50% at T1, 50% at T2, stop a little in profit after T1). Returns R parts in price units and the indices."""
    res = {"t1_i": None, "t2_i": None, "exit_i": None}
    stop, left, pnl, step = sl, 1.0, 0.0, 0
    t1, t2 = f0 - T1 * rng, f0 - T2 * rng
    stop5, open5, pnl5, got1 = sl, True, 0.0, False
    for i in range(k + 1, len(h)):
        if open5:
            if h[i] >= stop5:
                pnl5 += (0.5 if got1 else 1.0) * (entry - stop5); open5 = False
            elif got1 and l[i] <= t2:
                pnl5 += 0.5 * (entry - t2); open5 = False
            elif not got1 and l[i] <= t1:
                got1, pnl5, stop5 = True, pnl5 + 0.5 * (entry - t1), entry - be
        if h[i] >= stop:
            pnl += left * (entry - stop)
            res["exit_i"], left = i, 0.0
            break
        while step < len(TARGETS) and l[i] <= f0 - TARGETS[step][0] * rng:
            ext, part, new_stop = TARGETS[step]
            px = f0 - ext * rng
            part = min(part, left)
            pnl += part * (entry - px)
            left -= part
            stop = entry - be if new_stop == "be" else f0 - new_stop * rng
            res[{0: "t1_i", 1: "t2_i"}.get(step, f"t{step + 1}_i")] = i
            step += 1
        if left <= 1e-9:
            res["exit_i"] = i
            break
    res.update(pnl=pnl, pnl5=pnl5, open=res["exit_i"] is None, open5=open5)
    return res


def monthly_levels(m, mdone, t):
    """Monthly S/R levels from every monthly candle closed by t (all history, as MT5 has it)."""
    mm = m[mdone <= t]
    if len(mm) < 24:
        return []
    c = {k: mm[k].values.astype(float) for k in ("open", "high", "low", "close")}
    return sorted(p for p, _, _ in sr_mod.levels(c, tol_atr=MN_TOL, min_each=MN_MIN_EACH, max_levels=40,
                                                 sep_atr=MN_SEP))


def lq_triggers(o, h, l, c):
    """Setup 3 weeks (short view): a weekly swing high H1, at least LQ_GAP1 weeks later a lower swing high H2 (the
    liquidity), at least LQ_GAP2 weeks after H2 a week that trades above H2 but closes below it (the grab; no weekly
    close above H2 since H2, the high stays below H1), then within LQ_RED weeks a red week: the trigger.
    Returns (trigger week, grab week, H1, H2). Swing highs are weekly fractals (2 weeks each side), known 2 weeks on."""
    sh = [i for i in range(2, len(h) - 2) if h[i] == np.max(h[i - 2:i + 3])]
    out, used = [], set()
    for b_, i2 in enumerate(sh):
        prev = [i for i in sh[:b_] if i2 - i >= LQ_GAP1 and i2 - i <= LQ_LOOK and h[i] > h[i2]
                and np.max(h[i + 1:i2]) <= h[i]]
        if not prev:
            continue
        i1 = prev[-1]
        for g in range(i2 + max(LQ_GAP2, 3), min(len(c), i2 + LQ_MAXW)):
            if c[g - 1] > h[i2] or h[g - 1] >= h[i1]:  # broken (a close above) or above H1: no grab any more
                break
            if h[g] > h[i2] and c[g] < h[i2] and h[g] < h[i1]:
                for j in range(g, min(len(c), g + LQ_RED)):
                    if c[j] > h[i2]:
                        break
                    taps = sum(1 for q in range(g, j + 1) if h[q] > h[i2] and c[q] < h[i2])
                    if c[j] < o[j] and j not in used and taps >= LQ_TAPS:
                        out.append((j, g, i1, i2)); used.add(j)
                        break
                break
    return sorted(out)


def run_view(sym, d, w, dirn, start, end, log, m=None):
    """dirn -1: shorts on the real prices; +1: longs = shorts on negated prices."""
    if USE_PROFILES:  # the rules of this ticker
        apply_profile(sym)
    sgn = -1 if dirn == 1 else 1  # price transform for this view
    def px(df):
        o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
        return (o, h, l, c) if sgn == 1 else (-o, -l, -h, -c)
    wo, wh, wl, wc = px(w)
    state, events, wa, fakes = weekly_structure(wo, wh, wl, wc)
    trig = weekly_triggers(wo, wh, wl, wc, wa, state)
    if FAKE_TRIGGER:  # a fake counter-trend weekly BoS (the next week closed back) is a trigger for the trend (setup 6)
        have = {j for j, _ in trig}
        trig = sorted(trig + [(i1, "valse BoS") for i0, i1, dd, line in fakes
                              if dd == 1 and state[i1] == -1 and i1 not in have])
    wdone = complete_times(w["time"], "W1").values
    wstart = w["time"].values
    o, h, l, c = px(d)
    a = atr(h, l, c)
    global ATR_REF
    ATR_REF = a
    ddone = complete_times(d["time"], "D1").values
    dt = d["time"].values
    dsw = zigzag(h, l, a, D_REV)
    if DEW_FILTER:  # in this view a trade needs a bearish daily trend: close below the WMA, DPO below 0 (non-centred,
        wts = np.arange(1, DEW_WMA + 1, dtype=float)  # so no future candles: close minus the SMA of n/2+1 days ago)
        wma = np.r_[np.full(DEW_WMA - 1, np.nan), np.convolve(c, wts[::-1] / wts.sum(), "valid")]
        sma = pd.Series(c).rolling(DEW_DPO).mean().values
        dpo = c - np.r_[np.full(DEW_DPO // 2 + 1, np.nan), sma[:-(DEW_DPO // 2 + 1)]]
        dew_ok = {"both": (c < wma) & (dpo < 0), "wma": c < wma, "dpo": dpo < 0}[DEW_FILTER]
    lows = [(s, cf) for s, kind, cf in dsw if kind == -1]
    run_start = np.zeros(len(state), int)  # first week of the current structure state
    for i in range(1, len(state)):
        run_start[i] = run_start[i - 1] if state[i] == state[i - 1] else i
    if dirn == -1:  # the structure is the same in both views; log it once, in real terms
        for i0, i1, dd, line in events:
            if pd.Timestamp(start) - pd.Timedelta(days=400) <= pd.Timestamp(wstart[i1]) <= pd.Timestamp(end):
                log.append((week_label(wstart[i1]), f"{'bearish' if dd == -1 else 'bullish'} week-BoS bevestigd "
                            f"(lijn {line:.5f}, breukweek {week_label(wstart[i0])})", 0))
    trades, last_exit_t, armed, fib = [], np.datetime64("1900-01-01"), None, None
    k0 = int(np.searchsorted(dt, np.datetime64(pd.Timestamp(start).tz_localize(None)), "left"))
    k1 = int(np.searchsorted(dt, np.datetime64(pd.Timestamp(end).tz_localize(None)), "left"))
    k0 = max(k0, 30)

    mdone = complete_times(m["time"], "MN", d["time"]).values if m is not None else None
    mstate = weekly_structure(*px(m))[0] if (m is not None and MONTHLY_FILTER) else None  # monthly structure

    def against_month(k):  # the last completed month says the trend is the other way (GBPJPY 2024: weekly bearish
        if mstate is None:  # BoS inside a bullish monthly trend)
            return False
        mi = int(np.searchsorted(mdone, ddone[k], "right")) - 1
        return mi >= 0 and mstate[mi] == 1
    mlev, next_refresh = [], None

    def week_of(k):  # last completed week at the close of day k
        return int(np.searchsorted(wdone, ddone[k], "right")) - 1

    wlow = [i for i in range(2, len(wl) - 2) if wl[i] == min(wl[i - 2:i + 3])]  # weekly fractal swing lows

    def weekly_break_line(j):
        """The weekly BoS line the trigger week retests: body-low of the last weekly fractal swing low that a weekly
        close broke BEFORE week j, and that week j's high reached again (setup 1: Dec 2017, 1.17503)."""
        for i in reversed([i for i in wlow if i + 2 < j]):
            line = min(wo[i], wc[i])
            if np.any(wc[i + 1:j] < line) and wh[j] >= line:
                return float(line)
        return None

    def find_bos(ka, kb):
        """Latest first close below the body-low of the last confirmed daily swing low, ka <= day <= kb."""
        best = None
        for k in range(ka, kb + 1):
            sl_ = [(s, cf) for s, cf in lows if cf <= k - 1]
            if not sl_:
                continue
            s, cf = sl_[-1]
            # the BoS line: the lowest body around the swing low (setup 13: the trader's line 1.18627 is the close two
            # days after the swing's wick); a break counts from the moment the swing is confirmed
            if BOS_CLUSTER == "cluster":
                line = float(np.min(np.minimum(o[max(0, s - 2):min(s + 3, k)], c[max(0, s - 2):min(s + 3, k)])))
                fresh = not np.any(c[cf:k] < line)
            elif BOS_CLUSTER == "confirm":  # body of the swing candle; a close beyond it before the swing was
                line = min(o[s], c[s])  # confirmed does not count (setup 13: 23 Oct 2020)
                fresh = not np.any(c[cf:k] < line)
            else:
                line = min(o[s], c[s])
                fresh = not np.any(c[s + 1:k] < line)
            if c[k] < line and fresh:
                best = (k, s, line)
        return best

    def try_entry(k, fd, trig_label, band=None):
        """Entry check at the close of day k for the fib fd; band = (line, close) of the weekly BoS for the first
        trade after it (setup 11), else the fib zone (and the weekly break line of setup 1). Returns the trade."""
        nonlocal last_exit_t
        f0, f1 = fd["f0"], fd["f1"]
        rng = f1 - f0
        if k <= fd["bos"] or rng <= 0 or (MONTHLY_FILTER and against_month(k)) or (DEW_FILTER and not dew_ok[k]):
            return None
        tol = TOUCH_TOL * a[k - 1]  # the wick test at entry
        lv = sr_levels(o, h, l, c, SR_TOL * a[k - 1], k)
        if fd.get("virtual") is not None:  # setup 3 exact: a level at this fib depth instead of a daily S/R
            inzone = [(f0 + fd["virtual"] * rng, 0)]
        elif band is not None:  # first trade after a weekly BoS: daily S/R between the BoS line and the BoS-week close
            blo, bhi = min(band), max(band)
            inzone = [(p, n) for p, n in lv if blo - tol <= p <= bhi + tol and f0 < p < f1]
        else:
            zlo, zhi = f0 + ZONE[0] * rng, f0 + ZONE[1] * rng
            inzone = [(p, n) for p, n in lv if zlo - tol <= p <= zhi + tol]
            if fd.get("flip") and f0 <= fd["flip"] <= f1:  # first trigger after a weekly BoS: only the levels that
                fl = fd["flip"]  # belong to the break (setup 1); a break line outside the fib does not restrict
                inzone = [(fl, 0)] + [(p, n) for p, n in inzone if abs(p - fl) <= FLIP_BAND * a[k - 1]]
        for p, n in (inzone[:1] if BEST_ONLY else inzone):
            if h[k] < p - tol or c[k] >= p:
                continue
            pat = pattern(o, h, l, c, k, p, tol, ENG_TOL * a[k - 1])
            if not pat:
                continue
            back = range(max(fd["bos"] + 1, k - REJ_BACK + 1), k + 1)
            if fd.get("virtual") is None:
                rej = [i for i in back if h[i] >= p - tol and c[i] < p and h[i] - max(o[i], c[i]) >= tol]
                if len(rej) < REJ_N or not any(c[i] < o[i] for i in back if h[i] >= p - tol):
                    continue
                if NO_CLOSE_ABOVE and any(c[i] > p + tol for i in back):  # the level must hold: bodies stay below
                    continue
            elif pat.startswith("tweezer"):  # setup 3 exact: one candle, shooting star or engulfing
                continue
            entry = c[k]
            depth = (entry - f0) / rng
            if depth < MIN_DEPTH or (h[k] - f0) / rng < ZONE[0]:  # the entry candle's wick reaches the zone (>= 0.45;
                continue  # the trader's entries: 0.48 - 0.99; the engine's 17 Jun 2020 entry reached only 0.41)
            sl = (fd["hi"] if depth >= DEEP else max(f0 + 0.796 * rng, h[k], h[k - 1])) + SL_BUF * a[k]
            if sl <= entry:
                continue
            mres = manage(h, l, k, entry, sl, f0, rng, BE * a[k])
            risk = sl - entry
            cost = cost_price(sym, abs(entry))
            when = lambda i: day_label(dt[i]) if i is not None else ""  # noqa: E731
            if dirn == 1:  # the long runs on negated prices: name the pattern as it looks on the real chart
                pat = {"shooting star / doji": "hammer / doji", "bearish engulfing": "bullish engulfing",
                       "tweezer / bearish na test": "tweezer / bullish na test"}[pat]
            trades.append(dict(
                sym=sym, dir=dirn, trigger_week=trig_label, bos=day_label(dt[fd["bos"]]),
                fib1=f1 * sgn, fib0=f0 * sgn, level=p * sgn, entry_day=day_label(dt[k]),
                entry=entry * sgn, sl=sl * sgn, risk_pips=risk * (100 if "JPY" in sym else 10000),
                depth=round(depth, 2), pattern=pat, t1_day=when(mres["t1_i"]), t2_day=when(mres["t2_i"]),
                exit_day=when(mres["exit_i"]), open=mres["open"],
                R=round((mres["pnl"] - cost) / risk, 2), R_5050=round((mres["pnl5"] - cost) / risk, 2), entry_t=dt[k],
                m_sr_next=next((q for q in sorted(mlev, key=lambda q: -q * sgn) if q * sgn < entry), None),
                m_sr_before_t2=any(f0 - T2 * rng < q * sgn < entry for q in mlev),
                _k=k, _f0=f0, _rng=rng, _entry=entry, _hi=fd["hi"], _pat=max(h[k], h[k - 1]), _level=p,
                _band=fd.get("band"), _flip=fd.get("flip")))  # view-space fields for the stop study
            log.append((day_label(dt[k]), f"TRADE {pat} aan dag-S/R {p * sgn:.5f} ({n} reacties), instap {entry * sgn:.5f}, "
                        f"stop {sl * sgn:.5f}, diepte {depth:.2f} -> R {trades[-1]['R']:+.2f}", dirn))
            free = mres.get("t3_i") if mres.get("t3_i") is not None else mres["exit_i"]  # after T3 the runner no
            last_exit_t = dt[free] if free is not None else np.datetime64("2100-01-01")  # longer blocks new setups
            return trades[-1]
        return None

    bos_weeks = {i1: (i0, line) for i0, i1, dd, line in events if dd == -1}  # bearish (in this view) BoS confirmations
    fibB, done_bos, spent = None, set(), set()
    for k in range(k0, min(k1, len(c))):
        if m is not None and (next_refresh is None or pd.Timestamp(ddone[k]) >= next_refresh):
            mlev = monthly_levels(m, mdone, ddone[k])  # redrawn every MN_REFRESH months (1 Jan / 1 Jul)
            t = pd.Timestamp(ddone[k])
            mo = ((t.month - 1) // MN_REFRESH + 1) * MN_REFRESH + 1
            next_refresh = pd.Timestamp(year=t.year + (mo > 12), month=(mo - 1) % 12 + 1, day=1, tz=t.tz)
            if dirn == -1:
                log.append((day_label(dt[k]), "maand-S/R (her)tekend: " + ", ".join(f"{q:.5f}" for q in mlev), 0))
        wi = week_of(k)
        if wi < 0:
            continue
        if state[wi] != -1:
            if armed is not None:
                log.append((day_label(dt[k]), "structuur niet meer bearish: trigger vervalt", dirn))
            armed, fib, fibB = None, None, None
            continue
        if BOS_TRIGGER and wi in bos_weeks and wi not in done_bos:  # setup 11: the weekly BoS itself is the trigger
            done_bos.add(wi)
            i0, line = bos_weeks[wi]
            kb0 = int(np.searchsorted(dt, wstart[i0], "left"))  # first day of the break week
            hs = [sw_ for sw_, kind, cf in dsw if kind == 1 and cf < kb0]  # the swing the impulse started from
            if hs and dt[k] > last_exit_t and not any(
                    t["dir"] == dirn and t["entry_t"] >= wstart[run_start[wi]] for t in trades):
                sh = hs[-1]
                f1b = float(np.max(np.maximum(o[sh - 1:sh + 2], c[sh - 1:sh + 2])))  # highest body around the swing
                fibB = dict(bos=k, f1=f1b, hi=float(h[sh]), f0=float(np.min(l[sh:k + 1])), band=(line, wc[i0]))
                log.append((day_label(dt[k]), f"week-BoS als trigger (breukweek {week_label(wstart[i0])}): fib 1 = body "
                            f"vorige dag-swing {f1b * sgn:.5f}, niveaus tussen BoS-lijn {line * sgn:.5f} en slot "
                            f"BoS-week {wc[i0] * sgn:.5f}", dirn))
        if fibB is not None:
            if c[k] > fibB["f1"]:
                log.append((day_label(dt[k]), "BoS-trigger: slot voorbij fib 1, vervalt", dirn))
                fibB = None
            elif try_entry(k, fibB, "week-BoS " + week_label(wstart[wi]), band=fibB["band"]):
                armed, fib, fibB = None, None, None
                continue
            else:
                fibB["f0"] = min(fibB["f0"], l[k])
        if armed is None:
            cand = [j for j, kind in trig if run_start[wi] <= j <= wi and wstart[j] > last_exit_t and j not in spent]
            if cand:
                armed = cand[-1]
                kind = dict(trig)[armed]
                log.append((day_label(dt[k]), f"week-trigger {kind} (week {week_label(wstart[armed])})", dirn))
                ka = int(np.searchsorted(dt, wstart[armed], "left"))
                b = find_bos(ka, k)
                first = [j for j, kind in trig if run_start[wi] <= j <= wi][0] == armed and not any(
                    t["dir"] == dirn and t["entry_t"] >= wstart[run_start[wi]] for t in trades)
                if b:
                    fib = start_fib(b, o, h, l, c, k)
                    log.append((day_label(dt[b[0]]), f"daily BoS (lijn {b[2] * sgn:.5f}), fib 1 {fib['f1'] * sgn:.5f}", dirn))
                elif first:  # setup 1: the first trigger after the weekly BoS, the weekly BoS stands in for the daily
                    kb = int(np.searchsorted(dt, wdone[armed], "left")) - 1
                    top = ka + int(np.argmax(np.maximum(o[ka:kb + 1], c[ka:kb + 1])))
                    fib = dict(bos=kb, f1=float(max(o[top], c[top])), hi=float(np.max(h[ka:kb + 1])),
                               f0=float(np.min(l[top:k + 1])), line=None, flip=weekly_break_line(armed))
                    log.append((day_label(dt[k]), f"eerste trigger na de week-BoS: fib 1 = body swing high van de "
                                f"triggerweek {fib['f1'] * sgn:.5f}; niveaus rond de week-breuklijn "
                                f"{fib['flip'] * sgn if fib['flip'] else float('nan'):.5f}", dirn))
            continue
        if fib is None and REARM:  # a newer trigger week replaces an armed trigger that has no fib (setup 13)
            newer = [j for j, kind in trig if armed < j <= wi and j >= run_start[wi] and wstart[j] > last_exit_t]
            if newer:
                armed = newer[-1]
                log.append((day_label(dt[k]), f"nieuwe week-trigger {dict(trig)[armed]} (week {week_label(wstart[armed])})",
                            dirn))
                b = find_bos(int(np.searchsorted(dt, wstart[armed], "left")), k)
                if b:
                    fib = start_fib(b, o, h, l, c, k)
                    log.append((day_label(dt[b[0]]), f"daily BoS (lijn {b[2] * sgn:.5f}), fib 1 {fib['f1'] * sgn:.5f}", dirn))
                continue
        if fib is None:
            b = find_bos(k, k)
            if b:
                fib = start_fib(b, o, h, l, c, k)
                log.append((day_label(dt[k]), f"daily BoS (lijn {b[2] * sgn:.5f}), fib 1 {fib['f1'] * sgn:.5f}", dirn))
            continue
        if c[k] > fib["f1"]:
            log.append((day_label(dt[k]), f"slot boven fib 1 ({fib['f1'] * sgn:.5f}): fib vervalt", dirn))
            fib = None
            if VOID_SPENT:
                spent.add(armed)
                armed = None
            continue
        if FRACTAL_FIB:
            j = k - 1  # a 3-candle swing (in this view a high: higher than the candle before and after), confirmed today
            if j - 1 > fib["bos"] and h[j] > h[j - 1] and h[j] >= h[k]:
                fib["cand"] = j
            if fib.get("cand") is not None and l[k] < fib["f0"]:  # a new extreme after that swing: fib from the swing
                j = fib.pop("cand")
                fib["f1"], fib["hi"] = float(max(o[j], c[j])), float(h[j])
                log.append((day_label(dt[k]), f"fib 1 naar nieuwste swing {day_label(dt[j])} ({fib['f1'] * sgn:.5f})", dirn))
        if LAST_SWING_FIB and k == fib["bos"] + 1 and fib.get("s") is not None:  # a swing on the BoS candle is
            nf = start_fib((fib["bos"], fib["s"], fib["line"]), o, h, l, c, k)  # confirmed one day later
            if nf["f1"] != fib["f1"]:
                fib.update(f1=nf["f1"], hi=nf["hi"])
                log.append((day_label(dt[k]), f"fib 1 = body laatste swing {fib['f1'] * sgn:.5f}", dirn))
        tr = try_entry(k, fib, week_label(wstart[armed]))
        if tr:
            armed, fib, fibB = None, None, None
            continue
        fib["f0"] = min(fib["f0"], l[k])
    for t in trades:
        t["setup"] = "fib"
    if LQ_GRAB:  # setup 3: no weekly BoS needed (trader 2026-11-04, EURUSD May-June 2021)
        n0, saved, last_exit_t = len(trades), last_exit_t, np.datetime64("1900-01-01")
        keep = (DEEP, TARGETS)
        g_ = globals()
        if LQ_STOP_HI:  # stop above the swing high of the fib (the trader: 1.22559 above 1 June 2021)
            g_["DEEP"] = 0.0
        if LQ_TARGETS:
            g_["TARGETS"] = LQ_TARGETS
        seen = {(t["entry_day"], t["dir"]) for t in trades}
        for j, g, i1, i2 in lq_triggers(wo, wh, wl, wc):
            if wdone[j] < np.datetime64(pd.Timestamp(start).tz_localize(None)) or wstart[j] <= last_exit_t:
                continue
            kg = int(np.searchsorted(dt, wstart[g], "left"))  # the daily BoS may come from the grab week on
            kj = int(np.searchsorted(ddone, wdone[j], "right"))  # the trigger is known after the red week closed
            kend = min(len(c), int(np.searchsorted(ddone, wdone[min(j + LQ_WEEKS, len(wdone) - 1)], "right")), k1)
            fb = None
            for k in range(kj, kend):
                if fb is None:
                    b = find_bos(kg, k)
                    if b:
                        fb = start_fib(b, o, h, l, c, k)
                        if LQ_ENTRY_LEVEL is not None:
                            fb["virtual"] = LQ_ENTRY_LEVEL
                        log.append((day_label(dt[k]), f"LQ-grab (swing highs week {week_label(wstart[i1])} / "
                                    f"{week_label(wstart[i2])}, grab week {week_label(wstart[g])}): daily BoS (lijn "
                                    f"{b[2] * sgn:.5f}), fib 1 {fb['f1'] * sgn:.5f}", dirn))
                    continue
                if c[k] > fb["f1"]:
                    log.append((day_label(dt[k]), "LQ-grab: slot voorbij fib 1, vervalt", dirn))
                    break
                if try_entry(k, fb, "LQ " + week_label(wstart[j])):
                    break
                fb["f0"] = min(fb["f0"], l[k])
        g_["DEEP"], g_["TARGETS"] = keep
        new = [t for t in trades[n0:] if (t["entry_day"], t["dir"]) not in seen]  # not twice the same trade
        del trades[n0:]
        for t in new:
            t["setup"] = "lq"
        trades += new
        last_exit_t = saved
    if LQD:
        trades += daily_lq(sym, dirn, sgn, o, h, l, c, a, ddone, dt, wdone, state, k0, k1, log)
    if FAKE_RETEST:
        trades += fake_retest(sym, dirn, sgn, o, h, l, c, a, ddone, dt, w, wdone, state, fakes, k0, k1, log)
        trades.sort(key=lambda t: t["entry_day"])
    return trades


def lqd_features(o, h, l, c, a, g, i1, i2, ctx):
    """Setup-4 trade features at the close of the grab candle g (short view), for the loss study."""
    A = a[g]
    wts = np.arange(1, 31, dtype=float)
    wma30 = float(np.dot(c[g - 29:g + 1], wts) / wts.sum()) if g >= 29 else np.nan
    sma20 = float(np.mean(c[g - 30:g - 10])) if g >= 30 else np.nan
    rg = h[g] - l[g]
    lv = sr_levels(o, h, l, c, SR_TOL * a[g - 1], g)
    return dict(
        ctx="met trend" if ctx == -1 else "tegen trend",
        grab_atr=(h[g] - h[i2]) / A, back_atr=(h[i2] - c[g]) / A, red=bool(c[g] < o[g]),
        wick=(h[g] - max(o[g], c[g])) / rg if rg > 0 else 0.0, close_pos=(c[g] - l[g]) / rg if rg > 0 else 0.5,
        gap=g - i2, h12_gap=i2 - i1, h12_atr=(h[i1] - h[i2]) / A, risk_atr=(h[g] + LQD_BUF * A - c[g]) / A,
        range_atr=rg / A, below_wma30=bool(c[g] < wma30), dpo_neg=bool(c[g] - sma20 < 0),
        sr_at_h2=any(abs(p_ - h[i2]) <= 0.25 * A for p_, _ in lv),
        run_atr=(h[i2] - np.min(l[i2:g + 1])) / A,  # how far price fell from H2 before the grab
        trend20=(c[g] - c[g - 20]) / A if g >= 20 else 0.0)


def daily_lq(sym, dirn, sgn, o, h, l, c, a, ddone, dt, wdone, state, k0, k1, log):
    """Setup 4 (trader 2026-11-04; study daily_lq_study.py): a daily swing high H1 (fractal LQD_N each side), a
    lower daily swing high H2, at least LQD_GAP days later a daily candle trades above H2 and closes back below it
    (the high stays below H1, no close or high above H2 in between): short at the close of that grab candle. Stop
    above the grab high + LQD_BUF daily ATR, one target at LQD_TGT R (or the stop). LQD_CTX: "trend" only with the
    weekly structure (bearish in this view), "both" also against it."""
    out, N = [], LQD_N
    sh = [i for i in range(N, len(h) - N) if h[i] == np.max(h[i - N:i + N + 1])]  # known at i + N
    busy, cands = -1, []
    when = lambda i: day_label(dt[i]) if i is not None else ""  # noqa: E731
    for b, i2 in enumerate(sh):
        prev = [i for i in sh[:b] if 0 < i2 - i <= LQD_LOOK and h[i] > h[i2] and np.max(h[i + 1:i2]) <= h[i]]
        if not prev:
            continue
        i1 = prev[-1]
        for g in range(i2 + N + 1, min(len(c), i2 + LQD_LOOK)):
            if c[g - 1] > h[i2] or np.max(h[i2 + 1:g]) > h[i2]:
                break
            if g - i2 < LQD_GAP or not (h[g] > h[i2] and c[g] < h[i2] and h[g] < h[i1]):
                continue
            if not k0 <= g < k1:
                break
            wi = int(np.searchsorted(wdone, ddone[g], "right")) - 1
            ctx = state[wi] if wi >= 0 else 0
            if ctx != -1 and not (LQD_CTX == "both" and ctx == 1):
                break
            if LQD_SR and not any(abs(p_ - h[i2]) <= 0.25 * a[g] for p_, _ in sr_levels(o, h, l, c, SR_TOL * a[g - 1], g)):
                continue  # no daily S/R at the grabbed high (EURUSD: 16% win without, 42% with)
            cands.append((g, i1, i2, ctx))
            break
    # in date order: a trade blocks only grabs that come after it (2026-11-04 look-ahead check: processing per H2 let a
    # later trade of an earlier H2 block an earlier grab)
    for g, i1, i2, ctx in sorted(cands):
        if g <= busy:
            continue
        e, sl = c[g], h[g] + LQD_BUF * a[g]
        risk = sl - e
        tgt = e - LQD_TGT * risk
        if LQD_FIB:  # exits with the fib ladder of setup 1 on the leg: fib 1 = the grab high, fib 0 = the low since H2
            f0 = float(np.min(l[i2:g + 1]))
            mres = manage(h, l, g, e, sl, f0, h[g] - f0, BE * a[g])
            cost = cost_price(sym, abs(e))
            R = round((mres["pnl"] - cost) / risk, 2)
            ex = mres["exit_i"]
            out.append(dict(
                sym=sym, dir=dirn, trigger_week="", bos="", fib1=h[g] * sgn, fib0=f0 * sgn, level=h[i2] * sgn,
                entry_day=day_label(dt[g]), entry=e * sgn, sl=sl * sgn,
                risk_pips=risk * (100 if "JPY" in sym else 10000), depth=round((e - f0) / (h[g] - f0), 2),
                pattern="daily LQ grab" + (" (met trend)" if ctx == -1 else " (tegen trend)"),
                t1_day=when(mres["t1_i"]), t2_day=when(mres["t2_i"]), exit_day=when(ex), open=mres["open"], R=R,
                R_5050=round((mres["pnl5"] - cost) / risk, 2), entry_t=dt[g], m_sr_next=None, m_sr_before_t2=False,
                setup="lqd", _feat=lqd_features(o, h, l, c, a, g, i1, i2, ctx), _k=g, _f0=f0, _rng=h[g] - f0,
                _entry=e, _hi=h[g], _pat=h[g], _level=h[i2], _band=None, _flip=None))
            busy = ex if ex is not None else len(c)
            continue
        ladder = LQD_LADDER or ((LQD_TGT, 1.0, None),)  # (R level, part closed, new stop in R; None = keep)
        r, ex, hit, left, stop, step = 0.0, None, None, 1.0, sl, 0
        for q in range(g + 1, len(c)):
            if h[q] >= stop:
                r += left * (e - stop); ex, left = q, 0.0; break
            while step < len(ladder) and l[q] <= e - ladder[step][0] * risk:
                lv_, part, ns = ladder[step]
                part = min(part, left)
                r += part * ladder[step][0] * risk; left -= part
                if ns is not None:
                    stop = e - ns * risk
                hit = q if hit is None else hit
                step += 1
            if left <= 1e-9:
                ex = q; break
        if ex is None:
            r = None
        cost = cost_price(sym, abs(e))
        R = round(((r if r is not None else 0.0) - cost) / risk, 2)
        out.append(dict(
            sym=sym, dir=dirn, trigger_week="", bos="", fib1=h[i2] * sgn, fib0=h[i1] * sgn, level=h[i2] * sgn,
            entry_day=day_label(dt[g]), entry=e * sgn, sl=sl * sgn, risk_pips=risk * (100 if "JPY" in sym else 10000),
            depth=None, pattern="daily LQ grab" + (" (met trend)" if ctx == -1 else " (tegen trend)"),
            t1_day=when(hit), t2_day="", exit_day=when(ex), open=r is None, R=R, R_5050=R, entry_t=dt[g],
            m_sr_next=None, m_sr_before_t2=False, setup="lqd", _feat=lqd_features(o, h, l, c, a, g, i1, i2, ctx),
            _k=g, _f0=tgt, _rng=risk, _entry=e, _hi=h[g],
            _pat=h[g], _level=h[i2], _band=None, _flip=None))
        log.append((day_label(dt[g]), f"TRADE daily LQ grab van {h[i2] * sgn:.5f} (swing highs {day_label(dt[i1])} / "
                    f"{day_label(dt[i2])}), instap {e * sgn:.5f}, stop {sl * sgn:.5f} -> R {R:+.2f}", dirn))
        busy = ex if ex is not None else len(c)
    return out


def fake_retest(sym, dirn, sgn, o, h, l, c, a, ddone, dt, w, wdone, state, fakes, k0, k1, log):
    """Setup 2 (trader 2026-11-04, USDJPY Sep-Oct 2026): after a fake weekly BoS against the trend (the next week
    closed back), price first moves >= RT_AWAY daily ATR away from the line; then a daily candle tests the line with a
    wick (within RT_TOUCH ATR or through it) and closes back on the trend side: entry at that close. Stop beyond the
    extreme of the last 5 days + RT_SL daily ATR; the TARGETS ladder on f1 = the line, f0 = the extreme since the
    reclaim. Off after a daily close beyond the line or RT_WEEKS weeks. Study: fake_bos_retest_study.py."""
    out = []
    when = lambda i: day_label(dt[i]) if i is not None else ""  # noqa: E731
    for i0, i1, dd, line in fakes:
        if dd != 1 or state[i1] != -1:
            continue
        ka = int(np.searchsorted(ddone, wdone[i1], "right"))
        kb = min(len(c), int(np.searchsorted(ddone, wdone[min(i1 + RT_WEEKS, len(wdone) - 1)], "right")))
        away = False
        for k in range(ka, kb):
            if c[k] > line:
                break
            if not away:
                away = line - np.min(l[ka:k + 1]) >= RT_AWAY * a[k]
                continue
            if not (h[k] >= line - RT_TOUCH * a[k - 1] and c[k] < line and h[k] - max(o[k], c[k]) >= 0.1 * a[k - 1]):
                continue
            if not k0 <= k < k1:
                break
            e, wick = c[k], float(np.max(h[k - 4:k + 1]))
            sl = wick + RT_SL * a[k]
            f0 = float(np.min(l[ka:k + 1]))
            rng, risk = line - f0, sl - e
            mres = manage(h, l, k, e, sl, f0, rng, BE * a[k])
            cost = cost_price(sym, abs(e))
            out.append(dict(
                sym=sym, dir=dirn, trigger_week=week_label(w["time"].iloc[i0]), bos="", fib1=line * sgn, fib0=f0 * sgn,
                level=line * sgn, entry_day=day_label(dt[k]), entry=e * sgn, sl=sl * sgn,
                risk_pips=risk * (100 if "JPY" in sym else 10000), depth=round((e - f0) / rng, 2),
                pattern="valse-BoS retest", t1_day=when(mres["t1_i"]), t2_day=when(mres["t2_i"]),
                exit_day=when(mres["exit_i"]), open=mres["open"], R=round((mres["pnl"] - cost) / risk, 2),
                R_5050=round((mres["pnl5"] - cost) / risk, 2), entry_t=dt[k], m_sr_next=None, m_sr_before_t2=False,
                setup="retest", _k=k, _f0=f0, _rng=rng, _entry=e, _hi=wick, _pat=wick, _level=line, _band=None,
                _flip=None))
            log.append((day_label(dt[k]), f"TRADE valse-BoS retest van de week-lijn {line * sgn:.5f} (valse BoS week "
                        f"{week_label(w['time'].iloc[i0])}), instap {e * sgn:.5f}, stop {sl * sgn:.5f} -> R "
                        f"{out[-1]['R']:+.2f}", dirn))
            break
    return out


def start_fib(b, o, h, l, c, k):
    kb, s, line = b
    f1 = float(np.max(np.maximum(o[s:kb + 1], c[s:kb + 1])))
    hi = float(np.max(h[s:kb + 1]))
    if PULLBACK_FIB:  # setup 15: fib 1 = body of the last swing after the extreme of the leg, before the BoS (the
        t = s + int(np.argmax(np.maximum(o[s:kb + 1], c[s:kb + 1])))  # higher low the breaking move started from)
        js = [j for j in range(t + 1, min(kb, k - 1)) if h[j] >= np.max(h[j - PB_LEFT:j]) and h[j] > h[j + 1]
              and j - t >= 2 and h[j] - np.min(l[t + 1:j]) >= PB_MIN * ATR_REF[j]]  # a real pullback: >= PB_MIN ATR
        # from the low of the leg after the extreme
        if js:
            f1, hi = float(max(o[js[-1]], c[js[-1]])), float(h[js[-1]])
    if LAST_SWING_FIB:  # setup 14: fib 1 = body of the last 3-candle swing up to the BoS candle (confirmed by day k)
        js = [j for j in range(max(s + 1, SWING_LEFT), min(kb, k - 1) + 1)
              if h[j] > np.max(h[j - SWING_LEFT:j]) and h[j] >= h[j + 1]]
        if js and (LAST_SWING_FIB is True or js[-1] == kb):
            f1, hi = float(max(o[js[-1]], c[js[-1]])), float(h[js[-1]])
    return dict(bos=kb, f1=f1, hi=hi, f0=float(np.min(l[kb:k + 1])), line=line, s=s)


def main():
    global ENG2
    ap = argparse.ArgumentParser()
    ap.add_argument("syms", nargs="+")
    ap.add_argument("--from", dest="start", default="2005-01-01")
    ap.add_argument("--to", dest="end", default="2030-01-01")
    ap.add_argument("--prefix", default="v2_")
    ap.add_argument("--no-eng2", action="store_true", help="no setup-4 trigger (engulfing of a green week two back)")
    ap.add_argument("-v", action="store_true", help="print the step log")
    a = ap.parse_args()
    ENG2 = not a.no_eng2
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    for sym in a.syms:
        d, w, mn = load(sym, "D1"), load(sym, "W1"), load(sym, "MN")
        log, trades = [], []
        for dirn in (-1, 1):
            trades += run_view(sym, d, w, dirn, a.start, a.end, log, mn)
        t = (pd.DataFrame(trades).drop(columns=[x for x in trades[0] if x == "entry_t" or x.startswith("_")])
             .sort_values("entry_day") if trades else pd.DataFrame())
        t.to_csv(out / f"{a.prefix}{sym}.csv", index=False)
        if a.v:
            for day, msg, dirn in sorted(log):
                print(f"{day} {'short' if dirn == -1 else 'long ' if dirn == 1 else 'week '} {msg}")
        if len(t):
            cols = ["dir", "trigger_week", "bos", "entry_day", "entry", "sl", "fib1", "fib0", "depth", "pattern",
                    "t1_day", "t2_day", "exit_day", "R", "R_5050"]
            print(t[cols].to_string(index=False, float_format=lambda x: f"{x:.5f}"))
            print(f"{sym}: {len(t)} trades, win (T1) {(t.t1_day != '').mean() * 100:.0f}%, R {t.R.sum():+.1f} "
                  f"(gem. {t.R.mean():+.2f}), R_5050 {t.R_5050.sum():+.1f}")
        else:
            print(f"{sym}: geen trades")


if __name__ == "__main__":
    main()
