# R&D: resultaten per fase

Plan en spelregels: `docs/RND_PLAN.md`. Register van alle geteste cellen: `research/rnd/registry.csv`.

## Fase 1: weekcandles (30 assets, 2015-2025, ±34.000 weken, 52 cellen)

`research/rnd/weekly_events.py`. Maat: +1 weekATR vóór -1 (ev11, na kosten) en rendement na 10 dagen (fwd10), in weekATR.

- Engulfing, pin bar en sweep van de vorige week-high/low: kans op +1 vóór -1 overal 49-53%, ev rond 0 in beide periodes. **Geen voorspellende waarde.**
- Op een S/R-niveau van maand/week: gemiddeld **negatief** in de richting van het signaal, het sterkst met de trend mee:

| Cel | 2015-20 | 2021-25 | Lat |
|---|---|---|---|
| afketsen op niveau, mee met weektrend (ev11) | -0,073 (t -5,1) | -0,043 (t -2,5) | door |
| idem, fwd10 | -0,076 (t -5,7) | -0,051 (t -3,5) | door |
| afketsen op niveau, mee met maandtrend (ev11) | -0,111 (t -7,4) | -0,055 (t -3,0) | |
| sweep op niveau, mee met maandtrend (ev11) | -0,110 (t -3,9) | -0,065 (t -1,9) | door |

~~Kandidaat voor fase 3: de afketsing faden.~~ **Ingetrokken**: deze cellen werden met 0 vergeleken in plaats van met
de basislijn (alle weken, zelfde kosten, -0,02). Tegen de basislijn haalt geen enkele weekcel de lat
(`research/rnd/excess.py`).

## Fase 2: dag en 4u, met liquiditeit (30 assets, 2015-2025; 97 cellen per timeframe)

`research/rnd/events.py`, beoordeeld met `research/rnd/excess.py` (meerwaarde boven de basislijn, zelfde kosten).
Kosten per trade, uitgedrukt in ATR (mediaan): week 0,017; dag 0,04; **4u 0,105**.

| Timeframe | Basislijn ev11 na kosten | Cellen met bevestigde meerwaarde |
|---|---|---|
| Week | -0,02 | geen |
| Dag | -0,05 | geen |
| 4u | -0,13 | 2 positief (+0,02-0,03 ATR), 4 negatief (pin bar iets slechter) |

De enige positieve cellen (4u: terugkeer in een FVG tegen de week-/maandtrend, niet op een niveau) leveren
+0,02-0,03 ATR boven de basislijn, tegenover 0,10 ATR kosten: na kosten nog steeds verlies.

**Conclusie fase 1-2:** engulfing, pin bar, sweep van de vorige candle/dag/week, sweep van gelijke toppen/bodems
en FVG-terugkeer, op of naast S/R van maand/week, met of tegen de trend: geen van deze signalen voorspelt de
volgende candles beter dan toeval, op week, dag of 4u. Op 4u maken de kosten (10% van een ATR per trade) een
edge bovendien zeer moeilijk.
