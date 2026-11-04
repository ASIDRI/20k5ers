# Setups van de trader - stap voor stap gedocumenteerd

Doel: elke setup die de trader aanlevert vastleggen zoals hij hem leest (top-down: maand -> week -> dag), met de
prijzen nagerekend op onze eigen data (`load(sym, "D1")`, broker-tijd: een dagkaars met tijd `... 21:00` is de
handelsdag erna). **Nog niet verwerkt in de engine**; eerst alle setups verzamelen, daarna de gemeenschappelijke regels
eruit halen en vooraf vastleggen.

Per setup: context, trigger, fib, instap, stop, targets, beheer, uitkomst, en wat het betekent voor de engine (alleen
notities).

## Overzicht en win rate
Beheer van de trader: **T1 = -0,2**, daarna stop een beetje in winst; **T2 = -0,58** (vanaf setup 6; eerder -0,6, en
-0,65 in setup 1 omdat daar de maand-S/R lag), daarna stop naar **fib 0**. Hoeveel op T1 gesloten wordt, ligt nog niet vast; hieronder ter vergelijking 50% op T1.

| # | instrument | richting | instap | diepte | T1 | T2 | R bij T1 | R bij T2 | 50% T1, rest T2/stop |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EURUSD | short | 10 jul 2018 | 0,83 | ja | ja (-0,65) | +2,6 | +3,6 | +3,1R |
| 2 | EURUSD | short | 16 okt 2018 | 0,41 (lont 0,55) | ja | ja (-0,6) | +1,8 | +2,9 | +2,4R |
| 3 | EURUSD | short | 1 feb 2019 | 0,66 | ja | nee, stop in winst | +1,8 | - | ± +1,5R |
| 4 | EURUSD | short | 2 mei 2019 | 0,31 (lont 0,796) | nee | nee | - | - | **-1R** |
| 5 | EURUSD | short | - (juli 2019) | geen pullback naar het dag-S/R | - | - | - | - | geen trade |
| 6 | EURUSD | short | 9 aug 2019 | 0,69 | ja | ja (-0,58) | +2,6 | +3,7 | +3,2R (rest op fib 0: +2,0R) |
| 7 | EURUSD | short | 21 nov 2019 | 0,38 (lonten 0,59) | nee | nee | - | - | **-1R** |
| 8 | EURUSD | short | - (jan 2020) | tikt alleen de fib-start, dag-S/R net erboven, geen patroon | - | - | - | - | geen trade (uitzondering later te testen) |
| 9 | EURUSD | short | - (feb 2020) | prijs schiet door beide dag-S/R, slot boven de swing high | - | - | - | - | geen trade |

**Win rate: 4 / 6 (67%) T1 geraakt; T2 3 / 6** (setup 5, 8, 9: geen trade). Totaal bij 50% op T1 / 50% op T2 of stop: ± +8,2R
over 6 trades (± +1,4R gem.).

---

## Setup 1 - EURUSD short, juli 2018 (start: dinsdag 1 mei 2018)
Grafieken: `docs/setups_trader/01_eurusd_2018_short/01.png` ... `08.png`.

### 1. Maand: twee S/R-niveaus (01.png, 02.png)
- **Maand-S/R 1 = 1,15542**: 2015 twee keer weerstand (tap 1 juli 2015, tap 2 mei 2016), daarna steun in november
  2017 (tap support). Rol-wissel: weerstand -> steun.
- **Maand-S/R 2 = 1,13125**: zone van weerstandslontjes in 2015, steuntik juli 2017.
- Mei 2018 ("monthly start"): de daling vanaf de top van februari 2018 (1,2556) komt aan bij maand-S/R 1.

### 2. Week: BoS en bearish engulfing (03.png, 04.png)
- **Weekly BoS = 1,17496**: de body-low van de swing van december 2017 (week 11 dec: slot 1,1750). De week van 21 mei
  2018 sluit eronder (1,1649) -> structuur op de week bearish.
- Daarna een bounce van maand-S/R 1 (lontjes 1,1510 / 1,1508 / 1,1527), maar de **week van 11 juni 2018 is een
  bearish engulfing** (open 1,1775, slot 1,1609; omvat de bullish body van de week ervoor 1,1659 -> 1,1769) en zijn
  top (1,1852) komt terug tot boven het BoS-niveau en wordt afgewezen.
- Lezing van de trader: we zitten op maand-S/R (steun), er kan een kleine bounce komen, maar door de weekly BoS + de
  bearish weekly engulfing zoeken we **shorts op de dag** (bearish V).

### 3. Dag: S/R-flip op het BoS-niveau en de fib (05.png, 06.png)
- Het weekly-BoS-niveau is ook een **dagelijks S/R-niveau** (1,1743-1,1750): steun 17-21 mei en 11-13 juni, weerstand
  23 mei. Na de breuk van 14 juni (ECB-dag, -2,2%) wordt het weerstand.
- **Fib**: van de **body van de laatste dag-swing high** (14 juni, open 1,17916) naar de **lont van de laatste swing
  low** bij de maand-S/R (21 juni, low 1,15080). Bereik 283,6 pips.
  - 0,5 = 1,1650 | 0,618 = 1,1683 | 0,66 = 1,1695 | **0,796 = 1,1734** | 1 = 1,1792
  - -0,2 = 1,1451 | **-0,25 = 1,1437** | -0,28 = 1,1429 | **-0,65 = 1,1324**
- Pullback omhoog tot het BoS-/S-R-niveau, daar **shooting star (9 juli) en inverted hammer (10 juli)**: rejection
  aan de weerstand.

### 4. Trade (06.png - 08.png)
| | prijs | toelichting |
|---|---|---|
| instap short | **1,1743** | op het weekly-BoS / dag-S/R-niveau, na de shooting star + inverted hammer; diepte **0,83** in de fib |
| stop | **1,1859** | net boven de lont van de swing high (1,1852); risico 116 pips |
| target 1 | -0,25 / -0,28 (1,1437 / 1,1428) | geraakt 10 augustus (low 1,1388); daarna stop in winst |
| target 2 | **-0,65 (1,1324)** = vlak boven maand-S/R 2 (1,13125) | geraakt 15 augustus (low 1,1301) |
| stop na T2 | net achter het belangrijke niveau: **maand-S/R 1 (1,15542)** | geraakt 21-22 augustus (top 1,1602 / 1,1623) |

In R (risico 116 pips): T1 = **+2,6R**, T2 = **+3,6R**, de rest op de stop boven 1,1554 = ongeveer **+1,6R**.
Hoeveel er per target gesloten wordt, gaf de trader hier niet aan (eerder: 50% op T1); bij 50% op T1 en 50% op T2 is
het +3,1R, bij 50% T1 en de rest op de stop +2,1R.
Duur: swing high 14 juni -> instap 10 juli (18 handelsdagen wachten) -> T2 15 augustus.

### 5. Wat de trader hier anders doet dan de engine (alleen notities)
1. **Short terwijl de prijs op maand-steun staat.** Onze `m_block` ("maand-S/R in de weg") zou deze trade blokkeren.
   Voor de trader weegt de week-structuur (BoS + engulfing) zwaarder dan de maand-S/R; de maand-S/R is hier alleen
   "misschien eerst een kleine bounce" en wordt daarna **target** (S/R 2) en **stopniveau** (S/R 1).
2. **De trigger is op de week, tegen de maand-uptrend van 2017 in.** De engine laat shorts tegen de maandtrend pas toe
   na het maanddoel (`mt_done`); nog na te gaan of dat hier zo was.
3. **De instap ligt op een sleutelniveau**: weekly BoS = dag-S/R-flip, op 0,83 in de fib. Past bij wat de data al
   zeiden (diepe instap, lang wachten na de top -> runners) en bij test 63 (retest van het gebroken BoS-niveau).
4. **Targets en beheer**: T1 rond -0,25 (onze eerste partial op -0,2), T2 op -0,65 omdat daar de volgende maand-S/R
   ligt (doel = fib-extensie die samenvalt met maand-S/R), en de stop na T2 **achter een structureel niveau** (de
   gebroken maand-S/R) i.p.v. onze vaste ladder (-0,25 / -0,618).
5. Patroon: shooting star + inverted hammer, twee dagen na elkaar aan de weerstand.

---

## Setup 2 - EURUSD short, oktober 2018 (vervolg op setup 1)
Grafieken: `docs/setups_trader/02_eurusd_2018_short/01.png` ... `05.png`.

### 1. Maand: niet kijken
De prijs zit **tussen de twee maand-S/R-niveaus** (1,15542 en 1,13125) -> de maandgrafiek geeft hier geen richting;
de week beslist.

### 2. Week: structuur nog bearish, wachten op een bearish engulfing binnen de range (01.png, 02.png)
- Wekelijkse markstructuur: **laatste swing high 1,17906** (week 9 juli) en **laatste swing low 1,13012** (week 13
  augustus, = T2 van setup 1). Zolang er geen weekslot boven de swing high komt, blijft de structuur bearish.
- Regel van de trader: **wacht op een wekelijkse bearish engulfing candle binnen de laatste swing high en swing low**.
- **Week van 24 september 2018**: open 1,1746, top 1,1815 (lont boven de swing high, maar **slot 1,1603 eronder**),
  omvat de bullish body van de week ervoor (1,1626 -> 1,1748) -> bearish engulfing. Vanaf nu deze week(en) een daily
  short zoeken.

### 3. Dag: BoS, nieuwe swing low, fib en S/R (03.png - 05.png)
- **Daily BoS 1,16664**: de body-low van de dag-swing van 18 september; 27 september sluit eronder (1,1641).
- Wachten op een **nieuwe dag-swing low**: 9 oktober, lont **1,14322**. Pas dan de fib trekken.
- **Fib**: body van de swing high (20 september slot 1,17776) -> lont van de swing low (1,14322); bereik 345 pips.
  - 0,5 = 1,1605 | 0,618 = 1,1646 | 0,66 = 1,1660 | 0,796 = 1,1707 | 1 = 1,1778
  - **-0,2 = 1,1363** | -0,25 = 1,1346 | -0,28 = 1,1336 | **-0,6 = 1,1225** | -0,65 = 1,1208
- **Nieuw dag-S/R-niveau 1,15936**: lontjes die er telkens op bouncen of van afwijzen (augustus-oktober, groene en rode
  pijlen), één keer exact (11 oktober slot 1,15936). Daar ligt ook ongeveer de **0,5-fib**.
- **Patroon**: spinning top / **shooting star op 16 oktober** (top 1,1622, slot 1,1575) aan het dag-S/R-niveau en de
  0,5. "Doordat de daily S/R er ook ligt (belangrijk)."

### 4. Trade
| | prijs | toelichting |
|---|---|---|
| instap short | **1,15737** | na de shooting star; de lont tikte 0,5 + dag-S/R, de instap zelf ligt op ±0,41 in de fib |
| stop | **1,16923** | boven het daily-BoS-niveau (1,1666) en de 0,66; risico 119 pips |
| target 1 | **-0,2 (1,1363)** | geraakt 25 oktober (low 1,1356) |
| target 2 | **-0,6 (1,1225)** | geraakt 12 november (low 1,1216) - "neem altijd deze als 2de target" |

In R: T1 = **+1,8R**, T2 = **+2,9R**; 50/50 = +2,4R. Tussen T1 en T2 kwam de prijs terug tot 1,1500 (7 november): een
stop in winst op de instap of achter maand-S/R 1 (1,1554) bleef staan, een stop op fib 0 (1,1432) of -0,25 niet.
Duur: swing low 9 oktober -> instap 16 oktober -> T1 25 oktober -> T2 12 november.

### 5. Notities voor de engine (nog niet verwerken)
1. **Maand alleen als de prijs bij een maand-S/R is**; ertussen beslist de week-structuur.
2. **Week-trigger = bearish engulfing binnen de laatste swing high/low**, slot niet voorbij de swing high (een lont
   erboven mag). Dat is een andere week-trigger dan in de engine (`wk_trig`: engulfing + BoS); hier is de BoS al
   eerder gebeurd (setup 1) en blijft de structuur geldig tot een weekslot voorbij de laatste swing high.
3. **Volgorde op de dag**: week-engulfing -> daily BoS -> wachten op een nieuwe swing low -> fib -> instap op een
   **dag-S/R-niveau met meerdere lont-rejections** dat samenvalt met een fib-niveau (hier 0,5), met een patroon.
4. **Instap niet diep** (±0,41 op slot, lont tot ±0,55) - in tegenstelling tot setup 1 (0,83). Het S/R-niveau bepaalt
   de instap, niet een vaste fib-zone.
5. **Targets vast: T1 = -0,2, T2 = -0,6** (setup 1: -0,65 omdat daar de maand-S/R lag).
6. Stop boven het daily-BoS-niveau, niet boven de swing high (kleiner risico dan bij setup 1).

---

## Setup 3 - EURUSD short, februari 2019 (vervolg op setup 2)
Grafieken: `docs/setups_trader/03_eurusd_2019_short/01.png` ... `06.png`.

### 1. Maand: rond maand-S/R 2 (01.png)
De prijs zit rond **maand-S/R 2 (1,13125)**. Lezing: "het kan wat trager gaan" - maand-steun remt, maar beslist niet.

### 2. Week: nieuwe BoS, terug naar een week-S/R, bearish engulfing (01.png - 03.png)
- Nog geen bullish weekstructuur, wel een **nieuwe weekly BoS op 1,13929** (de body-low van de week van 13 augustus
  2018, doorbroken eind oktober / begin november: weekslot 1,1338 op 9 november). Verwachting: nog lager.
- Werkwijze: **zoek een week-S/R-niveau waar de prijs naar terugkeert, en wacht daar op een bearish weekkaars.** Er is
  er maar één die als steun én weerstand getest is: **week-S/R 1,15000** (steun begin oktober 2018, groene pijlen;
  weerstand week van 5 november, top 1,1500, rode pijl).
- De prijs gaat er naartoe (week van 7 januari 2019, top 1,1570, lont door 1,1500 tot vlak bij maand-S/R 1) en de
  **week van 14 januari is een bearish engulfing** (open 1,1461, slot 1,1362; omvat de body 1,1397 -> 1,1469).

### 3. Dag: BoS, fib, retest van de week-S/R (04.png, 05.png)
- **Daily BoS 1,13440**: de body-low van de swing low van 2 januari (slot 1,13447). **24 januari = bearish BoS
  candle** (slot 1,1305, lont 1,12894).
- **Fib**: body van de dag-swing high (9/10 januari, 1,15426) -> lont van de swing low (24 januari, 1,12894); bereik
  253 pips.
  - 0,5 = 1,1416 (valt op de **weekly BoS 1,1413**) | 0,618 = 1,1446 | **0,66 = 1,1457** | 0,786 = 1,1488 | 1 = 1,1543
  - -0,2 = 1,1239 | -0,25 = 1,1226 | **-0,28 = 1,1219** | -0,6 = 1,1138
- Pullback helemaal terug naar de **week-S/R 1,1500** (± 0,79-0,83 in de fib; de trader: "aan de 0,786"):
  - **2 dag-lonten tikken het niveau** (30 januari top 1,1502, 31 januari top 1,1514) -> rejection;
  - 31 januari sluit bearish (1,1480 -> 1,1447);
  - 1 februari **doji / shooting star** (top 1,1488, slot 1,1456).
- Regel van de trader (nog te bekijken): **minstens 1 bearish kaars tussen de rejection en de instap, daarna een doji
  / hammer / shooting star op de dag.**

### 4. Trade (05.png, 06.png)
| | prijs | toelichting |
|---|---|---|
| instap short | **1,14548** | na de doji / shooting star (1 februari), ± 0,66 in de fib |
| stop | **1,15743** | boven de swing high (1,1570) en maand-S/R 1 (1,15542); risico 119 pips |
| target 1 | **-0,2 (1,1239)** | geraakt 15 februari (low 1,1234) -> stop in winst |
| target 2 | -0,6 (1,1138) | **niet geraakt** (laagste punt 1,1176 op 7 maart) |
| uitkomst | **winst: T1, daarna stop in winst geraakt** | |

In R: T1 = **+1,8R**. Waar de stop na T1 stond, gaf de trader niet aan; met onze data: na T1 steeg de prijs tot 1,1334
(18 februari), 1,1358 (19 februari) en 1,1420 (28 februari). Stop op fib 0 (1,1289) -> geraakt 18 februari, rest
+1,4R; stop boven maand-S/R 2 (± 1,1315) -> 18 februari, rest ± +1,2R; stop boven de daily BoS (± 1,1346) -> 19
februari, rest ± +0,9R. Op de instap (break-even) was hij pas niet geraakt (top 20 maart 1,1448), maar T2 kwam ook
niet. Bij 50% op T1: totaal ± +1,4 tot +1,6R.

(De trader noemde dit "trade 2"; in dit document is het setup 3, na de shorts van juli en oktober 2018.)

### 5. Notities voor de engine (nog niet verwerken)
1. **Week-S/R als terugkeerniveau**: de trader kiest het (enige) week-niveau dat als steun én weerstand getest is, en
   wacht dáár op de bearish weekkaars. In setup 1 en 2 was dat het weekly-BoS-niveau; hier een apart week-S/R-niveau.
2. Volgorde opnieuw: week-engulfing -> daily BoS (bearish BoS candle) -> fib -> pullback tot een S/R-niveau ->
   lont-rejections -> **minstens één bearish kaars** -> doji/hammer/shooting star -> instap.
3. Fib-confluentie: 0,5 op de weekly BoS, de instapzone tussen 0,66 en het week-S/R-niveau (± 0,8).
4. Stop boven de swing high én de maand-S/R. Targets bevestigd: **T1 -0,2, T2 -0,6**. Hoeveel er op T1 gesloten
   wordt, ligt nog niet vast; eerst de win rate goed krijgen.
5. De maand-S/R (1,13125) stond hier tussen instap en T2: de prijs stopte erop en T2 kwam niet. Bij setup 1 lag T2
   (-0,65) precies op de maand-S/R en werd hij wel geraakt.

---

## Setup 4 - EURUSD short, mei 2019 (vervolg op setup 3) - verlies
Grafieken: `docs/setups_trader/04_eurusd_2019_short/01.png` ... `06.png`.

### 1. Maand
Nog steeds rond **maand-S/R 2 (1,13125)**.

### 2. Week: nieuwe BoS, doji, engulfing t.o.v. een oudere up-candle (01.png, 02.png)
- Week nog steeds in downtrend; **nieuwe weekly BoS 1,12940** (body-low van februari 2019; de week van 4 maart sluit
  eronder op 1,1235).
- **Week van 18 maart: doji / weekly shooting star** (open 1,1323, top 1,1448, slot 1,1301).
- **Week van 25 maart: bearish engulfing t.o.v. de up-candle van maandag 11 maart** (die week 1,1234 -> 1,1325; de
  week van 25 maart sluit op 1,1218, onder zijn open). Nieuwe regel van de trader: **de engulfing mag ook gelden
  t.o.v. de week vóór de vorige week, niet alleen de week ervoor.**

### 3. Dag: BoS, nieuwe swing low, fib, dag-S/R (03.png - 05.png)
- **Daily BoS 1,11938**: body-low van de laatste dag-swing low (7 maart, slot 1,1194, lont 1,1176); 24 april sluit
  eronder (1,1154).
- Wachten op een **nieuwe dag-swing low**: 26 april, lont **1,11115**.
- **Fib**: body van de laatste swing high (15 april, 1,13046) -> lont swing low (1,11115); bereik 193 pips.
  - **0,5 = 1,1208** | 0,618 = 1,1231 | 0,66 = 1,1239 | **0,796 = 1,1265** | 1 = 1,1305
  - **-0,2 = 1,1073** | -0,25 = 1,1063 | -0,28 = 1,1057 | **-0,6 = 1,0996** | -0,65 = 1,0986
- **Dag-S/R 1,12342** (tussen 0,618 en 0,66): steun 15 februari, rejections begin april (rode pijlen, toppen
  1,1246-1,1255), steun 10 en 18 april (groene pijlen; 18 april low 1,1229).
- Eis van de trader voor een dag-S/R-niveau: **minstens 2 bounces + 2 sells, of 1 bounce + 2 sells, of 2 sells + 1
  bounce; liefst één lont die het niveau exact raakt.**
- **Patroon**: **daily shooting star op 1 mei** (open 1,1215, top 1,1265 = tot de 0,796, slot 1,1195), de dag erna
  (2 mei) een **bearish engulfing t.o.v. de groene kaars van de dag vóór de shooting star** (30 april 1,1185 ->
  1,1215; 2 mei sluit op 1,1173).

### 4. Trade (05.png)
| | prijs | toelichting |
|---|---|---|
| instap short | **1,11722** | slot van de bearish engulfing (2 mei); ± 0,31 in de fib (de lont van de shooting star kwam tot 0,796) |
| stop | **1,12796** | "een beetje boven het short-patroon" (top shooting star 1,1265); risico 107 pips |
| target op de grafiek | **1,09845 (-0,65)** | T1 -0,2 = 1,1073, T2 -0,6 = 1,0996 |
| uitkomst | **verlies, -1R** (bevestigd door de trader, 06.png) | |

De laagste punten na de instap zijn 1,1107 (23 mei) en 1,1116 (30 mei): **T1 (1,1073) mist met ± 34 pips**, de swing
low (1,1111) wordt niet gebroken. De prijs blijft een maand zijwaarts tussen de swing low en het dag-S/R-niveau; op 5
juni komt hij tot 1,1307 -> **stop (1,1280) geraakt, -1R**.

Mogelijke oorzaken (verschil met setup 1-3; nog geen regel, eerst meer setups):
- **Vierde short op rij rond maand-S/R 2** (1,13125): sinds november 2018 handelt de prijs er rond; de week maakte geen
  echte nieuwe lows meer (week-lows 1,1176 maart, 1,1112 april). De neerwaartse kracht op de week was op.
- De week-trigger was zwakker: geen engulfing van de vorige week maar van twee weken terug, na een doji.
- De instap lag ondiep (0,31 op slot) en de stop krap boven het patroon; de prijs kwam terug tot boven de 1 (1,1305).
- T1 lag onder de swing low (nieuwe low nodig) - bij setup 1-3 werd die telkens snel gebroken.

### 5. Notities voor de engine (nog niet verwerken)
1. Week-engulfing ruimer: **slot onder de open van een up-candle van 1 of 2 weken terug**, ook na een doji.
2. Dag-S/R-niveau objectief te maken: **>= 3 lont-reacties met minstens 1 bounce en 1 sell (2+2, 1+2, 2+1)**, liefst
   één exacte tik.
3. Patroon: shooting star + de dag erna een bearish engulfing (t.o.v. de laatste groene kaars); instap op het slot.
4. **Stop boven het patroon**, niet boven de swing high -> kleiner risico (107 pips; setup 1: 116 met stop boven de
   swing high).
5. Instap weer ondiep (0,31 op slot), het patroon raakte de 0,796 met de lont. Diepte op slot is dus geen goede maat
   voor de trader; **de lont-tik van het patroon in de zone + het S/R-niveau** is wat telt.

---

## Setup 5 - EURUSD short, juli 2019 - geen trade (geen pullback naar het dag-S/R-niveau)
Grafieken: `docs/setups_trader/05_eurusd_2019_short/01.png` ... `07.png`.

### 1. Week onder maand-S/R 2 -> terug naar de maandgrafiek (01.png, 02.png)
- De week zit nu **onder maand-S/R 2 (1,13125)**. Dan opnieuw naar de maandgrafiek kijken of er lager een S/R-niveau
  ligt: **maand-S/R 3 = 1,08739** - heel duidelijk: 2015-2017 meerdere exacte taps als steun (groene pijlen) en
  weerstand (rode pijlen), twee keer lonten erboven maar de volledige body eronder. Dit wordt het volgende maanddoel.

### 2. Week: compact, chaotische kleine bullish BoS die geen echte flip is (03.png, 04.png)
- De weekgrafiek is compact en geeft weinig aanwijzingen; de structuur blijft bearish.
- Nieuw week-S/R-niveau om naar terug te keren: **week-S/R 1,13929** (steun aug-okt 2018, groene pijlen; weerstand
  dec 2018 - maart 2019, rode pijlen).
- **De kleine "weekly BoS" 1,13239** (top van de week van 8 april): de week van 3 juni sluit erboven (1,1333), de week
  van 10 juni weer eronder (1,1210), de week van 17 juni weer erboven (1,1369). Volgens de trader **geen echte
  structuurbreuk en geen echte last swing high**: "vrij chaotisch en niet zo duidelijk".
- Daarna aan de week-S/R 1,1393: **week van 24 juni = doji** (1,1372 -> 1,1372, top 1,1412) en **week van 1 juli =
  bearish engulfing** (1,1361 -> 1,1226), terug onder 1,13239 en onder maand-S/R 2.

### 3. Vraag van de trader: hoe ziet een bot dat deze kleine BoS geen trendwissel is?
Gemeten op onze weekdata (ATR 14 weken: ± 120 pips in juni 2019, ± 185 pips in mei 2018):

| kenmerk | deze "BoS" (juni 2019) | echte BoS (setup 1, mei 2018) |
|---|---|---|
| grootte van de swing waaruit de top komt | opwaartse poot 1,1184 -> 1,1324 = 140 pips = **1,1 ATR** | vanaf de swing low van december 2017 (1,1718) liep de poot tot 1,2556 = 840 pips = **4,5 ATR** |
| hoe ver het slot voorbij het niveau | 1,1333 vs 1,1324 = **9 pips = 0,07 ATR** | week van 21 mei sloot 100 pips (0,6 ATR) onder 1,1750 |
| acceptatie | **volgende week sluit er weer onder** | **bleef eronder** |
| efficiëntie van de beweging (netto / som van weekbewegingen, 10 weken) | **0,01 - 0,18** (zijwaarts) | **0,70 - 0,85** (trend) |
| hogere tijdframe | breuk loopt recht in maand-S/R 2 (van onder, nu weerstand) en week-S/R 1,1393 | breuk weg van de week-S/R, maandtrend nog niet tegen |

Voorstel om dit objectief te maken (te testen, nog niet verwerkt):
1. **Swing-hiërarchie**: alleen een **grote week-swing** telt voor een trendwissel (zigzag met omkeer >= ± 2 ATR, zoals
   de `REV`-parameter van de engine). De top van april (1,1324) is dan geen swing; de laatste échte swing high blijft
   1,1448 (maart) -> een bullish flip vraagt een weekslot boven 1,1448.
2. **Kwaliteit van de breuk**: slot minstens ± 0,25-0,5 ATR voorbij het niveau, met een grote body.
3. **Acceptatie**: geen slot terug binnen het niveau in de 1-2 weken erna; anders is het een **mislukte BoS** - en die
   telt juist als signaal in de oude richting (zoals hier).
4. **Chaos-filter**: bij een lage efficiëntie (< ± 0,2 over 10 weken) zijn kleine breuken ruis; dan gelden de randen
   van de range (hier week-S/R 1,1393 boven, swing low 1,1107 onder) en de week-kaarspatronen aan die randen.
5. **Hogere tijdframe eerst**: een bullish week-BoS tegen een bearish maandstructuur, die eindigt net onder een maand-
   of week-S/R, is geen flip.

---

### 4. Dag: BoS en fib, maar geen pullback naar het dag-S/R-niveau -> geen trade (05.png - 07.png)
- Na de nep-BoS blijft de weekstructuur bearish; week-doji/shooting star + bearish engulfing aan de week-S/R 1,1393.
- **Daily BoS 1,11941**: body-low van 18 juni (slot 1,11942); 23 juli sluit eronder (1,1152).
- **Fib**: body van de dag-swing high (18/19 juli, 1,12770) -> lont van de swing low (25 juli, 1,11014); bereik 176
  pips. 0,5 = 1,1189 | 0,618 = 1,1210 | 0,66 = 1,1217 | 0,796 = 1,1241. -0,2 = 1,1066.
- **Dag-S/R 1,12153** (± 0,65 in de fib): rejections half mei (rode pijlen), steun 6 juni, 5 juli en 18/19 juli (groene
  pijlen).
- De pullback na de swing low kwam maar tot **1,1162 (30 juli, ± 0,35)** - het S/R-niveau werd niet bereikt. Op 31 juli
  zakt de prijs door tot 1,1060 (-0,2) en 1 augustus 1,1027.
- **Geen trade**: geen terugkeer naar het dag-S/R-niveau = geen instap, ook al loopt de beweging daarna in de goede
  richting. De trader jaagt de move niet na.

### 5. Notities voor de engine (nog niet verwerken)
1. **De instap is voorwaardelijk op het bereiken van het dag-S/R-niveau** (zoals een limietorder in de zone); geen
   bereik -> setup vervalt. Gemiste moves horen erbij en tellen niet als verlies.
2. Een **nep-BoS op de week** (zie de criteria hierboven) verandert de structuur niet; de week-triggers (doji +
   bearish engulfing aan de week-S/R) blijven gelden.

---

## Setup 6 - EURUSD short, augustus 2019 (vervolg op setup 5) - winst
Grafieken: `docs/setups_trader/06_eurusd_2019_short/01.png` ... `05.png`.

### 1. Context
Zelfde week-context als setup 5 (bearish structuur, nep-BoS genegeerd, doji + bearish engulfing aan week-S/R
1,1393). Volgend maanddoel: maand-S/R 3 = 1,08739.

### 2. Dag: dezelfde swing high, nieuwe swing low, fib opnieuw (01.png)
- Wachten op een **nieuwe dag-swing low**: 1 augustus, lont **1,10270**.
- **Regel van de trader: omdat er van de vorige swing high geen trade kwam, blijft die eerste swing high het
  startpunt van de fib** (body 18/19 juli, 1,12770) -> fib naar de nieuwe lont 1,10270; bereik 250 pips.
  - 0,5 = 1,1152 | 0,618 = 1,1182 | **0,66 = 1,1192** | 0,796 = 1,1226 | 1 = 1,1277
  - **-0,2 = 1,0977** | -0,25 = 1,0965 | -0,28 = 1,0957 | **-0,58 = 1,0882** | -0,6 = 1,0877
- **Dag-S/R 1,12153** (± 0,75 in de nieuwe fib) en het **daily-BoS-niveau 1,11941** (± 0,67) vormen samen de zone.

### 3. Trade (02.png - 05.png)
- Pullback naar de zone (5 augustus, +1%), daarna **daily tweezer tops / shooting stars**: 6 augustus (top 1,1250,
  slot 1,1202) en 7 augustus (top 1,1242, slot 1,1199) - **2 lonten die het dag-S/R raken en afwijzen**, en
  **minstens 1 bearish kaars** (8 augustus 1,1199 -> 1,1180).

| | prijs | toelichting |
|---|---|---|
| instap short | **1,11988** | in de zone (daily BoS / dag-S/R), ± 0,69 in de fib |
| stop | **1,12839** | **boven de swing high** (1,1282), "we zitten er dicht bij" -> 85 pips risico |
| target 1 | **-0,2 (1,0977)** | geraakt 30 augustus (low 1,0963); stop daarna **een beetje in winst** |
| target 2 | **-0,58 (1,0882)** | geraakt 1 oktober (low 1,0879); -0,6 (1,0877) net niet. Stop daarna naar **fib 0** |
| rest | **fib 0 (1,1027)** | geraakt 11 oktober (top 1,1063) -> trade voorbij, winst |

Tussen T1 en T2 kwam de prijs terug tot 1,1110 (13 september): een stop "een beetje in winst" (onder de instap 1,1199)
bleef staan.

In R (risico 85 pips): T1 = **+2,6R**, T2 = **+3,7R**, de rest op fib 0 = **+2,0R**. Verdeling nog niet vastgelegd;
bijvoorbeeld 50% T1 / 25% T2 / 25% op 0 = **+2,7R**; 50% T1 / 50% T2 = +3,2R.

### 4. Nieuwe regels van de trader (vanaf nu)
1. **Target 2 = -0,58** (i.p.v. -0,6): hier kwam de prijs tot -0,59, net niet -0,6.
2. **Beheer**: na T1 de stop een beetje in winst; na T2 de stop naar fib 0.
3. **Fib-startpunt blijft de eerste swing high zolang er van die swing geen trade kwam**; alleen het eindpunt (nieuwe
   swing low) schuift op. (Vergelijk `--reanchor` in de engine: daar schuift fib 0 mee naar een nieuw extreem.)
4. Stop boven de swing high wanneer de instap er dichtbij ligt; anders boven het patroon (setup 4).

---

## Setup 7 - EURUSD short, november 2019 (vervolg op setup 6) - verlies
Grafieken: `docs/setups_trader/07_eurusd_2019_short/01.png` ... `07.png`.

### 1. Maand: niveau bijstellen naar de lont (01.png)
De prijs kwam vlak bij maand-S/R 3: de week van 30 september zakt tot **1,08792**. De trader **verhoogt het
maandniveau een klein beetje naar die lont**: maand-S/R 3 = **1,08792** (was 1,08739). Een S/R-niveau wordt dus
bijgewerkt naar de nieuwste exacte reactie.

### 2. Week: nieuw week-S/R met 2 + 2 exacte hits, bearish engulfing (02.png, 03.png)
- **Week-S/R 1,11622**: 2 exacte hits als steun (eind mei 2019, groene pijlen) en 2 exacte hits als weerstand (weken
  van 22 juli en 19 augustus; die laatste top 1,11641) - in een bearish trend.
- De prijs stijgt in oktober terug tot dat niveau (week van 14 oktober, top 1,1172; weken 21 en 28 oktober toppen
  1,1179 / 1,1176).
- **Week van 4 november = bearish engulfing** aan het niveau (open 1,1169, slot 1,1019; omvat de body van de week
  ervoor 1,1080 -> 1,1165).

### 3. Dag: BoS-kaars, dag-S/R, fib (04.png, 05.png)
- **Daily BoS candle 6 november**: **body-slot (1,1066) onder de lont van de laatste swing low** (1,1073, 25/29
  oktober). Regel: de BoS is een slot onder de **lont** van de laatste swing low.
- **Dag-S/R 1,10865**: soms ver terug in de tijd zoeken. Eerste bounce + body-slot erboven vrijdag 16 augustus, maar
  **de trader telt altijd vanaf een exacte lont-bounce**: **27 augustus** (low 1,10858); **12 september** een exacte
  rejection (top 1,10873); later nog reacties eind oktober / begin november (rode en groene pijlen).
- **Fib**: body van de swing high (1/4 november, 1,11692) -> lont van de nieuwe swing low (14 november, 1,09891);
  bereik 180 pips.
  - 0,5 = 1,1079 | **dag-S/R 1,10865 = ± 0,54** | 0,618 = 1,1100 | 0,66 = 1,1108 | 0,796 = 1,1133 | 1 = 1,1169
  - -0,2 = 1,0953 | -0,25 = 1,0944 | -0,28 = 1,0939 | **-0,58 = 1,0885 (valt vrijwel op maand-S/R 3, 1,08792)**
- De pullback bereikt het dag-S/R-niveau op 18 november (top 1,1090). Volgende stap: wachten op een **dagelijks
  bearish kaarspatroon** daar.

### 4. Notities voor de engine (nog niet verwerken)
1. **S/R-niveaus bijwerken** naar de nieuwste exacte lont-reactie (maand 1,08739 -> 1,08792).
2. **Week-S/R-kwaliteit**: 2 exacte hits als steun + 2 als weerstand (sterker dan het minimum 1 + 2 / 2 + 1).
3. **Dag-S/R telt vanaf een exacte lont-bounce**, niet vanaf een slot erdoor.
4. **BoS-lijn = de body-low van de laatste swing low** (beslissing van de trader na setup 7; bij een short; bij een
   long de body-high), met een body-slot eronder. Nagekeken: bij setup 1-5 geeft de lont-low precies dezelfde
   BoS-dag (1: week van 21 mei 2018; 2: 27 sep; 3: 24 jan; 4: 24 apr; 5: 23 jul); alleen bij setup 7 is het met de
   body een dag eerder (5 i.p.v. 6 november, body-low 1,10795 tegen lont 1,1073).
5. **T2 (-0,58) valt samen met een maand-S/R** - zelfde soort confluentie als T2 in setup 1.

### 5. Patroon, trade en uitkomst: verlies (06.png, 07.png)
- **Lont 1 + body eronder**: 18 november (top 1,1090 tikt het dag-S/R 1,10865, slot 1,1073).
- **Lont 2 + body eronder + bearish kaars**: 21 november (top 1,1097, slot 1,1058).

| | prijs | toelichting |
|---|---|---|
| instap short | **1,10578** | slot van 21 november; ± 0,38 in de fib (lonten tot ± 0,59) |
| stop | **1,11342** | ± 0,796, boven de twee lonten; risico 76 pips |
| target 1 | -0,2 (1,0953) | **niet geraakt**: laagste punt 1,0981 (29 november), ± 28 pips te kort |
| uitkomst | **verlies, -1R** | 11 december top 1,1145 -> stop geraakt |

De prijs maakte een dubbele bodem net boven de swing low (1,0981 tegen 1,0989) en steeg daarna door tot boven de
week-S/R (13 december top 1,1200).

### 6. Vergelijking van de twee verliezers (setup 4 en 7) met de winnaars (nog geen regel)
| | winnaars (1, 2, 3, 6) | verliezers (4, 7) |
|---|---|---|
| instap op slot in de fib | 0,83 / 0,41 / 0,66 / 0,69 | **0,31 / 0,38** |
| na de instap | swing low snel gebroken | **dubbele bodem bij fib 0**, T1 ± 30 pips te kort |
| stop | boven de swing high of een sleutelniveau (85-119 pips) | boven het patroon (107 / 76 pips) |
| week-context | verse BoS of engulfing van de vorige week | 4e short rond maand-S/R 2 (setup 4); week-downtrend al lang bezig, maand-S/R 3 vlak onder (setup 7) |

Twee verliezers is te weinig om een regel te maken; wel opvallend: **beide ondiep (< 0,4 op slot)** en **beide stopten
precies op de swing low** (geen nieuwe low). Mogelijke filters om later te testen: instap-diepte op slot >= ± 0,5, of
T1 pas tellen als de prijs eerst onder fib 0 sluit.

---

## Setup 8 - EURUSD short, januari 2020 (vervolg op setup 7) - week-trigger zonder engulfing
Grafieken: `docs/setups_trader/08_eurusd_2020_short/01.png`, `02.png`.

### 1. Week: shooting star + body-slot onder de week-S/R (01.png)
- Na setup 7 terug tot de **week-S/R 1,11622**; structuur nog bearish.
- **Week van 30 december 2019: shooting star** (open 1,1177, top 1,1239, slot 1,1159).
- **Week van 6 januari 2020: body-slot onder het niveau** (open 1,1167, slot 1,1121).
- **Geen bearish engulfing aan het niveau**: de vorige week was zelf bearish, en de laatste up-candle (week van 23
  december, open 1,1081) wordt pas in de week van 20 januari onder zijn open gesloten (1,1025).
- **Wel een bearish engulfing later, midden in de beweging (02.png)**: week van 3 februari 2020 (open 1,1096, slot
  1,0946) omvat de bullish week ervoor (1,1034 -> 1,1095). Die ligt ± 120-170 pips onder de week-S/R, 4 weken na de
  shooting star - een engulfing binnen de bearish structuur zoals in setup 2, niet aan het niveau.

### 2. Vraag van de trader: inzoomen na shooting star + slot onder het niveau, of wachten op een engulfing?
Voorstel voor de bot (te testen, nog niet verwerkt): **beide gelden als week-trigger aan een week-S/R in een bearish
structuur**:
- (a) bearish engulfing t.o.v. een up-candle van 1 of 2 weken terug (setup 1-4, 6, 7), of
- (b) een afwijzingskaars aan het niveau (shooting star / doji / pin met lont door het niveau) **gevolgd door een
  week-body-slot onder het niveau** (setup 8; vergelijk setup 4-5: doji, daarna engulfing).
Wachten op (a) geeft hier pas in de week van 3 februari een trigger, 4 weken later en ± 170 pips onder het
niveau. Of (b) even goed werkt als (a), moet
de backtest uitwijzen (beide varianten apart meten), niet deze ene trade.

### 3. Dag (variant b: inzoomen na shooting star + slot onder de week-S/R) (03.png - 06.png)
- **Daily BoS 1,10763**: body-low van 20 december 2019 (slot 1,10765); 23 januari 2020 sluit eronder (1,1056).
- **Dag-S/R 1,11087**: meerdere lont-reacties okt 2019 - jan 2020 (rode en groene pijlen).
- **Fib**: body swing high (21/22 januari, 1,10936) -> lont swing low (29 januari, 1,09924); bereik 101 pips. Het
  dag-S/R-niveau ligt **net boven de fib-start (± 1,15)**.
  - 0,5 = 1,1043 | 0,618 = 1,1055 | 0,66 = 1,1059 | 0,796 = 1,1073 | **1 = 1,1094**
  - **-0,2 = 1,0972** | **-0,58 = 1,0934**
- 31 januari: sterke bullish dagkaars tot **1,10956 = tikt de fib-start** (± 13 pips onder het dag-S/R) en sluit op
  1,1095. Geen dagpatroon -> volgens de regels **geen trade**.
- Daarna meteen omlaag: 3 februari bearish (slot 1,1061), T1 (1,0972) op 6 februari, T2 (1,0934) op 10 februari.

### 4. Vraag van de trader: als het dag-S/R vlak boven de fib-start ligt, meteen short op de tik van de fib-start?
Zonder patroon, als uitzondering. Wat het hier had opgeleverd (stop net boven het dag-S/R, ± 1,1115):
| instap | risico | T1 | T2 |
|---|---|---|---|
| limiet op de fib-start 1,1094 (31 jan) | ± 21 pips | +5,8R | +7,6R |
| slot van de eerste bearish dag erna 1,1061 (3 feb) | ± 54 pips | +1,6R | +2,3R |

Beoordeling: één voorbeeld, achteraf gekozen - te weinig om er een regel van te maken. Het risico van een limiet
zonder bevestiging: de prijs loopt door tot het S/R-niveau en erboven (dan is het een nieuwe swing high en wordt de fib
opnieuw getrokken). Omdat het risico zo klein is, hoeft de win rate niet hoog te zijn; dat moet de backtest uitmaken.
Te testen als **aparte instap-variant** met eigen statistieken:
- (i) limiet op de fib-start als het dag-S/R binnen ± 0,25 ATR (dag) erboven ligt, stop boven het S/R;
- (ii) zelfde, maar instap op het slot van de eerste bearish dagkaars na de tik (minder kans om overreden te worden,
  kleinere R).
**Voorkeur van de trader: variant (i)** (limiet op de fib-start). Later testen; (ii) ter vergelijking meenemen.

---

## Setup 9 - EURUSD short, februari 2020 (week-engulfing van setup 8) - geen trade (prijs schiet erdoor)
Grafieken: `docs/setups_trader/09_eurusd_2020_short/01.png` ... `04.png`.

### 1. Week (01.png)
**Week van 3 februari 2020 = bearish engulfing** (open 1,1096, slot 1,0946; omvat de bullish week ervoor) binnen de
bearish structuur, onder de week-S/R 1,11622. Inzoomen op de dag.

### 2. Dag: fib en twee dag-S/R-niveaus (02.png, 03.png)
- Sterke daling: door maand-S/R 3 (1,08792) heen tot de swing low van 20 februari (lont **1,07780**).
- **Fib**: body van de swing high (31 jan / 3 feb, 1,1095) -> lont swing low (1,07780); bereik 317 pips.
  - 0,5 = 1,0936 | 0,618 = 1,0974 | 0,66 = 1,0987 | 0,796 = 1,1030 | 1 = 1,1095 | -0,2 = 1,0715
- **Dag-S/R 1,09270** (± 0,47; steun sep 2019, groene pijlen) en, omdat de swing groot was, **nog een dag-S/R hoger:
  1,10283** (± 0,79; reacties aug 2019 - jan 2020, rode en groene pijlen).

### 3. Waarom geen trade (04.png)
- 27 februari: dagkaars van +1,1% (1,0883 -> 1,1001) **door het eerste niveau zonder patroon**; 28 februari slot
  1,1028 op het tweede niveau (top 1,1053), geen bearish patroon.
- **2 maart: slot 1,1133 boven de swing high / fib-start (1,1095)** -> de bearish dagstructuur is gebroken, de setup
  vervalt. Daarna door tot boven de week-S/R (5/6 maart top 1,1355).

### 4. Notities voor de engine
1. **Bij een grote swing meerdere dag-S/R-niveaus in de fib** (hier ± 0,47 en ± 0,79): elk niveau is een kans, maar
   alleen met een patroon.
2. **Ongeldig bij een dagslot boven de fib-start (swing high)**: dan geen trade meer op deze fib.
3. Geen patroon = geen trade, ook niet op het tweede niveau (de uitzondering "tik van de fib-start" uit setup 8 zou hier
   ook niet gelden: het dag-S/R ligt ver onder de fib-start).

---

## Setup 10 - EURUSD maart 2020: echte of mislukte bullish week-BoS? (context)
Grafieken: `docs/setups_trader/10_eurusd_2020_short/01.png` ... `03.png`.

### 1. Wat er gebeurt
- **Wekelijkse BoS-lijn 1,11755**: body-high van de laatste week-swing high (weken van 23/30 december 2019, top 1,1239).
- **Week van 2 maart 2020: slot 1,12839** boven die lijn (open 1,1045, top 1,1355 door maand-S/R 2 1,13125).
- **Week van 9 maart: GEEN engulfing** (correctie, de trader): open 1,1351, top 1,1496 = exact aan week-S/R 1,1500,
  slot 1,1105 - terug onder de BoS-lijn, maar **boven de open van de groene week ervoor (1,1045)**, dus de groene body
  wordt niet omsloten. Het is een bearish afwijzingskaars met een lange bovenlont. Week van 16 maart: slot 1,0696
  (ook geen engulfing volgens de harde regel: de vorige week is rood).

### 2. De vijf criteria van setup 5 toegepast (ATR 14 weken ± 140 pips)
| criterium | waarde | oordeel |
|---|---|---|
| 1. grote swing? | de top van december liep 460 pips (± 4 ATR) omlaag tot 1,0778 | **ja**, echte swing high |
| 2. kwaliteit van de breuk | slot 107 pips (0,77 ATR) boven de lijn, body 240 pips | **ja** |
| 3. acceptatie | de week erna sluit terug onder de lijn (bearish afwijzingskaars, geen engulfing) | **nee -> mislukte BoS** |
| 4. chaos-filter (efficiëntie 10 weken) | 0,12 in de breukweek (twee weken V-vorm, +5%) | **nee** (< 0,2) |
| 5. hogere tijdframe | maandstructuur bearish; slot net onder maand-S/R 2 (1,13125), daarna lont tot week-S/R 1,1500 | **nee** |

**Wat de bot had gezegd:**
- Na het slot van de week van 2 maart: **"BoS onbevestigd"** - criteria 1 en 2 kloppen, maar 4 en 5 niet. Nog geen
  bullish structuur; geen longs, de shorts nog niet afschrijven; één week wachten op acceptatie.
- Na het slot van de week van 9 maart: **"mislukte BoS"** -> de bearish weekstructuur blijft. Een week-trigger voor
  shorts is het **niet** volgens de engulfing-regel; hoogstens volgens variant (b) van setup 8 (afwijzingskaars met
  lont door week-S/R 1,1500 + slot terug onder de BoS-lijn) - nog te beslissen.
De prijs: week van 16 maart slot 1,0696, onder maand-S/R 3.

Kanttekening: criterium 3 vraagt per definitie een week geduld; in die week is de status "onbeslist". Dat moet de
bot zo behandelen: geen nieuwe trades in de richting van de nieuwe BoS tot hij bevestigd is.

### 3. Controle: had de bot met dezelfde criteria de BoS van setup 1 (mei 2018) wél als echt gezien?
Week-BoS-lijn 1,17503 (body-low december 2017); breukweek 21 mei 2018, slot 1,16490; ATR ± 181 pips.
| criterium | setup 1 (mei 2018) | setup 10 (maart 2020) |
|---|---|---|
| 1. grote swing | poot 840 pips (4,5 ATR) ✓ | 460 pips (4 ATR) ✓ |
| 2. breuk | slot 101 pips (0,56 ATR) voorbij, body 124 pips ✓ | 107 pips (0,77 ATR), body 240 ✓ |
| 3. acceptatie **de week erna** | week van 28 mei slot 1,16591, blijft eronder ✓ | sluit terug boven -> ✗ |
| 3'. acceptatie **2 weken** | week van 4 juni sluit terug **erboven** (1,17690) ✗ | ✗ |
| 4. efficiëntie 10 weken | 0,74 ✓ | 0,12 ✗ |
| 5. "tegen de maandtrend" | ja, tegen de maand-uptrend van 2017 ✗ | ja ✗ |
| 5'. **ruimte tot het volgende HTF-niveau bij het slot** | 95 pips (0,52 ATR) boven maand-S/R 1,15542 ✓ | 29 pips (0,2 ATR) onder maand-S/R 1,13125 ✗ |

Conclusie: setup 1 wordt alleen herkend met **criterium 3 = alleen de week erna** (bij 2 weken faalt hij: de week van
4 juni sloot 19 pips terug boven de lijn, waarna de bearish engulfing van 11 juni volgde - een retest, geen mislukking)
en met **criterium 5' = ruimte tot het volgende HTF-niveau** in plaats van "niet tegen de maandtrend". Met die twee
aanpassingen: setup 1 = echte BoS (alle criteria ✓), setup 10 = onbevestigd -> mislukt, setup 5 = geen BoS.

**Bijgestelde criteria (hypothese, te testen):**
1. swing uit een poot >= ± 2 ATR;
2. slot >= ± 0,25-0,5 ATR voorbij de lijn;
3. de week erna sluit niet terug voorbij de lijn (één week);
4. efficiëntie over 10 weken >= ± 0,2;
5. bij het slot >= ± 0,5 ATR ruimte tot het volgende maand- of week-S/R-niveau in de breukrichting.

---

## Harde regel engulfing, bearish en bullish (week en dag) - vastgelegd door de trader
- **Body over body**: open van de rode kaars >= slot van de groene kaars ervoor, en slot van de rode kaars < open van de
  groene kaars. Lonten tellen niet.
- **Bullish engulfing omgekeerd**: open van de groene kaars <= slot van de rode kaars ervoor, en slot van de groene
  kaars > open van de rode kaars. Lonten tellen niet.
- Nagekeken op onze weekdata:
| week | open rood vs slot groen | slot rood vs open groen | engulfing? |
|---|---|---|---|
| setup 1, 11 jun 2018 | +6,2 pips ✓ | ✓ | ja |
| setup 2, 24 sep 2018 | **-2,5 pips** | ✓ | strikt nee (bijna) |
| setup 3, 14 jan 2019 | **-7,8 pips** | ✓ | strikt nee (bijna) |
| setup 7, 4 nov 2019 | +3,8 pips ✓ | ✓ | ja |
| setup 9, 3 feb 2020 | +1,1 pips ✓ | ✓ | ja |
| setup 10, 9 mrt 2020 | +67 pips ✓ | **slot 1,1105 > open 1,1045** | **nee** |
- Bij forex opent de week bijna altijd op het slot van de vorige week (± een paar pips, verschilt per broker); de
  open-voorwaarde faalt daardoor soms met 2-8 pips (setup 2 en 3, op FOREXCOM-data mogelijk wel geldig). Voorstel voor de
  bot: **open >= slot groen min een kleine tolerantie (± 0,05 ATR)**, slot < open groen strikt. Te beslissen door de
  trader.
- Setup 4 gebruikte een ruimere vorm (slot onder de open van een groene week van 2 weken terug, na een doji); dat is
  volgens deze harde regel geen engulfing, maar een eigen trigger-type.

---

## Voorstel: welke gemiste trades wél te nemen (te testen, elk apart vooraf vastgelegd)
| gemist | wat had het gevangen | voorstel |
|---|---|---|
| setup 2, 3 strikt geen engulfing (open 2,5 / 7,8 pips onder het vorige slot) | tolerantie op de open | **engulfing met open >= slot vorige - 0,05 week-ATR**, slot strikt onder de open van de groene kaars |
| setup 8 (tik van de fib-start, dag-S/R net erboven) | limiet op de fib-start | variant (i), voorkeur trader |
| setup 8 week-trigger (shooting star + slot onder week-S/R, geen engulfing) | trigger-variant (b) | **afwijzingskaars aan week-S/R + volgende week body-slot onder het niveau** |
| setup 5 (geen pullback tot het dag-S/R) | lagere tijdframe | **4u-instap**: 25 juli 2019 een 4u-shooting star (top 1,1188, slot 1,1134) precies bij de retest van de daily-BoS-lijn 1,1194 / fib 0,5; instap op 4u-patroon aan een dag-niveau (BoS-lijn of 0,5) als de prijs het dag-S/R niet haalt |
| setup 9 (prijs schoot door alles) | - | **niet** vangen: zonder patroon had dit verloren |
| setup 4-vorm (groene week 2 weken terug) | - | voorlopig **niet** als trigger: enige voorbeeld was een verliezer |
Elke uitbreiding geeft meer trades én meer verliezers; alleen houden wat in de backtest (37 + holdout, per periode)
de verwachting per trade niet verlaagt.

---

## Strategie v2 in de engine: `research/strategy/trader_strategy.py` - replicatie EURUSD vanaf 1 mei 2018
De vorige strategie is gearchiveerd (`docs/STRATEGY_V1_ARCHIVE.md`). De nieuwe engine volgt de regels van dit document
(zie de docstring bovenaan het bestand):
week-structuur (zigzag 1,5 week-ATR, BoS-criteria 2-4 van setup 5/10) -> week-trigger (engulfing body over body met
0,05 ATR tolerantie op de open, of de setup-4-vorm) -> daily BoS (zigzag 1,5 dag-ATR, body-low) -> fib (hoogste body
tussen de gebroken swing low en de BoS -> laagste low; fib 1 blijft staan zolang er geen trade kwam; slot boven fib 1 =
vervalt) -> dag-S/R in fib 0,45-1 -> minstens 2 afwijzingslonten aan het niveau in 5 dagen + minstens 1 bearish kaars
+ patroon, instap op het slot (>= 0,25 diep) -> stop (diep >= 0,66: boven de swing high, anders boven max(0,796,
patroon)) -> T1 -0,2 (50%, stop iets in winst), T2 -0,58 (25%, stop naar fib 0), rest tot -1,618.
Een nieuwe week-trigger telt pas na het sluiten van de vorige trade.

    python research/strategy/trader_strategy.py EURUSD --from 2018-05-01 --to 2020-04-01 -v

| trader | engine | overeen? |
|---|---|---|
| 1: short 10 jul 2018, 1,1743 (fib 1,17916 -> 1,15080), T1 + T2 | short **26 jun 2018**, 1,16465, zelfde fib (1,17930 -> 1,15080), bearish engulfing aan dag-S/R 1,1683 -> -1R | **nee**: andere instap (eerder, lager niveau) |
| - | short 23 aug 2018 (trigger week 23 jul) -> -1R | extra (gevolg van 1: de trader zat toen nog in trade 1) |
| 2: short 16 okt 2018, 1,15737, T1 + T2 | short **16 okt 2018, 1,15747**, zelfde fib, T1 25 okt, T2 12 nov -> +1,6R | **ja** |
| 3: short 1 feb 2019, 1,14548 aan week-S/R 1,1500, T1, stop in winst | short **31 jan 2019, 1,14474** aan dag-S/R 1,1502, zelfde fib, T1 15 feb -> +1,4R | **ja** (1 dag eerder) |
| 4: short 2 mei 2019, 1,11722, verlies | short **1 mei 2019, 1,11949**, trigger week 25 mrt, fib 1 1,13046 (exact) -> -1R | **ja** (1 dag eerder) |
| 5: geen trade (geen pullback) | geen trade | **ja** |
| 6: short 9 aug 2019, 1,11988, T1 + T2, rest op fib 0 | short **6 aug 2019, 1,12018**, zelfde fib, T1 30 aug, T2 1 okt, rest fib 0 10 okt -> +2,7R | **ja** |
| 7: short 21 nov 2019, 1,10578, verlies | short **20 nov 2019, 1,10724**, zelfde fib -> -1R | **ja** (1 dag eerder) |
| 8: geen trade (alleen tik fib-start) | geen trade | **ja** |
| 9: geen trade (prijs schiet erdoor) | geen trade | **ja** |
| (10: maart 2020, nog geen dagbeelden) | short 31 mrt 2020 -> -1R | nog te bekijken |

**Resultaat: 5 van de 6 trades en alle 3 de no-trades komen overeen.** Afwijking: setup 1 - de engine neemt op 26 juni
2018 een bearish engulfing aan een lager dag-niveau (1,1683, ± 0,6 in de fib); de trader wachtte op het niveau van de
weekly BoS / dag-S/R 1,1743-1,1750. Een objectieve keuze "het sterkste niveau" (meeste lont-reacties, ook alleen op
draaipunten) wijst het niveau van de trader niet aan (rang 4-13 van de kandidaten in de zone); de samenval met een
week-niveau (weekly BoS-lijn / week-S/R, zoals in setup 1 en 3) is de beste kandidaat om dat te regelen.
De parameters (zigzag 1,5 ATR, 2 lonten in 5 dagen, diepte >= 0,25) zijn afgesteld op deze 10 setups: dit is een
replicatie, nog geen test. De echte test komt over alle instrumenten en periodes.

### Data FOREXCOM vs onze data (2026-11-01)
Prijzen van de screenshots tegen onze data: slotkoersen en swingpunten verschillen 0-1,5 pip (bv. instap setup 2
1,15737 vs 1,15747; weekly BoS 1,17496 vs 1,17503; maand-S/R 1,08792 gelijk). Dag- en weekgrenzen zijn dezelfde (17:00
New York). **Alleen de weekopen verschilt**: FOREXCOM opent de week op het slot van de vorige week (trader: week van 14
januari 2019 open = slot ervoor = 1,14685; week van 24 september 2018 open 1,17492), onze data opent op de eerste koers
na het weekendgat (1,14609 en 1,17457). Op FOREXCOM zijn de engulfings van setup 2 en 3 dus strikt geldig.
In de engine: `WEEK_OPEN_PREV_CLOSE = True` - de open-voorwaarde van de week-engulfing wordt tegen het vorige slot
gecontroleerd. Gevolg: ook de week van 1 juli 2019 (doji + engulfing aan week-S/R 1,1393, setup 5) wordt nu als trigger
herkend, zoals de trader hem tekende (op onze data faalde hij met 10,7 pips). De replicatie blijft 5/6 trades en 3/3
no-trades; setup 6 komt nu uit de juiste trigger-week.

### Is de engine-trade van 26 juni 2018 geldig volgens de regels? (vraag van de trader)
Volgens alle regels in dit document: **ja**. Week bearish (BoS april/mei 2018), trigger week van 11 juni (engulfing),
fib 1,17930 -> 1,15080 (zelfde als de trader), instap 1,16465 op ± 0,49, twee afwijzingslonten aan ± 1,1716 (25 juni top
1,1713 slot 1,1704 eronder; 26 juni top 1,1721) + bearish engulfing; stop 1,1744. Uitkomst: laagste punt daarna 1,1527
(28 juni), T1 1,1451 niet geraakt, 6 juli stop geraakt -> **-1R**.
Getest of een objectieve regel hem uitsluit zonder de 5 overeenkomende trades te breken:
- geen dagslot boven het niveau tijdens de test (nu ingebouwd, `NO_CLOSE_ABOVE`): het niveau 1,1683 valt af (25 juni
  sloot erboven), maar 1,1716 blijft geldig;
- exacte tikken (marge 0,03-0,07 dag-ATR i.p.v. 0,1): verandert niets (EURUSD 2017-18 heeft op bijna elke prijs
  tikken);
- recente reacties (laatste 60 dagen): 1,1716 had er 3 (21 mei, 1 juni, 25 juni), net als de niveaus van de trader.
Wat de trader anders deed: zijn niveau (1,1743-1,1750) viel samen met de **weekly BoS-lijn**, en zijn instap lag dieper
(0,83). Open vraag aan de trader: had hij deze trade ook genomen, of is er een regel die hem uitsluit?

### Replicatie na de regel "niveaus van de week-breuk" (trader 2026-11-01): 6/6 trades, 3/3 no-trades
De trader: bij de eerste short na een week-BoS zijn de dag-S/R-niveaus die bij de breuk horen de sleutel (1,17273 en
1,17492 rond de weekly BoS-lijn); de trade ligt binnen die twee. In de engine: voor de eerste trigger na een week-BoS
tellen alleen de week-breuklijn die de triggerweek opnieuw test (body-low van de laatste gebroken week-fractal-low:
week van 11 dec 2017, 1,17503) en dag-S/R binnen 0,35 dag-ATR ervan (`FLIP_BAND`). Het niveau 1,1704 (26 juni) valt
daarbuiten.

| # | trader | engine |
|---|---|---|
| 1 | 10 jul 2018, 1,1743, stop 1,18589; T1 10 aug, T2 15 aug | **10 jul 2018, 1,17444, stop 1,18604, diepte 0,83; T1 10 aug, T2 14 aug, rest 21 aug -> +2,6R** |
| 2 | 16 okt 2018, 1,15737 | 16 okt 2018, 1,15747; T1 25 okt, T2 12 nov -> +1,6R |
| 3 | 1 feb 2019, 1,14548; T1, stop in winst | 31 jan 2019, 1,14474; T1 15 feb -> +1,4R |
| 4 | 2 mei 2019, 1,11722; verlies | 1 mei 2019, 1,11949 -> -1R |
| 5 | geen trade | geen trade |
| 6 | 9 aug 2019, 1,11988; T1, T2, rest fib 0 | 6 aug 2019, 1,12018; T1 30 aug, T2 1 okt, rest 10 okt -> +2,7R |
| 7 | 21 nov 2019, 1,10578; verlies | 20 nov 2019, 1,10724 -> -1R |
| 8, 9 | geen trade | geen trade |

Geen extra trades meer in 1 mei 2018 - 1 april 2020 (de extra trade van 23 aug 2018 viel weg: de engine zat toen in
trade 1, net als de trader). Totaal 6 trades, 4 winnaars (T1), +6,3R (50/25/25) of +7,4R (50/50).
Nog steeds: de parameters zijn op deze setups afgesteld; replicatie, geen test.
Daarna (april 2020 - 2025) vindt de engine op EURUSD nog 6 trades (+4,2R): ± 1 per jaar - weinig.

### Eerste run buiten de replicatie: januari 2021 - januari 2022 (trader 2026-11-01)
Engine v2 zoals hierboven (geen parameters veranderd), gedraaid vanaf juni 2019 zodat structuur en triggers op tijd
staan, geteld: instappen in 2021.
| set | trades | per week | win (T1) | T2 | R (50/25/25) | gem. R | R 50/50 |
|---|---|---|---|---|---|---|---|
| 37 instrumenten | 60 | 1,2 | **30%** | 22% | **-6,6R** | -0,11 | -8,7R |
| holdout 29 exoten | 61 | 1,2 | **36%** | 23% | +1,6R | +0,03 | +0,9R |
Winnaars gemiddeld +2,0R, verliezers -1,0 à -1,1R -> break-even ligt rond 34% win rate. 2021 is dus ongeveer
break-even (37: iets negatief, holdout: iets positief). De 67% van de EURUSD-replicatie (4/6) herhaalt zich in 2021
niet. Eén jaar en ± 60 trades per set is een kleine steekproef (onzekerheid op de win rate ± 6 procentpunt).
Starten op 1 januari 2021 zonder aanloop geeft een opstart-piek (22 trades in januari, oude triggers); daarom de
aanloop vanaf 2019.

### Alleen EURUSD (trader: "je moest gewoon zoeken op EURUSD")
De trader stuurde **6 trades over mei 2018 - maart 2020 (± 1 jaar en 11 maanden) = ± 3 trades per jaar** op EURUSD.
Correctie in de engine: de week-breuklijn van de eerste trade na een week-BoS beperkt de niveaus alleen als die lijn
binnen de fib ligt (in maart 2021 koos de engine een lijn op 1,0823 bij een prijs rond 1,19, waardoor er niets kon).
Patronen van longs krijgen nu hun echte naam (hammer, bullish engulfing). De replicatie 2018-2020 blijft 6/6.
EURUSD 2016-2025, met aanloop vanaf januari 2016:
| jaar | trades | T1 geraakt | R |
|---|---|---|---|
| 2016 | 4 | 3 | +2,9 |
| 2017 | 2 | 0 | -2,0 |
| 2018 | 2 | 2 | +4,2 |
| 2019 | 4 | 2 | +2,1 |
| 2020 | 2 | 1 | +1,9 |
| 2021 | 3 | 0 | -3,1 |
| 2022 | 0 | - | - |
| 2023 | 1 | 0 | -1,0 |
| 2024 | 2 | 2 | +2,3 |
| 2025 | 3 | 3 | +5,5 |
| **totaal** | **23 (± 2,3 per jaar)** | **13 (57%)** | **+12,7R** |
2021 op EURUSD: 3 longs (28 jan, 2 jun, 9 sep), alle drie -1R; EURUSD daalde dat jaar van 1,23 naar 1,12, de
week-structuur draaide pas in mei bullish en in oktober weer bearish.

### Maand-S/R in de engine (trader 2026-11-01: "vanaf er data is, om de zoveel tijd herbekijken")
Methode van les 1 (`sr_levels.py`: lont-tikken van beide kanten, minstens 2 per kant, marge 0,15 maand-ATR, minstens
0,75 maand-ATR uit elkaar) op ALLE gesloten maandkaarsen (onze EURUSD-data: vanaf december 2002), herberekend elke 6
maanden (1 januari / 1 juli). Voorlopig alleen context: in het log en per trade het eerstvolgende maandniveau in de
handelsrichting (`m_sr_next`) en of er een maandniveau vóór T2 ligt (`m_sr_before_t2`); de trades veranderen niet.
Vergelijking met de maandniveaus van de trader (grafiek 2 maart 2020): engine 1 jan 2020 = 1,08560 / 1,12684 /
1,15748 / 1,20750 / 1,25374 / 1,28580 / 1,32590 / 1,36920 / 1,40152 / 1,43386; trader = 1,08792 / 1,13941 (of
1,13125) / 1,15699 / 1,26002 / 1,28643 / 1,33583 / 1,36803 / 1,40143. Binnen 30 pips: 1,15699, 1,28643, 1,36803,
1,40143, 1,08792 (23 pips); verder af: 1,26002 (63 pips), 1,33583 (99 pips), 1,13125 (44 pips); extra bij de engine:
1,20750 en 1,43386.

### Week van 16 maart 2020: geen bearish continuation-BoS (vraag van de trader)
De engine ziet het slot onder 1,08321 niet als nieuwe week-BoS: de structuur was al bearish, en een doorbraak in de
richting van de bestaande structuur is geen BoS-gebeurtenis (alleen een flip telt). De efficiëntie was die weken 0,0 -
0,3 (chaos). Wel nam de engine nog een short op **21 mei 2020** (1,09505, stop 1,12837, -1R) uit de oude trigger van
de week van 3 februari, met een fib vanaf de swing high van 9 maart (1,14400) - twijfelachtig in die chaos. Een
chaos-filter op de instap (week-efficiëntie < 0,2) helpt niet: de winnaars van setup 2, 3 en 6 hadden 0,01 / 0,02 /
0,11. Open vraag aan de trader: zou hij die short van 21 mei 2020 nemen?

### Week van 1 juni 2020: weekly bullish BoS (trader) - aanpassing van de BoS-criteria
De trader: slot 1,12920 boven de weekly BoS-lijn 1,11423 = bullish BoS. De engine zag hem een week later (breukweek 8
juni, bevestigd 15 juni), omdat de efficiëntie-regel (>= 0,2) de week van 1 juni afkeurde (0,11). Diezelfde regel was
nodig om de nep-BoS van juni 2019 (efficiëntie 0,08) tegen te houden - de twee zijn op efficiëntie niet te scheiden.
Wel te scheiden: in juni 2020 sloot de week ook boven de **lont** van de swing high (1,11448), in juni 2019 niet
(slot 1,13688 onder de lont 1,14482). Nieuwe regel: de BoS-week sluit voorbij de body-lijn + 0,25 ATR **én voorbij de
lont van de swing**; de efficiëntie-regel vervalt; de acceptatie (de week erna niet terug) blijft (die houdt maart 2020
tegen). Gevolg: bullish BoS breukweek 1 juni 2020, bevestigd na de week van 8 juni (zoals de trader); juni 2019 blijft
nep; minder flips over 2015-2025 (13 i.p.v. 18). Replicatie 2018-2020 blijft 6/6. EURUSD 2016-2025: 26 trades, 14 met
T1 (54%), +16,6R.
De lijn zelf: engine 1,11194 (body van de swing-high-week 30 maart), trader 1,11423 (slot van de week ervoor) - de
trader neemt de hoogste body rond de swing high; verschil 23 pips, geen gevolg voor de BoS-week.

---

## Setup 11 - EURUSD long, juni 2020 (eerste trade na de bullish week-BoS) - winst, T1 + T2 + T3
Grafieken: `docs/setups_trader/11_eurusd_2020_long/01.png` ... `08.png` (01-03: maand en week, 04-08: dag).
- **Week**: bullish week-BoS, breukweek 1 juni 2020 (slot 1,12920 boven de BoS-lijn 1,11423); geen extra week-engulfing:
  de trader gaat na de BoS meteen naar de dag.
- **Fib**: van de **body van de vorige dag-swing low** (25 mei, body-low 1,08969; trader ± 1,0900) naar de **lont van de
  swing high**; eerst 5 juni (1,13839), daarna een nieuwe swing high op 10 juni (**1,14224**) -> fib 0 schuift mee, fib 1
  blijft. 0,5 = 1,1160 | 0,618 = 1,1098 | -0,2 = 1,1528 | -0,58 = 1,1727 | **-1 = 1,1948** (trader 1,19510).
- **Niveaus**: dag-S/R **1,12121** (± 0,40 in de fib), weekly BoS-lijn 1,11423, slot van de BoS-week 1,12920 - de
  dag-S/R ligt tussen de BoS-lijn en het slot van de BoS-week (zoals in setup 1: 1,17273 / 1,17492 tussen 1,17503 en
  1,16490).
- **Instap**: **daily bullish engulfing op 22 juni** (open 1,11822, laag 1,11685 = lont tot de 0,5, slot 1,12616) aan
  het dag-S/R; trader instap 1,12609, stop **1,11088** (onder de lont / boven de 0,618); risico 152 pips.
- **Uitkomst**: T1 21 juli (top 1,1540), T2 28 juli (1,1774), **T3 = fib -1 op 18 augustus** (1,1966) -> in R: T1
  +1,7R, T2 +3,0R, T3 +4,5R; bij 50/25/25 ± +2,8R.
- **Nieuwe beheerregels van de trader**: na fib **-1 de volledige trade sluiten** (in de engine: T3 = -1 i.p.v. -1,618),
  of met een tijdslimiet werken zodat we snel opnieuw trades kunnen zoeken ("we mogen er niet te lang in blijven");
  meestal raakt na T2 de stop in winst, hier kwam T3 snel.

### Wat de engine hier deed
De engine zag de bullish BoS (breukweek 1 juni, bevestigd na 8 juni) maar wachtte op een week-trigger (engulfing 2
weken terug, week van 29 juni) en nam een **long op 10 juli 2020** (1,13002, stop 1,12420, kleine fib 1,12187 ->
1,13707 uit de triggerweek): T1 14 juli, T2 20 juli, T3 21 juli -> +2,5R. Dezelfde beweging, maar later en met een
andere fib.
Wat nodig is om de trade van de trader te vinden: (1) de bevestigde week-BoS zelf als trigger voor de eerste trade;
(2) de fib van de eerste trade vanaf de body van de vorige dag-swing (low bij een long, high bij een short); (3) de
dag-S/R tussen de BoS-lijn en het slot van de BoS-week. **Conflict met setup 1**: in setup 1 liet de trader de
engulfing van 26 juni 2018 liggen, hoewel 25 juni boven het niveau sloot en 26 juni terug eronder (een reclaim); in
setup 11 nam hij de engulfing van 22 juni 2020, hoewel 18 en 19 juni ónder 1,12121 sloten (ook een reclaim). Het
verschil zit in welk niveau als dag-S/R telt (1,1704 / 1,1716 in 2018 niet, 1,12121 in 2020 wel); tellen van
lont-reacties (3/5 pip, op draaipunten of alle kaarsen) scheidt die niet. Vraag aan de trader.

### Engine: de week-BoS als trigger voor de eerste trade (setup 11)
Nieuw (`BOS_TRIGGER`): bij elke bevestigde week-BoS start de engine meteen een eerste-trade-setup, naast de gewone
week-triggers: fib 1 = de hoogste body rond de laatste dag-swing die bevestigd was vóór de breukweek (het begin van de
impuls; juni 2020: 25 mei, 1,08969), fib 0 = het extreem sindsdien (schuift mee), niveaus = dag-S/R tussen de BoS-lijn
en het slot van de BoS-week (juni 2020: 1,11194 - 1,12916); verder dezelfde instapregels. Vervalt bij een slot voorbij
fib 1 of na de eerste trade.
Resultaat juni 2020: **long 17 juni 2020** (hammer aan dag-S/R 1,12313, instap 1,12436, stop 1,09940 = boven de
0,796) -> T1 gehaald, +1,75R. De trader: 22 juni (engulfing aan 1,12121, instap 1,12609, stop 1,11088). Zelfde trade,
3 handelsdagen eerder; de engine-stop ligt verder (0,796-regel), dus minder R. Replicatie 2018-2020 blijft 6/6.

### Regel: de lont van de instapkaars bereikt de zone (>= 0,45 in de fib)
De engine ging in juni 2020 al op 17 juni long (hammer, lont tot 0,41 in de fib). Bij alle trades van de trader kwam
de lont van de instapkaars minstens tot 0,48: setup 1 0,99 | 2 0,55 | 3 0,79 | 4 0,79 | 6 0,89 | 7 0,60 | 11 0,48. In
het gewone pad dwong de zone (niveau in 0,45-1) dat al af, in het BoS-pad niet. Nieuw: de lont van de instapkaars moet
tot minstens 0,45 komen. Resultaat: **long 22 juni 2020, bullish engulfing, instap 1,12616** (trader 1,12609) -> T1,
+1,56R (stop engine 1,09936 boven de 0,796; trader 1,11088, onder de weekly BoS-lijn 1,11423 - daardoor minder R bij de
engine). Replicatie 2018-2020 blijft 6/6; nu 7/7 trades van de trader (setup 1-4, 6, 7, 11) met dezelfde instapdag op
3 na (1 dag eerder). EURUSD 2016-2025: 26 trades, 12 met T1, +14,0R. "Geen slot voorbij het niveau tijdens de test"
blijft aan (zonder: 31 trades, +8,9R).
Open punt: de stop van de trader in setup 11 lag achter de weekly BoS-lijn (± 0,6 in de fib), niet boven de 0,796.

### Stopanalyse (eerste ronde, `research/strategy/v2_stop_study.py`)
Zelfde instappen en targets, alleen de stop anders. "Winnaars" = trades die T1 halen met de wijdste stop (fib 1).
Tegenbeweging vóór T1 bij de 14 EURUSD-winnaars (in de fib, 0 = extreem, 1 = fib 1): 0,43 - 0,99 (mediaan ± 0,8) - een
stop onder fib 1 stopt dus winnaars uit.
| stopregel | EURUSD 26 trades: T1 / winnaars uitgestopt / R | 37 instrumenten 954 trades: T1 / uitgestopt / R |
|---|---|---|
| fib 1 (+0,1 ATR) | 14 / 0 / +15,0 | **459 / 0 / +120** |
| fib 0,886 | 11 / 3 / +16,9 | 408 / 51 / +113 |
| engine nu (diep: swing high, anders max(0,796, patroon)) | 12 / 2 / +14,1 | 391 / 71 / +97 |
| fib 0,796 | 10 / 4 / +22,1 | 357 / 102 / +93 |
| boven het niveau + 0,5 ATR | 12 / 2 / +31,2 | 289 / 172 / +50 |
| boven het patroon + 0,1 ATR | 10 / 4 / +19,2 | 256 / 205 / +6 |
| boven de swing high (lont) | 14 / 0 / +8,3 | 485 / 0 / +54 |
Op EURUSD alleen (26 trades) lijken krappe stops beter, maar over 954 trades is **fib 1 + 0,1 ATR** de beste: geen
winnaars uitgestopt en het meeste R; krappe stops (patroon, niveau) stoppen 150-200 winnaars uit. Voorstel: stop op
fib 1 (de body van de swing) + 0,1 ATR. Nog niet ingevoerd.

### 10 jaar EURUSD op een 50k-account (engine v2, 26 trades, 2016-2025: +14,0R)
| risico per trade | winst over 10 jaar | max drawdown |
|---|---|---|
| 1% (500 per R) | ± 7.000 (+14%) | 4,3% |
| 2% (1.000 per R) | ± 14.000-15.000 (+28-30%) | 8-9% |
Per jaar bij 1%: 2016 +665, 2017 -505, 2018 +2.110, 2019 +1.045, 2020 +275, 2021 -2.060, 2022 +4.130, 2023 -510,
2024 -1.525, 2025 +3.390. Langste verliesreeks: 4. Met ± 2,6 trades per jaar op één paar is het rendement klein.

### Stop per trade afhankelijk van het dag-S/R (trader: "geen vaste SL")
Getest, zelfde instappen en targets:
| stopregel | EURUSD: uitgestopte winnaars / R | 37 instr.: uitgestopte winnaars / R | risico (ATR, mediaan) |
|---|---|---|---|
| volgend fib-niveau boven het dag-S/R (0,5 -> boven 0,618; 0,786 -> boven 0,886) | 4 / +22,7 | 192 / +16 | 0,9 |
| twee fib-niveaus boven het dag-S/R | 2 / +18,0 | 129 / +44 | 1,3 |
| boven het volgende dag-S/R + 0,1 ATR | 4 / +25,7 | 199 / +4 | 0,8 |
| fib 1 + 0,1 ATR (ter vergelijking) | 0 / +15,0 | 0 / +120 | 2,3 |
Op EURUSD alleen (26 trades) zien de stops die meeschuiven met het niveau er goed uit, over 954 trades niet: ze stoppen
130-200 latere winnaars uit. De winnaars trekken vóór T1 vaak diep terug (tot fib 1). Wel: met een stop op fib 1 is
het risico per trade in pips groter (± 2,3 dag-ATR), dus de positie kleiner; in R is dat al verrekend.

### 37 instrumenten per jaar, nieuwste engine (aanloop vanaf juni 2015)
| jaar | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|
| trades | 62 | 101 | 92 | 102 | 109 | 97 | 95 | 90 | 105 | 89 |
| win (T1) | 40% | 34% | 49% | 41% | 44% | **30%** | 51% | 38% | 40% | 47% |
| R | +5,9 | -10,7 | +16,2 | +8,9 | +26,0 | **-17,5** | +33,0 | +2,7 | -7,1 | +43,9 |
Totaal 942 trades, 41% T1, +101R (gem. +0,11R). De eerdere 2021-run (30%, -6,6R, oudere versie) was het slechtste jaar
van de tien; ook met de nieuwste versie is 2021 negatief (-17,5R). 3 van de 10 jaren negatief.

### 5ers 50k met de scaling van de vorige bot (`research/strategy/v2_fiveers_sim.py`)
Model van `backtest/src/csv_mt5_simulator.py`: risico % van het saldo per trade (vorige bot 0,6%), max 7 open trades
en 5% open risico; bij +10% op het niveau uitbetaling (80% split onder 175k) en een niveau hoger (50k, 60k, 70k, 80k,
100k, ...); breach onder 90% van het niveau. Resultaat geboekt op de uitstapdag.
| set | risico | uitbetaald 2016-2025 | account eind | opmerking |
|---|---|---|---|---|
| 37 instrumenten (942 trades) | 0,6% | **± 15.000 (± 1.500 per jaar)** | 80k | 529 trades overgeslagen (al 7 open) |
| 37 instrumenten | 1,0% | 0 | - | **breach juni 2017** (verliesreeks 2017) |
| alleen EURUSD (26 trades) | 0,6% | 0 | 50k (saldo 54.299) | +8,6%, nog geen +10% |
| alleen EURUSD | 1,0% | ± 4.600 (2022) | 60k | |
Conclusie: met deze versie en deze risico's ver van 50k per jaar; de winst per trade (± +0,1R over alle instrumenten)
is te klein en bij 1% risico gaat de 10%-limiet eraan in een slechte periode.

### Risicoregels van de vorige bot (trader: "1,8% en kijken of de markt volatiel is")
De vorige bot had: 1,8% per trade in de challenge en gefund onder 300k (0,6% vanaf 300k), risico omlaag naar 0,4 /
0,25 / 0,15% vanaf 1,5 / 2,5 / 5,5% totale drawdown, max 3,5% open risico, en een volatiliteitsfactor (rustige markt
x1,7, onrustige x0,6; `backtest/RECOMMENDED_CONFIG.md`). Die waarden zijn met Optuna afgesteld op de vorige strategie,
waarvan de winst uit een blik in de toekomst kwam - dus niet blind over te nemen.
Benadering met v2 (zonder volatiliteitsfactor): 37 instrumenten -> geen enkele uitbetaling in 10 jaar (saldo 51.525;
in elke drawdown zakt het risico naar 0,15-0,4% en het herstel duurt lang; 603 trades overgeslagen door de 3,5%-grens);
alleen EURUSD -> 1 uitbetaling (5.189, oktober 2019). De risicoregels komen terug als de strategie vastligt: dan een
nieuwe Optuna-ronde op v2, met walk-forward en een apart gehouden periode.

---

## Setup 12 - EURUSD long, oktober 2020 - geen trade (geen dagpatroon)
Grafieken: `docs/setups_trader/12_eurusd_2020_long_notrade/01.png` ... `04.png`.
- Na setup 11 (uit op fib -1, 18 augustus) weer longs zoeken: de weekstructuur is bullish.
- **Week-S/R 1,16211** (onder de prijs; steun 2017 en 2018, weerstand aug-okt 2018), maand-S/R 1,15699 eronder. De prijs
  zakt terug tot de week-S/R (eind september, low ± 1,1612) en de **week van 19 oktober is een bullish engulfing**.
- **Dag**: daily BoS 1,18483; fib van de body van de swing low (± 1,1702) naar de lont van de swing high (± 1,1881); dag-S/R
  **1,17814** op ± 0,6. De prijs zakt terug door de zone (eind oktober) zonder bullish dagpatroon en sluit onder fib 1 ->
  **geen trade**; daarna verder tot de week-S/R.
- **Engine**: geen trade, zelfde reden: daily BoS 21 oktober (lijn 1,18283), fib 1 1,17073, 29 oktober slot onder fib
  1 -> fib vervalt. (De engine had nog de oudere week-trigger van de week van 24 augustus aan staan; de dag-afloop is
  dezelfde.) Volgende engine-trade: long 28 januari 2021 (-1R) - nog niet door de trader bekeken.

---

## Setup 13 - EURUSD long, november 2020 - winst tot -1,618
Grafieken: `docs/setups_trader/13_eurusd_2020_long/01.png` ... `04.png`.
- **Week**: bullish engulfing in de week van 2 november 2020 (open 1,1650 = slot ervoor, slot 1,1874 boven de open van
  de rode week ervoor 1,1853) vanaf de week-S/R 1,16211.
- **Dag**: daily BoS **1,18627** (trader; body rond de swing high van 21 oktober - het slot van 23 oktober is 1,18612)
  -> 6 november sluit erboven (1,18737). Duidelijk dag-S/R **1,17814** (veel reacties aug-okt, rode en groene pijlen).
- **Fib**: de trader neemt de fib vanaf de **swing low van de dag** (4 november, lont 1,16027, body ± 1,171) naar de
  swing high van 9 november (1,19202). Bounce van het dag-S/R + golden pocket (0,618-0,66), instap **1,18339** (13
  november), stop **1,17447** (onder de 0,796).
- **Uitkomst**: -0,2 / -0,58 / -1 en zelfs **-1,618 (1,2251) op 17 december**. Nieuwe beheerregel van de trader: **na
  -1 de stop naar -0,5, en een TP4 op -1,618**.

### Engine
Aanpassingen (de replicatie-check `research/strategy/v2_replication.py` toont na elke stap alle trades van de trader):
1. **Nieuwere week-trigger vervangt een oude** die geen actieve fib heeft (`REARM`): de engine had nog de trigger van
   eind augustus aan staan; nu telt de engulfing van 2 november.
2. **Daily BoS telt pas vanaf de bevestiging van de swing** (`BOS_CLUSTER = "confirm"`): het slot van 23 oktober boven
   de body van 21 oktober kwam vóór de swing high bevestigd was en telt niet; de BoS is 6 november. (De variant "BoS-lijn
   = uiterste body binnen 2 kaarsen rond de swing" vond de trade ook, maar kostte over de 37 instrumenten ± 35R.)
3. **Beheer** (`TARGETS`): 50% op -0,2 (stop iets in winst), 20% op -0,58 (stop naar fib 0), 15% op -1 (stop naar
   -0,5), 15% op -1,618 (TP4). Na T3 blokkeert het restje geen nieuwe setups meer.
Resultaat: **long 10 november 2020** (hammer aan dag-S/R 1,17890, instap 1,18156, stop 1,16873) - T1 30 nov, T2 2 dec,
rest tot 18 januari -> +1,77R. De trader: 13 november. Fib 1 van de engine 1,16387 (laagste body tussen de gebroken
swing en de BoS) i.p.v. de body van de swing-low-kaars (± 1,171) - verschil blijft open.
**Replicatie: 8/8 trades van de trader (setup 1, 2, 3, 4, 6, 7, 11, 13), 4/4 no-trades (5, 8, 9, 12); 1 extra
engine-trade (21 mei 2020, -1R).** EURUSD 2016-2025: 27 trades, 56% T1, +18,0R. 37 instrumenten: 958 trades, +97,7R
(gem. +0,10R, t 2,0) - gelijk aan vóór deze stap.

---

## Setup 14 - EURUSD long, april 2021 - T1 + T2 (engine: nog niet gevonden)
Grafieken: `docs/setups_trader/14_eurusd_2021_long/01.png` ... `05.png`.
- **Week**: twee nieuwe week-S/R-niveaus **1,19159** en **1,18003**; de prijs zakt in maart 2021 terug tot onder
  1,18003 (low 1,1704) en de **week van 5 april is een bullish engulfing** (open 1,1761 = slot ervoor, slot 1,1900
  boven de open van de rode week ervoor 1,1794). De trader ziet de weekstructuur nog **bullish**.
- **Dag**: daily BoS **1,19326** (body van de swing high half maart), gebroken half april; fib van de **body van de
  swing-kaars** (19 april: lont 1,19426, body-low ± 1,1973-1,1990) naar de lont van de swing high (20 april, 1,20799).
  Dag-S/R **1,20032** ("moeilijker te vinden maar correct": weerstand 1 sep en 1 dec 2020, steun 5 feb en 1 mrt 2021).
- **Instap meteen op de hammer van 21 april** (laag 1,19985 door het dag-S/R, slot **1,20350** = fib 0,5), stop
  **1,19864** (onder fib 1), target op het scherm 1,21368 (-0,58 / -0,65): -0,2 en -0,58 geraakt 28-29 april (top
  1,2150), daarna terug.

### Wat de engine hier doet en waarom hij de trade (nog) niet vindt
1. **Week**: de engine ziet in maart 2021 een **bearish week-BoS** (week van 1 maart: slot 1,1913 onder de body-low
  1,2047 én de lont 1,1952 van de week-swing low van begin februari; de week erna bleef eronder) en zoekt daarna
  shorts: 15 april 2021 (-1R) en 8 juni 2021 (-1R). De trader ziet geen bearish structuur.
2. **Fib**: met de structuur bullish (test, maart-BoS weggelaten) vindt de engine de trigger (week van 5 april) en
  een daily BoS (19 april), maar trekt de fib over de hele poot (fib 1 = 1,17158, de laagste body sinds de gebroken
  swing) -> de zone ligt veel lager en er komt geen trade. De trader neemt de kleine laatste swing (19 -> 20 april).
3. **Instap**: de trader stapt in op de **eerste** hammer aan het niveau; de engine vraagt nu 2 afwijzingslonten in 5
  dagen (setup 1-4, 6, 7).

### Week-swing alleen als hij een BoS maakte (trader, setup 14)
De trader: de low van de week van 1 februari 2021 "heeft zelf nog geen BoS gemaakt, er was ook geen higher high, dit
is gewoon een correctie van de swing top van 4 januari"; 1,18574 (nov 2020) is geen swing low "omdat er geen bearish
candle bij is"; zijn week-BoS-lijn is **1,16469** (rode week 26 okt 2020). In de engine als optie `STRUCT_SWINGS`: een
week-swing low telt pas als de prijs daarna boven de vorige swing high kwam (higher high), een swing high pas na een
lower low. Gevolg: de bearish BoS van maart 2021 verdwijnt (volgende bearish BoS oktober 2021), maar de bullish BoS van
juni 2020 schuift naar juli 2020 (de top van 30 maart 2020 maakte geen lower low; lijn wordt de top van 9 maart,
1,1351) -> setup 11 en 13 worden gemist. Optie staat **uit** tot de trader uitlegt waarom juni 2020 wel een BoS is.
Aanvulling van de trader (juni 2020): "ik tel dit omdat het eigenlijk wel van een swing low komt, alleen zijn het equal
lows (16 en 23 maart 2020: 1,0638 / 1,0636) ... de markt was duidelijk akkoord". Regel: een week-swing telt ook als de
swing ervóór een equal high / equal low was (twee weken op rij binnen 0,1 week-ATR, `EQ_TOL`). Rond januari 2021 is er
geen equal high (1,2310 / 1,2350, 39 pips). `STRUCT_SWINGS` staat nu **aan**: bullish BoS breukweek 1 juni 2020 blijft,
de bearish BoS van maart 2021 verdwijnt (volgende bearish BoS oktober 2021), de shorts van april en juni 2021 vallen weg.
Replicatie: 8/9 trades (setup 14 nog niet), 4/4 no-trades.

### Engine-short 21 mei 2020: trigger is op na een vervallen fib (`VOID_SPENT`, aan)
De trader: "Ik snap niet waarom hij hier short zou gaan?" De engine gebruikte de bearish engulfing van de **week van
3 februari 2020**. De fib daarvan verviel op 2 maart (slot boven fib 1). Daarna nam de engine dezelfde oude trigger
voor de daily BoS van 13 maart: fib 1,14400 -> 1,0636, instap 1,09505 op 21 mei, -1R. Ondertussen werd de markt
bullish (BoS 1,11423, setup 11).
Regel: als een fib vervalt (slot voorbij fib 1), is de week-trigger **op**. Voor een nieuwe trade is een nieuwe
week-trigger nodig.
EURUSD 2016-2025: **24 trades, 58% T1, +19,2R**. Ervoor: 26 trades, +20,1R. Weg: de short van 21 mei 2020 (-1R) en
een winnaar van 7 juni 2016 (+1,9R). Replicatie: 8/9 trades, 4/4 no-trades, **geen extra engine-trades meer tot
mei 2021**.

### Swing low = 3 candles (hoger, lager, hoger)? Getest als algemene regel (`FRACTAL_FIB`, uit)
De trader definieert een swing low met 3 candles: candle 1 hoger, candle 2 lager, candle 3 hoger. Bij 19 april 2021
(1,19426) zijn de eerste twee candles echter bullish, met een veel hogere derde candle. De trader twijfelde zelf:
"Ik weet niet of dit voordelig is voor onze bot."
Test: na de daily BoS verschuift fib 1 naar de nieuwste 3-candle swing zodra de prijs een nieuw extreem maakt.
- **Resultaat: slechter.** 6/9 trades: setup 1, 2 en 6 worden gemist. 39 trades, 41% T1, +7R.
- Setup 14 wordt er nog steeds niet mee gevonden.
De optie staat daarom uit.

### Setup 14: instap op de tweede afwijzing (trader, aanvulling)
De trader: "één hammer niet per se, maar de tweede candle heeft ook een wick en body die boven het level sluit".
- 21 april: hammer, low 1,19985, slot 1,20349.
- 22 april: low 1,19938, slot 1,20148.
- Twee afwijzingen van het dag-S/R 1,20032. Instap **1,20147** = slot 22 april.
- Stop **1,19872**, max **+4,6R** (top 1,21419).
De instapregel van de engine (2 afwijzingslonten, een bullish candle erbij) klopt hier dus al. Het enige verschil is
de **fib**. In de grafiek van de trader ligt fib 1 op ± **1,1995** en fib 0 op 1,20799. In de data is 1,19950 de
high van 16 april, de top van de consolidatie van 14-16 april vóór de impuls van 19 april. De engine heeft fib 1 op
1,17158 en daardoor ligt het niveau maar op diepte 0,21. Vraag aan de trader: waar komt fib 1 = 1,1995 vandaan?

### Setup 14 gevonden: fib vanaf de BoS-candle als die zelf de swing is, tweezer van elke kleur (aan)
De trader: "Body start op 1,19947 en wick swing high op 1,20800". Fib 1 = begin van de body van **19 april** (de
candle die de swing low 1,19426 zet en meteen de daily BoS maakt), fib 0 = lont 20 april.
In onze data opent 19 april op 1,19734. Dat is de zondag-open na de gap; de feed van de trader opent op ± 1,1995.
1. **`LAST_SWING_FIB = "bos"`**: fib 1 = body van de laatste swing als die swing **de BoS-candle zelf** is.
   - De engine controleert dit één dag na de BoS, want dan is de swing bevestigd.
   - De swing moet voorbij de **3 candles ervoor** gaan (`SWING_LEFT = 3`). 19 april gaat lager dan 14-16 april.
   - In setup 2 gaat de BoS-candle (3 okt 2018) maar voorbij één candle; daar blijft de grote fib staan.
   - Als algemene regel (altijd de laatste 3-candle swing) gemist: setup 2 en 3.
2. **`TWEEZER_ANY = True`**: de tweede test aan het niveau mag ook een rode candle zijn, als hij een lont door het
   niveau heeft en erboven sluit. 22 april 2021 is rood: low 1,19938, slot 1,20148, na de hammer van 21 april.

Resultaat:
- **Engine-trade setup 14**: 22 april 2021, dag-S/R 1,20042 (trader 1,20032).
  - Instap **1,20148** (trader 1,20147), stop **1,19876** (trader 1,19872).
  - **+3,16R**: T1 26 april, T2 29 april.
- Replicatie: **9/9 trades, 4/4 no-trades, geen extra engine-trades tot mei 2021**.
- EURUSD 2016-2025: **26 trades, 54% T1, +17,8R**. Ervoor: 24 trades, +19,2R.
  - Erbij: setup 14 (+3,2R), en 10 juni 2021 (-1R) in plaats van 25 juni 2021 (-1R).
  - In 2025: 17 juli (-1R, rode tweezer zoals 22 april 2021) en 22 september (-1R) in plaats van 27 augustus (+2,6R).
  - Setup 2 valt nu op 15 okt 2018 (+1,61R).
- 37 instrumenten: met beide regels 971 trades, **+83R** (gem. +0,086R, t 1,7). Zonder: 932 trades, +70R (t 1,5).
- Ter info, opgeteld over eerdere stappen: de structuurregels (`STRUCT_SWINGS`, `VOID_SPENT`) zakten de 37 instrumenten
  van +98R naar +70R, terwijl EURUSD beter matcht.

### Versies naast elkaar; keuze: versie C (setup-14-regels weer uit)
De trader: "Ik heb liever dat de andere trades hetzelfde blijven en deze setup 14 er dan niet bij (moeilijke trade)".
Alle versies zijn opnieuw gedraaid met dezelfde code, EURUSD en 37 instrumenten, 2016-2025:

| versie | EURUSD trades | T1 | R | trader-trades | no-trades | extra tot mei 2021 | 37 instr. trades | R | t |
|---|---|---|---|---|---|---|---|---|---|
| A oud | 27 | 56% | +18,0 | 8/9 | 4/4 | 21 mei 2020, 15 apr 2021 | 969 | +93,9 | 1,90 |
| B + weekstructuur | 26 | 58% | +20,1 | 8/9 | 4/4 | 21 mei 2020 | 950 | +82,0 | 1,75 |
| **C + trigger op na vervallen fib** | **24** | **58%** | **+19,2** | 8/9 | 4/4 | geen | 932 | +70,4 | 1,52 |
| D + setup-14-regels | 26 | 54% | +17,8 | 9/9 | 4/4 | geen | 971 | +83,3 | 1,74 |

De eerder genoemde +98R op 37 instrumenten was versie A in een oudere codestand; nu meet die versie +94R.
Gekozen: **C**. `TWEEZER_ANY` en `LAST_SWING_FIB` staan weer uit; setup 14 blijft gedocumenteerd als gemist.

### Instrumenten weglaten?
Per instrument (versie C) negatief in beide periodes (2016-20 en 2021-25): GBPNZD, GBPCAD, GBPJPY, USDCAD,
NAS100USD, GBPCHF.
- Zonder de 4 slechtste (GBPNZD, GBPCAD, GBPJPY, USDCAD): 826 trades, +113R. Dat is achteraf gekozen.
- Test vooruit: kies op 2016-2020 en kijk naar 2021-2025.
  - De 20 instrumenten die positief waren in 2016-20 brachten in 2021-25 samen **+20,6R**.
  - De 17 die negatief waren brachten **+30,3R**.
  - In versie A hetzelfde beeld: +15,6R tegen +29,2R.
- Het backtestresultaat per instrument voorspelt dus niet welk instrument later werkt. Instrumenten weglaten op
  basis van de backtest is curve-fitting. Beter: per instrument regels van de trader zelf, zoals nu voor EURUSD.

### Wick-regel bij de weekly BoS en een trigger na een valse BoS (getest, nog uit)
De trader: "Dit hoefde toch niet: niet onder de wick van de swing". Klopt. `BREAK_WICK` was een eigen toevoeging om
setup 5 (juli 2019) te filteren.
Voorstel van de trader: "Mss ook een regel wanneer het dus een fake BoS geweest is, kijken voor een continuation
setup terug met daily BoS?"
In de engine: `FAKE_TRIGGER`. Een poging tot week-BoS tegen de trend in, waarbij de week erna terug sluit, maakt van
die terugsluitweek een week-trigger voor de trend.

| wick-regel | valse-BoS-trigger | EURUSD trades | T1 | R | trader-trades | fout | 37 instr. | R | t |
|---|---|---|---|---|---|---|---|---|---|
| aan | uit (versie C) | 24 | 58% | +19,2 | 8/9 | s14 | 932 | +70,4 | 1,52 |
| aan | aan | 26 | 54% | +17,2 | 8/9 | s14, extra 21 mei 2020 | 937 | +70,4 | 1,51 |
| uit | uit | 26 | 62% | +19,8 | 7/9 | s5, s6, s14, extra 19 jul + 16 sep 2019 | 947 | +87,3 | 1,87 |
| uit | aan | 28 | 57% | +17,8 | 7/9 | s5, s6, s14, extra 2019 + 21 mei 2020 | 952 | **+98,5** | **2,09** |

- **Valse BoS'en die de engine ziet op EURUSD sinds 2016**:
  - Bullish poging week 2 maart 2020 (lijn 1,11773), week 9 maart sluit terug.
  - Bearish poging week 16 aug 2021 (lijn 1,17602), week 23 aug sluit terug.
- Met de valse-BoS-trigger komt de short van **21 mei 2020** terug. Daarvan zei de trader: "Ik snap niet waarom hij
  hier short zou gaan".
- Op 37 instrumenten is "wick-regel uit + valse-BoS-trigger aan" de beste versie tot nu toe: +98,5R, t 2,1.
- Beide opties staan uit voor EURUSD. Kandidaat voor de andere instrumenten.
