# 20k5ers

Bot voor de 5ers prop-firm. **Stand 2026-10-29:** de vorige bot en zijn strategie zijn buiten dienst gesteld
en uit de repo gehaald (terug te vinden in de git-geschiedenis). Zijn backtestwinst kwam uit een blik in de
toekomst (`docs/LOOKAHEAD_FINDING.md`, `docs/AUDIT_PLAN.md`). Er draait geen live-bot.

Nu: een nieuwe strategie op basis van de Market Matrix-video's, getest in een gekeurde testomgeving.

| Wat | Waar |
|---|---|
| Regels uit de video's, tests 1-3 | `docs/STRATEGY_FROM_VIDEOS.md`, `research/strategy/` |
| R&D-programma (fases, register, resultaten) | `docs/RND_PLAN.md`, `docs/RND_RESULTS.md`, `research/rnd/` |
| S/R-niveaus (maand/week, wick-tikken, point in time) | `research/strategy/sr_levels.py` |
| Video's verwerken (screenshots + transcript in sync) | `scripts/video_digest.py` |
| Testomgeving: alleen afgesloten candles, serverklok, strikte broker | `backtest/src/candle_avail.py`, `server_clock.py`, `backtest/src/csv_mt5_simulator.py` (`BROKER_STRICT=1`), `backtest/src/audit_referee_tests.py` |
| Replay van een live-bot op de nagebootste MT5 (per 15 min) | `backtest/src/live_replay.py --code-root ...` |
| Infrastructuur voor de volgende live-bot | `tradr/mt5/client.py`, `tradr/risk/`, `tradr/brokers/fiveers_specs.py`, `challenge_risk_manager.py`, `config.py`, `broker_config.py`, `symbol_mapping.py`, `news_calendar.py`, `deploy/` |
| Lange runs zonder tijdslimiet | `backtest/run_job.sh` |
| Kosten per symbool (spread + slippage) | `research/costs.json` |
