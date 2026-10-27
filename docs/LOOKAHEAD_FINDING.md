# Look-ahead in the backtest simulator (found 2026-10-27)

**The headline results ($4M, 95% challenge pass, all PDFs before this date) are not valid.**

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
