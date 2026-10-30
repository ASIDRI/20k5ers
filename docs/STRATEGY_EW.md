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
