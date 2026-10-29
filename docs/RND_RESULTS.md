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

## Fase 2b: systematische regels als portefeuille op de daggrafiek (na kosten, risico afgestemd op volatiliteit)

`research/rnd/systematic.py`. Families: momentum 3/6/12 maanden, Donchian-uitbraak 20/55, video-terugval in de
12-maandentrend (eigen ontwerp), RSI(2)-terugkeer in de 200-dagentrend.

- **28 forex-paren, 2015-2025:** alle families negatief in beide periodes (Sharpe -0,9 tot +0,3).
  Controle van de motor op 2006-2014: momentum verdiende in 2006-2009 (Sharpe 0,61) en niet meer daarna, zoals
  bekend uit de literatuur. *Daarmee is 2005-2014 voor deze families gezien en geen onaangeroerde slotkluis meer.*
- **Indices, goud, zilver, olie, crypto (D1 uit eigen M15), 2015-2025:** momentum en uitbraak positief in beide
  periodes (Sharpe 0,4-1,0), maar **kopen en houden doet even goed of beter** (0,68 / 1,05). De shorts verliezen; de
  winst is de stijging van die markten (beta), geen voorspellend voordeel. De trendfilter voegt weinig toe
  (lang-only momentum 0,80-0,87 / 1,13-1,21 tegen kopen en houden 0,68 / 1,05).
- Per index wisselend tussen de periodes (bv. RSI(2)-dip kopen op SPX500: 0,04 / 0,99; video-terugval: 0,49 / 0,50,
  per dag in de markt nauwelijks beter dan kopen en houden). NAS100-data 2021-2025 verdacht (kopen en houden Sharpe -0,04).
