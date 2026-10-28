# Look-ahead in the backtest simulator (found 2026-10-27)

**The headline results ($4M, 95% challenge pass, all PDFs before this date) are not valid.**

> **Correction 2026-10-28.** The "completed candles only" rule used for the leak-free numbers below was
> itself wrong for one kind of file. The forex MN CSVs are stamped with the LAST day of the month, not the
> first, so the rule "stamp + 31 days" hid every completed month for one more month (the bot saw the month
> before last). Metals, indices, oil, crypto MN and all D1/W1/H4 files are stamped at the open, so the rule
> was right there. The new rule (`backtest/src/candle_avail.py`) reads each file's own convention and was
> checked against the M15 data (`audit_referee_tests.py candles`: 0 look-ahead, 0 needless lag).
> The daily-candle-only test below (-$2,869 in 2019) did not touch the MN files, so the main conclusion
> probably holds, but every leak-free number here is being measured again under `docs/AUDIT_PLAN.md`.
> `HTF_NO_LOOKAHEAD=crude` reproduces the old rule.

## What was wrong
`backtest/src/csv_mt5_simulator.py` served every candle that had *opened* before the simulated
time. The CSV stores each candle with its open time and its FINAL high/low/close, so the daily,
weekly, monthly and 4-hour candle that was still forming already contained the rest of its period.
At the 00:00 UTC scan the bot saw that day's complete range (up to 22 hours ahead); on a Monday the
weekly candle already held the whole week. The real `MT5Client.get_ohlcv` returns completed
candles only (`copy_rates_from_pos(..., 1, ...)`), so live never sees this.

## Evidence (same configuration as the headline, 1 year each, $50k funded, climb cap)
| Year | net P&L with leak | net P&L completed candles only |
|---|---|---|
| 2016 | $751,869 | -$3,058 |
| 2018 | $726,048 | -$3,899 |
| 2019 | $709,601 | -$4,561 |
| 2021 | $510,467 | +$10,506 |
| 2023 | $637,379 | -$3,871 |

Which candle matters (2019): completing only the daily candle gives -$2,869; only weekly $344,667;
only monthly $632,887; only 4-hour $641,079. The daily candle carries the effect.

Leak-free 2015-2025 continuous funded run: account breached the 10% total-drawdown wall on 2019-01-02
(4 years in). Leak-free challenges (steps 1 and 2 at 1.8%, first 30 of the 100 random starts):
1 passed, 1 breached, 28 too slow. With the leak: 94 of 100.

## What changed
- `csv_mt5_simulator.py` now returns completed candles only by default. `HTF_NO_LOOKAHEAD=0`
  reproduces the old stored results.
- Evidence scripts: `w5_lookahead_test.py`, `w5_clean_study.py`; outputs in `backtest/output/replay/`.
- `live_replay.py` / `live_replay_compare.py`: run the real live bot against recorded prices.
- The PDF reports carry an invalidation banner.

## What it does not mean
The live bot itself is unchanged and behaves as designed (it only ever sees completed candles).
It means the parameters were tuned on leaked data, so there is no evidence of an edge. Do not trade
real money or buy a challenge on these results. All earlier optimisation (915 setups, ticker study,
risk ladders, climb cap) used the leaky simulator and has to be redone.

## The mechanism (why it made so much money)
`strategy_core.compute_trade_levels` uses `current = daily_candles[-1]["close"]` and places the entry at
`current` when it lies near the fib level. With the leak, that "current price" was the close of a day that
had not happened yet, so orders were placed at the price where the day would END.
2019: 36.5% of trades opened within 5% of the day's range from that day's (future) close; with completed
candles 9.1%.

## The real live bot, replayed bar by bar (live_replay.py, 2019, live timing: scan 00:15 server time)
| Candles given to the bot | trades | win rate | trading P&L |
|---|---|---|---|
| leaky (old simulator) | 886 | 56.2% | +$247,199 (scaled to $450k) |
| completed only, like MT5 | 118 | 39.0% | -$2,709 |

In the MT5-like run the live bot stopped on 2019-02-07: ChallengeRiskManager's emergency close-all at
5.5% total drawdown ("halting all trading", permanent until restart). The backtest has no such halt
(TDD_EMERGENCY_HALT=0, wall-guard instead). This is a live/backtest divergence not covered by
w5_parity_audit.py.

## How to backtest from now on
**The real live bot is the backtest.** `backtest/src/live_replay.py` runs the unmodified
`main_live_bot.py` on recorded 15-minute prices with a fake MT5 (completed candles only, like
`copy_rates_from_pos(..., 1, ...)`), a fake clock (scan at 00:15 server time, rollover queue, Monday
01:00, nightly de-risk on New York time) and the bot's DDD thread called every bar. About 5 minutes per
year in quiet mode. Options: `--params-json` (test parameters in memory, live files untouched),
`--env-json` (settings), `--no-stop-on-breach`. It reports 5ers numbers: max daily/total drawdown,
first breach, whether the bot halted itself.

- `live_screen.py` runs many parameter sets through it in parallel.
- The old engine (`main_live_bot_backtest.py`) now also uses the live clock (`LIVE_TIMING=1`, via
  `live_clock.py`, which reads the rules from main_live_bot.py itself). On January 2019 it matched 77
  of ~100 live trades; it still lacks live-only bookkeeping (orphan-order recovery), so it is only a
  fast pre-filter. Final numbers must come from live_replay.py.

## All 50 historical parameter sets, real live bot, 2019 (live_screen.py)
Every unique parameter set from the git history and params/ (34 with 5 take-profits) was run through
live_replay.py: 1.0% base risk, flat $50k, completed candles, --validated-halts. **All 50 lose money.**
Best: profit factor 0.80 (sets from 2026-03-22, -$3,364); most -$4,700 to -$4,800 with the account
drawn down to the 10% wall (the wall-guard then throttles risk). Profit factors 0.65-0.80, win rate 44-50%.

## Live-bot issues found by the replay (not fixed, need a decision)
1. ChallengeRiskManager closes all and halts PERMANENTLY at 2.5% daily or 5.5% total drawdown. It ignores
   TDD_EMERGENCY_HALT=0; below -5.5% every restart halts again, so the bot can never trade again.
2. After a 10% stop-out (monitor_5ers_drawdown) the main loop `continue`s without sleeping: a busy loop
   that writes the same error forever.

## Running tests: no time limits
All study scripts run their backtests without a time limit (subprocess timeouts removed; doe_harness
RUN_TIMEOUT_S defaults to none; challenge_score has no per-step limit). Start long jobs with
`backtest/run_job.sh <name> <command>`: detached from the session, no timeout, resumable (finished runs
are skipped when the same command is started again). Log in backtest/output/jobs/.
