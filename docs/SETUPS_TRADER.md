# Setups van de trader - stap voor stap gedocumenteerd

Doel: elke setup die de trader aanlevert vastleggen zoals hij hem leest (top-down: maand -> week -> dag), met de
prijzen nagerekend op onze eigen data (`load(sym, "D1")`, broker-tijd: een dagkaars met tijd `... 21:00` is de
handelsdag erna). **Nog niet verwerkt in de engine**; eerst alle setups verzamelen, daarna de gemeenschappelijke regels
eruit halen en vooraf vastleggen.

Per setup: context, trigger, fib, instap, stop, targets, beheer, uitkomst, en wat het betekent voor de engine (alleen
notities).

## Overzicht en win rate
Beheer van de trader: **T1 = -0,2**, daarna stop in winst; **T2 = -0,6** (bij een maand-S/R vlak erbij: daar, zoals
-0,65 in setup 1). Hoeveel op T1 gesloten wordt, ligt nog niet vast; hieronder ter vergelijking 50% op T1.

| # | instrument | richting | instap | diepte | T1 | T2 | R bij T1 | R bij T2 | 50% T1, rest T2/stop |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EURUSD | short | 10 jul 2018 | 0,83 | ja | ja (-0,65) | +2,6 | +3,6 | +3,1R |
| 2 | EURUSD | short | 16 okt 2018 | 0,41 (lont 0,55) | ja | ja (-0,6) | +1,8 | +2,9 | +2,4R |
| 3 | EURUSD | short | 1 feb 2019 | 0,66 | ja | nee, stop in winst | +1,8 | - | ± +1,5R |
| 4 | EURUSD | short | 2 mei 2019 | 0,31 (lont 0,796) | nee | nee | - | - | **-1R** |

**Win rate: 3 / 4 (75%) T1 geraakt; T2 2 / 4.** Totaal bij 50% op T1: ± +6,0R over 4 trades (± +1,5R gem.).

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
