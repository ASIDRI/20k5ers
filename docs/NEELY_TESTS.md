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

### Uitkomst test N2 (EURUSD): verworpen (beide cellen)
Run: `python research/neely/neely_count.py --tf D1` en `--tf W1`, daarna `python research/neely/n2_eval.py`.

| Teller | Trades | 2005-14 | 2015-20 | 2021-25 | t |
|---|---|---|---|---|---|
| dag, `cx >= 2 & op_tijd` | 647 | -0,09R (PF 0,87) | -0,31R (PF 0,58) | -0,37R (PF 0,47) | -3,3 |
| week, `cx >= 2 & op_tijd` | 122 | -0,28R (PF 0,60) | -0,29R (PF 0,54) | +0,17R (PF 1,33) | -1,5 |

- Hoger in de telling (Complexity >= 3) is niet beter: op de dag +0,04 / -0,43 / -0,36R.
- Per patroon (dag, beslissend): driedubbel -0,46R (194), triangle -0,27R (134), flat -0,17R (148), zigzag 0,00R (78),
  terminal **+0,65R (44)**. Op de week ook terminal +0,29R (8). Dit zijn kleine aantallen en het is één van ±20
  gerapporteerde cijfers; zie dit hooguit als idee voor een vooraf vast te leggen test op de andere 33 instrumenten.
  Het is geen resultaat.
- Lookahead-test: de teller is op 2013 en 2022 (dag) en 2017 (week) afgeknipt. Alles ervóór blijft gelijk.

**Huidige telling EURUSD** (data tot 14-12-2025; grafieken `docs/neely_eurusd_D1.png`, `docs/neely_eurusd_W1.png`):
- **Week:** na de bodem van februari 2025 (1,0360) volgt een reeks :3's omhoog. Eerst een dubbele, dan een zigzag
  en een driedubbele tot 1,1830 (juni). Daarna een triangle (Complexity 2) tot 1,1590 en drie zijwaartse flats tussen
  1,149 en 1,173. Laatste afgeronde golf: een zigzag omhoog van 1,1491 naar 1,1682 (november). Er wacht geen patroon
  op bevestiging.
- **Dag:** een driedubbele omhoog (Complexity 3) van 1,1491 (20-11) naar 1,1763 (10-12), daarna een flat omlaag naar
  1,1727. Er wacht geen patroon op bevestiging.
- Volgens deze telling is alles sinds februari 2025 opgebouwd uit correctieve stukken (:3), zonder één impuls. In
  Neely's taal is dat een complexe correctie, geen nieuwe trend. Gezien de uitkomst hierboven is dat geen
  handelsadvies.

**Conclusie N2.** De reconstructie telt EURUSD wel over meerdere graden, zonder toekomst te zien, maar de bevestigde
patronen voorspellen de volgende beweging niet: de trades verliezen op dag en week. Twee grenzen blijven:
- De telling komt niet verder dan weken (dag) of maanden (week). De grote meerjarige graad bouwt deze teller niet op.
- De regels uit hoofdstuk 6-12 zijn gereconstrueerd, niet gelezen. Een echte toets van Neely vraagt die hoofdstukken.

## Test N3 (vooraf vastgelegd, 2026-10-30): stops, doelen en instap met Optuna, alleen op 2005-2014

Aanleiding: in N1 klopt de richting vaak. T1 wordt vóór de stop geraakt in 55% (A dag), 51% (B dag), 63% (A week) en
56% (B week) van de gevallen. Maar met een doel op ±0,5R is 60-72% nodig om quitte te spelen. De vraag is of andere
stops, doelen en instappen die voorsprong in winst omzetten. Code: `research/neely/n3_optuna.py`.

**Signalen ongewijzigd:** de N1-signalen met de beslissende filter `htf == 1 & lab_ok`, 34 instrumenten, vier cellen
(setup A/B x dag/week). Alleen de trade rond het signaal verandert:

| Parameter | Betekenis | Bereik |
|---|---|---|
| `s` | stop `s` x ATR voorbij het ongeldigheidspunt (eind van e / c) | 0 - 1,5 |
| `e` | 0 = markt op het slot; > 0 = limietorder `e` x (slot - stop) terug richting de stop, geldig voor de duur van het patroon | 0 - 0,6 |
| `k` | doel in R vanaf de vulling | 0,3 - 5 |
| `be` | stop naar instap zodra de prijs `be` x R mee is (of nooit) | 0,3 - 3 / uit |
| `H` | tijdstop: uit op het slot `H` candles na de vulling | 2 - 120 |

**Vulling en uitstap (voorzichtige kant):**
- Een limietorder vult op zijn prijs.
- In de vulcandle telt alleen de stop; het doel telt pas vanaf de volgende candle.
- Vallen stop en doel in dezelfde candle, dan telt de stop eerst. Een gap voorbij de stop wordt uitgevoerd op de open.
- Kosten per symbool. Eén positie per richting per instrument.

**Optuna:** TPE, seed 0, 300 trials per cel. Optuna ziet **alleen trades met signaal vóór 2015**. Doel: de t-waarde
van R per trade, met minstens 100 trades.

**Beslissend:** per cel worden de beste parameters van 2005-2014 ongewijzigd toegepast op 2015-2020 en 2021-2025.
- Een cel slaagt als beide periodes gemiddeld boven 0 zitten met PF >= 1,05, en de twee samen t >= 2,0 halen.
- Bij vier cellen geldt een geslaagde cel als kandidaat. Die moet daarna slagen op de 31 holdout-instrumenten van
  test 33, met dezelfde parameters (eigen vastlegging).
- Gerapporteerd: het resultaat op 2005-2014 zelf (dat is per constructie te mooi) en een N1-achtige referentie (markt
  op het slot, stop 0,1 ATR, doel = mediaan rr1).

### Uitkomst test N3: verworpen (alle vier de cellen)
Run: `python research/neely/n3_optuna.py --trials 300` (17 seconden; beste parameters in `research/neely/out/n3_best.json`).

| Cel | Beste op 2005-14 | 2005-14 (gezien) | 2015-20 | 2021-25 | t buiten |
|---|---|---|---|---|---|
| A dag | s 1,45, e 0,54, k 3,3, H 76 | +0,04R | -0,05R | -0,31R | -2,0 |
| B dag | s 1,49, e 0,27, k 4,6, be 1,15, H 95 | +0,04R | -0,04R | -0,14R | -2,6 |
| A week | s 0,43, e 0,09, k 2,3, H 119 | +0,25R | -0,05R | +0,06R | 0,0 |
| B week | s 1,33, e 0,21, k 2,3, H 119 | +0,26R (t 3,6) | -0,12R | +0,25R | 0,7 |

- Optuna vond telkens hetzelfde soort oplossing: een stop ver voorbij het ongeldigheidspunt (tot 1,5 ATR), een doel
  van 2-5R en een instap via een terugval. Dat is het omgekeerde van N1 (vaak klein winnen). Het slaagpercentage zakt
  daarbij naar 12-40%.
- In 2005-2014 ziet dat er goed uit (B week t 3,6), maar in de periodes die Optuna niet zag, valt het terug naar rond
  nul of negatief. Dat is het patroon van overfitting: wat Optuna vond, was ruis in 2005-2014.
- De N1-achtige referentie verliest in alle periodes, met slaagpercentages van 56-68%.
- Les: de richtingstreffer van 55-63% hangt aan een doel dicht bij de instap. Zodra het doel verder ligt, is er geen
  voorsprong meer. De telling voorspelt een kleine terugbeweging, geen beweging waaraan iets te verdienen is na
  stop en kosten.

## Test N4 (vooraf vastgelegd, 2026-10-30): Optuna op de signalen én de trade, alleen op 2005-2014

Vraag van de trader: Optuna ook laten kiezen welke signalen en setups er gehandeld worden. Code:
`research/neely/n4_optuna.py`.

**Signalen.** Eén ruime run van N1 (`neely_bt.py --loose --sim-min 0.2 --prefix n4_<tf>_`), met daarin elk bevestigd
patroon met zijn kenmerken. Dat omvat ook expanding triangles, patronen die DETOUR een impuls noemt, en setups zonder
ruimte tot T1. Optuna (TPE, seed 0, 500 trials per tijdframe, dag en week apart) kiest:
- Welke setups: A, B of beide; triangles alleen contracting of alle; zigzag, flat of beide; DETOUR-patronen wel/niet.
- Drempels:
  - Similarity 0,2-0,6 (boek: 1/3);
  - hoger tijdframe: mee / niet tegen / maakt niet uit;
  - startlijsten wel/niet;
  - grootte van het patroon >= 0-5 ATR;
  - bevestiging hooguit 0-20 candles na het eind;
  - slot minstens 0-1 ATR voorbij de lijn;
  - instap hooguit 0,5-6 ATR van het ongeldigheidspunt.
- Trade: stop, limietinstap, doel in R, stop naar instap en tijdstop, zoals in N3. Dezelfde vul- en uitstapregels.
- Doel: de t-waarde van R per trade op signalen vóór 2015, met minstens 150 trades.

**Beslissend, per tijdframe (2 cellen), twee stappen. Beide moeten slagen.**
1. Buiten de steekproef: met de beste parameters van 2005-2014 zitten 2015-2020 en 2021-2025 elk gemiddeld boven 0
   met PF >= 1,05, en de twee samen halen t >= 2,0. Kanttekening: deze jaren zijn in N1-N3 al gemeten, al heeft
   Optuna ze niet gezien.
2. Alleen als stap 1 slaagt: de **31 holdout-instrumenten van test 33**, die nooit in een Neely-test zaten, met
   dezelfde parameters. Elke periode (2005-14, 2015-20, 2021-25) moet gemiddeld boven 0 zitten met PF >= 1,05, en de
   drie samen moeten t >= 2,0 halen.

Een cel die beide haalt, is een kandidaat voor papertrading. Het is nog geen bewezen edge.

### Uitkomst test N4: verworpen in stap 1 (beide cellen); holdout niet gebruikt
Run: `python research/neely/n4_optuna.py --trials 500` (35 seconden; parameters in `research/neely/out/n4_best.json`).

| Tijdframe | Signalen | Beste op 2005-14 | 2005-14 (gezien) | 2015-20 | 2021-25 | t 2015-25 |
|---|---|---|---|---|---|---|
| Dag | 92.121 | t 3,72 | +0,19R (431, PF 1,43) | -0,15R (121, PF 0,75) | -0,18R (88, PF 0,71) | -2,2 |
| Week | 18.215 | t 4,61 | +0,44R (653, PF 1,64) | -0,23R (397, PF 0,71) | +0,04R (299, PF 1,05) | -1,5 |

- Dag: Optuna koos contracting triangles plus zigzags (geen flats), Similarity >= 0,60, een patroon >= 2,4 ATR en een
  bevestiging binnen 3 candles, minstens 0,83 ATR voorbij de lijn. Daarbij een stop 1,4 ATR voorbij het
  ongeldigheidspunt en een doel van 1,1R.
- Week: triangles plus flats, startlijsten aan, een doel van 5R.
- De twee tijdframes kozen dus verschillende setups, en geen van beide hield stand. Hoe meer vrijheid Optuna kreeg,
  hoe mooier 2005-2014 (t 3,7-4,6) en hoe slechter de jaren daarna. Dat is overfitting.
- De 31 holdout-instrumenten van test 33 zijn **niet** gebruikt en blijven onaangeroerd.

**Stand na N1-N4.** Vaste boekregels (N1), een telling over meerdere graden (N2), geoptimaliseerde stops en doelen
(N3) en geoptimaliseerde signalen en setups (N4): geen enkele versie houdt stand buiten de data waarop ze gekozen is.
De Neely-patronen (hoofdstuk 2-5, plus deze reconstructie van 6-12) voorspellen op deze data geen beweging waaraan na
kosten iets te verdienen is.

## Controle (beschrijvend, 2026-10-30): is de trefkans van Neely beter dan toeval?

In N3 is de trefkans van 55-63% in N1 gelezen als richtingsvoorsprong. **Dat was onjuist.** Bij een doel op ±0,5R en
een stop op 1R raakt ook een munt het doel in ±67% van de gevallen (zonder drift: kans = stop / (stop + doel)). De
eerlijke vergelijking is daarom: dezelfde trades, met dezelfde stop- en doelafstand en dezelfde motor, maar in de
omgekeerde richting. Zo zijn de geometrie, de candle-regels en de periode gelijk, en verschilt alleen de richting.
Bruto, zonder kosten:

| Setup | Trades | Neely-richting | Omgekeerd | Verschil (95%) |
|---|---|---|---|---|
| A triangle, dag | 6.828 | 59,9% / -0,088R | 64,0% / -0,018R | -0,069R (±0,036) |
| B zigzag/flat, dag | 31.422 | 53,6% / -0,028R | 53,8% / -0,033R | +0,005R (±0,022) |
| A triangle, week | 1.405 | 65,0% / -0,038R | 64,3% / -0,035R | -0,003R (±0,077) |
| B zigzag/flat, week | 6.404 | 57,0% / -0,020R | 56,1% / -0,024R | +0,005R (±0,045) |

De richting die Neely aanwijst, is niet beter dan de omgekeerde richting. Bij de triangle-thrust op de dag is ze zelfs
slechter. De hoge trefkans kwam alleen uit de plaats van het doel. Er is dus geen voorsprong die met stops, doelen,
positiegrootte of kansberekening in winst om te zetten is.

**Stop en doel in dezelfde dagcandle (2026-10-30).** De motor (`test18.follow`) kent na de instap alleen dagcandles.
Raakt één dag zowel de stop als het doel, dan is uit die candle niet af te lezen wat eerst kwam. De motor neemt dan
de stop (voorzichtig). Dit gaat over de **uitvoering** van een open trade, niet over het signaal: het signaal
gebruikt alleen gesloten candles. Opgelost met de 4u-candles van die dag, in tijdsvolgorde:
- Het gebeurt bij 5,9% (triangle) en 2,3% (zigzag/flat) van de trades. 4u beslist in 85-91% van die gevallen.
- Triangle, dag: Neely -0,029R tegen omgekeerd +0,030R.
- Zigzag/flat, dag: Neely -0,007R tegen omgekeerd -0,015R.
- De trefkansen komen dan uit op die van toeval (64,3% tegen ±66%; 55,1% tegen ±55,6%).
Beide richtingen gaan iets omhoog; het verschil tussen Neely en omgekeerd verandert niet.
