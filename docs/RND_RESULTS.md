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

Kandidaat voor fase 3: **de afketsing op een niveau in trendrichting faden**. Effect klein (±0,04-0,05 weekATR per signaal).
