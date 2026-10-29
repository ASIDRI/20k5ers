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

## Fase 2c: de edge zit in de prop-firm-deal (`research/rnd/prop_ev.py`)

Model 5ers High Stakes: stap 1 +8%, stap 2 +5%, breach bij -10% van de start of -5% van de dagstart; funded: 80% van
de winst, uitbetaling telkens bij +4%, 2 jaar. Fee als fractie van het account. Strategieën: dagrendementen na kosten
van een mand (SPX500, NAS100, UK100, goud, zilver), risico afgestemd op een jaarvolatiliteit. 'zero' = zelfde mand
zonder drift (puur het effect van de grenzen).

| Strategie, 6-10% vol, fee 0,5% | Kans stap 1+2 | EV per challenge (% van account) |
|---|---|---|
| nul-edge (geen drift) | 32-45% | +1,4 à +1,6 |
| kopen en houden | 64-91% | +8,8 à +9,3 |
| trend long-only (12 mnd) | 43-57% | +4,3 à +4,5 |
| momentum 6 mnd long/short | 60-83% | +6,1 à +6,8 |

Zelfde test op **2005-2014** (met 2008; SPX500, NAS100, goud, zilver): trend long-only 6% vol +7,8%, momentum
long/short +6,6 à +7,0%, kopen en houden +5,2 à +7,4%, nul-edge +0,5 à +1,5%.

**Gevoelig voor het verlies tijdens de dag** (factor op het slot-tot-slotverlies): bij 1,5-2 blijft EV positief
(fee 1%: +2 à +5%), bij 3 rond nul of negatief. Lager risico (6-10% per jaar) is steeds beter dan 15-20%.
Volgende stap: meten met de echte 15-minutendata en een plafond op de hefboom, in plaats van een factor aan te nemen.

### Gemeten op het echte 15-minutenpad (`research/rnd/prop_m15.py`, 2015-2025, hefboomplafond 3, fee 0,5%)

Equity elke 15 minuten op de slechtste prijs van elke candle, alle instrumenten tegelijk op hun slechtst (voorzichtig).
Gemeten verlies tijdens de dag: mediaan 1,4-1,7 keer het slot-tot-slotverlies (de eerder aangenomen 1,5 klopte).

| Strategie | Vol | Geslaagd (stap 1+2) | Breach | Mediaan dagen | EV per challenge | Slechtste dag |
|---|---|---|---|---|---|---|
| trend long-only | 5% | 100% | 0% | 531 | +7,0% | -4,0% |
| trend long-only | 6% | 98% | 2% | 418 | +9,0% | -4,8% |
| trend long-only | 8% | 84% | 16% | 252 | +11,0% | -6,4% |
| kopen en houden | 6% | 100% | 0% | 461 | +9,5% | -4,0% |
| momentum 6 mnd l/s | 6% | 78% | 22% | 566 | +6,6% | -4,5% |
| video-terugval long | 6% | 53% | 47% | 392 | +2,2% | -6,0% |

Startdata overlappen en vallen in een stijgende markt; de dagdatatest op 2005-2014 (met 2008) was ook positief.
Nog te verifiëren: tijdslimiet/inactiviteitsregels en hefboom per instrument bij de 5ers.

## Fase P1: drie paren in kaart (`research/rnd/pair_diag.py`, M15 2015-2025, beide periodes)

| | EURUSD | AUDNZD | USDJPY |
|---|---|---|---|
| Uurbasis | geen | **terugkeer**: ac1 -0,044 / -0,063; VR20 0,89 / 0,84 | geen |
| S/R maand/week keert (vs willekeurig) | 50,6 vs 54,6 / 52,3 vs 45,9 (wisselt) | **51,9 vs 48,2 / 54,5 vs 49,4** | 46,3 vs 45,8 / 42,5 vs 49,2 (breekt eerder) |
| Tijd | 11u UTC -0,9 / -1,35 bp (t -3,3 / -5,1), kleiner dan kosten 1,8 bp | geen | geen |
| Kosten heen en terug | 1,8 bp | 3,3 bp | 1,8 bp |

## Fase P2 (vooraf vastgelegd, 2026-10-29): AUDNZD terugkeer op uurbasis

Signaal op een gesloten uurcandle: z = (slot - gemiddelde N uur) / stdev N uur, N in {20, 50}; |z| >= 2 -> trade tegen de
uitrekking in, instap op de open van het volgende uur; uitstap bij terugkeer naar het gemiddelde (gemeten op het slot)
of na 24 uur; SL 2 uur-ATR. Kosten 3,3 bp per trade. Variant: alleen bij een S/R-niveau van maand/week (binnen 0,5 dag-ATR).
4 varianten (N x met/zonder S/R) in het register.
Geslaagd als een variant in 2015-2020 t >= 3 haalt op het nettoresultaat per trade, en in 2021-2025 hetzelfde teken heeft
met minstens de helft van het effect; daarna slotkluis op 4u-data 2005-2014 (eigen vastlegging).
