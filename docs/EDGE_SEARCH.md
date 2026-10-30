# Zoektocht naar een edge met een economische reden

Na de video-strategieën (tests 1-33), Neely (N1-N4) en de Elliott Wave van de trader (E1) is het patroon duidelijk:
regels op het koersbeeld (patronen, golven, S/R, fib) geven op deze data geen voorsprong na kosten, ook niet vóór
kosten. Het enige dat stabiel positief was, zijn markten met een **reden** om te stijgen (aandelenindices, goud),
gecombineerd met de 5ers-regels (`docs/RND_RESULTS.md`, fase 2c). Daarom zoeken we hier naar effecten met een
economische reden en literatuur erachter. Elke test wordt vóór de run vastgelegd.

## Test X1 (vooraf vastgelegd, 2026-10-30): turn-of-month in Amerikaanse aandelenindices

**Reden.** Pensioen-, salaris- en fondsstromen rond de maandwissel. Volgens de literatuur valt een groot deel van het
aandelenrendement op de laatste handelsdag van de maand en de eerste drie van de volgende maand (Lakonishok & Smidt
1988; McConnell & Xu 2008).

**Regel.** Koop bij het slot van de voorlaatste handelsdag van de maand (dag -2) en verkoop bij het slot van de derde
handelsdag van de volgende maand (dag +3). Dat is 4 handelsdagen in de markt (dagen -1, +1, +2, +3). Handelsdagen zijn
de dagcandles op maandag t/m vrijdag. Welke dag de laatste van de maand is, staat vooraf in de beurskalender; in de
data lezen we het af aan de volgende candle. Kosten per symbool (`test2.cost_price`).

**Beslissend:** SPX500 en NAS100 (dagdata 2005-2025), elke trade als het gemiddelde van de twee. Slaagt als:
1. de netto trade gemiddeld boven 0 zit in elke periode (2005-14, 2015-20, 2021-25); en
2. het gemiddelde dagrendement op de TOM-dagen hoger is dan op de andere dagen, in elke periode, met over 2005-2025
   samen t >= 2,0 (Welch).

**Gerapporteerd, niet beslissend:** UK100 (2015-2025, een andere markt: half-holdout), goud en EURUSD (controles
zonder reden; daar verwachten we niets), en het aandeel van het totale rendement dat op TOM-dagen valt.

**Bij slagen** volgt een eigen vastlegging: de 5ers-challenge met blootstelling alleen op TOM-dagen tegenover kopen en
houden bij dezelfde volatiliteit, op het echte 15-minutenpad (`research/rnd/prop_m15.py`).
