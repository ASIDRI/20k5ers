"""Strategy v2: the trader's top-down method as documented step by step in docs/SETUPS_TRADER.md (setups 1-10).

    python research/strategy/trader_strategy.py EURUSD [SYM ...] [--from 2018-05-01] [--to 2020-04-01] [--prefix v2_] [-v]

The previous engine (swing setups, tests 36-64) is archived in research/strategy/archive/strategy_v1_test36b.py.

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
   (25%), stop then to fib 0; the rest runs to fib -1 (T3, setup 11) or the stop. R_5050: 50% at T1, 50% at T2 (stop after T1 a
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
BOS_TRIGGER = True  # the confirmed weekly BoS arms the first trade itself (setup 11)
FLIP_BAND = 0.35  # daily ATR around the weekly break line: the levels of the first trade after a weekly BoS (setup 1)
MIN_DEPTH = 0.25  # entry close at least this deep in the fib (the trader's entries: 0.31 - 0.83)
T1, T2, T3 = 0.2, 0.58, 1.0  # T3: the trader closes everything at fib -1 (setup 11)
MN_TOL, MN_MIN_EACH, MN_SEP, MN_REFRESH = 0.15, 2, 0.75, 6  # monthly S/R (wick taps both sides), redrawn every 6 months
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
    last = {1: None, -1: None}
    for i in range(len(c)):
        while p < len(sw) and sw[p][2] <= i:
            last[sw[p][1]] = sw[p][0]; p += 1
        if pend is not None:
            d, line, i0 = pend
            if (c[i] - line) * d > 0:
                s = d; events.append((i0, i, d, line))
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
    return state, events, a


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
    if c[k] < o[k] and h[k - 1] >= p - tol and c[k - 1] < p:
        return "tweezer / bearish na test"
    return None


def manage(h, l, k, entry, sl, f0, rng, be):
    """Exits from the day after the entry. Returns dict with R parts (in price units) and the dates' indices."""
    t1, t2, t3 = f0 - T1 * rng, f0 - T2 * rng, f0 - T3 * rng
    res = {"t1_i": None, "t2_i": None, "exit_i": None}
    stop, got1, got2, pnl = sl, False, False, 0.0
    stop5, open5, pnl5 = sl, True, 0.0  # 50 / 50 variant
    for i in range(k + 1, len(h)):
        if open5:
            if h[i] >= stop5:
                pnl5 += (0.5 if got1 else 1.0) * (entry - stop5); open5 = False
            elif got1 and l[i] <= t2:
                pnl5 += 0.5 * (entry - t2); open5 = False
        if h[i] >= stop:
            pnl += (1.0 if not got1 else 0.5 if not got2 else 0.25) * (entry - stop)
            res["exit_i"] = i
            break
        if not got1 and l[i] <= t1:
            got1, res["t1_i"] = True, i
            pnl += 0.5 * (entry - t1); stop = entry - be
            if open5:
                pnl5 += 0.5 * (entry - t1); stop5 = entry - be
        if got1 and not got2 and l[i] <= t2:
            got2, res["t2_i"] = True, i
            pnl += 0.25 * (entry - t2); stop = f0
        if got2 and l[i] <= t3:
            pnl += 0.25 * (entry - t3); res["exit_i"] = i
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


def run_view(sym, d, w, dirn, start, end, log, m=None):
    """dirn -1: shorts on the real prices; +1: longs = shorts on negated prices."""
    sgn = -1 if dirn == 1 else 1  # price transform for this view
    def px(df):
        o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
        return (o, h, l, c) if sgn == 1 else (-o, -l, -h, -c)
    wo, wh, wl, wc = px(w)
    state, events, wa = weekly_structure(wo, wh, wl, wc)
    trig = weekly_triggers(wo, wh, wl, wc, wa, state)
    wdone = complete_times(w["time"], "W1").values
    wstart = w["time"].values
    o, h, l, c = px(d)
    a = atr(h, l, c)
    ddone = complete_times(d["time"], "D1").values
    dt = d["time"].values
    dsw = zigzag(h, l, a, D_REV)
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
            sl_ = [s for s, cf in lows if cf <= k - 1]
            if not sl_:
                continue
            s = sl_[-1]
            line = min(o[s], c[s])
            if c[k] < line and not np.any(c[s + 1:k] < line):
                best = (k, s, line)
        return best

    def try_entry(k, fd, trig_label, band=None):
        """Entry check at the close of day k for the fib fd; band = (line, close) of the weekly BoS for the first
        trade after it (setup 11), else the fib zone (and the weekly break line of setup 1). Returns the trade."""
        nonlocal last_exit_t
        f0, f1 = fd["f0"], fd["f1"]
        rng = f1 - f0
        if k <= fd["bos"] or rng <= 0:
            return None
        tol = TOUCH_TOL * a[k - 1]  # the wick test at entry
        lv = sr_levels(o, h, l, c, SR_TOL * a[k - 1], k)
        if band is not None:  # first trade after a weekly BoS: daily S/R between the BoS line and the BoS-week close
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
            rej = [i for i in back if h[i] >= p - tol and c[i] < p and h[i] - max(o[i], c[i]) >= tol]
            if len(rej) < REJ_N or not any(c[i] < o[i] for i in back if h[i] >= p - tol):
                continue
            if NO_CLOSE_ABOVE and any(c[i] > p + tol for i in back):  # the level must hold: bodies stay below it
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
                m_sr_before_t2=any(f0 - T2 * rng < q * sgn < entry for q in mlev)))
            log.append((day_label(dt[k]), f"TRADE {pat} aan dag-S/R {p * sgn:.5f} ({n} reacties), instap {entry * sgn:.5f}, "
                        f"stop {sl * sgn:.5f}, diepte {depth:.2f} -> R {trades[-1]['R']:+.2f}", dirn))
            last_exit_t = dt[mres["exit_i"]] if mres["exit_i"] is not None else np.datetime64("2100-01-01")
            return trades[-1]
        return None

    bos_weeks = {i1: (i0, line) for i0, i1, dd, line in events if dd == -1}  # bearish (in this view) BoS confirmations
    fibB, done_bos = None, set()
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
            cand = [j for j, kind in trig if run_start[wi] <= j <= wi and wstart[j] > last_exit_t]
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
        if fib is None:
            b = find_bos(k, k)
            if b:
                fib = start_fib(b, o, h, l, c, k)
                log.append((day_label(dt[k]), f"daily BoS (lijn {b[2] * sgn:.5f}), fib 1 {fib['f1'] * sgn:.5f}", dirn))
            continue
        if c[k] > fib["f1"]:
            log.append((day_label(dt[k]), f"slot boven fib 1 ({fib['f1'] * sgn:.5f}): fib vervalt", dirn))
            fib = None
            continue
        tr = try_entry(k, fib, week_label(wstart[armed]))
        if tr:
            armed, fib, fibB = None, None, None
            continue
        fib["f0"] = min(fib["f0"], l[k])
    return trades


def start_fib(b, o, h, l, c, k):
    kb, s, line = b
    f1 = float(np.max(np.maximum(o[s:kb + 1], c[s:kb + 1])))
    return dict(bos=kb, f1=f1, hi=float(np.max(h[s:kb + 1])), f0=float(np.min(l[kb:k + 1])), line=line)


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
        t = pd.DataFrame(trades).drop(columns="entry_t").sort_values("entry_day") if trades else pd.DataFrame()
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
