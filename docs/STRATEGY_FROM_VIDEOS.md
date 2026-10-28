# Strategie uit de video's ("The Market Matrix")

Bron: zes video's (Google Drive, op volgorde aangeleverd). Per video: transcript met tijdstempels en
screenshots in sync (`scripts/video_digest.py`; uitvoer lokaal in `research/videos/`, niet in git).
Doel: elke regel zo exact vastleggen dat hij in code kan, en dan testen op de gekeurde referentie
(alleen afgesloten candles, per 15 minuten, strikte broker; zie `docs/AUDIT_PLAN.md`).

Per regel: wat de video zegt (met tijd), en hoe het meetbaar wordt. "Open" = nog niet eenduidig, keuze nodig.

## 1. Support en resistance (12:35)

| # | Regel uit de video | Meetbaar gemaakt |
|---|---|---|
| SR1 | Begin altijd op de **maandgrafiek** om de belangrijke S/R-zones te vinden; S/R op lage timeframes "werkt niet goed" (00:12, 00:42) | S/R-niveaus alleen uit MN (en W1 ter bevestiging, 05:43) |
| SR2 | Trek de lijn van **links naar rechts** door zoveel mogelijk **tikken** (taps): wicks en lichamen die het niveau raken en keren (01:41, 03:55) | Niveau = prijs waar het aantal keerpunten (swing highs/lows van MN-candles) binnen een tolerantie maximaal is; sterkte = aantal tikken |
| SR3 | **Hoe meer tikken op de maand, hoe sterker** het niveau (04:00) | Sterkte-score per niveau; minimum aantal tikken als filter (open: 3? 5?) |
| SR4 | Rol wisselt: resistance wordt support en omgekeerd; "throw-over"/deviatie (even door het niveau en terug) hoort erbij (02:17, 03:42) | Een tik telt ook als de wick door het niveau gaat maar de close terugkomt aan de oorspronkelijke kant |
| SR5 | **Niet te veel niveaus**: 3 à 4 hoofdniveaus, vooral de dichtstbijzijnde rond de huidige prijs (05:02, 09:09, 10:15) | Per symbool de N sterkste niveaus, waarvan de dichtstbijzijnde boven en onder de prijs gebruikt worden |
| SR6 | Wicks die **meteen** afketsen of afwijzen zijn heel belangrijk (09:14) | Extra gewicht voor tikken met een lange wick en een close ver van het niveau |
| SR7 | Bij een niveau: let op een **mogelijke omkeer**; breekt de prijs er hard door, dan mogelijke support/resistance bij de retest (10:38-10:59) | Geen instap op zichzelf: het niveau is de **locatie**; de instapregels komen uit de volgende video's |
| SR8 | "Er spelen veel meer factoren mee" (06:51, 11:09): S/R alleen is geen strategie | Combinatie met structuur, fib en frameworks (video 2-4) |

Belangrijk voor de code: de huidige bot heeft een filter "location" (S/R), maar dat staat **uit**
(`use_htf_filter: false`). Wat deze video beschrijft, zit dus nu niet in de bot.

## 2. Market Structure (ca. 28:00)

Context: alle voorbeelden op de MONTHLY (1M) chart (DXY en BTCUSD Bitstamp, log-schaal voor BTC). Doel van de les: bias bepalen (bullish/bearish), niet entries. Hij zegt dat hij zelf vooral op daily handelt (11:15).

| # | Regel uit de video (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| MS1 | Bias bepalen op hoge timeframe: monthly, soms weekly bij te weinig historie; later ook daily genoemd (01:10, 26:23). Handel met de trend van dat TF (01:17). | Bias-TF = 1M (fallback 1W als < ~N jaar data; N niet genoemd). Open: aantal candles minimaal. |
| MS2 | Uptrend = higher lows (HL) en higher highs (HH); downtrend = lower highs (LH) en lower lows (LL) (00:57, 01:27, 15:46). Alleen prijs "nabij" telt, ver verleden is ruis (00:52, 21:22). | Swing-detectie op OHLC (own interpretatie): swing high = candle-high met n candles lager links+rechts (n=2 voorstel; video noemt geen n, hij kijkt "met het oog"). Trend = laatste 2 swing-lows oplopend + laatste 2 swing-highs oplopend. Lookback beperken tot recente swings (Open: laatste 4-6 swings op 1M). |
| MS3 | Key level in uptrend = het laatste higher low voor de high (13:27, 19:47: "last key higher low moving towards the high"). Key level in downtrend = laatste lower high (13:33, 03:08 "key lower high"). Elke nieuwe high wordt opnieuw een key level om doorheen te breken (16:11). | key_low = low van de laatste swing-low die de laatste swing-high voorafging (up). key_high = high van laatste LH vóór de laatste low (down). Na elke BOS: key opnieuw bepalen (10:07: "we change the key level"). Getekend als horizontale lijn "KEY" vanaf de body/wick-extreem. |
| MS4 | Key levels tekent hij met de BODIES: "I actually use the bodies to see my key levels too" (05:50). Op frames (12:20, 19:21) start de KEY-lijn op de top van een candle met wick/body-top; wicks daarbuiten gelden als deviatie. | Key-prijs = max(open,close) van de swing-candle (body-top) voor key high; min(open,close) voor key low. Open: wick-extreem als alternatief; niet eenduidig, test beide. |
| MS5 | Break in market structure (BOS/shift) = key level wordt doorbroken met een "breakaway candle with force" (04:07, 04:19, 07:26, 08:30). Een wick erboven of deviatie telt NIET (06:00, 09:22). | Break = candle CLOSE voorbij key (niet alleen wick). Force = body groot: Open: body >= x * gemiddelde body van laatste N candles (x=1.5, N=10 voorstel, video geeft geen getal) of body/range >= 0.6. Tolerantie 0. |
| MS6 | Breakaway = candle die WEGBREEKT van het level (breekt en blijft/vervolgt), niet breekt-en-terugkeert (17:52-18:26 "it breaks, pulls back, stays here, ranging, this will be a deviation"; 19:00-19:38). | Filter: candle N sluit voorbij key; volgende candle(s) (Open: 1-2) sluiten niet terug binnen oude range. Terugkeer binnen key = deviatie/fakeout, geen BOS. |
| MS7 | Volledige bearish->bullish shift (03:00-03:40): LH's, dan break van de key lower high met force, daarna HL, daarna HH = bevestigde shift. Hij wil liefst instappen op de HL (03:40). | Statemachine: down-trend -> close boven key_LH (MS5) -> wacht swing-low die hoger is dan de laatste LL (HL) -> prijs maakt HH boven break-high = shift bevestigd. Spiegelbeeld voor bearish. |
| MS8 | In uptrend: wacht op HL op key level, bounce, dan breakout boven vorige high (10:01-12:13). Breakout direct kopen is niet de beste trade, kan deviatie zijn en trapt je (10:38-10:53). | Setup-trigger = prijs retest key_low/HL-zone na BOS, niet breakout-entry. (Eigen vertaling: entry op retest, niet op de break-candle.) |
| MS9 | HL mag een deviatie onder de vorige low hebben die terugkeert, telt nog steeds als HL (12:27-12:46). Sterk bullish = HL en direct hoger (12:46). | Tolerantie: wick onder vorige swing-low toegestaan zolang candle-close erboven blijft (consistent met MS5). |
| MS10 | Bullish blijft zolang er geen breakaway-close onder het laatste key HL is (13:01, 26:09). Wicks/deviaties onder of boven key zonder breakaway = bias ongewijzigd (14:00-14:30, 19:00). | bias_bull = niet (close < key_low met MS6-bevestiging). Anders geen verandering. |
| MS11 | Meerdere schalen: een break op lager TF is "short-term structure" binnen een hogere trend; nabije structuur weegt zwaarder dan oude (21:07-23:36, 24:49-25:59). Voorbeeld BTC: bullish op macro, break onder key op recente high geeft bearish nabij, maar bias nabij blijft bullish zolang recent HL-structuur intact (23:40). | Twee niveaus: macro (hele 1M) en nabij (laatste swings). Regel: gebruik nabije structuur voor bias; macro alleen als context. Open: definieer "nabij" (bv. laatste 12-24 maandcandles of laatste 2 swing-paren). |
| MS12 | Geen BOS maar break zonder force + ranging = nog steeds oude trend (17:44-18:29, 27:07-27:11); bij gebrek aan breakaway-candles: range, moeilijk te traden (27:09-27:16). | State "range" wanneer key doorbroken (wick of close) maar niet MS6; geen trade, bias blijft. |
| MS13 | Als prijs breekt maar op een key level direct afgewezen wordt (clean rejection, bearish candle na deviatie), verwacht hij naar de vorige key HL (19:34-19:55). | Deviatie boven key_high gevolgd door close terug eronder -> target = key_low (laatste HL). |
| MS14 | BTC: gebruik logaritmische schaal (15:21). | Rekenen met log-prijs/percentages voor swingdetectie op BTC (Open: swing-drempel in %). |
| MS15 | Hij geeft zelf aan dat het niet 100% is: "high probability" met kracht, niet altijd (09:08-09:22). | Geen harde garantie; gebruik als filter, niet als enige signaal. |

**Instap / SL / TP:** niet concreet benoemd in deze les. Alleen: entry bij voorkeur op het HL/key level na een shift (03:40, 11:33-11:49), bevestiging via Fibonacci-reactie (03:43-04:00, "later uitgelegd" = v3) en kracht van de candle. Geen SL/TP-getallen.

**Open (voor jou):** (1) swing-n; (2) body vs wick voor key; (3) "force" numeriek; (4) hoe "nabij" te begrenzen; (5) hij werkt op 1M/1W/1D voor bias, dus voorstel: bias op 1D (en 1W) i.p.v. 1M bij een intradag-bot.

Beelden bekeken: 00:40, 02:40, 03:20, 04:00, 05:40, 06:00, 08:20, 10:20, 12:20, 16:20, 19:21, 22:21, 25:01, 27:21. Zichtbaar: TF 1M; getekende zigzag-schetsen; horizontale lijnen met label "KEY" (template "18. KEY"); groen vak = zone; tekstbox "A breakaway candle is most important for a shift in market structure". Geen fib in deze video.

## 3. Fibonacci (ca. 31:00)

Context: bouwt voort op v2 (key level, breakaway candle). Voorbeelden op 1M en 1W (DXY, BTCUSD Bitstamp). Transcript schrijft "FIPS/Ibaraki" voor Fibs (spraakherkenning). Fib-tool: TradingView "Fib Retracement", getoond op frame 02:20.

| # | Regel uit de video (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| FIB1 | Instellingen fib: levels 0 en 1 als begin/eind van de tekening (02:09), plus 0.618, 0.66, 0.796, en negatieve extensies -0.25, -0.65, -1, -1.5 (02:22-02:38). Frame 02:20 bevestigt aangevinkt: 0, 1, 0.796, -1.5, -1, -0.25, -0.65; chart-frames (04:20) tonen ook 0.618 en 0.66. Standaardlevels 0.382/0.5/1.618 etc. staan UIT. "Extend lines right" aan. | Levels = {0, 0.618, 0.66, 0.796, 1} voor entry-zone/anker, {-0.25, -0.65, -1, -1.5} voor targets. Prijs(level) voor long: P = low_wick + (1-level)*(high_body - low_wick) met 1 = swing-low, 0 = swing-high (afgeleid uit frames 05:20, 04:20; 0.618-0.796 zit tussen low en high, targets boven high). |
| FIB2 | Ankerpunten "body to wick" (03:04-03:09): op de reversal/shift trek je de fib van de BODY tot de top-WICK (bij monthly, ook weekly mogelijk, 02:52). In de frames: level 1 op de wick van het laagste punt (bv. 70.698), level 0 op de body-top van de eerste HH/ high-candle (~90). | Long-fib: A = low van de swing-low (wick, 1.0); B = max(open,close) van de swing-high-candle (body, 0.0). Spiegel voor short: 1.0 = high-wick, 0 = min(open,close) van de swing-low (frame 18:40: 1 aan de top, -0.25/-0.65 onder de low). Open: bij eerste voorbeeld zegt hij "start on the body... to the top wick"; welke kant body/wick precies is bij de tweede variant (06:07-06:27 "start with the last low... bodies... you can go a bit lower") niet eenduidig. Voorstel: low=wick, high=body, test ook beide=body. |
| FIB3 | Fib alleen tekenen na een shift/break in market structure: breakaway candle door key level, dan fib van de laatste low vóór de breakaway candles (06:00-06:20: "last low before the breakaway candle started") naar de high. Alternatief anker: start van de breakaway ("real breakaway", 24:14-24:40), kies het anker dat uitlijnt met zones/key (24:40-25:13). | Sequentie: BOS (MS5) -> laatste swing-low vóór de breakaway-beweging = anker 1; hoogste punt van de impuls (body, of wick) = anker 0. Meerdere kandidaat-fibs (laag-wick / laag-body; extreem / begin breakaway) berekenen en kiezen waarvan 0.618-0.796 samenvalt met key level of S/R (24:40-25:13). Tolerantie niet genoemd. Open: kies kandidaat met kleinste afstand tot key/SR. |
| FIB4 | Golden pocket = 0.618-0.66; golden zone = 0.618/0.66 t/m 0.796 ("golden pocket and 0.796 is the golden zone", 03:36-03:54). Entry rond 0.66 ("around 66", 04:26), eventueel bijkopen rond 0.65/0.66-0.796 ("around 65 you might want to add", 04:35). | Entry-zone = [P(0.618), P(0.796)] met hoofdlimiet op P(0.66); optionele tweede entry op P(0.796). (Zijn "65" = 0.66 volgens transcript, onzeker.) |
| FIB5 | Niet blind kopen met SL net onder 0.66 ("that is wrong", 03:54-04:02); entry rond 0.66 kan dieper gaan, maar niet onder de laatste low (04:12). | Geen SL onder 0.66/0.796; zie SL. |
| FIB6 | Bevestiging: de reactie bij de golden pocket moet samenvallen met een key level / S/R (06:33-07:05: "bouncing from golden pocket but also from our key level"; 24:40-25:13 "this aligns best"). Sterkere trade als er direct reactie is ("instantly moves higher"); zonder directe reactie "more difficult" (10:46-11:11). | Filter: |P(0.618..0.796) ∩ key/SR-zone| != leeg (zone-overlap) én candle(s) in de zone sluiten met bullish reactie (Open: eerste bullish close na aanraking, of wick-reject). |
| FIB7 | Targets: T1 = -0.25, T2 = -0.65, T3 = -1, T4 = mogelijk -1.5 (05:09-05:20, 12:43). Voorbeelden: -0.25 geraakt, -0.65 als volgende (26:00-26:21), -0.65 viel samen met een eerdere high, daarna draaide koers om (12:43-12:55). | TP-prijzen = P(-0.25), P(-0.65), P(-1), P(-1.5) op dezelfde fib. Long: P(l)=low+(1-l)*(high-low) met l negatief boven high. |
| FIB8 | Positiebeheer: eerste snelle winst: neem de helft vroeg (op de eerste initiele candles/T1) en zet stop op break-even ("stop loss and profit", 04:46-05:09: "take half quickly, place your stop loss at profit"), loop dan naar T1/T2/T3/T4. | 50% sluiten bij T1 (-0.25) (of zodra trade snel in winst staat: Open: exacte trigger), SL naar BE/instap, rest tot -0.65 / -1 / -1.5. "Stop loss and profit" in transcript = "stop loss at break-even/profit" (interpretatie). |
| FIB9 | SL: onder de laatste low (de key HL/swing-low waar de fib van is getekend) vanwege de breakaway candles (04:35-04:40, 07:05, 12:01-12:11: "easy, it's here for me, because we have the shift"). | SL = swing-low (fib 1.0) minus kleine buffer (Open: buffer, bv. 0-1 ATR). Short: boven fib 1.0 (high). |
| FIB10 | Bias-regel: blijf bullish zolang key HL/key level niet met breakaway doorbroken wordt; sweep/wick onder key zonder breakaway = nog bullish (09:48-10:07). Als prijs onder het key level accepteert en wegbreekt van de high (breakaway omlaag), dan was de high een deviatie en is doel het vorige key HL; dan GEEN fib-long-strategie (07:51-08:30, 09:02-09:34). Daarna fib opnieuw vanaf nieuw anker (10:18). | Zie MS10/MS13. Als close < key_low met MS6-bevestiging: long-setup op deze fib ongeldig; hertekenen met laatste structuur. |
| FIB11 | Zelfde in downtrend gespiegeld: LH, LH, key lower high, breakaway erboven (11:19-11:46: niet altijd force nodig, wel wegbreken; minder force = vertraging/mogelijk deviatie), dan fib omgedraaid (flip van laag naar top, 11:46-11:54), entry in golden pocket, SL boven/waar structuur-shift (12:01-12:11), targets -0.25/-0.65 (12:43). | Short: fib 1 = high-wick, 0 = low-body (zie FIB2). Entry in [P(0.618), P(0.796)] gemeten van de low naar boven; TP -0.25/-0.65 onder de low. |
| FIB12 | Hiërarchie van timeframes: monthly overrulet weekly (19:55-20:01); begin op hoogste TF, ga dan naar lagere; handel in de richting van de HTF-bias (13:35-13:49, 30:32-30:43, 17:15-18:30). Een weekly short tegen een monthly bull heeft "less probability" (19:02-19:13). | Bias = 1M; setup-TF = 1W (en daily/lager "other lesson"). Weekly-signaal tegen 1M-bias: lagere prioriteit/geen trade (Open: vlag "counter-trend, halve size" is mijn voorstel, niet gezegd). |
| FIB13 | Geen setup / neutraal: als prijs het key level breekt en weer terug is (deviatie) of in een range zit (dubbele bodem, geen breakaway) is er geen bias, wacht op breakaway (14:12-15:30, 20:15-20:57). | State "range/neutral": geen fib-entry; wachten op BOS (MS5). |
| FIB14 | Schaal: BTC fibs op logaritmische schaal (22:53-23:44, frame 18:40/23:00 toont "Logarithmic" aangevinkt); voor Forex/aandelen/indices (EURUSD, stock market) regulier lineair ("always regular scale"). | BTC: bereken fib-prijs op ln(prijs): P = exp(ln(low)+(1-l)*(ln(high)-ln(low))). Overige: lineair. |
| FIB15 | Strategie samengevat (26:51-27:30): breakaway candle vanuit key level -> fib (template) -> terug naar golden pocket -> target -0.25 (valt samen met -0.65 van een ander fib: "alignment") -> SL naar winst. Op het volgende key level wordt opnieuw gekeken (breekt prijs er weer weg, dan zelfde patroon; 31:00-31:35). | Pipeline: BOS -> fib -> pullback-entry -> multi-TP. Confluentie-bonus: P(-0.25) van fib A ≈ P(-0.65) van fib B (Open: tolerantie, bv. 0.3%). |
| FIB16 | Entry-TF: monthly entry genoemd (07:05 "this is the entry on the monthly time frame"); ook weekly (21:48-27:30). Lagere TF volgen in latere les (08:30 "for another lesson", 15:08). | Detectie op 1M en 1W; daily niet gespecificeerd in deze les. |

**Instap / SL / TP (samenvatting):**
- Entry: limit rond 0.66 (golden pocket 0.618-0.66), optioneel add tot 0.796; alleen met key-level/SR-confluentie en na BOS met breakaway candle in de trendrichting.
- SL: onder de laatste swing-low (fib 1.0) = onder de low van het shift-punt; niet net onder 0.66.
- TP: T1 -0.25, T2 -0.65, T3 -1, T4 -1.5 (mogelijk). Helft winnen bij T1/snel in winst, SL naar BE.
- Geen risicopercentage of R-getal genoemd. Hij noemt ook geen candle-aantal voor "snelle" winst.

**Open voor jou:** (1) exact body/wick-anker per kant; (2) wanneer "half sluiten" (T1 of eerder); (3) SL-buffer; (4) kandidaat-fib selectie (confluentie-tolerantie); (5) of de bot op 1D werkt terwijl de les 1M/1W gebruikt; (6) transcriptie "65" vs 0.66 (frames tonen een 0.66-level, dus 0.66).

Beelden bekeken: 02:00, 02:20, 03:20, 04:20, 05:20, 06:20, 07:00, 08:20, 11:40, 12:00, 12:40, 18:40, 23:00, 24:20, 26:00, 27:00. Zichtbaar: TF 1M (DXY, BTCUSD Bitstamp) en 1W; fib-levels 0, 0.618, 0.66, 0.796, 1, -0.25, -0.65, -1, -1.5; "KEY" lijnen; tekstbox "Fibo: Body to wick"; S/R-lijn (label S/R); log-schaal bij BTC.

## 4. Structural Frameworks (22:55)

| # | Regel uit de video (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| SF1 | Doel: hoge-kans patronen op hogere timeframe om met de trend mee te handelen (00:18-00:35). Hoger timeframe is altijd belangrijker dan lager (06:25). | TF-hiërarchie M > W > D. Bias komt van de hoogste TF; lagere TF alleen voor entry/verfijning. |
| SF2 | Vier bouwstenen: (1) shift in market structure = (inverse) head & shoulders, (2) bullish N-patroon (impuls, correctie, hogere beweging), (3) bearish V-patroon (spiegel), (4) vijfgolfstructuur = L-schouder, kop, R-schouder + N + N (1-2-3-4-5) (00:35-02:38). | Bullish: IHS (3 lage swing-pivots, midden = laagste) gevolgd door N-patroon(en). Bearish: HS gevolgd door V-patroon(en). Swing = fractal-pivot op de gekozen TF (Open: n bars links/rechts, video geeft geen getal; voorstel 2-3 op W). |
| SF3 | Marktstructuur eerst bepalen: reeks lagere highs/lagere lows (03:13, 10:55). Key level = het niveau waar de structuur begon te draaien / SR uit les 1 (03:24, 03:41). | Downtrend = opeenvolgende LH+LL op W/M. Key level = laatste swing-high (downtrend) of swing-low (uptrend) vóór de breakaway; opslaan als horizontaal prijsniveau. |
| SF4 | Kan de prijs niet lager expanderen (maakt geen breakaway-candle onder de vorige low), dan is het eerste doel het key level erboven (03:45-04:03, 11:17-11:28). | "Unable to expand" = nieuwe lage swing zonder dat een candle onder de vorige swing-low sluit met breakaway-karakter (zie SF5); de low wordt gehouden of maar licht onderschreden. Target1 = key level (swing-high). |
| SF5 | Breakaway candle(s): niet een week die blijft hangen en weer terugvalt, maar een krachtige candle, of meerdere kleinere candles achter elkaar in dezelfde richting, die door het key level breken (04:13-04:26, 15:52-16:07, 20:22-20:30 "one, two, three"). Eerste voorbeeld op EURUSD W: "niet heel schoon", 3 candles omhoog (04:17-04:26). | Break = body-sluiting voorbij het key level (Open: wick of close; beelden tonen sluiting erboven, video zegt niet expliciet). Breakaway = candle met groot lichaam (Open: drempel bv. body >= 1.5x gemiddelde body van 10 candles) OF >= 3 opeenvolgende candles in richting met close voorbij het niveau. |
| SF6 | Na de break (flip): key level wordt support (bij omhoogbreuk) en moet blijven houden (08:38-08:42, 12:33-12:45). SR-niveaus van een hogere TF (les 1) overrulen flips/golden pocket (12:45-13:18). | Na break: zone rond key level = support. Prijs sluit er niet duidelijk onder = geldig. Prioriteit: SR van hoogste TF > flip-level > fib-zone (indien conflict). |
| SF7 | Fibonacci "van body naar wick" (04:42-04:52, 22:21) op de beweging van laatste low naar high (bij long). Golden pocket = 0.618-0.66 (beeld 15:40: 0.618, 0.66, 0.796 getekend). Target-extensies: -0.25 (T1), -0.65 (T2), -1 (T3) (16:51-17:06). | Fib: 1.0 = swing-low (body-kant bij begin, wick-kant bij einde: Open: video zegt "body to wick", exacte kant niet uitgesproken), 0.0 = swing-high. Entry-zone = prijs tussen 0.618 en 0.66 (op beeld ook 0.796 als extra niveau). Targets: high + 0.25*range, high + 0.65*range, high + 1.0*range. |
| SF8 | Bevestiging via steun: linkerschouder-support die rechterschouder ondersteunt, "vier taps van support" (05:07-05:27); rechterschouder valt samen met golden pocket + key level/SR (15:25-15:42). | Confluentie-score: aantal van {golden pocket, key level/SR, vorige schouder-low, vorige swing} binnen dezelfde zone. Tolerantie Open (voorstel: zone-breedte of 0.1-0.2% van prijs). |
| SF9 | Entry bij rechterschouder / N-correctie in golden pocket, wacht op reactie: "bounce, bounce" en dan breakaway-candle omhoog; dan long (15:25-16:16). Op W duurde het 3 weken voordat de trade in winst stond (17:50). | Trigger long: prijs raakt zone (0.618-0.66 + SR) en een volgende W-candle sluit hoger met breakaway-karakter (SF5) of sluit boven de vorige candle-high. Open: entry op close van trigger-candle of limit in de zone. |
| SF10 | Na IHS volgt N-patroon voor nog een been omhoog; opnieuw fib van laatste low naar high, long bij golden pocket, SL eronder, target -0.25 (20:02-20:53). Vijfgolf compleet = IHS + N + N. Zelfde omgekeerd (HS + V, bearish; schaal omgedraaid) (21:39-22:14). | Herhaal SF7/SF9 na elke geldige correctie zolang bias intact: N1 na IHS, N2 na N1. Bearish: alles spiegelen (V na HS, short in golden pocket van de dalende beweging). |
| SF11 | Bias blijft behouden tot een echte shift in market structure op hogere TF bij het key level (21:04-21:26, 22:46-22:51). Wat nu gebeurt weegt zwaarder dan wat je verwacht door de hogere-TF structuur: bij nieuwe lage low in een downtrend niet longen (13:53-14:36). | Bias = bullish tot er een W/M-close onder het laatste key level (hogere low) komt met breakaway-karakter; tot dan geen short. Long pas als de lagere TF zelf al gekeerd is (geen nieuwe LL meer, SF4). |
| SF12 | Niet sluiten uit ongeduld: positie aanhouden zolang geen structuurbreuk; "break of structure" = niet door high heen kunnen en daarna lager sluiten (07:19-07:43). | Trailing: SL naar break-even/in winst na T1 (zie Instap/SL/TP); exit bij structuurbreuk (close onder laatste hogere low / key level op W). |

**Instap / SL / TP (video 4)**
- Entry: long in de golden pocket (0.618-0.66) van de laatste beweging, na bevestiging door bounce + breakaway-candle (15:25-16:16, 20:47). Op NZDJPY W-beeld: entry ca. 76.4 (positie 17:40 beeld: entry 76.405).
- SL: onder de rechterschouder / onder het SR-niveau ("stop loss over here to be certain", 16:16-16:31, 20:49). Beeld 17:40 (NZDJPY W): SL 74.515, ca. 2.5% onder entry, onder S/R 75.127; target 82.341 (-1 niveau), RR ca. 3.1 (3.58 verhouding op beeld). Beeld 16:20 toont eerder een sterk ruimere SL (72.268, onder key 73.112) en RR ca. 1:1: geschrapt, nauwelijks bruikbaar.
- TP: T1 = -0.25, T2 = -0.65, T3 = -1 fib-extensie (16:51-17:06); nu al "good RR". Andere techniek voor target volgt in de liquiditeitslessen (16:40). 
- Na bereiken T1: stop loss naar break-even of "in profit" (17:06, 05:44: "take half profits"). Dus partial 50% bij T1 (05:44, eigen lezing: "half profits" bij eerste target).
- Mogelijk herinstap bij terugkeer naar support/rechterschouder (18:57-19:37).

**Beelden bekeken:** EURUSD W: 01:20, 02:00, 03:40, 04:20, 05:20, 06:20, 07:40, 08:40; NZDJPY M: 10:20, 12:00, 12:40; NZDJPY W: 14:40, 15:40, 16:20, 17:40, 18:40, 20:40; 22:00 (NZDJPY W, omgekeerd/bearish voorbeeld met V).

## 5. Liquidity: Magnetic Price Levels (10:30)

Voorbeeldinstrument op alle beelden: XAGUSD (M, W, D, 4h). Video is een inventarisatie van "liquidity pinpoints"; er worden geen entry/SL/TP-regels gegeven, die komen in de volgende les (liquidity flows, 10:15).

| # | Regel uit de video (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| MPL1 | Liquiditeit is waar de markt naartoe getrokken wordt en/of omkeert: de "magneet" (00:08-00:32). Vier typen (beeld 00:40): swing highs & lows, equal highs & lows, previous candle high/low (M/W/D), range highs & lows. | Elk type = lijst van horizontale prijsniveaus met type-tag en TF. Bot houdt een register "liquidity pool" met level, type, zijde (boven = buy-stops, onder = sell-stops), TF, status (open/genomen). |
| MPL2 | Swing high/low op hogere TF (monthly) is vroegere liquiditeit. "Waar zou je swing low zijn als prijs hier was?" (00:47-01:45). Beeld 01:40-04:20 (XAGUSD M): niveaus gemarkeerd "LQ" op 48.00 (swing high 2011), 3.46 (low 1991), 30.14, 13.65, 4.88. | Swing = pivot met N bars links/rechts (Open: video noemt geen N; voorstel M/W: 2, D: 3-5, 4h: 5). Niveau = high resp. low (wick) van de pivot. Een swing-niveau is "open" zolang er sindsdien geen candle doorheen is gegaan. |
| MPL3 | De reversal gebeurt zodra prijs liquiditeit pakt: bij het niveau breekt prijs weg of keert om (01:53-02:25). Daarna richting het volgende doel (hogere targets), het "attract/target/key level" (02:25-03:00). | Sweep-event = high > niveau (voor liquidity high) of low < niveau (voor liquidity low). Open: alleen wick (sweep) of ook close voorbij het niveau (break). Video: "either break away from or reverse", dus 2 uitkomsten: (a) wick door niveau en terug = reversal, (b) close voorbij + doorgang = breakaway. Detectie: sweep zonder close voorbij = reversal-kandidaat. |
| MPL4 | Equal highs / equal lows zijn altijd aantrekkelijke liquiditeitspools: na marktstructuurverschuiving schilderen ze equal high/equal low, prijs reist onder de equal lows en daar keert hij om (03:00-04:09). Genoemd: "relative equal lows" (03:52), "equal highs ... we move higher, reverse". | Equal level = twee of meer swing-pivots van gelijk type waarvan de highs (lows) binnen een tolerantie liggen. Tolerantie Open: voorstel 0.1 x ATR(14) op de TF, of een vast aantal pips (bv. 3 pips op D). Level = max (voor highs) / min (voor lows) van de groep. |
| MPL5 | Previous candle high/low op monthly, weekly, daily: pmH/pmL, pwH/pwL, pdH/pdL. Prijs neemt het niveau en keert om (04:16-06:54). Voor lagere-TF handel: altijd vorige week- of maandlow/high markeren (05:07-05:20). Voorbeeld: pwH genomen, prijs daalt; pwL genomen, prijs stuitert (04:52-05:07). Inside week: neemt pwH, de week erna pwL, structuurshift, omhoog (05:28-05:45). Beeld 05:20 (W): pmH 27.927, pwL 22.281 (roze lijnen). Beeld 07:20 (D): pdH 22.892. | pXH/pXL = high/low van de vorige afgesloten candle op M, W, D. Een niveau wordt actief zodra de nieuwe periode begint (week: maandag, dag: 00:00 broker-tijd; Open: videobroker is OANDA op TradingView, daily-open tijdzone niet genoemd). Open/gesweept = hoogste high (laagste low) van de lopende periode voorbij het niveau. |
| MPL6 | Intraday-patroon in een uptrend: prijs pakt vorige dag-high en gaat terug omlaag (06:31-06:39); in uptrend pakt prijs vorige dag-low en gaat omhoog (06:39-06:54). "Het is belangrijk je trend te kennen" (06:57). Voorbeeld daily: shift, breakaway, linkerschouder-kop-rechterschouder, support/resistance/support, neemt pdL, dan omhoog (07:00-07:18). | Bias-filter: in uptrend alleen long-reversal na sweep van pdL/pwL/pmL; in downtrend alleen short-reversal na sweep van pdH/pwH/pmH. Sweeps tegen de trend in (bv. pdH in uptrend) = geen entry, wel doel/magneet. (Eigen afleiding uit de opmerking over trendrichting.) |
| MPL7 | Range: consolidatie markeren als range; range high = liquiditeit, range low = liquiditeit (07:25-07:54). Beeld 09:40 en 10:20 (XAGUSD D): twee LQ-lijnen, high 25.39 (swing/range top) en low 21.42, over meerdere maanden. Voorbeeld: neemt range-high-liquiditeit, kan het key (hogere) low niet breken, neemt de range low voor een SFB (komt in latere les), beweegt impulsief weg van key lower high (07:59-08:36). | Range = periode waarin prijs tussen twee horizontale grenzen blijft (Open: min. aantal touches/candles niet genoemd; voorstel >= 2 touches per kant en >= 20 candles). Range high/low = hoogste/laagste wick. Beide zijden = liquiditeitsniveau. |
| MPL8 | Volgorde in een trend: eerst bias/trend (uit eerdere lessen) bepalen. Neemt prijs in een downtrend het eerste niveau (high), verwacht dan dat de equal lows genomen worden (09:42-10:15). "Search for a grab towards that liquidity, to then turn around and take out the equal lows." | Sequence-regel: bias bearish + sweep van liquidity high (swing/equal highs/pXH) -> volgend doel = dichtstbijzijnde onderliggende pool (equal lows of swing low, in richting van de trend). Spiegel voor bullish. Doel = "magnet" en bruikbaar als TP-kandidaat (eigen interpretatie; entry-regels pas in les 6 "liquidity flows"). |
| MPL9 | Samenvatting (08:41-09:36): swing highs, equal lows (die uiteindelijk pakt de high om lagere equal-lows te halen), equal highs, vorige maand H/L, vorige week H/L, vorige dag H/L, range high/low. | Implementeer als 7 level-generators: swingH/L, equalH/L, pmH/L, pwH/L, pdH/L, rangeH/L. Prioriteit: hogere TF > lagere TF (zie SF1). |

**Instap / SL / TP (video 5):** niet behandeld. Enige indicatie: bij lagere-TF handel de vorige week-/maandlow als doel/trigger gebruiken (05:07-05:20); entry via SFB wordt in een latere les uitgelegd (08:15). Beeld 08:20 (4h) toont een sweep van een LQ-low (ca. 21.44) met lange wick onder, daarna sterke stijging, met 21.976 als LQ erboven: voorbeeld van "pak liquiditeit, keer om". Het label-menu op beeld 07:40-08:20 laat de gebruikte niveau-templates zien (pdH, pdL, pwH, pwL, pmH, pmL, pdEQ, pwEQ, pmEQ, KHL/KLH, SFP, KEY, FVG, HVN, NYO, dGAP/wGAP, dOPEN/wOPEN/mOPEN, OB): bevestigt dat de cursist op de chart met vaste labels werkt (pwH, pmH enz.).

**Beelden bekeken:** M XAGUSD 00:40, 01:40, 02:20, 03:20, 04:20; W 05:20; D 06:20, 07:20, 07:40 (labelmenu); 4h 08:00, 08:20 (menu); 4h 09:20 (sweep); D 09:40 (range 25.39/21.42), 10:20.

## 6. Case study NZDCAD (10:00)

Reversal-long op NZDCAD (New Zealand dollar / Canadian dollar), trade gepubliceerd 29 jun 2023 (Discord-screenshot 00:10, 4h, "Jun 29, 2023 08:11"). Volgorde: M -> W -> D -> 4h. Prijsopmerking: de transcriptie zegt "0.88", maar het Discord-beeld toont entry rond 0.808 (blauwe labels 0.8086/0.8084); beschouw "0.88" als verhoorde "0.808" (eigen interpretatie, prijs 0.88 komt niet voor op de lage-TF-chart).

| # | Regel uit de video (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| CS1 | **Monthly, stap 1: hoogste-TF SR-level.** "We zoeken het eerste hoge-TF support/resistance": prijs had meerdere bounces/rejections/deviation op hetzelfde niveau; dit is het hoofd-SR-niveau (00:28-00:46). Beeld 00:56: zwarte S/R-lijn op 0.81626. | Op M: zoek horizontaal niveau met >= 2-3 reacties (wick-rejections/sluitingen terug) binnen tolerantie (Open: bv. 0.2-0.3% van prijs). Opslaan als SR (0.81626). |
| CS2 | **Monthly, stap 2: trend + trendshift.** Trend gaat omlaag; zoek of een trendshift mogelijk is via breakaway candles/grote krachtige candles (00:49-01:05). Vorige high (key level) werd doorbroken en prijs brak weg uit die zone (01:05-01:28); geen hogere highs maar de krachtige beweging over de high zegt "kan marktstructuur shiften" (01:28-01:40). Beeld 01:16: KEY-lijn 0.80496 (laag), fib 0.705/0.79. | Detecteer downtrend (LH+LL op M). Shift-kandidaat = M-candle(s) met breakaway-karakter (SF5) die sluiten boven de vorige lower-high (key level). Key level = die LH. |
| CS3 | **Monthly, stap 3: zoek links-schouder / kop / mogelijk rechterschouder** en leg Fibonacci van body naar wick. Prijs staat nu in de golden pocket (02:01), gestuiterd van KEY op monthly en op SR (02:05-02:09). Beeld 02:16 (W) / 02:36 (M): fib 0 op ca. 0.8805 (hoog 2022), 1 op ca. 0.7725 (laag), golden pocket 0.618-0.66 rond 0.8100-0.8150, 0.796 op ca. 0.795. | Fib op laatste impuls (laagste low -> hoogste high van de shift), 0.618/0.66 = golden pocket, 0.796 = diepste verdedigingsniveau. Check: prijs-lows/closes binnen of net onder pocket + SR + KEY (SF8-confluentie). |
| CS4 | **Weekly: fair value gap (wFVG).** Een kleine maar degelijke weekly FVG ligt onder de prijs en kan als support dienen (02:14-02:50). Beeld 01:56: wFVG ca. 0.80615-0.80511 (beeld 02:56 D); 03:16 labels wFVG 0.80615 en dFVG 0.80428. "Ik was al geïnteresseerd in een long." | FVG (3-candle gap): bullish FVG = low(candle3) > high(candle1) op W; zone = [high(c1), low(c3)]. Detectie op W en D. Support-kandidaat voor longs. |
| CS5 | **Daily: dFVG binnen de wFVG** (03:03-03:16). Ook een order block (OB) is zichtbaar; die komt uit de M: OB = eerste neerwaartse candle in een uptrend waarbij een FVG naast zit (links en rechts monthly FVG) (03:17-04:04). Beeld Discord 00:10: OB-label 0.80496 (4h, SL ligt hier net onder). | OB (bullish) = laatste/eerste down-candle voor een impulsieve opwaartse beweging die een FVG achterlaat. Video: "first down candle in an uptrend where you have a fair value gap in between". Zone = candle high-low (Open: body of wick; beeld toont OB-lijn op 0.80496 = KEY-lijn, dus waarschijnlijk low). |
| CS6 | **Confluentie-samenvatting voor de zone:** golden pocket + krachtige moves + weekly FVG + OB als support (04:04-04:11) -> "misschien kunnen we shiften in trend". | Zone-score: telt {golden pocket, SR, KEY, wFVG, dFVG, OB, vorige swing low}. Bot-eis (Open): min. 3 overlappende componenten op D/W/M voordat naar 4h wordt gegaan. |
| CS7 | **4h: liquiditeit.** Teken liquidity levels: laatste low van een kleine range (0.80678 = LQ), en een tweede (0.80450 = equal-low/LQ-low) (04:17-04:43). Beelden 04:43, 05:03: LQ 0.80678 en LQ 0.80450 getekend met een lijn vanaf de bijbehorende swing low. | Level-generator uit MPL (swing-low en equal lows). Hier: swing-low op 4h (0.80678) en lagere equal-low/low (0.80450). |
| CS8 | **Setup-trigger: sweep zonder breakaway.** Prijs ging recht onder het liquidity-level, had moeite met breakaway-candles, consolideerde onder maar bleef het niveau rejecten (05:03-05:23). Daarna werd het volgende niveau (equal lows, 0.80450) gebroken en wéér was de prijs niet in staat om ver lager weg te breken (05:23-05:36). "Zodra we weer binnen de range terug handelden, target ik..." (05:40). | Sweep-detectie 4h: low < LQ-level maar geen follow-through: (a) de volgende N candles sluiten niet duidelijk lager (Open: N=1-3; breakaway-candle-drempel zie SF5), (b) candle sluit terug boven het level ("back inside the liquidity zone"). Trigger = close terug boven het gesweepte niveau (0.80678). Beeld 05:23-06:43 toont lage wick tot ca. 0.8030 en een sterke bullish 4h-candle terug door 0.80678. |
| CS9 | **Target (eerste):** de laatste lower high die faalde om een nieuwe low te maken (05:40-05:55) = "liquidity level" (zie beeld 06:43: lijn op 0.80892; later op 0.82952 (laatste hoge swing-high, 4h LQ in beeld 07:03)). "Back inside the liquidity zone -> target the last lower high failing to break away" (06:15-06:31). Mogelijk groeit het uit tot een volledige reversal: de echte high die tot het falen leidde ligt veel hoger (06:33-06:51, beeld LQ 0.82952). | Na trigger: T1 = dichtstbijzijnde lower-high (swing-high) boven entry; verdere T's = volgende swing-highs ("higher and higher and higher", 07:15). Gebruik MPL-levels als targets. Discord-trade gebruikte target 0.82340 (KEY) en SL onder OB. |
| CS10 | **Entry:** "perfect entry voor een reversal" (06:51-06:56), gebaseerd op M (en W), daarna 4h met liquiditeit (07:00-07:15). Entry nabij 0.808 (zie Discord-beeld). | Entry = market/limit na de 4h-trigger (CS8) binnen de HTF-zone (CS6). Open: entry op candle-close van de terugbreuk-candle of limit op 0.808 (beeld: ca. 0.8085 na eerste bullish candle). |
| CS11 | **Bevestiging op lagere TF / voortgang:** op D zie je wegbeweging van het key level (shift); links-schouder en kop aanwezig, mogelijk rechterschouder volgt (07:31-07:48). Faalt prijs beyond dit LQ-level te komen, dan target de laatste low op D, terug in dFVG, en daarna hoger: dat zou de rechterschouder zijn (07:48-08:11, 08:41-09:07). Beeld 08:03 D: tekening L-schouder/kop/R-schouder; beeld 08:23 (4h) tekening verwachte hogere piek en terugval naar 0.822. | Voortgangscheck D: LS/Kop/RS-detectie (SF2); bij failure boven LQ (0.82952) verwacht pullback naar laatste low/dFVG en herinstap in golden pocket (SF9/SF10). |
| CS12 | **Trade management:** zodra de prijs eerste targets raakt (de 4h-LQ-niveaus erboven), neem de helft van de winst en zet de SL op entry of net onder entry ("in profit") (09:23-09:57). | Bij T1: sluit 50% van positie; SL naar break-even (entry) of net eronder/erboven. Trailing daarna via nieuwe structuur (SF12). |

**Instap / SL / TP (video 6, uit Discord-beeld 00:10 en 4h-beelden):**
- Entry: ca. 0.8086 (long, 18 000 units op het beeld; transcriptie: "0.88" = waarschijnlijk 0.808).
- SL: 0.80437 = net onder OB (0.80496) en onder de laagste wick van de sweep (ca. 0.8030 laagste wick van de 4h, dus SL zit boven laagste wick: let op, SL-afstand 0.00428 = 0.53% op het beeld). Open: of de SL precies "onder OB" of "onder sweep-low" is (beeld toont SL-lijn net onder de OB-markering, boven de laagste wick).
- TP: 0.82340 = weekly/KEY-niveau (beeld "KEY 0.82340", "wFVG 0.82538" erboven); winst 0.01475 (1.82%), RR ca. 3.45.
- Video noemt TP als "laatste lower high / liquidity level" en daarna hogere LQ-levels (0.82952). Half profit + SL op BE bij eerste target (09:37-09:57).

**Volledige beslissingsvolgorde (samengevat voor de bot):** (1) M: SR met meerdere reacties + downtrend + krachtige candle boven key level = shift-kandidaat; (2) M: fib body-to-wick, prijs in golden pocket + KEY + SR; (3) W: FVG/steun onder prijs; (4) D: dFVG binnen wFVG + OB (herkomst M); (5) 4h: LQ-lows tekenen (swing low + equal lows), wachten op sweep zonder breakaway en terugkeer erboven; (6) long, TP = laatste lower high en hogere LQ's, SL onder OB/sweep; (7) bij T1 helft eruit, SL naar entry.

**Beelden bekeken:** 00:10 (Discord-trade), 00:16 (4h), 00:56 (M), 01:16 (M, KEY 0.80496), 01:56 (W-labelmenu met wFVG/dFVG/KEY-templates), 02:16 (W, fib + KEY), 02:36 (M, fib), 02:56 (D), 03:16 (D, wFVG/dFVG), 03:43 (M), 04:03 (M), 04:23/04:43/05:03/05:23/05:43/06:03/06:43 (4h, LQ-lijnen en sweep), 07:03 (4h, LQ 0.82952), 07:43 (D), 08:23 (4h tekening), 09:03 (4h tekening), 09:43 (4h).

## Controle

Video 2-6 zijn uitgeschreven door een hulpagent en daarna steekproefsgewijs nagekeken op de beelden:
de fib op DXY maand (video 3, 12:00: 0 / 0,618 / 0,66 / 0,796 / 1 en -0,25 / -0,65 / -1 / -1,5, KEY-lijnen)
en de NZDCAD-trade (video 6, 00:10: 4u, instap ±0,8087, SL 0,80437 onder het orderblok, TP 0,8234 op KEY,
risico 0,53%, R:R 3,45). Beide kloppen.

## Synthese: de methode als stappenplan

1. **Maand (en week): kaart.** S/R-niveaus met veel tikken (SR1-SR6); trend uit hogere/lagere toppen en
   bodems; het sleutelniveau (KEY) = laatste hogere bodem / lagere top, op candle-lichamen (MS).
2. **Maand/week: de breuk.** Pas een setup als een **krachtige candle voorbij KEY sluit** en doorloopt (BOS).
   Een wick of een valse uitbraak telt niet. Patroonketen: (omgekeerde) kop-schouders, dan N/V-patroon (SF).
3. **Fib na de breuk**, lichaam tot wick, over de swing van de breuk. Instapzone 0,618-0,796, instap rond 0,66;
   de zone moet samenvallen met KEY of een S/R-niveau (FIB).
4. **Lagere timeframes (dag, 4u): timing.** In de zone: FVG/orderblok, liquiditeit onder de lows die weggehaald
   wordt zonder doorbraak (sweep), dan de instap (MPL, CS).
5. **SL** onder de swing low / het orderblok of de rechterschouder, niet net onder 0,66.
6. **TP** op -0,25 / -0,65 / -1 (/-1,5) van de fib, of op de volgende KEY/liquiditeit. Helft nemen bij het eerste
   doel, SL naar instap.
7. **Risico** klein: in de case 0,53% per trade.

## Setup B: trendvoortzetting (aangevuld door de gebruiker)

Naast de omkeer (setup A: BOS door KEY) ook voortzetting, altijd met de S/R van de hoge timeframe:

1. Uitbraak: een candle **sluit** boven een S/R-niveau van maand/week (veel tikken).
2. Retest: de prijs komt terug naar het niveau en houdt; hogere bodem op of net boven het niveau, geen slot eronder.
3. Bullish N: vanuit die bodem **sluit** de prijs boven de vorige swing high.
4. Fib van de retest-bodem (1, wick) naar de nieuwe top (0, lichaam); instap in de golden pocket (0,618-0,66, tot 0,796).
5. SL onder de retest-bodem (dus ook onder het niveau); TP -0,25 / -0,65 / -1 of de volgende S/R.
Short: spiegelbeeld (bearish V). Schema: `docs/strategy_continuation.png`.

## Verschil met de huidige bot

| Onderdeel | Video's | Huidige bot |
|---|---|---|
| Voorwaarde | BOS: candle sluit voorbij KEY | Geen; trend uit gemiddelden van closes |
| Locatie | Zone moet samenvallen met KEY/S-R | S/R-filter staat uit |
| Instap | 0,618-0,796, rond 0,66, na sweep op 4u/dag | 0,45 (0,8 volatiel), of de laatste close |
| SL | Onder swing low / orderblok | Swing + 0,4-0,5 ATR |
| TP | Fib-extensies -0,25/-0,65/-1, of volgende KEY | Vaste R-veelvouden 0,65 / 1,85 / 2,75 / 2,5 / 3,5 |
| Filters | Elke stap moet kloppen | Score die altijd slaagt (B8) |
| Risico | ±0,5% | 1,8% x 1,45 in rustige markten |

## Open keuzes voor de code (te beslissen of te testen)

- Swing-definitie (aantal candles links/rechts) en wat "krachtig" is voor de BOS-candle (lichaam t.o.v. gemiddelde).
- Tolerantie voor "raakt KEY/S-R" en voor gelijke toppen/bodems.
- Welke timeframe de instap timet: dag of 4u; FVG/orderblok-definitie.
- Eerste doel: -0,25 of de volgende KEY; wanneer precies "helft nemen".

## Test 1: mechanische versie op de daggrafiek (30 assets, 2015-2025)

`research/strategy/setup_study.py` + `winners.py`. 2.722 gevulde trades, gemiddeld -0,05R (voor kosten).
Per soort: omkeer bij niveau -0,01R (413), omkeer zonder niveau -0,06R (931), voortzetting -0,05R (1.378).

Winnaars tegenover verliezers, gezocht op 2015-2020 en gecontroleerd op 2021-2025 (gem. R per helft):

| Kenmerk | 2015-20 | 2021-25 |
|---|---|---|
| Kleine setup (beweging <= 2,6 ATR) | +0,15 | +0,05 |
| Grote setup (> 4,2 ATR) | -0,14 | -0,24 |
| Tegen de weektrend | +0,09 | 0,00 |
| Mee met de weektrend | -0,13 | -0,12 |
| Niveau in de golden pocket | -0,19 | -0,11 |
| Klein + snelle top + geen niveau in de zone | +0,26 | +0,01 |

Per asset: 9 in beide helften negatief, 5 in beide positief; bij toeval verwacht je er ongeveer 7 à 8 van elk.
Conclusie: wat in 2015-2020 hielp, krimpt in 2021-2025 tot ongeveer 0. Geen voordeel dat na kosten overblijft.
