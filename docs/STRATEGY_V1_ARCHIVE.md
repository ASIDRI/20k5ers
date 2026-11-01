# Strategie v1 (gearchiveerd 2026-11-01)

De vorige strategie - swing-setups uit tests 36-64 (`docs/STRATEGY_FROM_VIDEOS.md`) - staat ongewijzigd bewaard in:

- `research/strategy/archive/strategy_v1_test36b.py` (engine, kopie van `research/strategy/test36b.py`)
- `research/strategy/archive/strategy_v1_t36_eval.py` (evaluatie, kopie van `research/strategy/t36_eval.py`)

De originele bestanden staan ook nog op hun plaats, zodat de gedocumenteerde tests reproduceerbaar blijven.

Beste versie van v1 (test 64, de enige die de volledige lat haalde):
maand-setting (`(ms_trend == 1) | (mt_done == -1)`), geen maand-S/R in de weg (`~m_block`), instap in de fib >= 0,66,
instap op of voorbij de point of control van de poot (`poc_thru`); beheer `R_lad`. 37 instrumenten: 61 trades/jaar,
+0,12 / +0,07 / +0,17R per periode (t 2,30); holdout +0,06 / +0,27 / +0,12R.

    python research/strategy/test36b.py SYM ... --swing --zone 0.5,0.796 --h4pat --prefix t63_ ...
    python research/strategy/indicator_study.py --write t64 t63_ t63x_
    python research/strategy/t36_eval.py --prefix t64_

De actieve strategie is nu v2: `research/strategy/trader_strategy.py` (regels: `docs/SETUPS_TRADER.md`).
