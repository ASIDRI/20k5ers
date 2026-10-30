# Elliott Wave op de manier van de trader

Bron: twee video's van de trader (Google Drive), verwerkt met `scripts/video_digest.py`. Die tool maakt een transcript
met tijdstempels, een screenshot bij elke beeldwissel (en minstens elke 20 s), en zet bij elk screenshot wat er op dat
moment gezegd wordt. Tijdstempels hieronder zijn [mm:ss] in de video. Transcript: `docs/ew/v2_transcript.txt`.
Belangrijkste screenshots: `docs/ew/`.

1. **"Elliott Wave Theory"** (78 min, Engels gesproken). De theorie en hoe hij **analyseert**. Hij zegt zelf aan het
   eind: "this is how I make my analysis, this is not how I trade; my strategy video is the one you have to check"
   [77:46-78:13].
2. **"How I made 5X in 3 Days Trading On Binance (Small Account Challenge)"**: in verwerking. Daar verwacht ik de
   handelsregels.

Neely is geschrapt (samenvatting in `docs/RND_RESULTS.md`). Dit is een nieuwe start.

---

## Video 1: "Elliott Wave Theory"

### Uitgangspunt
- Elliott Wave gaat over **kansen, niet zekerheden**. Fibonacci-verhoudingen zijn "probabilities and never
  certainties" [01:22, 36:04]. De theorie dient om **kansen weg te strepen**; wat overblijft is het meest
  waarschijnlijk. Hij houdt altijd **alternatieve tellingen** bij [52:02-52:10].
- **Nooit alleen gebruiken**: altijd samen met Fibonacci, **MACD en RSI** [52:10-52:25]. Instappen legt hij uit in de
  strategievideo.
- Boek: "Elliott Wave Principle" van Prechter & Frost [00:12-00:21].
- Hij handelt **niet** elke golf of elk patroon. "My strategy is based on the most probable patterns at key Fibonacci
  levels" [28:53-29:42]. Combinaties (W-X-Y) handelt hij niet stuk voor stuk; hij zoekt het **eind van een correctie
  op een belangrijk fib-niveau** en beslist daar [31:59-32:20].

### Structuur (de standaardregels)
- **Impuls 5-3-5-3-5:** golven 1, 3 en 5 zijn impulsief (zelf 5 golven), 2 en 4 corrigerend (A-B-C) [01:32, 04:21-05:24].
- **Kanaal:** trek een lijn door de toppen van 1 en 3 en een parallel daaronder; 2 en 4 raken de onderlijn. Golf 5
  raakt de bovenlijn, blijft eronder (afgekapt, "truncated"), of schiet erdoorheen (verlengde 5) [01:58-04:11].
- **Eén van 1, 3, 5 is verlengd**, meestal 3. **Golf 3 is nooit de kortste** [02:39-03:33].
- Is 3 verlengd, dan zijn **1 en 5 meestal even lang** [32:54-33:00].
- **Harde regels:**
  - golf 2 gaat nooit voorbij het begin van 1 [33:24-33:41];
  - golf 4 komt nooit in het gebied van 1, behalve in een diagonaal [33:44-34:42];
  - golf 3 gaat altijd voorbij het eind van 1 [34:42-34:46];
  - golf 4 gaat nooit voorbij het eind van 2 [34:50-34:58].
- **Afwisseling:** is golf 2 scherp (zigzag), dan is 4 zijwaarts (flat/triangle), en andersom. Meestal is 2 scherp en
  zakt hij diep, richting het begin van 1 [12:42-13:20, 16:18-16:44, 32:29-32:49].
- Golf 2 duurt meestal **korter** dan golf 1 [33:14-33:20].
- **Diagonalen:**
  - Komen alleen voor als golf 1, golf 5, golf A of golf C, als wig 3-3-3-3-3 met overlap [05:55-08:26]. Er bestaan
    ook expanderende diagonalen [61:25-62:08].
  - Een eind-diagonaal in golf 5 is het meest gezien in crypto. Typisch: **golf 5 schiet door de bovenlijn, met een
    piek in volume**, en zakt dan scherp. "Interesting area to go short" [08:43-10:50].
  - Is golf 1 een diagonaal, dan is golf 3 waarschijnlijk verlengd [35:01-35:22].
  - Nooit twee diagonalen in één correctie [11:44-11:59].
- **Correcties:**
  - Zigzag 5-3-5 (scherp, meestal golf 2).
  - Flat 3-3-5 (zijwaarts, meestal golf 4): regulier, expanded (irregular) of running.
  - Triangle A-B-C-D-E (zijwaarts, meestal golf 4).
  - Combinaties: dubbele/driedubbele zigzag W-X-Y(-X-Z).
  [13:43-31:31]
- **Volume** droogt op tijdens een correctie en piekt aan het eind van C [20:14-20:25, 48:11-48:37].
- Uitbraak uit het correctiekanaal ("jump line") **op een belangrijk fib-niveau** = koopkans, of wachten op een
  hertest van die lijn [23:30-24:13].

### Fibonacci per golf (de kern; zijn Google-doc in beeld [39:46], `docs/ew/v2_39m46_wave2_fib_stop.jpg`)

| Golf | Hoe trekken | Kansen (in volgorde) | Wat hij doet |
|---|---|---|---|
| **2** | retracement van begin 1 -> top 1 [37:40-37:49] | **0,618 / 0,66** (golden pocket, meest), 0,5, zelden 0,786 [37:49-38:57] | **Kopen** in stappen: eerst op 0,5, bijkopen op 0,618/0,66, nog meer op 0,786. **Stop onder het begin van golf 1** (anders klopt de telling niet) [38:57-40:05] |
| **3** | trend-based fib extension: begin 1 -> eind 1 -> eind 2 [40:20-40:41] | **1,618** of **2,618** x golf 1 [40:13-40:50] | Bij 1,618: kijken of er 5 golven in 3 zitten -> mogelijk short / winst nemen. Gaat hij door 1,618, dan verwacht hij 2,618 [41:01-41:26] |
| **4** | retracement van eind 2 (begin 3) -> top 3 [42:08-42:18], plus het kanaal (1-3 parallel door 2) [41:44-42:02] | **0,236** of **0,382** van golf 3 [42:18-42:36] | **Kopen** bij 0,236 en/of 0,382, liefst als het kanaal geraakt wordt. **Stop onder 0,382 én onder het kanaal**; daaronder is het geen golf 4 [42:36-43:56] |
| **5** | (a) trend-based ext. begin 1 -> eind 1 -> eind 4: **1:1** (5 = 1); (b) ext. begin 1 -> eind 3 -> eind 4: **0,618** (meest) of **0,786** [44:06-45:29] | 1:1, 0,618, 0,786 | **Short / long verkopen** waar een fib-kans samenvalt met de bovenlijn van het kanaal en een niveau van golf 3 [45:38-46:03]. Zijn Google-doc: "if neither 1 or 3 is extended expect wave 5 to be 1,618 x 1-3" |

**Correcties (Google-doc):**
- **Zigzag:** C = A (meest), of 1,618 x A, of 0,618 x A. Trekken met een trend-based extension: begin A -> eind A ->
  eind B [47:06-49:31].
- **Regulier flat:** A, B en C zijn ongeveer gelijk [49:44-50:09].
- **Expanded flat:** B = 1,236 of 1,382 x A (retracement van A); C = 1,618 x A (expanded) of 0,618 (running)
  [50:14-51:35].
- Het eind van C aan een **volumepiek op een fib-niveau** = het eind van de correctie [48:11-48:41].

Samengevat: "you'll want to buy here at the golden ratio [golf 2], you'll want to buy here [golf 4], you want to short
here [eind 3 op 1,618] and you want to short this one [eind 5] or just sell your buy position" [46:20-46:40].

### Hoe hij een grafiek telt (Bitcoin weekgrafiek [52:47-69:48], AXS 8u [69:55-75:52])
- Hij begint op de **weekgrafiek, in log-schaal** [55:14]. Golf 1 = een duidelijke grote eerste beweging vanaf een
  bodem (BTC vanaf juli 2013).
- Hij trekt de fib's van golf 2, 3, 4, 5 zoals in de tabel en controleert waar de prijs "exact" reageerde: golf 2 op
  0,66, golf 3 op 1,618, golf 4 op 0,382, golf 5 op 1:1 [53:39-56:58].
- Daarna telt hij **binnen** de golven op een lager tijdframe (3 dagen) en houdt hij twee tellingen naast elkaar
  (diagonaal klaar tegenover expanderende diagonaal met nog een golf 5 te gaan). De **ongeldigheidslijn** beslist
  welke telling overblijft [62:21-68:42, `docs/ew/v2_68m54_btc_count.jpg`].
- Log of niet log maakt de fib-doelen anders. Hij gebruikt liever **niet-log** voor de fib's [70:00-71:31].
- Werkwijze: "trial and error: count the waves, have alternate counts, find the probabilities, react on the
  probabilities" [76:01-76:20].

### Wat dit betekent voor een bot (eerste inschatting, nog niet getest)
De drie handelsmomenten die hij noemt, zijn concreet te maken:
1. **Golf-2-koop:** na een afgeronde golf 1, kopen tussen 0,5 en 0,786 (golden pocket 0,618-0,66), met de stop onder
   het begin van golf 1. Doel: golf 3 op 1,618 x golf 1.
2. **Golf-4-koop:** na golf 3, kopen op 0,236-0,382 van golf 3 aan de kanaallijn, met de stop onder 0,382 en het
   kanaal. Doel: golf 5 (1:1 met golf 1, of 0,618 van 1-3).
3. **Short aan het eind van golf 3 of 5** op samenvallende fib-niveaus en de kanaallijn (bij een eind-diagonaal met
   volumepiek).

Open vragen die de strategievideo moet beantwoorden:
- Wanneer is golf 1 "vastgesteld"?
- Hoe gebruikt hij MACD en RSI voor de instap?
- Op welk tijdframe handelt hij?
- Hoe beheert hij een trade: winst nemen, stop verplaatsen?
EOF

---

## Video 2: "How I made 5X in 3 Days Trading On Binance (Small Account Challenge)"

61 minuten, live opgenomen van 22 tot 24 januari 2022. Transcript: `docs/ew/v1_transcript.txt`. Hij scalpt
crypto-futures op Binance (DYDX, GALA, FTM, CRV) op de **1-minuutgrafiek** (soms 3 of 5 minuten), met **20x hefboom**
en een account van 100 USDT (100 -> 523 USDT). Zijn scherm toont steeds hetzelfde: de golftelling,
fib-retracements/extensies, de **RSI** (paneel 1), de **MACD** met histogram (paneel 2) en twee EMA's, en vaak de
BTC-grafiek ernaast [04:30, `docs/ew/v1_04m30_dydx_1m_count_fibs_rsi_macd.jpg`].

### De twee setups die hij steeds handelt
1. **Het eind van een correctie kopen** (de meeste trades): A-B-C of W-X-Y naar beneden, ingekocht op een fib-niveau.
   - Bij een golf 2 / B-golf: 0,382 [02:37-03:19], 0,5 [04:12, 05:37, 13:18], golden pocket 0,618-0,66 [17:14, 23:21]
     of 0,786 [23:21, 41:29, 58:08]. "In highly leveraged markets the 0.382 can also be a second-wave correction"
     [03:02-03:19].
   - Bij C of Y: C = A (1:1-extensie) [18:14] of 0,618 x A [21:03-21:40, "truncated C"].
   - Bij een irregular flat: 1,236 / 1,382 [28:34, 41:29, 54:09, 55:37].
   - Samenvallende niveaus versterken elkaar, bijvoorbeeld 0,786 op de ene grafiek met 1,618 op de andere [42:41-43:10].
2. **Het eind van een vijfgolvenbeweging tegen in handelen** (short na 5 golven omhoog, of long na 5 omlaag): op 0,786
   [01:15-01:23, 31:32-31:54], als een trendlijn op 3 minuten breekt [09:37-10:02], of bij 5 golven met MACD-divergentie
   [12:10-12:33].

### Bevestiging (naast de telling en het fib-niveau)
- **MACD-divergentie:** de prijs maakt een lagere low, de MACD een hogere [10:54, 12:27-12:33, 28:34-28:54]. Voor een
  short: een hogere high met een lagere high op de MACD [54:20].
- **MACD-histogram:** "the histogram always shows the A or the W as the lowest", met daarna hogere lows op het
  histogram [34:26-34:49, `docs/ew/v1_34m41_gala_wxy_histogram.jpg`].
- **RSI verborgen bullish divergentie:** een hogere low in de prijs, een lagere low op de RSI [04:27-04:42].
- Steun van de **55-EMA** [04:42].
- Wachten tot de prijs **de trendlijn breekt** met een MACD-kruising [11:10-11:31, 24:15]. Ook steun van het
  **volumeprofiel** (point of control) [06:02-06:17, 17:45], een order block [04:12] en een eerdere weerstand of steun.
- Fib's op de log- én niet-loggrafiek, en op meerdere grafieken van dezelfde munt [31:38-32:21, 42:41-43:03, 48:37].

### Instap, stop en beheer
- **Instap:** op het fib-niveau, met **bijkopen** op de volgende niveaus (0,5 -> golden pocket -> 0,786) [05:37-05:45,
  17:22-17:55, 41:29-42:08, 58:17-58:31].
- **Stop:** krap, net voorbij het punt waar de telling niet meer klopt ("that is my invalidation") [19:03-19:35]: onder
  het fib-niveau [21:40-21:54], boven de laatste top bij een short [31:54-32:02], of onder het begin van golf 1.
  "Sometimes a little bit too tight" [22:37]. Hij verliest daardoor geregeld, met kleine verliezen [11:51, 12:33,
  19:48, 23:05, 52:29, 54:01].
- **Winst nemen in stukken:** telkens **50%** (of 25%) op het volgende fib-niveau. Dat zijn 0,236 / 0,382 / 0,5 /
  golden pocket van de vorige beweging en de 1:1-extensie [03:24-03:38, 06:26-07:17, 13:39-15:15, 24:15-26:11,
  59:18-60:58].
- Na de eerste winstname: **stop naar instap** ("so that I cannot have a loss") [32:40-34:00, 44:12-44:20, 49:54-50:06].
- Geen posities 's nachts [26:11-26:27].

### Wat dit betekent voor de 5ers-bot
- Dit is **discretionair scalpen op crypto, op 1 minuut, met 20x hefboom**. Elke trade hangt af van een telling die hij
  ter plekke maakt, met een tweede telling als alternatief. Drie dagen live is geen bewijs van een edge: de titel
  ("5X") kiest de goede periode uit, en hij verloor ook trades.
- De vaste kern is wél te coderen: (1) een swing (golf 1 / A / W) afgerond, (2) een terugval naar 0,382-0,786 (of de
  1:1-extensie bij C/Y, of 1,236-1,382 bij een irregular flat), (3) een bevestiging (MACD-divergentie of een
  RSI-divergentie, een trendlijnbreuk), (4) een stop net voorbij de ongeldigheid, (5) de helft eraf op het volgende
  fib-niveau en de stop naar instap.
- **Kosten zijn het grote probleem op 1 minuut.** In de eerdere R&D kostten de spread en slippage op 4u al 10% van een
  ATR per trade (`docs/RND_RESULTS.md`, fase 2). Op 1 minuut is dat veel meer. De repo heeft geen 1-minuutdata; wel 15
  minuten (2015-2025) voor 28 forexparen, goud, zilver, indices, olie, BTC en ETH.
- In de theorievideo verwijst hij naar een aparte "strategy video" met zijn instappen [52:25, 77:46]. Dat lijkt deze
  video niet te zijn. Als die bestaat, is dat de belangrijkste bron.

---

## Test E1 (vooraf vastgelegd, 2026-10-30): tellen op week en dag, handelen op 4 uur

De trader: "probeer op 4 uur de trades te doen, maar ook op de daily en weekly chart de golven tellen". Code:
`research/ew/ew_bt.py` (`--now` toont de huidige telling), `research/ew/ew_eval.py`.

**Motor (ongewijzigd):**
- alleen gesloten candles (`complete_times`);
- instap op het slot van de 4u-candle die bevestigt;
- `test18.follow` / `managed`: de stop gaat voor als stop en doel in dezelfde candle vallen;
- kosten per symbool;
- één positie per richting.

**Instrumenten:** de 34 van tests 20-33. Goud, zilver en NAS100 gebruiken de 4u-reeks van OANDA (vanaf 2015) met de
dag- en weekreeks onder de andere naam.

**Swings:** een top (bodem) is bevestigd als de prijs K x ATR(14) terug is, en is bekend bij het slot van die candle.
K = 2 (week), 3 (dag), 2 (4u).

**Telling op week en dag** (gespiegeld voor omlaag; video "Elliott Wave Theory"):

| Telling | Voorwaarden | Verwachting |
|---|---|---|
| in golf 3 | golf 2 = 0,382-0,786 van golf 1 (±0,03) [37:49-38:57] | omhoog |
| in golf 5 | zoals hierboven; 3 voorbij 1 en niet korter dan 1 [34:42, 03:33]; golf 4 = 0,20-0,50 van 3 (0,236-0,382 met marge), boven de top van 1 [33:44, 42:18] | omhoog |
| 5 golven af | "in golf 5" + een nieuwe top voorbij 3 met golf 5 >= 0,5 x golf 1 | omlaag |

De telling die op de laatste swing eindigt, wint. Ze vervalt zodra het laatste slot voorbij haar ongeldigheidsniveau
komt.

**Setup 1 (beslissend): het eind van de correctie kopen, met de grotere telling mee.**
- Een 4u-poot 0 -> 1 van minstens 4 ATR(4u), met het eind bevestigd.
- Dan een 4u-slot waarbij:
  - de low sinds punt 1 het 0,382-niveau heeft bereikt (zone 0,382-0,786) [38:04-39:22, video 2 02:37-05:45];
  - de MACD(12,26,9) zijn signaallijn kruist in de handelsrichting [video 2 11:10-11:31];
  - het slot boven het 0,786-niveau staat.
- Dit moet binnen de duur van de poot zelf gebeuren (minimaal 6 candles) ("wave 2 is mostly shorter in time than
  wave 1" [33:14]).
- Ongeldig: een slot voorbij het begin van de poot. Een nieuwe top voorbij 1 vóór de instap: overslaan.
- Stop: 0,1 ATR(4u) voorbij het begin van de poot (het begin van golf 1) [39:45-40:05].
- **Beheer `R_m` (beslissend):** de helft op punt 1 (hertest van de top), stop naar instap, de rest op de
  1,618-extensie (0 -> 1 -> low van de correctie) [40:13-40:50, video 2: telkens de helft, daarna de stop naar
  instap].
- **Beslissende regel:** `d1 == 1 & w1 >= 0`, dus de dagtelling in de handelsrichting en de weektelling er niet tegen.

**Setup 2 (tweede cel): een afgeronde vijfgolvenbeweging op 4u tegen in handelen.**
- De 4u-swings 0..5 voldoen aan "5 golven af", met MACD-divergentie (de MACD-lijn bij 5 lager dan bij 3, voor een
  top) [video 2 12:10-12:33, 54:20].
- Instap op het slot dat swing 5 bevestigt. Stop: 0,1 ATR voorbij 5.
- `R_m`: de helft op het eind van golf 4, stop naar instap, de rest op 0,618 van de hele beweging 0 -> 5.

**Lat (per cel):**
- Elke periode (2005-14, 2015-20, 2021-25) zit gemiddeld boven 0 met PF >= 1,05, en de drie samen halen t >= 2,0.
- Een geslaagde cel moet daarna slagen op de 31 holdout-instrumenten van test 33 (eigen vastlegging).
- Gerapporteerd: zonder dag/week-filter, met alleen dag of alleen week, `R_t1` (alles op punt 1), `R_t2` (alles op
  1,618) en `R_tight_m` (stop onder de low van de correctie, zoals in zijn live trades).

Vóór deze vastlegging is de code op EURUSD gedraaid om te zien dat hij werkt (aantallen, geen rendement).
