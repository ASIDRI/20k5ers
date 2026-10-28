# R&D: een echte edge zoeken

Uitgangspunt: de oude bot had geen edge (zijn winst kwam uit een lek) en de video-methode als regels evenmin
(test 1-3, `docs/STRATEGY_FROM_VIDEOS.md`). Dit programma zoekt systematisch verder met dezelfde bouwstenen
(S/R van maand en week, structuur, fib, liquiditeit, candlepatronen op week, dag en 4u), zonder in de val te
lopen die het project eerder deed: net zo lang varianten proberen tot er een mooi lijkt.

## Spelregels

1. **Drie periodes, strikt gescheiden.**
   - Ontdekken: 2015-2020.
   - Bevestigen: 2021-2025.
   - Slotkluis: 2005-2014 (forex). Alleen voor finalisten, één keer, met criteria die vooraf vastliggen.
2. **Register.** Elke geteste variant komt in `research/rnd/registry.csv` (wat, wanneer, uitkomst). Het aantal
   varianten bepaalt de lat: een variant moet in de ontdekperiode een t-waarde >= 3 halen (niet 2), daarna in de
   bevestigingsperiode dezelfde richting en minstens de helft van het effect.
3. **Altijd na kosten** (spread en slippage per symbool, zoals de live simulator).
4. **Alles point in time:** alleen afgesloten candles; niveaus alleen uit data tot dat moment; swings pas als bevestigd.
5. **Eerst kijken of er informatie in een signaal zit, dan pas een trade ontwerpen.** Een signaal zonder
   voorspellende waarde wordt met geen enkele SL/TP-combinatie winstgevend.

## Fases

| Fase | Wat | Uitkomst |
|---|---|---|
| 0 | Onderzoeksgereedschap: gebeurtenissen, uitkomstmeting, kosten, register | `research/rnd/` |
| 1 | **Gebeurtenisstudies op week**: engulfing, pin bar (afwijzingswick), sweep van de vorige week-high/low met slot terug (SFP); telkens op een S/R-niveau van maand/week of niet; met of tegen de trend | Welke signalen voorspellen de volgende 1-4 weken? |
| 2 | Hetzelfde op **dag en 4u**, en liquiditeit: sweeps van vorige dag/week/maand high-low, gelijke toppen/bodems, FVG | Idem, lagere timeframes |
| 3 | **Combinaties** van wat in fase 1-2 overeind bleef (bv. weeksignaal + 4u-instap), en de trade zelf: instap (markt, limiet op 0,5/0,618/0,705/0,786), SL, doelen (vaste R, volgende niveau) | Kleine, vooraf gekozen raster, geen eindeloos zoeken |
| 4 | **Robuustheid**: per asset, per jaar, buurparameters, dubbele kosten, walk-forward | Valt het niet om bij kleine wijzigingen? |
| 5 | **Slotkluis 2005-2014** voor maximaal 3 finalisten, met vooraf vastgelegde criteria | Ja/nee |
| 6 | **Prop-firm**: de finalist in de live-bot, in de gekeurde replay (15 min, strikte broker, 5ers-regels, risico per trade) | Haalt hij de challenge zonder breach? |

## Meting in fase 1-2

Instap op de open van de eerste candle na het signaal. Hoofdmaat (vooraf gekozen):
- **P(+1 ATR vóór -1 ATR)**, met de ATR van de signaal-timeframe; zonder edge is dat ±50% min kosten;
- **rendement na 1, 2 en 4 perioden** in ATR, in de richting van het signaal.
Vergelijking telkens met hetzelfde patroon elders (niet op een niveau) en met alle candles (basislijn).
