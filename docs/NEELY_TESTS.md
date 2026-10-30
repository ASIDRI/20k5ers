# Neely Elliott Wave: tests

Strategie en bouwplan: `docs/NEELY_BOT_STRATEGIE.md` (uit "Mastering Elliott Wave", hoofdstuk 1-5). De Neely-strategie
vervangt de strategie van test 20-33 (`research/strategy/test20.py`, fib body -> wick). **Alleen de strategie
verandert. De motor blijft dezelfde:**
- alleen gesloten candles (`backtest/src/candle_avail.complete_times`);
- instap op het slot van de bevestigende candle, uitstap met `test18.follow` / `test18.managed`: de stop gaat vóór het
  doel als ze in dezelfde candle vallen, geen tijdslimiet;
- kosten per symbool (`research/costs.json`, `test2.cost_price`);
- evaluatie met `t17_eval`: één positie per richting per instrument, drie periodes, dezelfde lat.

Code: `research/neely/neely_core.py` (laag 0 t/m 6, ongewijzigd uit het bouwplan), `research/neely/neely_bt.py`
(setups), `research/neely/neely_eval.py` (rapport). Tests: `research/neely/test_neely_core.py` (9 boekgevallen) en
`research/neely/test_neely_bt.py`. Die laatste knipt de data af op een datum en controleert dat elke trade vóór die
datum precies gelijk blijft (EURUSD, GBPJPY, XAUUSD dag; EURUSD week). Zo ziet de scan geen toekomst.

## Test N1 (vooraf vastgelegd, 2026-10-30): setup A en B uit het bouwplan

**Laag 0 (data).** Per candle twee punten, de high en de low **in de volgorde waarin ze optraden** (boek optie b).
De volgorde komt uit het lagere tijdframe: 4u binnen een dag, dag binnen een week. Als de high en de low in dezelfde
sub-candle vallen of er geen sub-data is, geldt: een dalende candle maakte eerst zijn high, een stijgende eerst zijn low.
**Laag 1.** Monowaves op die reeks (`find_monowaves`). Een monowave is pas af als het volgende punt omkeert, en is
bekend bij het slot van de candle waarin dat gebeurt. De lopende (laatste) monowave wordt nooit gebruikt.
**Graad.** Hoofdstuk 7 (Compaction) ontbreekt in de pdf, dus graad = tijdframe: monowaves op de dag (hogere tijdframe
week) en op de week (hogere tijdframe maand).

**Setup A: thrust na een contracting triangle.** De laatste vijf afgeronde monowaves a-e voldoen aan `triangle_check`
(minimumregels uit het boek) met een contracting variant, en elk paar buren voldoet aan Similarity and Balance
(`similar`). De thrust gaat tegen a in (de kant van b en d). Bevestiging: een candle **sluit** voorbij het eind van d
en voorbij de b-d-lijn. Ongeldig vóór de bevestiging: een candle handelt voorbij het eind van e, of er komt geen
bevestiging binnen de duur van de triangle (minimaal 3 candles). Stop: 0,1 ATR voorbij het eind van e.
T1 (beslissend): eind van e + 75% van de breedste poot. T2: 100%. Beheer: de helft op T1, stop naar instap, de rest
op 125%.

**Setup B: hervatting na een voltooide zigzag of flat.** De laatste drie afgeronde monowaves a, b, c voldoen aan
`abc_classify` (zigzag of flat), met a ~ b en b ~ c. DETOUR (blz. 4-8): als de twee golven vóór a samen met a, b, c
`impulse_check` doorstaan, is het een impuls en geen correctie, dus overslaan. Trade tegen a in. Bevestiging: een
candle **sluit** voorbij de 0-B-lijn (begin a tot eind b). Bij een truncated zigzag moet daarnaast minstens 81% van de
zigzag terug zijn, bij een elongated zigzag meer dan 61,8% van c. Ongeldig: een candle voorbij het eind van c, of
geen bevestiging binnen de duur van het patroon. Stop: 0,1 ATR voorbij het eind van c. T1 (beslissend): begin van a
(volledige terugname). T2: eind van c + 161,8% van a. Beheer: de helft op T1, stop naar instap, de rest op T2.

**Filters (bekend bij de instap):**
- `htf`: richting van het hogere tijdframe, namelijk het laatste **afgesloten** week- of maandslot tegenover het
  gemiddelde van de laatste 10. Boek: het hoogste niveau levert de richtingsfilter.
- `lab_ok`: de startlijsten van de Pre-Constructive Rules (bouwplan 5.2). Elke patroongolf waarvan de Retracement
  Rule bij de instap al vaststaat (m2 af), moet het label dat het patroon nodig heeft in zijn lijst hebben. Nodig
  zijn: triangle F3 c3 c3 sL3 L3, zigzag 5 F3 L5, flat F3 c3 L5. Golven waarvan m2 nog niet af is, worden niet
  getoetst (`lab_n` = aantal getoetste golven).

**Beslissend, vier cellen (setup A/B x dag/week):** `htf == 1 & lab_ok`, `R_t1`, één positie per richting, 34
instrumenten (de 28 forexparen, XTI_USD en UK100_USD, plus XAUUSD, XAGUSD, NAS100USD en SPX500USD), instappen
2005-2025. Een cel slaagt als elke periode (2005-14, 2015-20, 2021-25) gemiddeld boven 0 zit met PF >= 1,05, en de
drie samen t >= 2,0 halen. Omdat er vier cellen zijn, is een geslaagde cel nog geen edge. Hij moet daarna ook slagen op
de 31 holdout-instrumenten van test 33 (eigen vastlegging). Gerapporteerd naast de beslissende regel: alleen htf,
alleen labels, alle patronen, T2, beheer, en kosten <= 0,1R.

Eerlijkheidsnoot: vóór deze vastlegging is de code één keer op EURUSD (dag) gedraaid om te controleren dat hij werkt.
Er zijn daarna geen regels of parameters aangepast. Wel zijn de uitstappen vervangen door die van de bestaande motor
(eerst stond er een tijdslimiet in).

### Uitkomst test N1: verworpen (alle vier de cellen)
Run: `python research/neely/neely_bt.py <34 symbolen> --tf D1` (en `--tf W1`), daarna `python research/neely/neely_eval.py`.
Beslissend (`htf == 1 & lab_ok`, `R_t1`, één positie per richting, na kosten):

| Cel | Trades | 2005-14 | 2015-20 | 2021-25 | t |
|---|---|---|---|---|---|
| A triangle-thrust, dag | 2.403 | -0,19R (PF 0,61) | -0,15R (PF 0,64) | -0,08R (PF 0,78) | -8,4 |
| B zigzag/flat-hervatting, dag | 14.476 | -0,09R (PF 0,82) | -0,11R (PF 0,77) | -0,07R (PF 0,84) | -9,4 |
| A triangle-thrust, week | 479 | +0,02R (PF 1,06) | +0,01R (PF 1,03) | -0,09R (PF 0,75) | -0,3 |
| B zigzag/flat-hervatting, week | 2.884 | -0,03R (PF 0,92) | -0,08R (PF 0,83) | -0,08R (PF 0,82) | -3,0 |

- **Ook vóór kosten geen voordeel.** Bruto `R_t1`: dag A -0,08R, dag B -0,03R, week A +0,02R, week B -0,03R. De
  kosten (mediaan 0,02-0,05R) zijn dus niet de oorzaak.
- **De patronen zijn klein.** Zonder Compaction (hoofdstuk 7) zijn het patronen van losse monowaves: mediaan 3-4
  candles, stop ±0,8-1,0 ATR, T1 op 0,5-0,7R. Op de dag geeft setup B ±20 trades per instrument per jaar.
- **De labelfilter (startlijsten 5.2) filtert bij setup B niets.** Een zigzag-a die ≤ 61,8% wordt teruggenomen valt
  altijd in Rule 1-3 (alle hebben :5), en een b die door c > 100% wordt teruggenomen valt in Rule 5+ (heeft :F3).
  Bij flats is het bijna net zo. Zonder de volledige alinea's per Conditie (bouwplan 5.3-5.4) zegt de startlijst te
  weinig. Bij triangles zijn bij de instap gemiddeld maar 2,4 van de 5 golven toetsbaar (m2 nog niet af).
- Gerapporteerd, niet beslissend: week A met beheer (`R_m`) +0,09 / +0,11 / +0,00R (PF 1,28 / 1,33 / 1,00, t 1,7).
  Dit is één van ±60 gerapporteerde cijfers en haalt de lat ook niet (2021-25 = 0). Het is daarom geen kandidaat. Een
  eventuele vervolgtest moet eerst vooraf worden vastgelegd en dan gemeten op de 31 holdout-instrumenten van test 33.

**Conclusie:** de standaardpatronen uit hoofdstuk 5 (triangle-thrust, hervatting na zigzag/flat), herkend op
monowaves per tijdframe en verhandeld op gesloten candles, voorspellen op deze 34 instrumenten niets, op dag noch week.
Wat ontbreekt om het boek eerlijker te testen, zijn hoofdstuk 6-12: Compaction/graad, Post-Constructive bevestiging,
complexe correcties en de Exception Rule. Ook de volledige opzoektabel van 5.3 ontbreekt. Zonder die onderdelen is
"Neely" hier in feite patroonherkenning op swings, en die heeft net als de eerdere tests geen voorsprong.

## Test N2 (vooraf vastgelegd, 2026-10-30): EURUSD tellen zoals Neely, met een reconstructie van hoofdstuk 6-12

Vraag van de trader: de ontbrekende hoofdstukken zelf invullen door de markt te tellen en te volgen zoals Neely,
alleen voor EURUSD. Code: `research/neely/neely_count.py`. Alles wat met **[R]** is gemarkeerd, is een **eigen
reconstructie**, niet gelezen uit de pdf.

**De teller (online, één gesloten candle per stap).**
- Twee tellers, omdat het boek met meerdere grafieken werkt: dag (volgorde high/low uit 4u) en week (volgorde uit
  dag). Elk houdt één reeks golven bij, monowaves en samengevoegde patronen, steeds afwisselend in richting.
- Patronen: impuls 5-3-5-3-5, terminal 3-3-3-3-3 met overlap, triangle, zigzag 5-3-5 en flat 3-3-5, met de toetsen uit
  hoofdstuk 5.
  - [R, hfst. 8] dubbele correctie 3-x-3: x kleiner dan beide, de tweede voorbij de eerste.
  - [R, hfst. 8] driedubbele 3-x-3-x-3, op dezelfde manier.
- Structuur van een monowave: :5 of :3 volgens zijn startlijst (5.2). Een samengevoegd patroon is :5 (impuls) of :3.
- Similarity and Balance gelden voor elk paar buren. Daarnaast DETOUR: de impuls gaat vóór de zigzag die erin past.
- [R, hfst. 6, Post-Constructive stage 1] Een patroon is af als de prijs de 2-4-lijn (b-d bij een triangle, 0-B bij
  een zigzag/flat/dubbele) breekt vóórdat het eind van de laatste golf wordt overschreden. `op_tijd` = die breuk kwam
  binnen de tijd van de laatste golf plus één candle.
- [R, hfst. 7, Compaction] Een afgerond patroon wordt één golf, met Complexity = hoogste binnen + 1. Bij meerdere
  tegelijk gaat het patroon met de minste prijs x tijd voor (7.1).

**Aanpassingen aan de teller, gedaan voordat er één rendement bekeken is.** Ze zijn gebaseerd op de vorm van de
telling, niet op winst. Ze zijn nodig omdat de telling anders niet opbouwt (eerst bleven er 3.245 losse golven en
Complexity max 3):
1. Een samengevoegd patroon moet netto in de richting van zijn eerste golf eindigen. Anders breekt de afwisseling.
2. [R, 7.2 / hfst. 12 missing waves] Een golf die kleiner is dan 1/3 van beide buren, in prijs én tijd, hoort bij de
   grotere beweging en wordt opgenomen ("opgenomen").
3. DETOUR-voorrang voor de impuls.
4. Voor het tellen geldt de tijdregel van stage 1 niet, voor het handelen wel (`op_tijd`).
5. [R] De Complexity-regel (7.4) geldt alleen tussen samengevoegde patronen. Een dagmonowave kan intraday-structuur
   verbergen.
6. De driedubbele correctie toegevoegd.

Ook zo bouwt de telling **niet** op tot de grote meerjarige graad. Op de dag zijn de grootste patronen een paar weken,
op de week een paar maanden (`docs/neely_eurusd_D1.png`, `docs/neely_eurusd_W1.png`).

**Handelen** (zelfde motor als N1). Bij het slot van de candle die een patroon bevestigt, wordt er een trade genomen
tegen de laatste golf in.
- Doel T1 bij zigzag, flat, dubbele, driedubbele en terminal: het begin van het patroon (volledige terugname).
- Doel T1 bij een triangle: eind van e + 75% van de breedste poot.
- Doel T1 bij een impuls [R, stage 2]: het eind van golf 4, of 61,8% terug van golf 5 als 5 de verlengde is.
- Stop: 0,1 ATR voorbij het eind van het patroon.
- Uitstap: `test18.follow`; kosten van EURUSD.

**Beslissend:** `cx >= 2 & op_tijd`, `R_t1`, één positie per richting, EURUSD, instappen 2005-2025. Er zijn twee
cellen (dagteller en weekteller). Een cel slaagt als elke periode (2005-14, 2015-20, 2021-25) gemiddeld boven 0 zit met
PF >= 1,05, en de drie samen t >= 2,0 halen. Omdat dit één instrument is, is een geslaagde cel alleen een kandidaat.
Hij moet dan eerst op de andere 33 instrumenten getest worden (eigen vastlegging). Gerapporteerd: per Complexity, per
patroon, met en zonder `op_tijd`.
