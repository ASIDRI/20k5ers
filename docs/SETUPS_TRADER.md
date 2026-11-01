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
Grafieken: `docs/setups_trader/10_eurusd_2020_short/01.png`, `02.png`.

### 1. Wat er gebeurt
- **Wekelijkse BoS-lijn 1,11755**: body-high van de laatste week-swing high (weken van 23/30 december 2019, top 1,1239).
- **Week van 2 maart 2020: slot 1,12839** boven die lijn (open 1,1045, top 1,1355 door maand-S/R 2 1,13125).
- **Week van 9 maart: bearish engulfing** (open 1,1351, top 1,1496 = exact aan week-S/R 1,1500, slot 1,1105 - terug
  onder de BoS-lijn; omvat de bullish body van de week ervoor). Week van 16 maart: slot 1,0696.

### 2. De vijf criteria van setup 5 toegepast (ATR 14 weken ± 140 pips)
| criterium | waarde | oordeel |
|---|---|---|
| 1. grote swing? | de top van december liep 460 pips (± 4 ATR) omlaag tot 1,0778 | **ja**, echte swing high |
| 2. kwaliteit van de breuk | slot 107 pips (0,77 ATR) boven de lijn, body 240 pips | **ja** |
| 3. acceptatie | de week erna sluit terug onder de lijn, met een bearish engulfing | **nee -> mislukte BoS** |
| 4. chaos-filter (efficiëntie 10 weken) | 0,12 in de breukweek (twee weken V-vorm, +5%) | **nee** (< 0,2) |
| 5. hogere tijdframe | maandstructuur bearish; slot net onder maand-S/R 2 (1,13125), daarna lont tot week-S/R 1,1500 | **nee** |

**Wat de bot had gezegd:**
- Na het slot van de week van 2 maart: **"BoS onbevestigd"** - criteria 1 en 2 kloppen, maar 4 en 5 niet. Nog geen
  bullish structuur; geen longs, de shorts nog niet afschrijven; één week wachten op acceptatie.
- Na het slot van de week van 9 maart: **"mislukte BoS"** -> de bearish weekstructuur blijft, en de bearish engulfing
  aan week-S/R 1,1500 / boven maand-S/R 2 is meteen een **week-trigger voor shorts**.
De prijs: week van 16 maart slot 1,0696, onder maand-S/R 3.

Kanttekening: criterium 3 vraagt per definitie een week geduld; in die week is de status "onbeslist". Dat moet de
bot zo behandelen: geen nieuwe trades in de richting van de nieuwe BoS tot hij bevestigd is.
