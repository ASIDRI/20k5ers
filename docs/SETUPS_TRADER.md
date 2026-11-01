# Setups van de trader - stap voor stap gedocumenteerd

Doel: elke setup die de trader aanlevert vastleggen zoals hij hem leest (top-down: maand -> week -> dag), met de
prijzen nagerekend op onze eigen data (`load(sym, "D1")`, broker-tijd: een dagkaars met tijd `... 21:00` is de
handelsdag erna). **Nog niet verwerkt in de engine**; eerst alle setups verzamelen, daarna de gemeenschappelijke regels
eruit halen en vooraf vastleggen.

Per setup: context, trigger, fib, instap, stop, targets, beheer, uitkomst, en wat het betekent voor de engine (alleen
notities).

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

## Setup 3 - EURUSD short, februari 2019 (vervolg op setup 2) - uitkomst volgt
Grafieken: `docs/setups_trader/03_eurusd_2019_short/01.png` ... `05.png`.

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

### 4. Trade (uit 05.png)
| | prijs | toelichting |
|---|---|---|
| instap short | **1,14548** | na de doji / shooting star, ± 0,66 in de fib |
| stop | **1,15743** | boven de swing high (1,1570) en maand-S/R 1 (1,15542); risico 119 pips |
| target (op de grafiek) | **1,12159 (-0,28)** | |
| uitkomst | *volgt* | |

### 5. Notities voor de engine (nog niet verwerken)
1. **Week-S/R als terugkeerniveau**: de trader kiest het (enige) week-niveau dat als steun én weerstand getest is, en
   wacht dáár op de bearish weekkaars. In setup 1 en 2 was dat het weekly-BoS-niveau; hier een apart week-S/R-niveau.
2. Volgorde opnieuw: week-engulfing -> daily BoS (bearish BoS candle) -> fib -> pullback tot een S/R-niveau ->
   lont-rejections -> **minstens één bearish kaars** -> doji/hammer/shooting star -> instap.
3. Fib-confluentie: 0,5 op de weekly BoS, de instapzone tussen 0,66 en het week-S/R-niveau (± 0,8).
4. Stop boven de swing high én de maand-S/R; target -0,28 op de grafiek (T1 -0,2 zoals altijd; T2 -0,6 volgens setup
   2 - na te gaan met de uitkomst).

---
