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

### Uitkomst X1: verworpen
`python research/edge/tom.py`. SPX500 + NAS100, netto per trade (4 dagen):
- per periode: +0,01% (2005-14), +0,19% (2015-20), -0,01% (2021-25);
- het dagrendement op TOM-dagen tegenover de andere dagen: +0,059 vs +0,034% (t 0,6), +0,064 vs +0,065% (t 0,0),
  +0,004 vs +0,074% (t -1,1).

Het effect is weg. In 2005-14 viel nog 29% van het rendement op de 19% TOM-dagen; in 2015-20 19%, en in 2021-25 1%.
Dat past bij de literatuur, die zegt dat bekende kalendereffecten na publicatie verzwakken. UK100 laat ook niets zien.

Controles:
- **Goud:** de 4-daagse trade is positief (+0,28%, t 2,0), maar het dagrendement op TOM-dagen verschilt niet
  significant van de rest (t 1,0). Het grootste deel is de stijging van goud zelf. Er is ook geen reden voor het
  effect, en het is één van de ±20 gerapporteerde cijfers. Daarom telt dit niet als vondst.
- **EURUSD:** niets (2005-25 t -0,2).

## VectorVest market timing: bronnen

- De VectorVest-handleiding van de trader (`help.pdf`, 225 p., VectorVest 7), hoofdstuk "Market Timing Explained" en
  "VectorVest Timing Systems" (p. 162-175).
- VectorVest-websites: [VectorVest Timing Systems](http://www.vectorvest.com/realtime/training/help/VectorVest_Timing_Systems1.htm),
  [The DEW timing signal (AU)](https://www.vectorvest.com.au/the-dew-timing-signal/),
  [DPO-blog (BE)](https://www.vectorvest.be/blog/vectorvest/dpo-of-detrended-price-oscillator/),
  [webinar "When to buy & sell"](http://www.vectorvest.com/e-reports/webcast-pdfs/AU_PPX_SESSION_3_BW.pdf).
- Onafhankelijke reviews ([TraderHQ](https://traderhq.com/vectorvest-review-insights/),
  [Liberated Stock Trader](https://www.liberatedstocktrader.com/vectorvest-review/)) vonden geen onafhankelijke
  backtest van de timingsignalen. De resultaten op de VectorVest-sites zijn voorbeelden, geen statistiek.

**Wat VectorVest zelf beschrijft** (alles op de VVC, het gemiddelde van ±8.000 Amerikaanse aandelen):

| Systeem | Regel | Volgens VectorVest |
|---|---|---|
| Primary Wave | slot VVC hoger dan een week eerder = Up, lager = Dn | het snelst, "fairly reliable" |
| Two-Week Rule | twee weken omhoog zonder tussenliggende daalweek = Up (omgekeerd Dn) | trager, ±1 keer per jaar omgedraaid |
| Confirmed Up/Dn | Two-Week Rule + de BSR (aandelen met koopadvies / verkoopadvies) kruist 1,00 | het traagst, het betrouwbaarst |
| DEW (ProTrader) | Up: slot boven de 30-daagse **gewogen** MA én DPO > 0. Down: slot onder de 30-WMA én DPO < 0. "It's that simple." | gematigd; sneller dan Confirmed, betrouwbaarder dan de Primary Wave |
| "Prudent-Aggressive" | slot boven de 40-daagse MA én MTI > 1,00 | |

- **DPO:** het slot van n/2+1 dagen geleden min het SMA van n dagen, met n = 20 (VectorVest-blog en -webinar).
- **Enveloppen:** zelden gebruikte uitzondering (bij een slot buiten de envelop volstaat één van beide voorwaarden).
  Hun breedte is niet gepubliceerd; daarom laten we ze weg.
- **BSR en MTI:** niet na te maken zonder de VectorVest-ratings van alle aandelen.

## Test V1 (vooraf vastgelegd, 2026-10-30): de VectorVest-timing (DEW) op de aandelenindices

Tests 15 en 16 pasten een benadering van RT, MTI en DEW toe op forex. Hier staan de **gepubliceerde** regels op de
markt waarvoor ze gemaakt zijn. SPX500 en NAS100 dienen als benadering van de VVC (dagdata 2005-2025).

**Regels** (dagelijks na het slot, gesloten candles; de positie geldt van dat slot tot het volgende):
- **DEW:** Up -> long. Down -> long-only: uit de markt; long/short: short. Geen nieuw signaal: de positie blijft.
- **Primary Wave:** slot > slot van 5 handelsdagen eerder -> long, anders uit (of short bij long/short).
- **Two-Week Rule:** op afgesloten weekcandles, twee weken omhoog -> long tot twee weken omlaag.
- Kosten per positiewissel (`test2.cost_price`). Swaps niet meegeteld; die zijn bij timing lager dan bij kopen en
  houden, omdat je minder dagen in de markt zit.

**Beslissend: DEW long-only tegenover kopen en houden**, op het gemiddelde van SPX500 en NAS100. Slaagt als in elke
periode (2005-14, 2015-20, 2021-25) zowel de Sharpe minstens zo hoog is als die van kopen en houden, als de maximale
drawdown kleiner is. Dat is de voorsprong die voor de 5ers telt: hetzelfde rendement per risico met minder diepe
dalen.

**Gerapporteerd, niet beslissend:** DEW long/short, Primary Wave, Two-Week Rule, UK100 (2015-25), goud. Een geslaagde
regel gaat naar een eigen vastlegging: de 5ers-challenge op het echte 15-minutenpad (`research/rnd/prop_m15.py`).

### Uitkomst V1: verworpen
`python research/edge/vv_timing.py`. Gemiddelde van SPX500 en NAS100, na kosten, zonder swaps:

| | 2005-14 | 2015-20 | 2021-25 |
|---|---|---|---|
| Kopen en houden | +7,8%/j, Sharpe 0,47, maxDD -55% | +15,3%/j, Sharpe 0,82, maxDD -31% | +14,6%/j, Sharpe 0,79, maxDD -30% |
| **DEW long-only** | +3,9%/j, Sharpe 0,39, maxDD -31% | +9,5%/j, Sharpe 0,79, maxDD -23% | +3,7%/j, Sharpe 0,35, maxDD -29% |
| DEW long/short | -2,8%/j, Sharpe -0,05 | +1,9%/j, Sharpe 0,20 | -8,0%/j, Sharpe -0,37 |
| Primary Wave long-only | -4,7%/j, Sharpe -0,34 | +3,0%/j, Sharpe 0,32 | +3,3%/j, Sharpe 0,33 |
| Two-Week Rule long-only | +0,6%/j, Sharpe 0,11 | +1,4%/j, Sharpe 0,18 | +7,4%/j, Sharpe 0,64 |

- De DEW verkleint de drawdown in elke periode, maar levert per eenheid risico **minder** op dan kopen en houden
  (Sharpe 0,39 / 0,79 / 0,35 tegenover 0,47 / 0,82 / 0,79). De lat vroeg beide; dat is dus niet gehaald.
- Een kleinere drawdown krijg je goedkoper door gewoon kleiner in te zetten. Kopen en houden op halve grootte heeft
  ongeveer dezelfde maxDD als de DEW (-15 tot -28%), met een hogere Sharpe.
- Short gaan op Down-signalen verliest bij alle drie de systemen; de Primary Wave long/short tot -18%/j.
- UK100 en goud: hetzelfde beeld (de DEW is lager dan kopen en houden, behalve de drawdown).
- Sluit aan bij de onafhankelijke reviews: er is geen controleerbaar bewijs dat de VectorVest-timing kopen en houden
  verslaat.

**Stand.** Ook de VectorVest-timing (DEW, Primary Wave, Two-Week Rule) geeft op de indices geen voorsprong boven
kopen en houden. Kopen en houden van indices en goud blijft het enige positieve; de schaal (volatiliteit) is de
knop voor de drawdown, niet de timing. Open: de swaps in de prop-simulatie.
