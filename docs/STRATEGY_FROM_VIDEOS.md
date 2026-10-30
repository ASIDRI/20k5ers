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

## 7. Forex HTF Analysis (64:22)

Context: live-analyse van 7 juni 2023 (TradingView, OANDA/TVC-data), werkwijze "van groot naar klein": maand -> week -> dag -> 4h -> 1h/15m. Per pair één chart-tab met drawings die per timeframe in een eigen **groep** worden bewaard (groepen "weekly", "daily"; drawings staan "sync globally", dus ook op telefoon/andere layout zichtbaar). Weinig harde trades: het is vooral een plan + wachten.

### Geanalyseerde instrumenten

| Instrument | Tijd | Conclusie (bias / level / wacht op) |
|---|---|---|
| NZDUSD (1M, 1W, 1D, 4h) | 00:00-15:15 | Maand: nog bearish (trendlijn), hoofd-SR = bounce/rejectie-support, volgende resistance erboven. Week: sterk SR-level gebroken met kracht, maar W-beweging / mogelijk 5-golf + ABC (corrective); "niet volledig bullish op inverse H&S". Voorkeur: lager (USD sterker). Daily: FVG + OB op resistance + golden pocket = interessant voor short. 4h: wacht op reactie; long alleen als de resistance flipt naar support. Eerder genomen long op -0.25 (07:09 = "reden dat ik de long nam"). Target bij pop: -0.25. |
| EURAUD (15m/1h) | 11:34-12:20 | Prijs op -0.25 + OB (groene zone) op 15m: "geen reactie, geen entry". Wacht tot 1h minstens afremt. |
| EURUSD/USD-kant (XY) | 15:20-17:00 | Geen bias; "laatste 5 golven omhoog", bounce komt, "dit wordt een goede trade". |
| AUDUSD (1D, 4h) | 17:13-20:50 | Aan einde 5-golf omhoog, trendlijn-resistance + liquidity erboven (previous day/week/month high gepakt). **Niet shorten** ("durf geen short te raken"), want nog heftig in uptrend en 4h nog niet vertraagd; wacht op AUD. |
| EURCAD (1D) | 21:00-25:20 | Equal lows dichtbij; USD zou kunnen dalen -> EUR hoger vanaf volume point of control. Mogelijke inverse H&S, maar "te vroeg om te callen", neckline nog niet gebroken, "niet ideaal om nu in te stappen". Nieuws vandaag: Balance of Trade, niet belangrijk. |
| GBPCAD (1M, 1W, 1D, 4h/1h) | 25:20-39:00 | Maand: bearish trendlijn, rejecties; volgend support = SR laag. Week: nog downtrend (geen high gebroken), W-W-W lager. Short-entry was H&S (perfect). Targets -0.25/-0.65/-1 (-1 = SR). Daily: -0.25 + mogelijk ABC; short-setup = daily FVG + OB + golden pocket (+ vPOC). 4h/1h: **geen long, liever short; geen trade nu** - plan ligt op chart. |
| Silver (1M, 1W, 1D, 4h) | 39:30-64:20 | Hogere TF bullish (uptrend), H&S -> verwacht M-patroon omhoog. Weekly-bias: groene support-box + golden pocket moet houden; daalt het eronder -> bearish. Daily: golden pocket + OB geraakt; rechter schouder nog nodig voor echte reversal; long-voorkeur. 4h: inverse H&S, entry op GP, -0.25/-0.65/-1. |
| DXY (1D) | 17:40 en 14:48 (tab), 05:15 | Alleen als correlatiecheck (tab "DXY" naast pairs); 5-golf-telling omhoog met pullback, SR-niveaus 101.68 / 104.64 / 105.04 / 105.33. |

### Regels (nieuw / preciezer dan eerder)

| # | Regel / werkwijze (met tijd mm:ss) | Meetbaar gemaakt |
|---|---|---|
| HTF1 | Vaste top-down volgorde: eerst maand (trendlijn, SR, patroon), dan week, dan dag, dan 4h/1h voor entry (00:00-15:00, 25:53-30:00, 41:03-64:00). "Je moet flippen tussen timeframes" (46:50). | Procesvolgorde M -> W -> D -> 4h -> 1h/15m; elke TF levert: trendrichting, SR, patroon, fib. Hogere TF-bias heeft voorrang boven lagere (zie HTF9). |
| HTF2 | Maand-trendlijn bepaalt bias: "nog bearish op de maandchart" (00:10), "we zitten in een downtrend, geen high gebroken" (27:39). Trendlijn getrokken over de top-wicks; breuk met kracht = verandering. | Bias per TF = onder dalende trendlijn + geen gebroken lower high -> bearish; omgekeerd bullish. Eigen interpretatie: gebruik trendlijn-over-hoogste-highs als extra filter naast KEY. |
| HTF3 | Per TF slechts 1-2 hoofdlevels: "dit is het main SR-level"; "next support/resistance" per timeframe; levels als horizontale rays gelabeld (template-lijst: yS/R, wS/R, dS/R, mS/R). (00:30, 01:02, 26:54-27:39, 40:39-41:42) | Max ~2 SR per TF actief: het level waar prijs nu zit + het eerstvolgende in de richting van de bias. Level = meest bounce/rejectie-wicks (zie eerdere regel). |
| HTF4 | Level-label per timeframe (maand/week/dag) wordt op het lagere TF-chart bewaard als groep, "ik herdoe de analyse niet meer, behoud alleen de belangrijke fibs/levels" (06:36, 34:33-35:39, 48:27, 57:41). | Gebot voor de bot: weekly/daily-levels + fib-zones persistent houden in 4h-niveau; niet elke dag herberekenen, alleen updaten bij BOS/level-break. |
| HTF5 | Drawings/hulplijnen gegroepeerd en "sync globally" (12:24-12:49). Alerts op de hoofdlevels, niet op de lagere TF-ruis (57:27: "daar wil ik alerts plaatsen"). | Alerts uitsluitend op HTF-levels (W/D SR, golden-pocket-zone, OB). |
| HTF6 | Fib body-naar-wick is voorkeur ("ik gebruik liever de bodies"), want op monthly/weekly reageerde prijs daar, terwijl wick-tot-wick de GP nooit raakte (32:44, 43:56-44:17, 46:50, 53:13-53:42). Bij silver wisselt hij naar wick omdat daar de bounce zat, "maar de regels zeggen body" (50:50-51:13). | Standaard fib: swing-body -> wick; alleen als dat consistent niet matcht met reactie -> wick-versie als alternatief (eigen interpretatie: vermijd, houd body). |
| HTF7 | Confluentie-eis voor interessante zone: golden pocket (0.618-0.66) + OB + (daily) FVG + SR-level samen. "Je wil trades maken op belangrijke levels" (54:29). Voorbeelden: NZDUSD daily (OB op resistance + GP, 09:36), GBPCAD daily (GP + OB + FVG, 34:00), Silver (GP + OB op daily, 54:35). | Zone kwalificeert als setup bij >= 3 van: SR (W/M), GP 0.618-0.796, OB, FVG, vPOC/point of control. Alleen op die zones zoeken naar lager-TF entry. |
| HTF8 | OB-definitie: FVG zoeken; de **eerste tegengestelde candle links van de FVG** = OB (in downtrend: eerste up-candle; in uptrend: eerste down-candle). Body is regel, soms wick (07:47-08:01, 09:15-09:36, 33:33-33:46, 50:34-51:13). OB werkt als S/R: "moet terug naar bullish zijde flippen, anders nog downtrend" (08:01). | OB = laatste candle tegen de impuls vlak voor de FVG, zone = body (optioneel wick). Open (niet gevulde) daily FVG's en gaps ("is die gap al gevuld?") als magneet/target (33:00, 51:13-51:29). |
| HTF9 | Lage TF entry pas bij "afremmen": 15m/1h moet vertragen na de grote beweging / reactie zien op -0.25+OB. "Geen reactie, geen entry" (11:34-12:07). Op 4h wicks die vertragen = signaal, "nog steeds broom links" -> wacht (19:49-20:30). | Entry-filter: na impulsbeweging naar de zone minstens 1 vertragende candle(s) (wicks/kleine bodies) op 1h/4h vóór entry; geen entry op doorlopende momentum-candles in tegenrichting. |
| HTF10 | Tegen de HTF-bias niet traden: bij silver "op de hogere TF ben ik bullish, dus liever long dan short" (55:52-56:01); bij NZDUSD "we zijn onder support, noteer hogere TF" (10:06). | Trade-richting = richting maand/week-bias; daily/4h-shorts in een weekly-uptrend overslaan (met uitzondering van de expliciete ABC-correctie-short, HTF14). |
| HTF11 | Liquidity-referenties: previous day high/low, previous week high, previous month high (18:39-18:50), equal highs/lows als "draw on liquidity" (29:53, 63:09), volume point of control (vPOC, 11:56, 31:11-31:38, 58:01-58:25: sessie-volumeprofiel op 4h; open vPOC's als target/support). Template-lijst toont: HVN, FVG, wGAP, dGAP, CR, MNY (midnight open), NYO, vPOC, Break, dOPEN/wOPEN/mOPEN, OB, SFP, pdH/pdL/pdEQ. | Bot-features: pdH/pdL, pwH/pwL, pmH, equal highs/lows, onbevestigde (nog open) vPOC, daily/weekly/monthly open, FVG/gap. Open vPOC = target of bounce-level. |
| HTF12 | Equal highs = niet automatisch breakout: "ik heb vaak gezien dat het dichtbij komt, iedereen denkt dat het breekt, maar dan juist lager gaat" (53:51-54:09). Equal lows/highs = liquidity-pool: reversal gebeurt "onder liquidity" (29:45). | Equal highs/lows niet als breakout-bevestiging; wel als liquidity-target + mogelijke sweep-and-reverse. |
| HTF13 | Value-area/range-regel (63:19-63:56): bij echte range -> reject VAH en short, of sweep boven range dan lager; maar alleen bij "mooie range"; zonder range negeren. | Range-play alleen als prijs duidelijk in range zit (vPOC in midden, VAH/VAL bepaald); anders overslaan. |
| HTF14 | Elliott-/golftelling als context voor wat nog kan: 5-golf omhoog afgerond -> ABC lager verwacht (03:12, 15:57-16:56, 17:13-19:40); "5 golven omhoog is de laatste, dus er komt een bounce" (16:51). Corrective W/ABC/WXY met target "Y" lager (31:57-32:29). | Eigen interpretatie, subjectief; niet meetbaar. Praktisch: na voltooide 5-golf-impuls richting niet meer volgen, verwacht tegenbeweging naar GP/-0.25-niveau. |
| HTF15 | Daily-"1-2-3 candles" die -0.25 vasthouden = bevestiging dat fib-level werkt (35:49). | Min. 3 daily-candles die op/boven (long) het -0.25-level sluiten = level houdt; eigen interpretatie van "123 candles". |
| HTF16 | Trade-selectie op silver 4h (57:53-62:52): (1) optimale trade = inverse H&S rechterschouder op GP met strakke SL net onder de steun (goede RR); (2) "worst RR" = SL breed; (3) volgende trade = continuatie. "Soms moet je elke trade nemen die je ziet." SL niet te ver: "als het onder je support (rechter schouder) blaast, verliest het meestal dat level en werkt het niet uit" (60:07-60:24). Targets -0.25 / -0.65 / -1 gebruikt als eerder; -0.25 hit bij vPOC. | SL = net onder steun/rechter schouder (niet onder het hele structuur-low); als prijs onder de schouder sluit -> trade ongeldig. Entry-kwaliteit rang: 1) GP + steun dichtbij, 2) verder weg. |
| HTF17 | Trade-timing nuance: een setup wordt niet nagejaagd: "I missed it ... je moet overal ogen hebben" (59:35-60:38); plan op chart is het belangrijkste ("ik heb mijn plan op de charts staan, dat is het belangrijkste", 38:09). | Geen late entry; als zone/entry gemist is en prijs naar -0.65/-1 loopt -> wacht op volgende setup. |
| HTF18 | Nieuws/sessie: slechts één opmerking: "Wat gebeurt er vandaag? Balance of trades, niet erg belangrijk" (25:07). Verder: previous day/week/month high en sessie-vPOC (4h) als referentie. | Economische-kalender check vóór trade: geen high-impact news in venster (niet exact bepaald in video). |
| HTF19 | Correlatie: USD-sterkte/zwakte vertaald naar pairs: bearish NZDUSD = USD sterker (05:04); een USD-daling -> EUR omhoog (22:20-22:25). DXY-tab staat open als check (zichtbaar in tabbalk vanaf ~17:40; DXY-chart met 5-golf op 15:40 frame). | Eigen interpretatie: USD-pairs onderling consistent houden (niet tegelijk long NZDUSD en short DXY-gevoelig), DXY-bias als filter. |
| HTF20 | Meerdere pairs tegelijk in watchlist (12 tabs); per pair beoordelen, meeste = "nog geen trade". | Bot: scan-lijst; per pair status {plan, wacht, trade}; geen verplichting om te traden. |

### Tegenstrijdig met eerdere regels
- Body-naar-wick-fib: eerder "body-to-wick"; hier consistent bevestigd, maar bij silver daily/weekly gebruikt hij wick (50:50-51:13) omdat daar de bounce zat; hij zegt "regels zeggen body". Dus uitzonderingsgedrag, geen echte tegenstrijdigheid.
- Eerdere regel: BOS = sterke candle-close voorbij KEY. Hier telt voor weekly "met kracht gebroken" (01:47) maar bij NZDUSD toch nog geen volledige bevestiging ("niet volledig bullish") - bevestiging via patroon (inverse H&S) is vereist naast de breuk.
- Entry op 0.618-0.796 (eerder) vs. "-0.25 + OB" als reactiezone (11:40, 35:49): hij gebruikt -0.25 van een vorige impuls ook als support/bounce-niveau, dus -0.25 is niet enkel target maar ook level (long op -0.25 NZDUSD).
- Equal highs ("breekt niet automatisch") past niet bij eerdere "open space: blijf N/V nemen" als blind vervolg.

### Wanneer GEEN trade
- Geen reactie / geen vertragende candles op 15m-1h na aankomst op de zone (11:34-12:07).
- Counter-trend tegen HTF-bias (silver: HTF bullish -> geen short, 55:52; AUDUSD nog in uptrend, 20:30).
- Patroon nog niet compleet: geen rechter schouder / neckline niet gebroken (EURCAD, 24:59-25:07; silver 50:02-50:18).
- Prijs net onder support of onder SR terwijl hogere TF nog tegen is (NZDUSD, 10:06).
- Tussen support en resistance in zonder duidelijk level (silver, 54:35-54:51).
- Equal highs net aangetikt: kan reversal zijn, niet breakout nemen (53:51).
- Geen range aanwezig -> geen vPOC/VAH-play (63:27-63:56).
- Corrective/onduidelijke golftelling ("ik zie de setup hier niet", GBPCAD 4h/1h, 36:31-37:21).
- Lage TF mist bullish indicatie ondanks zone (GBPCAD, "niet geïnteresseerd in long", 37:21).
- Setup al gemist / SL zou te ver onder de steun moeten (60:07-60:38).
- High-impact news (impliciet): vandaag alleen onbelangrijk, dus geen reden tot skippen (25:20).

### Beelden bekeken
00:20, 03:40, 07:40, 09:40, 11:40, 14:20, 15:40, 17:40, 22:00, 28:40, 33:40, 36:40, 43:02, 52:22, 55:02, 59:22, 61:22 (plus transcript volledig). Template-lijst van levellabels zichtbaar op 07:40 en 33:40; fib-template-lijst (EQ, GP, Gravis Fibs, Irregular Flat, Range, Standard, TrendPullBack) op 59:22.
Opmerking: frames 09:40/14:20 niet los geverifieerd voor elke claim; interpretaties van tijdsaanduidingen bij NZDUSD/EURAUD zijn gebaseerd op transcript + tabbalk. Geen expliciete risico-%/lotgrootte, sessietijd of nieuws-filter in de video genoemd.

## Test 2: zone met samenloop, instap na reactie op 4u (30 assets, 2015-2025, na kosten)

`research/strategy/test2.py`. 2.822 trades; gemiddeld -0,24R (2015-20) en -0,23R (2021-25) na kosten
(mediaan kosten 0,10R). TP1 gehaald: 14%. Kleine SL (8-40 pips op EURUSD) wordt vaak door ruis geraakt.

| Groep | 2015-20 | 2021-25 |
|---|---|---|
| Met samenloop (niveau, OB of FVG in de zone) | -0,23 | -0,19 |
| Zonder samenloop | -0,26 | -0,30 |
| Mee met week- en maandtrend | -0,30 | -0,30 |
| Tegen week- en maandtrend | +0,02 | +0,10 |

Enige groep die in beide helften niet negatief is: trades tegen de trend van week en maand (±470 trades),
net als in test 1. Statistisch (nog) niet te onderscheiden van nul.

## Test 3: vooraf vastgelegd (geschreven vóór de run, 2026-10-28)

Hypothese: setups **tegen** de trend van week en maand (wk = -1 en mn = -1 in test 1 en test 2) zijn winstgevend.
Gevonden op 2015-2025; getest op **2005-2014**, door geen enkele studie eerder gebruikt; 28 forex-paren
(olie en UK100 hebben geen data van voor 2015). Motor en instellingen ongewijzigd; kosten zoals in test 2.

Geslaagd als, voor die groep na kosten, ALLE drie gelden:
1. gemiddeld >= +0,10R per trade, met minstens 300 trades;
2. profit factor >= 1,2;
3. winst in minstens 6 van de 10 jaren.
Anders: verworpen, en dan wordt deze methode niet verder gebruikt voor de bot.

### Uitkomst test 3 (2005-2014, na kosten): VERWORPEN

| Motor | Trades | Gem. R | Profit factor | Jaren winst | Oordeel |
|---|---|---|---|---|---|
| Test 2 (zone + 4u-reactie) | 680 | -0,11 | 0,88 | 6/10 | verworpen (1 en 2 niet gehaald) |
| Test 1 (daggrafiek, limiet 0,66) | 1.010 | -0,01 | 0,98 | 3/10 | verworpen (alle drie niet gehaald) |

Het voordeel van "tegen de trend" uit 2015-2025 komt in 2005-2014 niet terug. Volgens de vooraf vastgelegde
regel wordt deze methode niet verder gebruikt voor de bot.

## Test 4: structuur op de week, instap na reactie op de dag (vooraf vastgelegd, 2026-10-29)

Zoals in de video's van boven naar beneden: breuk (BOS) en fib op de **weekgrafiek** (1 = swing-wick, 0 = top-wick),
zone 0,618-0,796; instap pas na een **afwijzingscandle op de daggrafiek** in de zone; SL voorbij de laagste wick in de
zone (0,2 dag-ATR buffer); setup vervalt bij een dagslot voorbij fib 1, als -0,25 eerst wordt geraakt, of na 60 dagen.
30 assets (28 forex, olie, UK100), kosten per symbool.

**Winnende setup = -0,25 geraakt vóór de SL** (definitie van de gebruiker). Twee uitstapmanieren worden gerapporteerd:
(a) alles dicht op -0,25; (b) helft op -0,25, SL naar instap, rest op -0,65 of het volgende niveau.

Geslaagd als, na kosten, in **2015-2020 én 2021-2025** apart:
1. gemiddeld >= +0,10R per trade (uitstap a of b), met minstens 100 trades per periode;
2. winnende setups boven het break-evenpercentage van die periode (1 / (1 + gemiddelde winst/risico op -0,25));
3. profit factor >= 1,2.
Varianten (samenloop met S/R, met/tegen trend) worden gerapporteerd maar tellen niet als aparte kans; als er één
geslaagd lijkt, moet die eerst opnieuw vooraf vastgelegd worden en door de slotkluis 2005-2014.

### Uitkomst test 4 (30 assets, na kosten): niet gehaald

| Periode | Trades | Winnend (-0,25 vóór SL) | Break-even | a: alles op -0,25 | b: helft + rest | c: ladder -0,25/-0,5/-0,618/-1 |
|---|---|---|---|---|---|---|
| 2015-20 | 262 | 13,4% | 12,5% | -0,07R (PF 0,93) | -0,09R (PF 0,90) | -0,13R (PF 0,85) |
| 2021-25 | 242 | 15,3% | 13,4% | -0,14R (PF 0,84) | -0,08R (PF 0,91) | -0,14R (PF 0,84) |

Met samenloop (niveau, OB of FVG in de zone) beter dan zonder (b: -0,05 / +0,03 tegen -0,22 / -0,38), maar niet positief
genoeg. FVG in de zone (b): +0,22 / +0,04 tegen -0,40 / -0,16 zonder; aanwijzing, ±120 trades per periode.

## Test 5: correcties van de trader op het dossier (vooraf vastgelegd, 2026-10-29)

Opmerkingen bij `docs/dossier_setups.pdf`: (1) de prijs mag tussen 0,618 en 1,1 komen en met wicks de low nemen en
toch een goede setup zijn; (2) AUDNZD 2017 is geen short maar een long met de fib vanaf de low van dec. 2016/jan. 2017
naar de top, ±1:1 teruggetrokken, daarna duidelijk gestegen.

Regels (`research/strategy/test5.py`): poten op de week (zigzag: keerpunt bevestigd na 2 week-ATR terug; poot >= 4
week-ATR); richting = de laatste grote poot; fib over die poot; zone 0,618-1,1; instap op een afwijzingscandle op de dag
in de zone; **SL voorbij het 1,1-niveau** (0,2 dag-ATR); ongeldig bij een dagslot voorbij 1,1, als -0,25 eerst komt, of
na 26 weken. Winnend = -0,25 vóór de SL. Uitstap a/b/c zoals test 4. Controle: AUDNZD 2017 wordt nu gevonden als long
(instap 4 juni 2017) en wint (+3,1R).

Geslaagd als (na kosten, 30 assets) in 2015-2020 én 2021-2025 elk: uitstap a, b of c gemiddeld >= +0,10R met >= 100
trades, PF >= 1,2, en winnend boven break-even. Dan één keer de slotkluis 2005-2014 (28 forex), met dezelfde criteria.

### Uitkomst test 5 (2015-2025, 30 assets): alles samen rond break-even; de video-filters wijzen consequent goed

Alles: P1 236 trades, a -0,02 / b -0,07 / c -0,06R; P2 169 trades, a -0,07 / b +0,03 / c +0,03R.
Met **voortzetting + S/R in de zone + maandtrend mee** (alle drie video-regels, vooraf bekend):
P1 142 trades, winnend 42%, a +0,12 / b +0,08 (PF 1,15) / c +0,11R (PF 1,20); P2 98 trades, winnend 40%,
a +0,06 / b +0,15 (PF 1,30) / c +0,18R (PF 1,36). Per paar te weinig trades (±1 per paar per jaar).

## Test 6 (vooraf vastgelegd, 2026-10-29): slotkluis 2005-2014 voor test 5 + de drie video-filters

Exact test 5 (`test5.py`, ongewijzigd), alleen trades met voortzetting (`cont`), S/R van maand/week in de zone (`lvl`)
en maandtrend mee (`mn = 1`). 28 forex-paren, 2005-01-01 tot 2014-12-31, kosten per symbool.
Geslaagd als uitstap c (fib-ladder) gemiddeld >= +0,10R, PF >= 1,2, met >= 100 trades; daarnaast gerapporteerd: a en b,
winnend %, per jaar.

### Uitkomst test 6 (slotkluis 2005-2014): verworpen volgens de vastgelegde lat, maar positief
192 trades, winnend 39%: a +0,15R (PF 1,24), b +0,11R (PF 1,18), **c +0,09R (PF 1,15)**; lat voor c was +0,10R en PF 1,2.
Wel: positief in alle drie de periodes (2005-14, 2015-20, 2021-25), ±430 trades; samen nog niet significant (t ±1,4).
Volgende ronde: nieuw dossier van deze versie, correcties van de trader, opnieuw vastleggen en testen.

## S1 als portefeuille (2005-2025, 30 assets): te traag en te veel tegelijk open voor de 5ers

S1 = test 5 + de drie video-filters. `research/strategy/s1_portfolio.py`: vast risico per trade (% van de start-
balans), dagelijks gewaardeerd op de slotkoers, kosten bij instap, slechtste intradag = alle open posities tegelijk op
hun ergste punt (voorzichtig; de ladder wordt niet gedeeltelijk gesloten in de waardering).
- ±420 trades in 21 jaar (±20 per jaar), mediane looptijd **±190 dagen**, gemiddeld **14 posities tegelijk open**
  (max ±40, sterk gecorreleerd: veel USD-paren in dezelfde richting).
- Per 1% risico: uitstap c +1,6%/jaar, max DD -29% (ook op slotkoersen -29%); uitstap a +2,4%/jaar, max DD -23%.
  Zeer ongelijk per jaar (2007 +17R, 2020 +28R, 2013 -12R).
- 5ers-challenge (start elke maand, +8% / +5%, -10% statisch, -5% per dag): bij 0,5-2% risico slaagt 2-50% afhankelijk
  van periode, mediaan 1-7 jaar per challenge; EV per challenge tussen -0,5% en +0,7% van het account = nul.
Conclusie: de kleine voorsprong per trade (+0,1 tot +0,15R) is echt in alle drie de periodes, maar met trades van een
half jaar en een gecorreleerde stapel open posities levert hij geen bruikbaar rendement/risico op voor een prop-account.

## Test 7 (vooraf vastgelegd, 2026-10-29): S1 één tijdframe lager - poten op de dag, instap op de 4 uur

Exact de regels van test 5, één tijdframe lager (`test5.py --struct D1 --entry H4`): zigzag op dagcandles (keerpunt na
2 dag-ATR terug, poot >= 4 dag-ATR), fib 0,618-1,1 over de laatste grote poot, instap op een afwijzingscandle op de
4 uur in de zone, SL voorbij 1,1 (0,2 x 4u-ATR), ongeldig bij een 4u-slot voorbij 1,1, als -0,25 eerst komt, of na 26
dagcandles. Filters zoals S1, één tijdframe lager: voortzetting (`cont`), S/R van maand/week in de zone (`lvl`), trend
van de week mee (`htf = 1`). Portefeuille: max. één open positie per valuta (`s1_portfolio.py --trend htf --one-per-ccy`).
30 assets, kosten per symbool. Ontwikkeling 2015-2020, bevestiging 2021-2025.
Geslaagd als in 2015-2020 én 2021-2025 elk: uitstap a of c gemiddeld >= +0,10R met >= 100 trades en PF >= 1,2, én de
portefeuille bij 1% risico max DD <= 15% en 5ers-EV > +1% per challenge. Dan één keer 2005-2014 met dezelfde lat
(let op: 2005-2014 is al eens gezien voor de weekversie, dus minder zuiver dan een echte slotkluis).

### Uitkomst test 7 (2015-2025, 30 assets): verworpen
Alles: P1 1125 trades a -0,07R, P2 885 trades a -0,09R. Met de vooraf gekozen filters (cont + lvl + weektrend mee):
P1 542 trades, winnend 33%, a -0,08 / b -0,08 / c -0,09R (PF 0,86); P2 383 trades, a -0,05 / b -0,03 / c -0,03R.
Eén tijdframe lager verdwijnt de kleine voorsprong van de weekversie: winnend ±33% tegen break-even ±37% (RR ±1,7).

## Video 8 (FTMO-interview, https://www.youtube.com/watch?v=yFm1ouJUCSE, vanaf 11:30)

Swing trader uit Antwerpen, zelfde top-down school (S/R, structuur, impuls/correctie, fib, H&S, bullish N):
- Maand: grote S/R-zone met een geschiedenis van sterke reacties; structuur draait (impulsen nu in de nieuwe richting).
- Week: impuls + 3-poot correctie; fib 0,618 / 0,786; uitbreiding -0,27 als doel; bullish candle bij -0,27 bevestigt.
- Dag: eerst een omkeerpatroon (inv. H&S na "momentum vertraagt": impulsen worden kleiner), daarna een voortzetting:
  bullish N = 5 poten, hogere toppen én hogere bodems, poot 3 impulsief. Fib van de hogere bodem naar de hogere top;
  **TP = -0,27** (dag-TP). Dagzone: van 0,618 tot de eerste structuur eronder. Wachten tot de markt naar de zone komt.
- 4 uur: na de aanraking van de zone "vertraging": 3 candles die de zone respecteren, waarvan minstens één bullish;
  limietorder op het lichaam van die candles, **SL onder de laagste wick + 10 pips**; bijschalen op een patroon in een
  patroon (2 uur). Stop naar break-even na een deel winst, of onder de volgende structuur; niet hebberig: uit op -0,27.
- 1-1,5% risico, weinig trades (14 in de getoonde periode, 71% winnend dankzij veel break-even), geen nieuws/indicatoren.

## Test 8 (vooraf vastgelegd, 2026-10-29): de regels van video 8

`research/strategy/test8.py`: dagpoten (zigzag test 5); bullish N / bearish V = voortzetting (`cont`) vanaf een hogere
bodem (`hl`); fib over de poot, TP -0,27; zone van 0,618 tot het vorige topje (de gebroken top), begrensd tussen 0,618
en 1 (anders 0,786); 4u-instap: >= 3 candles sinds de aanraking zonder slot voorbij de zone, minstens één in de
richting; limiet op de open van de laatste candle in de richting; SL laagste wick sinds de aanraking + 10 pips.
Ongeldig bij een 4u-slot voorbij de zone, TP vóór de vulling, of na 26 dagcandles. Uitstap (a) TP/SL, (b) idem met stop
naar instap bij +2R (of halfweg als dat dichter is). Filter: `cont` + `hl` + weektrend mee (`htf = 1`).
Geslaagd als in 2015-2020 én 2021-2025 elk: a of b gemiddeld >= +0,10R, >= 100 trades, PF >= 1,2. Kosten per symbool.
Rookproef EURUSD: mediane RR ±11 (zeer krappe stop), ±11% winnend; dat volgt uit de regels zoals beschreven.

### Uitkomst test 8 (2015-2025, 30 assets): verworpen
Alles: P1 963 trades, winnend 7,1% (break-even 7,4%, mediane RR 12,6), a -0,21R; P2 764 trades, a -0,33R.
Filter cont + hl + weektrend: P1 480 trades a -0,02 / b -0,02R; P2 349 trades a -0,42 / b -0,27R.
De krappe stop (laagste 4u-wick + 10 pips) geeft een hoge RR, maar de trefkans zakt evenredig: wat overblijft is toeval
min kosten. Bij RR > 10 kosten spread en slippage ook meer R per trade.

## Test 9 (2026-10-29): dag + 4 uur, ontdekking op 2015-2020, daarna vooraf vastgelegd

Op verzoek van de trader: geen trades op de week; setup op de dag, instap op de 4 uur. `research/strategy/test9.py`:
dagpoten (zigzag), zone 0,618-1,1, eerste 4u-afwijzingscandle in de zone; per trade drie stops (f110 / wick / f100)
x drie doelen (0 / -0,27 / -0,27 met stop naar instap halfweg) en kenmerken die bij de instap bekend zijn.
Ontdekking (`t9_discover.py`, alleen 2015-2020, 1129 trades): alles -0,03 tot -0,22R; stop f110 is de beste; krappe
wick-stop slecht. Duidelijk verschil per kenmerk: **grote poot** (leg_atr hoog) en **trage correctie** (retr_days hoog,
wait_bars hoog) positief; diep (> 0,64) en snelle terugval negatief. Dat is "impuls en correctie" uit de video's:
een impulsieve poot, gevolgd door een trage, corrigerende terugval.
Gekozen op 2015-2020: f110 + t27be, poot >= 5,44 dag-ATR en >= 17 dagen van de top tot de instap:
190 trades, +0,22R, PF 1,53 (ontdekking, dus optimistisch).

**Vooraf vastgelegd voor 2021-2025** (`t9_discover.py --confirm R_f110_t27be "leg_atr >= 5.44 & retr_days >= 17"`):
geslaagd als gemiddeld >= +0,10R, PF >= 1,2 en >= 80 trades. Daarna één keer 2005-2014 met dezelfde lat.

### Uitkomst test 9 bevestiging 2021-2025: geslaagd
Regel: 139 trades, winnend 33%, **+0,15R, PF 1,31** (lat +0,10R, PF 1,2, >= 80 trades). Alles zonder regel: -0,07R.
Per jaar (som R): 2021 +8,5, 2022 +5,7, 2023 +0,9, 2024 -5,4, 2025 +10,9. Volgende stap: 2005-2014, één keer.

### Uitkomst test 9 slotkluis 2005-2014 (28 forex; geen olie vóór 2015): verworpen
Regel: 297 trades, winnend 28%, **-0,04R, PF 0,93** (t -0,5). Alles zonder regel: -0,07R. Per jaar sterk wisselend
(2007 -11,5R, 2010 -20,3R, 2013-14 +7R). Over de drie periodes samen ±+0,08R: de voorsprong van 2015-2025 is
grotendeels selectie (gekozen op 2015-2020) en houdt niet stand op tien andere jaren.

## Test 10 (vooraf vastgelegd, 2026-10-29): de context van video 8 op dag + 4 uur

Zelfde motor als test 9 (`test9.py`, stop f110, doel -0,27, stop naar instap halfweg = `R_f110_t27be`), met twee
kenmerken uit video 8 die test 8 miste:
- **week-correctie in de fib**: de laatste afgeronde weekpoot wijst in de handelsrichting en de prijs heeft die poot
  voor 0,5-0,886 gecorrigeerd (`0.5 <= wk_depth <= 0.886`): de daginstap is het einde van de weekcorrectie;
- **vertraging**: de laatste tegenbeweging op de dag is kleiner dan de vorige (`decel`).
Regel: `0.5 <= wk_depth <= 0.886 & decel`. Daarnaast gerapporteerd (niet beslissend): met bullish N (`cont & hl`).
Getest op alle drie de periodes tegelijk (2005-2014, 2015-2020, 2021-2025), 30 assets, kosten per symbool.
Geslaagd als in elke periode gemiddeld >= +0,10R en PF >= 1,2, en samen >= 120 trades.

### Uitkomst test 10 (2005-2025, 30 assets): verworpen
Regel (week-correctie 0,5-0,886 + vertraging), `R_f110_t27be`: 2005-14 133 trades -0,01R (PF 0,98); 2015-20 58 trades
-0,02R; 2021-25 38 trades -0,28R. Samen 229 trades, winnend 26%, t -0,7. Met bullish N erbij: slechter (-0,02 tot
-0,31R). Ook elk kenmerk apart en elk doel (0, -0,27) blijft rond of onder nul. De week-context uit video 8 voegt op
de dag/4u-instap niets toe.

## Video 9 ("De makkelijkste manier om te starten met traden als beginner", zelfde school als video 8)

`research/videos/video9/` (transcript + 294 screenshots). Kern (vanaf 38:00):
- Basis: candles, impuls/correctie ("kracht naar boven, traag naar beneden"), marktstructuur (HH/HL). Correctie herken
  je aan veel tijd, weinig prijs. Break of structure ≠ trendwissel: pas vanaf de tweede lower low.
- Week = bias, in 4 fases: 1 correctie (tegen de trend, strenger), 2 impuls (met de trend), 3 pauze/omkeer bij de
  vorige top (niet handelen, tenzij de dag/4u het aangeeft), 4 extensie (met de trend). Paren zonder duidelijke
  HH/HL-structuur overslaan.
- Dag = patroon: H&S en inverse H&S (omkeer; zone op de body van schouder 1), bullish N / bearish V (voortzetting;
  HH/HL, derde poot impulsief). Fib van de wick van het uiterste naar de body van het begin; zone onder 0,618 tot de
  eerste structuur of het 1-niveau; TP -0,27 (anders -0,68).
- 4 uur = instap, drie manieren: vertraging (3 candles respecteren de zone, minstens één van de andere kleur; order
  op de body, SL onder de laagste wick + 5-10 pips), een 4u bullish N, of (meest gebruikt) een 4u inverse H&S.
  Stop naar break-even zodra de trade loopt.

## De eigen trades van de trader (2026-10-29, vijf grafieken)

EURUSD D1 (long, juni 2025: fib 1,1395 -> 1,1625, limiet 1,14765, SL 1,1355, TP -1 = 1,18745, RR 3,3), EURUSD W1
(long: 1,1172 -> 1,1830, limiet 1,13929, TP -0,28, RR 2,3), EURAUD D1 (short dec. 2025: limiet 1,77675, TP -1,618),
GBPAUD D1 (short: limiet 2,04388, TP -1,618), AUDCAD W1 (long: 0,8985 -> 0,922, limiet 0,90695, SL 0,89453,
TP -1,618, RR 4,7). Gemeen: **de poot breekt een sleutelniveau** ("Breaker", "KEY", maand/week S/R); fib over die
poot; **limietorder rond 0,618-0,68, precies op de retest van het gebroken niveau**; SL net voorbij 1 / de wick van de
start; **ver doel (-1 of -1,618)**. Geen 4u-bevestiging in deze voorbeelden; dag of week.

## Test 11 (vooraf vastgelegd, 2026-10-29): break & retest in de golden pocket (de eigen trades)

`research/strategy/test11.py --tf D1|W1`: top = kleine swing (1 candle aan elke kant); die top breekt een eerdere
swing S (2 candles aan elke kant, S nog intact: geen slot voorbij zijn body); start van de poot = het uiterste tussen S
en de top; fib 1 = body van de start, 0 = wick van de top; S (body of wick) ligt tussen 0,5 en 0,786 (de retest).
Limiet op 0,65 vanaf de candle na de top; SL wick van de start - 0,1 ATR; nieuwe top vóór de vulling verschuift fib en
order; vervalt bij een slot voorbij 1 of na 40 candles. Controle op de voorbeelden: EURUSD D1 exact (instap 1,14790,
SL 1,13625, +3,3R op -1), EURUSD W1 exact, EURAUD D1 zelfde poot (data stopt half dec. 2025), AUDCAD W1 zelfde zone
maar start enkele weken eerder, GBPAUD D1 niet gevonden.
**Beslissend: `R_t1` (doel -1, geen break-even).** Gerapporteerd: -0,27 / -0,618 / -1,618 en met break-even.
Geslaagd als, 30 assets, kosten per symbool, in elke periode (2005-14, 2015-20, 2021-25) gemiddeld >= +0,10R en
PF >= 1,2; D1 >= 100 trades per periode; W1 samen >= 60 trades (zelfde lat per periode).

### Uitkomst test 11 (2005-2025, 30 assets): verworpen
D1: 15.843 trades (±25 per asset per jaar), `R_t1`: 2005-14 -0,00R (PF 1,00), 2015-20 -0,11R (PF 0,87), 2021-25
-0,09R (PF 0,89); winnend ±23% bij mediane RR 3,4; t -3,4. Geen enkel doel of break-even-variant positief in alle
periodes. Met maand/week-S/R in de pocket (`htf`): -0,03R.
W1: 2.581 trades, `R_t1`: -0,02 / -0,13 / +0,19R; alleen 2021-25 positief (alle doelen), samen ±0 (t -0,35).
De vijf voorbeelden van de trader zijn winnaars uit een veel grotere verzameling setups die er mechanisch hetzelfde
uitzien: de code vindt ±25 setups per paar per jaar, de trader neemt er een paar. Wat die selectie maakt (week-fase,
welk niveau "KEY" is) zit niet in de regels zoals ze nu beschreven zijn.

## Test 12 (vooraf vastgelegd, 2026-10-29): video 9 - week-fase als bias, dag-patroon, 4u-instap

Zelfde motor als test 9/10 (`test9.py`; dagpoten, zone 0,618-1,1, 4u-afwijzingscandle, stop f110, doel -0,27 met
stop naar instap halfweg = `R_f110_t27be`), plus de week-fase uit video 9 (`week_phase`): trend op de week = laatste
twee toppen én bodems hoger (lager); fase 1 correctie, 2 impuls, 3 pauze (binnen 0,5 week-ATR onder de vorige top),
4 extensie; geen duidelijke trend = niet handelen. Toegestaan (`wk_ok`): met de trend in fase 2 of 4, tegen de trend
in fase 1. Dagpatroon: bullish N / bearish V (`cont & hl`).
Regel: `wk_ok & cont & hl`. Alle drie de periodes, 30 assets, kosten per symbool. Geslaagd als in elke periode
gemiddeld >= +0,10R en PF >= 1,2, samen >= 120 trades. Gerapporteerd: per fase, en zonder `cont & hl`.

### Uitkomst test 12 (2005-2025, 30 assets): verworpen
Regel `wk_ok & cont & hl`, `R_f110_t27be`: 2005-14 643 trades -0,10R (PF 0,81); 2015-20 319 trades -0,05R (PF 0,90);
2021-25 246 trades -0,04R (PF 0,92); samen 1.208 trades, winnend 24%, t -2,2. Per week-fase: geen enkele fase
positief in alle drie de periodes (fase 2 alleen in 2021-25 +0,24R; fase 1 tegen de trend het zwakst; geen duidelijke
trend het slechtst, zoals de video zegt, maar ook de toegestane fases blijven negatief).

## Test 13 (2026-10-29): de setups van de trader, regels uit en aan, ontdekking op 2015-2020

`research/strategy/test13.py` (zelfde motor als test 11, maar elke regel als kolom; EURUSD D1 juni 2025 nog steeds
exact gevonden, +3,3R) en `t13_discover.py` (alleen 2015-2020). D1, 5.423 trades in 2015-2020:
- Regels uitzetten verandert weinig: alle regels -0,11R; zonder pocket-eis -0,11; zonder break-eis -0,10.
  Herverankeren bij een nieuwe top kost geld (met: -0,16R, zonder: -0,05R).
- Wat wel scheidt: de trend op de eigen grafiek. Instap **tegen** de 50-candle-gemiddelde (long terwijl de prijs nog
  onder het gemiddelde zit = de eerste break na een daling, een omkeer) +0,07 tot +0,12R; **met** de trend -0,21R.
  Zelfde richting voor week- en maandtrend. Met de regels van de trader erbij (break + pocket): +0,12R, PF 1,16.
- W1: niets duidelijk en weinig trades.
Let op: de vijf voorbeelden van de trader zijn trades **met** de trend; volgens 2015-2020 is dat de zwakke kant.

**Vooraf vastgelegd** (D1, `R_w_t1`, regel `broke & pocket & ma == -1`): ontdekking 964 trades +0,12R PF 1,16.
Lat (lager dan eerder, omdat dit een andere vraag is: heeft deze vorm van de setup überhaupt een voorsprong?):
2021-2025 en 2005-2014 elk gemiddeld > 0 met PF >= 1,05, en samen (die twee periodes) t >= 2,0.

### Uitkomst test 13: verworpen
Regel `broke & pocket & ma == -1`, `R_w_t1`: 2021-2025 700 trades -0,14R (PF 0,83, t -2,1); 2005-2014 1.698 trades
-0,03R (PF 0,96). Samen -0,06R (t -1,7). De "tegen de trend"-voorsprong van 2015-2020 was toeval in die periode.
Blijvend uit deze test: de afzonderlijke regels van de setup (break van structuur, retest in de pocket) veranderen de
uitkomst nauwelijks, en herverankeren bij een nieuwe top maakt het slechter.

## Test 15 (vooraf vastgelegd, 2026-10-29): VectorVest-achtige trend (RT + MTI) als filter en op zich

Op vraag van de trader (VectorVest: "na 5 handelsdagen hoger = up", RT, MTI). De formules van VectorVest zijn niet
openbaar; benadering in `research/strategy/rt.py`: rt5 (slot / slot 5 dagen eerder), rt (3-daags EMA van het
geometrisch gemiddelde over 5/10/20 dagen), rtw (week, 1/2/4 weken), mti = valutasterkte (gemiddelde log-rt van de 28
paren per valuta, basis min quote). Regel: alle vier in de handelsrichting.
Getest zonder ontdekking, alle drie de periodes:
(a) op de setups van de trader (test 13 D1, `broke & pocket`, `R_w_t1`); (b) op video 9 (test 12, `wk_ok & cont & hl`,
`R_f110_t27be`). Geslaagd als elke periode gemiddeld >= +0,05R met PF >= 1,05 en samen t >= 2,0.
(c) op zich: long als alle vier up, short als alle vier down, anders vlak; dagelijks, kosten per wissel. Geslaagd als
elke periode positief na kosten en Sharpe samen >= 0,5.

### Uitkomst test 15: verworpen
(a) Setups van de trader: zonder VV -0,04 / -0,11 / -0,08R; met alle vier VV-signalen mee -0,07 / -0,15 / -0,05R
(t -3,6). (b) Video 9: zonder -0,10 / -0,05 / -0,04R; met -0,11 / -0,11 / -0,03R. (c) Op zich, 28 paren: -1,0% /
-2,7% / -2,6% per jaar na kosten (Sharpe -0,25 / -0,79 / -0,90). Een korte trend (5-20 dagen) mee hebben helpt niet;
eerder het omgekeerde (niet vastgelegd, dus geen conclusie).

## Test 14 en 16 (vooraf vastgelegd, 2026-10-29)

**Test 14 - video 9 puur, met zijn meest gebruikte instap (4u inverse H&S)**, `research/strategy/test14.py`: dagzone en
week-fase als test 12; 4u-swings (2 candles aan elke kant) vanaf 10 candles voor de aanraking: linkerschouder, top,
hoofd (lager, in de zone), top, rechterschouder (hoger dan het hoofd); instap op het slot boven de laatste top (de
nek); SL onder de rechterschouder - 10 pips; doel dag -0,27. Beslissend: `R_hs_t27` met `wk_ok & cont & hl` (zoals
de video). Gerapporteerd: -0,68, -0,27 met break-even, en alle setups. Geslaagd als elke periode (2005-14, 2015-20,
2021-25) gemiddeld >= +0,05R met PF >= 1,05 en samen t >= 2,0. Rookproef EURUSD+GBPAUD: mediane RR 4,6.

**Test 16 - DEW** (VectorVest "Daily Early Warning", niet openbaar; benadering in `rt.py`): de valutasterkte (mti)
draait vandaag in de handelsrichting terwijl rt5 al zo wijst. Als filter (`vv_dew == 1`) op de setups van de trader
en op video 9, en op zich (dag na het signaal long/short); zelfde latten als test 15.

### Uitkomst test 16 (DEW): verworpen
Filter op de setups van de trader: -0,05 / -0,12 / -0,11R (t -3,7); op video 9: -0,21 / -0,09 / -0,37R (t -3,3).
Op zich: -1,6% / -2,7% / -3,7% per jaar na kosten (Sharpe -0,35 / -0,75 / -1,22).

### Uitkomst test 14 (video 9 met 4u inverse H&S): verworpen
Beslissend `wk_ok & cont & hl`, `R_hs_t27`: 2005-14 224 trades +0,02R (PF 1,03); 2015-20 114 trades +0,22R (PF 1,27);
2021-25 74 trades **-0,56R** (PF 0,40); samen t -0,25. Mediane RR 4,2, winnend ±21%.
Alle setups met deze instap (zonder week-fase en N/V): +0,08 / +0,08 / -0,06R (t 0,95) - de minst slechte instap tot
nu toe, maar niet significant en negatief in de laatste vijf jaar. De filters uit de video (week-fase, bullish N)
maken het hier niet beter.

## Test 17 (vooraf vastgelegd, 2026-10-29): NZDCAD, de drie trades van de trader

Drie NZDCAD D1-trades (long okt. 2023 -> -0,65, short feb. 2024 -> ±-0,28 op week-S/R, long midden 2024: zone
gerespecteerd, prijs exact tot -0,2). Motor test 11 (`test11.py --reset-expiry`: herverankeren geeft de order
opnieuw 40 candles) met extra doelen -0,2 en -0,65; één positie per richting tegelijk (`t17_eval.py`).
Controle: short feb. 2024 gevonden (+1,9R op -0,2), long 2024 gevonden (vulling 21 juli, +2,1R op -0,2; verliest op
-0,27 en verder), long okt. 2023 net niet (poot start 0,7995 i.p.v. 0,7965, SL te krap, uitgestopt).
**Beslissend: NZDCAD, `R_t020`, één positie per richting.** Geslaagd als elke periode (2005-14, 2015-20, 2021-25)
gemiddeld >= +0,05R met PF >= 1,05 en samen t >= 2,0. Daarna zelfde regel op de andere paren (buiten NZDCAD
gekozen): samen gemiddeld > 0 met t >= 2,0. Let op: NZDCAD is door de trader gekozen en de voorbeelden liggen in
2023-2024 (periode 2021-25).

### Uitkomst test 17 (NZDCAD 2005-2025): verworpen
Eén positie per richting, `R_t020`: 2005-14 125 trades -0,08R (PF 0,89); 2015-20 67 trades -0,01R; 2021-25 47 trades
-0,34R (PF 0,56); samen t -1,3. Alle setups: -0,09 / -0,11 / -0,13R. Verdere doelen slechter (-0,65 en -1: -0,14 tot
-0,48R). Ook in 2021-25, waar de drie voorbeelden liggen, negatief: de voorbeelden zijn de winnaars uit ±10 trades per
jaar die er hetzelfde uitzien. Andere paren niet meer getest (de regel faalt al op NZDCAD).

Dossier voor de trader: `docs/dossier_nzdcad.pdf` (`dossier_t17.py`): de 23 NZDCAD-trades van 2023-2025 die de motor
neemt (5 winnaars op -0,2), één pagina per trade met fib, instap, SL en TP. Vraag: welke zou je nemen, welke niet,
en waarom - dat verschil is wat de regels nog missen.

## Jouw trades nagerekend (`research/strategy/trader_trades.py`, niveaus afgelezen van de screenshots)

Met de eigen instap/SL/TP van de trader: EURUSD D1 jun-25 +3,28R (TP -1), NZDCAD okt-23 +2,68R, NZDCAD feb-24 +2,81R,
NZDCAD jun-24 +6,6R (SL aangenomen 0,807); EURUSD W1, GBPAUD D1, AUDCAD W1 lopen nog in de data (SL niet geraakt);
EURAUD dec-25 nog niet gevuld. Verschillen met de motor: SL ruimer (onder het échte uiterste van de basis), doel op
een week/maand-niveau, deel winst op de eerste TP en daarna SL in winst.

## Test 18 (2026-10-29): het beheer van de trader

`research/strategy/test18.py` (motor test 11 met --reset-expiry): per trade de helft dicht op TP1 (-0,2 of -0,27),
SL naar de instap of de oude top (fib 0), rest naar -0,65 / -1 / -1,618 of trailen onder elke nieuwe swing
(`R_m_<tp1>_<lock>_<tp2>`); daarnaast het hele doel op het eerste maand/week-niveau voorbij -0,2 (`R_lvl`).
Werkwijze vooraf vastgelegd: beste beheer kiezen op 2015-2020 (D1, 30 assets, alle setups én één positie per
richting); dan dat ene beheer vastleggen en controleren op 2021-2025 en 2005-2014 (elk > 0 met PF >= 1,05, samen
t >= 2,0).

## Alle setups van de trader naast de motor (`compare_setups.py`, `docs/vergelijking_setups.pdf`)

| trade | jouw instap (fib) | jouw SL (fib) | jouw TP (ext) | jij | motor: zelfde poot? | motor met jouw TP |
|---|---|---|---|---|---|---|
| EURUSD D1 long jun-25 | 0,646 | 1,17 | -1,08 | +3,28R | ja (afstand 0,04) | +3,40R |
| EURUSD W1 long jul-25 | 0,665 | 1,09 | -0,29 | loopt | ja (0,01) | loopt |
| EURAUD D1 short dec-25 | 0,688 | 1,80 | -1,47 | nog niet gevuld | ja (0,09) | niet gevuld (data stopt) |
| GBPAUD D1 short nov-25 | 0,615 | 1,20 | -1,72 | loopt | nee (0,31) | niet gevuld |
| AUDCAD W1 long sep-25 | 0,640 | 1,17 | -1,83 | loopt | half (0,42; start eerder) | verlopen |
| NZDCAD D1 long okt-23 | 0,645 | 1,15 | -0,71 | +2,68R | bijna (start 0,7995 i.p.v. 0,7965) | -1R (SL te krap) |
| NZDCAD D1 short feb-24 | 0,693 | 1,05 | -0,32 | +2,81R | ja (0,08) | +2,27R |
| NZDCAD D1 long jun-24 | 0,87 | 1,04 | -0,22 | +6,6R | ja (0,04) | +2,13R |

Instap en SL van de trader liggen dicht bij die van de motor (instap 0,62-0,69, SL 1,04-1,20 in fib, uitschieter
EURAUD 1,80). Verschillen: (1) welke poot (startpunt) - kost NZDCAD okt-23; (2) orders van de trader blijven langer
staan (GBPAUD, AUDCAD); (3) het doel verschilt per trade (-0,22 tot -1,83). De regels zelf zijn niet fout; de motor
neemt alleen ook alle andere setups die er hetzelfde uitzien.

### Uitkomst test 18 (beheer): verbetert iets, maakt niet winstgevend
D1, één positie per richting (2005-14 / 2015-20 / 2021-25): helft op -0,2, SL naar oude top, rest -1: +0,00 / -0,03 /
-0,05R; volledig -0,2: -0,01 / -0,03 / -0,06R; -0,27 met break-even: -0,01 / -0,03 / -0,05R; doel op het eerste
maand/week-niveau: -0,01 / -0,02 / -0,21R. W1 op -0,2: -0,06 / -0,01 / +0,21R (alleen recent positief).
Het verschil zit dus vóór de instap: welke setups en wanneer.

## Test 19 (vooraf vastgelegd, 2026-10-29): instapmoment ("timing wanneer je erin gaat")

Voorbeeld van de trader: NZDCAD long begin 2025 - zone 0,618-0,796 op de week-S/R 0,8077, niet bij de eerste
aanraking in, wel bij de candle die met een wick in de zone komt en terug omhoog sluit (pijl rond 3 maart), daarna tot
-0,65. `research/strategy/test19.py`: poten en uitstappen als test 18, maar geen blinde limiet: instap op het slot van
de eerste dag-afwijzingscandle (wick tot 0,618 of dieper, slot boven de open in de bovenste 40% van de candle, slot
tussen 0,5 en 0,786). Na een aanraking beëindigt een nieuwe top de setup. Controle: NZDCAD-poot jan-feb 2025 gevonden,
instap 13 feb (slot 0,8126), +1,15R op -0,2.
**Beslissend: D1, 30 assets, één positie per richting, `R_t020`.** Geslaagd als elke periode (2005-14, 2015-20,
2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: `touch_n` (eerste aanraking of later),
`at_lvl`, krappe SL, beheer, W1.

### Uitkomst test 19 (instapmoment): verworpen
D1, één positie per richting, `R_t020`: -0,01 / -0,08 / -0,10R (t -2,5); W1: -0,07 / +0,02 / +0,09R. Eerste
aanraking of later (`touch_n`) maakt weinig uit.

## GBPNZD 2026 (de trader: "er zijn er maar 2")

Trader: long maart 2026 (kleine poot, instap 2,256, SL 2,23295, TP = BoS 2,32089, RR 2,8) en long aug-sep 2026 (poot
1 juni 2,2466 -> 7 juli 2,3555, instap 2,28456, SL 2,25626 onder de BoS, TP -0,2 = 2,37691, RR 3,3). Context: boven
week- en maand-S/R, weekstructuur bullish -> alleen longs. Motor test 19 nam er 8 (andere, kleinere poten).
Een daily zigzag met keerpunten na 3 dag-ATR vindt de grote poot exact (28 mei 2,2444 -> 6 juli 2,3534).

## Test 20 (vooraf vastgelegd, 2026-10-29): alleen de grote poten + de context van de trader

`research/strategy/test20.py`: daily zigzag (keerpunt na 3 ATR, poot >= 6 ATR); instap als test 19 (dag-
afwijzingscandle, slot tussen 0,5 en 0,786); SL voorbij 1 (0,1 ATR); doel -0,2. Controle GBPNZD 2026 (Yahoo-data):
long poot 28 mei -> 6 juli, instap 3 aug 2,2887, TP -0,2 op 27 okt: +1,89R (de trade van de trader); daarnaast een
short 24 mrt (-1R) die de trader niet nam (bullish context).
**Beslissend: `wk_struct == 1 & htf_sup`** (weekstructuur in de handelsrichting én een week/maand-S/R tussen fib 1
en de instap), één positie per richting, `R_t020`, 30 assets, 2005-2025. Geslaagd als elke periode gemiddeld > 0
met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: elk deel apart en alle grote poten.

### Uitkomst test 20: niet geslaagd volgens de lat, wel het beste tot nu toe
Regel `wk_struct == 1 & htf_sup`, één positie per richting, 483 trades (0,8 per paar per jaar):
`R_t020` +0,04R (PF 1,06) / -0,01R (PF 0,99) / +0,24R (PF 1,41), t 1,0 -> lat niet gehaald (2015-20 ±0, t < 2).
Met het beheer van de trader (helft op -0,2, SL naar oude top, rest -1): +0,06 / +0,02 / +0,26R, t 1,2.
Elk deel apart beter dan alle grote poten (-0,00 / -0,02 / +0,14R); alleen S/R: +0,02 / +0,05 / +0,19R (t 1,3).
Eerste versie die in alle drie de periodes ≥ 0 is met het beheer van de trader, maar nog niet sterk genoeg.

Correctie kosten: `test2.cost_price` gebruikte een pip van 0,0001 voor goud, zilver en indexen (kosten veel te laag).
Nu: XAU 0,1, XAG 0,01, NAS100/SPX500 1,0. Eerdere tests gebruikten die instrumenten niet.

**Test 20b (vooraf vastgelegd):** precies dezelfde regel en lat op instrumenten buiten de 30: XAUUSD, XAGUSD,
NAS100USD, SPX500USD (5ers-instrumenten met bekende kosten). Gerapporteerd apart en samen met de 30.

### Uitkomst test 20b (goud, zilver, NAS100, SPX500): te weinig trades om iets te zeggen
Regel, `R_t020`: 49 trades, -0,03 / +0,37 / -0,08R (t 0,3). Samen met de 30 (34 instrumenten, 527 trades):
+0,03 (PF 1,05) / +0,03 (PF 1,04) / +0,21R (PF 1,34), t 1,05; met het beheer van de trader +0,05 / +0,05 / +0,22R
(t 1,25). Positief in alle drie de periodes, maar nog niet sterk genoeg (t < 2); de laatste vijf jaar duidelijk beter.

## Test 21 (vooraf vastgelegd, 2026-10-29): test 20 optimaliseren over meerdere assets

Op vraag van de trader. Rooster (`t21_grid.sh`, `test20.py --rev --leg --band`): keerpunt REV 2 / 2,5 / 3 / 4 dag-ATR,
poot LEG 4 / 6 / 8 ATR, slot afwijzingscandle in 0,5-0,786 / 0,382-0,786 / 0,5-0,886, SL-buffer 0,1 / 0,5 ATR,
uitstap -0,2 / -0,27 / -0,65 / helft -0,2 + SL oude top + rest -1, filter geen / week / S/R / week+S/R
(36 x 2 x 4 x 4 = 1.152 combinaties), 34 instrumenten (de 30 + goud, zilver, NAS100, SPX500), één positie per richting.
**Kiezen** (`t21_select.py`): alleen op de helft van de instrumenten (even posities alfabetisch) en alleen 2005-2018;
de combinatie met het hoogste gemiddelde bij >= 150 trades. **Valideren**: precies die combinatie op de andere helft
(2005-2018) en op alle instrumenten 2019-2025. Geslaagd als beide gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.
Let op: 2019-2025 is voor de basisversie (test 20) al gezien; de andere helft van de instrumenten in 2005-2018 is de
zuiverste controle.

### Uitkomst test 21: verworpen
Gekozen op A (17 instrumenten) 2005-2018: zigzag REV 4 / poot 8 ATR, slot 0,382-0,786, geen filter, SL 0,1 ATR,
doel -0,65: training +0,27R (PF 1,38, t 2,3, 305 trades). Validatie: B 2005-2018 +0,14R (PF 1,19, t 1,2, 299
trades); alle instrumenten 2019-2025 **-0,08R** (PF 0,89, 252 trades); samen +0,04R (t 0,5) -> lat niet gehaald.
72% van de 864 combinaties met >= 150 trades was positief op de training, maar de uitkomsten wisselen per helft van
de instrumenten en per periode (bv. week+S/R-filter: A +0,03 tot +0,24R, B -0,04 tot -0,10R, 2019-25 +0,10 tot
+0,36R). Verschillen van ±0,1R bij ±300 trades vallen binnen het toeval (standaardfout ±0,07R).

## Vooruit meten (vanaf 2026-10-29)

`research/strategy/scan.py`: test 20 op de 28 forexparen met dagdata t/m gisteren (opgeslagen candles + Yahoo),
schrijft `docs/scan/scan_<datum>.md` (actieve setups met zone, SL, TP; trades sinds 2026-01-01) en vult
`docs/scan/journal.csv` aan (datum waarop elke trade voor het eerst gezien is). Vastgelegd: de vooruit-meting telt
alleen trades met `gezien` >= 2026-10-29 en `regel = ja` (weekstructuur + week/maand-S/R), volledig op -0,2; na 50
afgesloten trades beoordelen (gemiddeld > 0, PF >= 1,05). Eerste scan: 2026 tot nu, regel = ja: 9 afgesloten,
+2,30R (4 winnaars); zonder regel (alle 49): 33 afgesloten, -10,53R. Let op: GBPNZD-candle van 28 okt. 2026 bij Yahoo
heeft een piek tot 2,3809 (broker: 2,3769).

## Test 22 (vooraf vastgelegd, 2026-10-30): walk-forward-optimalisatie

`research/strategy/t22_walkforward.py`: elk jaar 2010-2025 de beste combinatie (uit de 1.152 van test 21, >= 100
trades in het venster) kiezen op de jaren ervóór, en dan dat jaar handelen. Vier varianten, niets meer: venster 5
jaar of alle eerdere jaren; beste combinatie of top 5 samen. Geslaagd als een variant over 2010-2025 gemiddeld > 0
met PF >= 1,05, in >= 10 van de 16 jaren positief, en t (op de jaarsommen) >= 2,0. Bij vier varianten is één
toevallige treffer mogelijk: een geslaagde variant moet ook in de andere drie in dezelfde richting wijzen.

### Uitkomst test 22: niet geslaagd
Alle vier varianten licht positief, geen haalt de lat (2010-2025, uit de steekproef):
venster 5 jaar top 1: +0,03R/trade, PF 1,04, 9/16 jaren positief, t 0,27; top 5: +0,04R, PF 1,05, 9/16, t 0,40;
alle eerdere jaren top 1: +0,09R, PF 1,12, 7/16, t 1,23 (koos meestal de grootste poten of week+S/R met beheer);
top 5: +0,05R, PF 1,07, 9/16, t 0,70. Rond 25 trades per jaar over 34 instrumenten -> ±+1 tot +2R per jaar,
dus ±1-2% per jaar bij 1% risico. Optimaliseren levert uit de steekproef een kleine, onzekere plus op; geen
bruikbare voorsprong voor een prop-challenge.

## Test 20w (vooraf vastgelegd, 2026-10-30): test 20 op de weekgrafiek

De trader handelt ook weekly (EURUSD W1, AUDCAD W1). `test20.py --tf W1`: precies test 20 (zigzag 3 ATR / poot 6 ATR,
afwijzingscandle met slot 0,5-0,786, SL 0,1 ATR voorbij 1, doel -0,2 en beheer), maar op weekcandles; de
structuurfilter gebruikt de maand-zigzag. Regel `wk_struct == 1 & htf_sup`, één positie per richting, 34
instrumenten, 2005-2025. Geslaagd als elke periode (2005-14, 2015-20, 2021-25) gemiddeld > 0 met PF >= 1,05 en
samen t >= 2,0. Daarnaast: D1 + W1 samen gerapporteerd.

### Uitkomst test 20w (weekgrafiek): verworpen
Regel, `R_t020`: 2005-14 +0,05R (58 trades) / 2015-20 -0,41R (37) / 2021-25 -0,22R (17); t -1,1. Te weinig trades
(0,2 per paar per jaar) en negatief sinds 2015.

## Test 23 (vooraf vastgelegd, 2026-10-30): kleine poot, TP op de volgende structuur (GBPNZD maart 2026)

Trade van de trader: kleine poot die een BoS breekt, instap 2,256 op de terugtest, SL onder de grote bodem (2,23295),
TP op de volgende BoS 2,32089 (RR 2,8). `test19.py` (poten met break + retest in de pocket, instap op de dag-
afwijzingscandle) met extra kolommen: SL onder de laagste low van de 20 candles voor de instap (- 0,1 ATR), TP = de
dichtstbijzijnde eerdere swingtop boven de poot die nog intact is (`R_struct`); context `wk_struct`, `htf_sup` als
test 20. Controle: de motor vindt de GBPNZD-poot van maart 2026 niet (andere poten); test toch zoals vastgelegd.
Regel `wk_struct == 1 & htf_sup`, `R_struct`, één positie per richting (op de eigen uitstap), 34 instrumenten,
2005-2025. Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.

### Uitkomst test 23: verworpen
Regel, `R_struct` (mediane RR 4,0): 2005-14 -0,03R (611 trades) / 2015-20 -0,21R (395) / 2021-25 -0,21R (274),
t -2,0. Zonder filter ook negatief (-0,03 / -0,13 / -0,12R).

## 5ers-challenge op test 20 (`research/strategy/prop_t20.py`)

526 trades (regel week + S/R, beheer van de trader, 34 instrumenten), +0,08R gemiddeld, ±25 per jaar; jaarsommen
wisselend (-11R tot +23R). Challenge (+8% dan +5%, -10% statisch; dagverlies niet gemodelleerd), start elke maand
2006-2024: 1% risico: 38% geslaagd, 47% breach, mediaan 617 dagen tot geslaagd; 1,5%: 28% / 68%, 314 dagen;
2%: 27% / 73%, 247 dagen. Volledig op -0,2 bij 1,5%: 23% / 72%. Slaagkans lager dan de breach-kans bij elk risico:
niet geschikt om challenges mee te kopen.

## Met de trend mee: welke maand/week-definitie? (`t20_trend.py`, beschrijvend - trades al bekend)

Test 20-trades (grote dagpoten, 34 instrumenten), beheer van de trader, één positie per richting, per periode:
- geen trendfilter: +0,02 / -0,00 / +0,11R
- weekstructuur (HH/HL): +0,03 / -0,01 / +0,20R
- maandstructuur (HH/HL): +0,02 / -0,03 / +0,21R
- **maandslot boven/onder het 10-maands gemiddelde: +0,04 / +0,05 / +0,10R** (1.093 trades; het meest stabiel)
- **weekstructuur + maandgemiddelde: +0,05 / +0,04 / +0,14R**
- week + maand gemiddelde eens: +0,05 / -0,05 / +0,31R (weinig trades)
- **tegen de maandtrend: -0,12 / -0,13 / +0,12R**
Conclusie: de maandtrend (eenvoudig: slot boven/onder het 10-maands gemiddelde) is het nuttigste "met de trend mee";
tegen de maandtrend handelen kost geld. De voorsprong blijft klein (+0,05R, t ±1,2).
Vooruit-meting (vastgelegd 2026-10-30): de scanner toont nu ook `maandtrend` (mee/tegen); naast de regel van test 20
wordt "regel + maandtrend mee" apart bijgehouden en op dezelfde manier beoordeeld (na 50 afgesloten trades).

### Regel + maandtrend (beschrijvend, 34 instrumenten, beheer van de trader)
regel (week + S/R): +0,05 / +0,05 / +0,22R, samen +0,08R PF 1,13 t 1,25 (526 trades)
regel + maandtrend mee: +0,07 / +0,09 / +0,15R, samen +0,09R PF 1,14 t 1,28 (483 trades) - iets stabieler
+ max. één positie per munt: +0,02 / +0,23 / -0,33R (166 trades) - slechter, niet gebruiken
5ers (start elke maand 2006-2024) met regel + maandtrend: 1% risico 40% geslaagd / 50% breach; 0,75%: 30% / 55%;
1,5%: 32% / 65%; 2%: 26% / 69%. Jaarsommen -13R tot +24R. Nog altijd meer breach dan geslaagd.

## Heranalyse van de trades van de trader (`trader_profile.py`, 2026-10-30)

9 dagtrades van de trader (EURUSD jun-25, EURAUD dec-25, GBPAUD nov-25, NZDCAD okt-23 / feb-24 / jun-24 / feb-25,
GBPNZD mrt-26 / aug-26) opgemeten met dezelfde kenmerken als 12.406 motor-setups (test 19/23 + test 20):
poot in ATR, duur poot en terugval, tijdverhouding correctie/impuls, snelheid, instapdiepte, afstand start tot
maand/week-niveau, niveau in de zone, BoS, beweging vooraf, maand/week-trend, weekstructuur, poot t.o.v. de range.
Uitkomst: op geen enkel kenmerk liggen de trades van de trader apart; ze zijn verspreid over de hele verdeling
(poot 1,2-10 ATR = percentiel 0-92; maandtrend 4x mee, 5x tegen; BoS 5 van 9; niveau in de zone 5 van 9). Enige
constante: instapdiepte 0,61-0,69 (limiet rond 0,65); bij de motor maakt instapdiepte geen verschil
(0,5-0,6: -0,01R; 0,6-0,65: +0,01R; 0,65-0,7: -0,06R).
De 50 meest gelijkende motor-setups per trade: gemiddeld -0,25 tot +0,52R, winnend 32-52% (gemiddeld ±+0,07R, ±40%).
Dat alle 9 voorbeelden winnen terwijl gelijkaardige setups ±40% winnen (kans 0,4^9 ≈ 0,03%) wijst op selectie van de
voorbeelden (getoonde winnaars) of op een oordeel van de trader dat niet in deze kenmerken zit; om dat te vinden zijn
ook de verliezende of overgeslagen setups nodig.

## Video's opnieuw: wat is gecodeerd en wat niet

Video 8 (FTMO): maand-S/R met reactiegeschiedenis (ja, Levels), impuls/correctie (ja, poten/zigzag), week 3-poot
correctie (nee), week -0,27 + bullish indicatiecandle (nee), dag momentum vertraagt (test 10), institutionele candle
(nee), dag H&S dan bullish N (deels: N in test 8/12, H&S-volgorde nee), 4u 3 candles respecteren de zone (test 8),
bijschalen (nee), TP -0,27 + BE (ja).
Video 9: week 4 fases (test 12), trendwissel pas na de tweede lower low (nee), fib wick -> body (ja, test 11),
zone 0,618 tot eerste structuur of 1 (test 8), TP -0,27 anders -0,68 (ja), 4u: vertraging (test 8), 4u bullish N (nee),
4u inverse H&S (test 14), BE (ja), correctie = veel tijd weinig prijs (tijdverhouding: geen verschil, zie hierboven).

## Test 24 (vooraf vastgelegd, 2026-10-30): alleen instappen na bevestiging in de golden pocket / 0,786

De trader: "Alleen een positie openen nadat er reactie is in goldenpocket of 0-786 die wijst op een bounce en
continuation. Soms valt de prijs ook onder de 1/1, dan is het belangrijk dat het daar liquiditeit heeft genomen van
een eerdere low. En dan opnieuw kijken op de 4u chart naar confirmation dat het toch nog een bullish N wordt."
`research/strategy/test24.py`: grote dagpoten (test 20); op 4u: aanraking 0,618; bevestiging = na de laagste 4u-low
sinds de aanraking (L*) een 4u-slot boven de laatste bevestigde 4u-swingtop van vóór L* (structuurbreuk = begin van
het tweede been van de N); instap op dat slot, alleen bij RR >= 1,5 tot -0,2. Onder fib 1 alleen geldig als de prijs
de liquiditeit van een eerdere dag-low heeft genomen (sweep), ongeldig > 1 ATR eronder. SL 0,1 ATR onder L*.
Controle (Yahoo-data tot nu): GBPNZD aug-26 bevestigd 4 aug (+6,5R op -0,2), NZDCAD jun-24 bevestigd 30 juli (+9,2R),
EURUSD/NZDCAD/GBPNZD samen ±+14R over 2023-2026 (veel -1R, enkele grote winnaars; RR 2-9).
**Beslissend: `R_t020`, één positie per richting, 34 instrumenten (4u-data), 2005-2025.** Geslaagd als elke periode
(2005-14, 2015-20, 2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: met de context van
test 20 (regel, maandtrend), beheer, en per kenmerk van de bevestiging (sweep, diepte L*, tijd tot bevestiging) -
ontdekking op 2005-2014, controle op 2015-2025.

### Uitkomst test 24: verworpen (beslissende regel), ontdekking van de bevestiging
Alle bevestigde setups, `R_t020`: 2005-14 -0,03R (809) / 2015-20 -0,15R (374) / 2021-25 +0,08R (294), t -0,7;
mediane RR 4,5, winnend ±19%. Met regel (week + S/R): -0,00 / -0,25 / +0,35R; met maandtrend: -0,12 / -0,12 / +0,10R.
Ontdekking op 2005-2014 (809 trades) per kenmerk van de bevestiging: snelle bevestiging (<= 15 4u-candles na de
aanraking) +0,19R tegen trage (> 47) -0,22R; sweep van een eerdere low onder 1 en dan bevestiging +0,40R (40 trades);
diepte L*, instapdiepte en RR zonder duidelijke lijn.
**Vastgelegd voor controle op 2015-2025:** (a) `conf_bars <= 15`, (b) `swept`. Geslaagd als gemiddeld > 0 met
PF >= 1,05 en t >= 2,0 op 2015-2025.
Controle 2015-2025: (a) snelle bevestiging -0,08R (157 trades, PF 0,91); (b) sweep -0,07R (38 trades, PF 0,91).
Beide verworpen: de voorsprong van 2005-2014 houdt niet stand.

## Video 10 ("Liquidity Pockets") en video 11 ("Liquidity Flows"), 2026-10-30

`research/videos/video10`, `research/videos/video11`. Video 11: breakaway candles (sterke candles die een sleutelniveau
doorbreken) zijn de belangrijkste candles. Breekt de markt weg van de key high, dan wordt de low eronder niet verwacht
genomen te worden: bounce op het sleutelniveau / golden pocket zoeken. Lukt het wegbreken niet en valt de prijs terug,
dan eerst de liquiditeit nemen van de higher low die de impuls startte (= start van de poot, fib 1); pas daarna, met
een setup (breakaway candles / N), long; doelen -0,25 / -0,65. Video 10: intraday (15 min / 1 u), indexen - hoog en
laag van de vorige New York-middagsessie (13:30-16:00 NY) als liquiditeit; neemt de prijs de high maar breekt hij niet
weg, dan de low als doel (en omgekeerd).

## Test 25 (vooraf vastgelegd): breakaway of niet (video 11) op de bevestigde trades van test 24

Per poot: `breakaway` = een dagcandle in de poot met body >= 1 dag-ATR die sluit voorbij de vorige swingtop (hoogste
high van de 40 dagen voor de start). Regel: (breakaway en de reactie-low blijft boven fib 1, `l_fib <= 1`) of (geen
breakaway en de reactie-low nam fib 1, `l_fib > 1`). `R_t020`, één positie per richting, 34 instrumenten, alle drie de
periodes (geen ontdekking). Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.

### Uitkomst test 25: verworpen
Regel video 11, `R_t020`: 2005-14 -0,05R (437) / 2015-20 -0,19R (202) / 2021-25 +0,40R (161), t 0,1.
Delen: breakaway + reactie binnen 1: -0,08 / -0,18 / +0,42R; geen breakaway + fib 1 genomen: +0,45 / +0,09 / +0,03R
(maar 43 trades); geen breakaway + binnen 1 (volgens de video vermijden): -0,01 / -0,05 / -0,37R.
In 2021-2025 maakt breakaway een groot verschil (+0,42 tegen -0,37R), daarvoor niet.

## Test 26 (vooraf vastgelegd, 2026-10-30): video 10 "Liquidity Pockets" intraday

`research/strategy/test26.py`, SPX500 (15 min, 2015-2026) en NAS100 (15 min tot 2022). Per dag: high/low van de
vorige New York-middagsessie (13:30-16:00 NY) = liquiditeit. Neemt de prijs de high en sluit een 15-min-candle terug
onder de high (geen breakaway) -> short, SL boven de sweep-high (+ 0,1 x de sessierange), doel de low; omgekeerd long.
Eerste trigger van de dag, vóór 15:00, RR >= 1, uit op doel/SL/16:00. Kosten per symbool. Beslissend: alle trades.
Geslaagd als elke periode (2015-18, 2019-22, 2023-26) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.
Gerapporteerd: met/tegen de dag-bias (slot vorige dag boven/onder 20-daags gemiddelde).

### Uitkomst test 26: verworpen (kosten)
Alle trades: 2015-18 -0,80R (1.501) / 2019-22 -0,21R (1.514) / 2023-26 -0,36R (706); met dag-bias even slecht.
Bruto (zonder kosten) wel licht positief in 10 van 12 jaren (+0,04 tot +0,24R), maar de stop is klein (mediaan
3-20 indexpunten) en de kosten (SPX500 2,4, NAS100 5 punten heen en terug) kosten 0,2-1,0R per trade.
**Test 26b (vooraf vastgelegd):** alleen trades met een risico van minstens 10x de kosten (kosten <= 0,1R). Zelfde
lat.
Uitkomst 26b: verworpen - 251 trades: -0,04 / -0,08 / -0,09R (t -0,9). De trades met een grotere stop (vooral 2020-22)
zijn ook bruto niet winstgevend; het bruto voordeel van de kleine trades verdwijnt in de kosten.

## Scanner test 24 (`scan24.py`, 2026-10-30)

Test 24 (4u-bevestiging in de golden pocket / 0,786, sweep onder 1) op de 28 forexparen met dag- en 4u-data tot nu
(Yahoo na half december 2025). `docs/scan/scan24_<datum>.md` (wachtende setups met het 4u-niveau dat bevestigt;
trades sinds 2026-01-01) en `docs/scan/journal24.csv`. Eerste scan, 2026: alle 45 trades (42 afgesloten) -1,5R op
-0,2 (9 winnaars); met de regel van test 20 (week + S/R): 11 trades, +15,0R (4 winnaars). Breakaway komt in de
Yahoo-data van 2026 bijna niet voor (1 van 45; in de backtest ±50%); dat kenmerk is in de live-scan nog niet
betrouwbaar.

## Test 27 (vooraf vastgelegd, 2026-10-30): alleen handelen als de strategie zelf recent werkt

Elke test is positief in 2021-2025 en zwak daarvoor. Is dat vooraf te zien? Regel: een trade alleen nemen als de
laatste 20 afgesloten trades van dezelfde regel (alle instrumenten; afgesloten vóór de vuldag) samen >= 0R waren.
Toegepast op (a) test 20 regel (week + S/R), `R_m_top_1`; (b) test 24 (4u-bevestiging) + regel, `R_t020`; één positie
per richting. Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.

### Uitkomst test 27: verworpen
(a) test 20 regel: zonder filter +0,05 / +0,05 / +0,22R; met filter -0,05 / +0,03 / +0,10R (t 0,0).
(b) test 24 + regel: zonder -0,00 / -0,25 / +0,35R; met +0,11 / -0,84 / +0,16R (t 0,1).

## Terug naar de basis: werken de S/R-niveaus wel? (`sr_quality.py`, 2026-10-30)

Elke maandeinde 2005-2025, 30 instrumenten: niveaus (punt in de tijd) binnen 3 week-ATR van de prijs; eerste
aanraking op de dag binnen 63 dagen; "houdt" = 1 dag-ATR terug weg voor een slot 0,5 ATR erdoor (binnen 20 dagen).
Vergeleken met dezelfde niveaus 1,5 week-ATR verschoven (nep-niveaus). Aandeel dat houdt, echt vs verschoven:
huidig (wick-tikken, onze methode) 71,0% vs 70,9% (+0,1 pp) - niet beter dan een willekeurige lijn;
swing (week-swings) 71,5 vs 70,6; cluster (>= 2 week-swings samen) 71,8 vs 70,0 (+1,8 pp, beste);
rolwissel (gebroken swing, "Breaker/KEY") 71,5 vs 70,7; body (opens/sloten) 71,4 vs 70,3; maand-swings 71,1 vs 70,0.
Per periode cluster +2,9 / +1,0 / +1,2 pp. Conclusie: onze S/R-methode deed niets; geen enkele definitie geeft
meer dan ±2 procentpunt boven een willekeurige lijn. Niveaus met meerdere reacties (cluster) zijn de beste keuze.

## Test 28 (vooraf vastgelegd): de regel van test 20/24 met cluster-S/R in plaats van de oude S/R

`htf_sup_c` = een cluster-niveau (>= 2 week-swings van de laatste 2 jaar binnen 0,25 week-ATR, punt in de tijd bij
de vulling) tussen fib 1 en de instap. Regel `wk_struct == 1 & htf_sup_c`, één positie per richting:
(a) test 20 met `R_m_top_1`; (b) test 24 met `R_t020`. Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en
samen t >= 2,0.

### Uitkomst test 28: verworpen
(a) test 20, cluster-S/R + week: +0,08 / -0,07 / +0,19R (t 0,9) - niet beter dan met de oude S/R (+0,05 / +0,05 /
+0,22R). (b) test 24: -0,07 / -0,32 / +0,46R (t -0,2). Een betere S/R-definitie verandert de uitkomst niet: het
S/R-filter voegt in beide gevallen weinig of niets toe (cluster in de poot of niet: geen vast verschil).

## Video 13 ("TradeRecap EUR/JPY - EUR/USD") en test 29 (vooraf vastgelegd, 2026-10-30)

`research/videos/video13`: intraday shorts EURUSD en EURJPY. De prijs neemt de high van vorige week (liquiditeit),
breekt dan op 15/5 min de "key higher low" en hij short in de fair value gap; doelen: evenwicht van gisteren,
weekopening, New York-middernacht; helft dicht, SL in winst; monthly open als order block.
**Test 29** (`research/strategy/test29.py`), 4 uur, 28 paren, 2005-2025: high van vorige week genomen, dan een
4u-slot onder de laatste 4u-swing-low van vóór de sweep-high -> short; SL boven de sweep-high (+ 0,1 dag-ATR); doel
weekopening (anders midden van vorige week), RR >= 1; uit bij doel, SL of einde van de week; omgekeerd voor longs.
Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.
Uitkomst test 29: verworpen - 1.244 trades: -0,08R (PF 0,82) / -0,07R (PF 0,81) / +0,02R (PF 1,08), t -2,3; bruto
(zonder kosten) -0,01R, dus geen voorsprong (kosten ±0,04R). Shorts na PWH-sweep -0,08R, longs na PWL-sweep -0,03R.

## Video 12 ("Forex HTF Analysis") en test 30 (vooraf vastgelegd, 2026-10-30)

`research/videos/video12`: maand eerst (trendlijnen, S/R met meerdere bounces/rejections, flips; deviaties mogen),
week (H&S, W/M, 5 golven; fib op de laatste impuls, reactie in de golden pocket, doelen -0,25 / -0,65), dag (fair
value gaps, order block = eerste tegengestelde candle links van de FVG; OB in de golden pocket), 4 uur (inverse H&S
op het niveau). Nieuw en concreet: de fib vaak **van body naar body** i.p.v. wick ("if you take the fib from the low
you never touch the golden pocket; if you take it from the body, it is clearly where we see that bounce").
**Test 30:** precies test 20 (grote dagpoten, afwijzingscandle, SL 0,1 ATR voorbij 1, regel week + S/R, beheer), maar
`--fib body`. Beslissend `wk_struct == 1 & htf_sup`, `R_m_top_1`, één positie per richting, 34 instrumenten.
Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: alle setups en R_t020.

### Uitkomst test 30 (body -> body): regel +0,13 / +0,07 / -0,07R (t 0,9), niet geslaagd; volgens de trader is dit
ook niet de juiste manier: "body to wick, altijd".
**Test 30b (vooraf vastgelegd):** fib 1 = body van de start-candle, 0 = wick van het uiterste; SL voorbij de wick van
de start (0,1 ATR); verder exact test 20. Zelfde regel, beheer en lat.

### Uitkomst test 30b (fib body -> wick): beste en stabielste versie tot nu toe, lat net niet gehaald
Regel (week + S/R), beheer (`R_m_top_1`): 2005-14 +0,12R (PF 1,20, 231 trades) / 2015-20 +0,07R (PF 1,10, 129) /
2021-25 +0,09R (PF 1,14, 82); t 1,41. Elke periode positief met PF >= 1,05; alleen t >= 2,0 niet gehaald.
Volledig op -0,2: +0,09 / +0,05 / +0,09R (t 1,1). Ook alle grote poten zonder filter nu positief in elke periode
(+0,05 / +0,04 / +0,01R). Ter vergelijking wick -> wick (test 20): +0,05 / +0,05 / +0,22R; body -> body: +0,13 /
+0,09 / -0,05R. Body -> wick geeft de gelijkmatigste uitkomst over de drie periodes.
5ers (test 30b, regel + beheer, 442 trades, ±21 per jaar, +0,10R gemiddeld; jaarsommen -14R tot +22R): 1% risico
26% geslaagd / 58% breach (mediaan 530 dagen); 1,5% 27% / 64%; 0,75% 19% / 59%. Stabieler per trade, maar te weinig
rendement per jaar (±+2R) voor +8% binnen redelijke tijd.

## Test 31 (vooraf vastgelegd, 2026-10-30): meer continuation-trades

De trader: "We zijn in de goede richting. Nu meer continuation trades." Test 30b (fib body -> wick, regel, beheer) met
(1) kleinere poten: zigzag-keerpunt na 2 dag-ATR, poot >= 4 ATR (in plaats van 3 / 6) - meer N's binnen een trend;
(2) alleen continuation: de poot eindigt voorbij het vorige keerpunt aan dezelfde kant (HH bij long, LL bij short)
(`cont`). Beslissend: `cont & wk_struct == 1 & htf_sup`, `R_m_top_1`, één positie per richting, 34 instrumenten.
Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: zonder S/R-eis, en
continuation binnen de grote poten (3 / 6).

### Uitkomst test 31: beslissende regel niet geslaagd
Kleinere poten (2 / 4), continuation + regel, `R_m_top_1`: 682 trades (1,0 per paar per jaar): +0,13 / -0,07 / +0,09R
(t 1,2) -> 2015-20 negatief. Zonder continuation-eis (alleen regel): 734 trades, +0,17 / -0,00 / +0,01R (t 1,7).
Grote poten (3 / 6), continuation + regel: 417 trades (0,6 per paar per jaar), +0,16 / +0,03 / +0,14R (PF 1,26 /
1,04 / 1,23, t 1,6) - de beste per trade, maar minder trades. Meer poten (kleiner) geeft ±1,7x zoveel trades, maar de
periode 2015-2020 wordt dan ±0 of negatief.

## Test 32 (vooraf vastgelegd, 2026-10-30): 4u-instap binnen de continuation-context (fib body -> wick)

De trader koos "2 en 3": (2) de 4u-bevestiging van test 24 als instap binnen de dagcontext van test 31, (3) de
scanners omzetten. `test24.py --fib bodywick`: grote dagpoten (3 / 6); fib 1 = body van de startcandle, 0 = wick van
het einde (zoals 30b). Op 4u: aanraking 0,618 van die fib; bevestiging = na de laagste 4u-low sinds de aanraking (L*)
een 4u-slot boven de laatste 4u-swingtop van vóór L*; instap op dat slot als RR >= 1,5 tot -0,2; SL 0,1 dag-ATR
onder L*. Onder de body van fib 1 maar boven de wick van de startcandle is toegestaan; onder die wick alleen na een
sweep van een eerdere dag-low (liquiditeit), ongeldig > 1 ATR onder die low (zonder eerdere low: 0,1 ATR onder de wick).
Kolom `cont` als test 31.
**Beslissend: `cont & wk_struct == 1 & htf_sup`, `R_m_top_1` (half op -0,2, stop naar de oude top, rest -1), één
positie per richting, 33 instrumenten met 4u-data, 2005-2025.** Geslaagd als elke periode (2005-14, 2015-20,
2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: zonder S/R-eis, regel zonder continuation,
`R_t020`, en de vergelijking met de dag-afwijzingscandle van 30b / 31 (zelfde poten).

### Uitkomst test 32: verworpen
Continuation + regel, `R_m_top_1`: 368 trades, +0,10 / -0,50 / -0,32R (PF 1,12 / 0,45 / 0,65, t -1,1); `R_t020`
+0,06 / -0,46 / -0,23R. Zonder S/R-eis: +0,07 / -0,26 / +0,18R (t 0,1). Alle grote poten: +0,08 / -0,16 / -0,03R.
Winnend slechts 11-22%: de krappe stop onder de 4u-reactie-low (L*) wordt te vaak geraakt voordat -0,2 komt. Op
dezelfde poten is de dag-afwijzingscandle met de stop voorbij de wick van fib 1 (30b / 31: +0,16 / +0,03 / +0,14R)
duidelijk beter. Conclusie: de 4u-bevestiging als instap met een krappe stop kost meer dan ze oplevert; de 4u-grafiek
blijft nuttig voor timing, maar de stop hoort voorbij de structuur (de wick van fib 1), niet onder de 4u-reactie.

## Test 33 (vooraf vastgelegd, 2026-10-30): de beste dagversie op nieuwe instrumenten (holdout)

Meer trades via meer markten, niet via lossere regels. Test 31 grote poten (fib body -> wick, 3 / 6, dag-
afwijzingscandle, SL voorbij de wick van fib 1), regel `cont & wk_struct == 1 & htf_sup`, `R_m_top_1`, één positie
per richting, op instrumenten die nooit in een test of optimalisatie zaten: AUDSGD CADSGD CHFZAR EURCZK EURHUF EURNOK
EURPLN EURSEK EURSGD EURTRY EURZAR GBPPLN GBPSGD GBPZAR NZDSGD SGDCHF SGDJPY TRYJPY USDCZK USDHUF USDMXN USDNOK USDPLN
USDSEK USDSGD USDTHB USDTRY USDZAR ZARJPY BTC_USD ETH_USD (31). Weggelaten: gekoppelde munten (HKD, DKK, CNH) en
dubbele reeksen (olie, SPX500_USD). Kosten per kant in basispunten van de prijs bij instap: TRY/THB 10, ZAR/MXN 4,
BTC 5, ETH 6, SGD/NOK/SEK/PLN/CZK/HUF 3 (±3-10x de majors).
Geslaagd als elke periode (2005-14, 2015-20, 2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0 op deze 31;
daarnaast samen met de 34 van test 31 (65 instrumenten).

### Uitkomst test 33: holdout positief in elke periode, lat (t >= 2) net niet gehaald
31 nieuwe instrumenten, continuation + regel, `R_m_top_1`: 307 trades, +0,03 / +0,18 / +0,08R (PF 1,05 / 1,31 /
1,13, t 1,0); `R_t020` +0,02 / +0,23 / +0,15R (t 1,25). Elke periode > 0 met PF >= 1,05, maar t < 2 -> niet
geslaagd. Wel belangrijk: de regel, gekozen op de 34 oude instrumenten, blijft positief op markten die nooit getest
zijn (ook na 3-10x hogere kosten) - geen teken van overfitting.
Samen 65 instrumenten, continuation + regel: 724 trades (0,5 per paar per jaar), +0,10 / +0,09 / +0,11R (PF 1,16 /
1,15 / 1,19, t 1,85) - de stabielste uitkomst tot nu toe. Continuation zonder S/R-eis: 1072 trades, +0,07 / +0,14 /
+0,10R (t 2,05, beschrijvend, niet vooraf als beslissend vastgelegd).

## Handelsuniversum van de trader (2026-10-30): geen exoten
De trader: geen exoten; wel forex (majors + crosses), goud, zilver, olie, indices, BTC, ETH. Universum = de 34 van
test 31 + BTC_USD, ETH_USD, XBR_USD (Brent, vanaf 2015) = 37 (`t37_` = koppelingen naar t31g_ / t33_). Pipwaarde XBR
gecorrigeerd (0,01). Continuation + regel, `R_m_top_1`: 439 trades, +0,16 / +0,02 / +0,11R (PF 1,26 / 1,03 / 1,18,
t 1,47) - gelijk aan test 31; zonder exoten valt de extra stabiliteit van test 33 weg (de exoten droegen vooral
2015-20).
5ers (`prop_t20.py --prefixes t37_ --rule "cont & wk_struct == 1 & htf_sup"`): ±21 trades per jaar, +0,10R gemiddeld
(±+2R per jaar). Geslaagd 28% / breach 56% bij 1% risico (mediaan 526 dagen tot geslaagd); 1,5%: 26% / 65%; 2%:
21% / 77%. De voorsprong per trade is echt maar te klein en te traag voor +8% en +5% vóór -10%.

## Test 34 (vooraf vastgelegd, 2026-10-30): dezelfde N op de 4u-grafiek (meer trades)
De trader: "21 trades per jaar kan niet, moet zeker 1000 zijn". Op de dagpoten is het maximum ±1,9 grote poten per
instrument per jaar (alle setups, zonder filter): 37 x 1,9 = ±70 per jaar; meer kan alleen op een lager tijdsframe.
`test20.py --tf H4 --fib bodywick`: zelfde regels op 4u-candles (zigzag na 3 4u-ATR, poot >= 6 4u-ATR, fib body ->
wick, afwijzingscandle met slot 0,5-0,786, SL 0,1 ATR voorbij de wick van fib 1, verlopen na 40 candles); structuur
`wk_struct` nu van de dagzigzag (2 / 4), S/R van week/maand, maandtrend als voorheen. 37 instrumenten van de trader.
**Beslissend: `cont & wk_struct == 1 & htf_sup`, `R_m_top_1`, één positie per richting.** Geslaagd als elke periode
(2005-14, 2015-20, 2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0. Gerapporteerd: aantal trades per jaar,
kosten in R, de andere regels.

### Uitkomst test 34: verworpen - op 4u is de N negatief, ook vóór kosten
Continuation + regel, `R_m_top_1`: 1148 trades (±55 per jaar), -0,09 / -0,07 / +0,01R (t -1,5). Alle grote 4u-poten:
7097 trades (±340 per jaar), -0,06 / -0,01 / -0,06R (t -2,9). Mediane kosten maar 0,024R; bruto gemiddeld -0,02R:
het is niet de kost, de setup heeft op 4u geen voorsprong. Dezelfde regels op de dag: +0,16 / +0,02 / +0,11R.
De voorsprong zit in de grote (dag-)structuur; meer trades via een lager tijdsframe vernietigt hem.

## Test 35 (vooraf vastgelegd, 2026-10-30): kleinere dagpoten, ±4 trades per week
De trader: "Er zijn wekelijks toch zeker 4 trades op basis van de daily." Met de grote poten (3 / 6 ATR) bestaan er
maar ±70 setups per jaar op 37 instrumenten. Test 30b (fib body -> wick, dag-afwijzingscandle, SL voorbij de wick van
fib 1, beheer) met kleinere dagpoten: zigzag-keerpunt na 1,5 dag-ATR, poot >= 3 ATR (`t35_`); ook gerapporteerd
1 / 2 (`t35s_`) en 2 / 4. 37 instrumenten van de trader.
**Beslissend: 1,5 / 3, `cont & wk_struct == 1` (continuation met de weekstructuur, zonder S/R-eis om het aantal te
houden), `R_m_top_1`, één positie per richting.** Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen
t >= 2,0. Gerapporteerd: trades per jaar en de andere regels.

### Uitkomst test 35: verworpen - kleinere poten geven het gewenste aantal, maar geen voorsprong
1,5 / 3, continuation + weekstructuur (beslissend): 1679 trades (±80 per jaar), +0,03 / -0,07 / +0,04R (t 0,2).
Alle setups 1,5 / 3: 4106 trades = ±196 per jaar (±3,8 per week, het aantal van de trader), -0,00 / -0,05 / -0,03R.
1 / 2 alle: ±310 per jaar, -0,04 / -0,04 / -0,03R (t -2,1). 2 / 4 met de 37: regel +0,17 / -0,02 / -0,03R.
Lijn over alle tests: hoe kleiner de poot, hoe meer trades en hoe kleiner de voorsprong; alleen de grote poten
(3 / 6) + continuation + regel zijn in elke periode positief (±21 per jaar). Het verschil tussen de ±4 setups per week
van de trader en het mechanische resultaat zit dan in een keuze die niet in de regels staat - alleen te vinden met
de volledige tradegeschiedenis (ook verliezers en overgeslagen setups).

# Opnieuw van nul: strategie uit video 12 ("Forex HTF Analysis"), 2026-10-30

De trader: "Start terug van scratch met de strategy en begin met 12 forex htf analysis." Alles hierboven blijft als
archief; de nieuwe engine (`test36.py`) gebruikt alleen wat video 12 zegt (transcript opnieuw gelezen):
1. **Maand**: trendlijnen en de grote S/R (meerdere bounces / rejections, flips; deviaties mogen). Richting: "we are
   still bearish on the monthly", "we didn't breach any kind of high" -> structuur (HH/HL of LH/LL).
2. **Week**: fib op de laatste impuls, **body -> wick**; reactie in de golden pocket (0,618-0,786); doelen **-0,25**,
   **-0,65**, -1 (vaak op een S/R-niveau). Patronen (H&S, W/M, 5 golven) als context.
3. **Dag**: zelfde fib; **fair value gaps**; **order block = de eerste tegengestelde candle links van de FVG (body)**.
   "Do you notice the golden pocket at the OB? That is why it makes it interesting." -> zone = OB in de golden pocket,
   bij voorkeur op HTF-S/R.
4. **4u / 1u**: alleen timing ("it needs to slow down"), inverse H&S op het niveau; "you don't want to see it below
   your support". Test 32 toonde dat een krappe 4u-stop niet werkt -> hier geen 4u-trigger, de stop achter de structuur.
5. **Liquiditeit**: equal lows/highs, vorige dag/week/maand-high genomen = plaats waar omkeringen gebeuren (context).

## Test 36 (vooraf vastgelegd): OB in de golden pocket (video 12)
`test36.py`, 37 instrumenten van de trader (forex zonder exoten, goud, zilver, olie, indices, BTC, ETH), 2005-2025.
- Poten: zigzag op dagcandles, keerpunt na 2 ATR, poot >= 4 ATR (beslissend); ook op weekcandles (2 / 4) gerapporteerd.
- Fib 1 = body van de startcandle, 0 = wick van het uiterste.
- OB: in de poot een dag-FVG in de richting van de poot (long: low[j+1] > high[j-1], candle j bullish); OB = de laatste
  tegengestelde candle (bearish bij long) in de 5 candles vóór j; zone = de body. Alleen OB's waarvan de body de
  golden pocket (0,618-0,786) raakt; de eerste die de prijs bereikt (hoogste bij long).
- Instap: limiet op de bovenkant van de OB-body, maar niet hoger dan 0,618 (long; short gespiegeld), eerste aanraking
  na de bevestiging van de poot; verlopen na 40 candles; vervalt bij een nieuwe top vóór de instap of een slot voorbij
  fib 1.
- SL: 0,1 ATR voorbij de wick van fib 1 (de structuur). Raakt de instapcandle ook de SL: -1R.
- Uit: beheer van de trader = half op -0,25, stop naar de oude top (in winst), rest op -0,65 (`R_m`); ook vol op -0,25
  (`R_t025`) en -0,65 (`R_t065`). Kosten per instrument.
- Context: hogere structuur (week-zigzag 2 / 4 voor dagpoten, maand voor weekpoten) in de handelsrichting
  (`hi_struct`), maand/week-S/R tussen fib 1 en de instap (`htf_sup`), maandslot vs 10-maandsgemiddelde (`m_ma`).
**Beslissend: dagpoten, `hi_struct == 1 & htf_sup` (alle setups met een OB in de golden pocket), `R_m`, één positie per
richting.** Geslaagd als elke periode (2005-14, 2015-20, 2021-25) gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0.
Gerapporteerd: trades per jaar, zonder OB (limiet op 0,618), zonder context, weekpoten.

### Uitkomst test 36: beslissende regel (dagpoten) verworpen; weekpoten met dag-OB veelbelovend (beschrijvend)
Dagpoten, OB in golden pocket + hogere structuur + S/R, `R_m`: 193 trades (9 per jaar), -0,04 / +0,12 / +0,00R
(t 0,15) -> verworpen. Alle dagsetups: 122 per jaar, +0,02 / -0,06 / -0,09R.
Weekpoten (fib op de week-impuls, OB uit de dag-FVG - zoals de video het eigenlijk doet), beschrijvend:
- alleen OB in de golden pocket: 373 trades (18 per jaar), +0,15 / +0,22 / +0,10R (PF 1,23 / 1,37 / 1,17, t 1,91);
- OB + S/R: 273 trades, +0,10 / +0,31 / +0,20R (t 1,89);
- zonder OB (limiet 0,618): 104 trades, -0,00 / -0,32 / +0,37R -> de OB maakt het verschil op de week;
- hogere (maand)structuur als filter helpt niet (2015-20 negatief).

## Test 36b (vooraf vastgelegd): weekpoot + dag-OB in de golden pocket op een holdout
De regel "weekpoten, alleen OB" (`has_ob`, `R_m`) is gekozen na het zien van de 37 instrumenten. Controle op de 31
exoten van test 33 (niet om te handelen - de trader handelt geen exoten - alleen als onafhankelijke markten die nooit
voor deze regel gebruikt zijn), kosten zoals test 33. Geslaagd als elke periode gemiddeld > 0 met PF >= 1,05 en samen
t >= 2,0 op de 31; daarnaast gerapporteerd: OB + S/R.

### Uitkomst test 36b: holdout positief in elke periode, lat net niet gehaald
29 exoten (BTC/ETH zitten al in de 37), weekpoten, alleen OB, `R_m`: 251 trades, +0,21 / +0,03 / +0,03R (PF 1,34 /
1,04 / 1,05, t 1,40) -> niet geslaagd (2015-20 PF 1,04, t < 2), wel nergens negatief. OB + S/R: +0,18 / +0,02 /
+0,26R (t 1,3). Zoals bij test 33: de voorsprong houdt stand buiten de markten waarop hij gekozen is, maar is klein.
Aantal op de 37 instrumenten van de trader: ±18 per jaar (weekpoten) - de video werkt van week naar dag, en levert
dus weinig setups.

## Test 37 (vooraf vastgelegd, 2026-10-30): + structural frameworks (video 4)
Video 4 ("Lesson 4 structural frameworks"): handel pas na een verschuiving van de marktstructuur - de prijs kan niet
verder dalen, breekt het key level (de laatste lower high) met breakaway-candles = inverse H&S; daarna fib body ->
wick op die impuls, instap in de golden pocket (rechterschouder), SL onder het hoofd, doelen -0,25 / -0,65 / -1, stop
in winst na het eerste doel. Daarna N-patronen (voortzetting) tot 5 golven, "we stay bullish until we have a break of
our key high or key level". Gecodeerd in `test36.py`: `bos` = tijdens de poot een slot (zelfde tijdsframe) voorbij het
vorige keerpunt aan dezelfde kant (het key level); `shift` = dat keerpunt lag zelf lager dan het vorige (de poot draait
een daaltrend = inverse H&S), anders voortzetting.
**Beslissend: weekpoten, `has_ob & bos`, `R_m`, één positie per richting.** Geslaagd als op de 37 instrumenten van de
trader elke periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0, én op de 29 holdout-exoten elke periode > 0.
Gerapporteerd: omkeer vs voortzetting, met S/R, dagpoten, en de voorbeeldtrades van de trader.

### Uitkomst test 37: op de 37 instrumenten geslaagd, holdout net niet (laatste periode)
Weekpoten, OB in de golden pocket + structuurbreuk, `R_m`: 287 trades (14 per jaar), +0,24 / +0,18 / +0,16R (PF
1,39 / 1,29 / 1,26, t 2,15) -> de lat op de 37 instrumenten van de trader is gehaald (eerste keer). Holdout (29
exoten): +0,33 / +0,14 / -0,02R (PF 1,57 / 1,22 / 0,97; 2021-25 maar 22 trades), t 2,12 -> voorwaarde "elke periode
> 0" op de holdout mist in 2021-25 -> formeel niet geslaagd, wel de beste en meest consistente uitkomst tot nu toe.
Omkeer (inverse H&S, eerste N na de breuk): +0,48 / +0,20 / +0,11R (t 2,37); voortzetting: +0,07 / -0,04 / +0,26R.
OB zonder breuk: -0,22 / +0,40 / +0,35R. Dagpoten met breuk: +0,02 / +0,08 / -0,08R -> op de dag werkt het niet.
**Voorbeeldtrades van de trader** (`trader_trades.py`) naast de engine: GBPAUD nov-25 = exact dezelfde dagpoot en
instap (2,04388), maar de engine schrapt hem: op 12 nov prikt een wick 29 pips onder fib 0 (1,99878 -> 1,99588)
vóór de instap; de trader houdt de fib (sweep van de low = liquiditeit) en wordt op 24 nov gevuld. NZDCAD jun-24 =
dezelfde weekpoot met OB + breuk + omkeer, maar de OB-instap (0,822) ligt hoger dan die van de trader (0,814, fib
±0,88) -> -1R in de engine. EURUSD jun-25 (D1) is een kleinere poot dan 2 / 4 ATR. EURAUD dec-25: data eindigt.

## Test 38 (vooraf vastgelegd): een wick voorbij fib 0 is een sweep, geen annulering
Uit de GBPAUD-trade van de trader. `test36.py --sweep`: vóór de instap vervalt de setup pas bij een **slot** voorbij
fib 0; een wick erdoor laat de fib staan. Verder exact test 37. Beslissend: weekpoten, `has_ob & bos`, `R_m`; zelfde
lat (37 instrumenten: elke periode > 0, PF >= 1,05, t >= 2,0; holdout: elke periode > 0). Ook dagpoten gerapporteerd.

### Uitkomst test 38: verworpen (niet beter dan 37)
Weekpoten, sweep toegestaan: +0,23 / +0,10 / +0,13R (t 1,88); holdout +0,31 / +0,09 / -0,07R. Een wick voorbij fib 0
laten staan voegt 14 trades toe maar verlaagt het gemiddelde; test 37 (schrappen bij een nieuwe extreme) blijft.

## Test 39 (vooraf vastgelegd, 2026-10-30): bias van de week, setups op de dag (video 12 + 4 + 3)
De trader: "De eerste video (12) was om trend te vinden, niet echt setups; die vind je in structural frameworks en
fibonacci." Video 3 (fibonacci): fib body -> wick op de impuls die het key level brak; instap rond 0,66 (golden zone
0,618-0,786, bijleggen bij 0,786); SL onder de laatste low ("it cannot go lower than your last low"); half op -0,25,
stop in winst, dan -0,65 / -1. "Each month you can trade with the mindset we are bullish until we hit a key level";
"start on the highest time frame, trade towards the day".
- **Bias (video 12 / 4)**: op weekcandles +1 na een weekslot boven de laatste bevestigde week-swinghigh (zigzag 2 / 4),
  -1 na een weekslot onder de laatste week-swinglow; blijft tot het tegengestelde key level breekt (`hi_bias`).
- **Setup (video 4 / 3)**: dagpoot (2 / 4 ATR) met structuurbreuk (`bos`, test 37) in de richting van de weekbias;
  fib body -> wick; limiet op 0,66 (of de OB-bovenkant als die er is, niet voorbij 0,66); SL 0,1 ATR onder de wick van
  fib 1; half -0,25, stop naar de oude top, rest -0,65 (`R_m`); vervalt bij een nieuwe extreme vóór de instap.
**Beslissend: dagpoten, `hi_bias == 1 & bos`, `R_m`, één positie per richting, 37 instrumenten.** Geslaagd als elke
periode gemiddeld > 0 met PF >= 1,05 en samen t >= 2,0, én op de 29 holdout-exoten elke periode > 0. Gerapporteerd:
trades per week, met OB / S/R, omkeer vs voortzetting, tegen de bias, weekpoten met maandbias.

### Uitkomst test 39: verworpen
Dagpoten met weekbias + structuurbreuk, `R_m`: 1270 trades (60 per jaar, 1,2 per week), +0,22 / -0,08 / -0,05R
(t 1,7) -> 2015-25 negatief. Holdout: +0,01 / +0,18 / +0,12R. Met OB of S/R niet beter. Tegen de weekbias: -0,13 /
+0,09 / -0,21R -> de bias helpt (mee beter dan tegen), maar de dagsetup zelf heeft na 2015 geen voorsprong.
Opvallend (beschrijvend): weekpoten met breuk **tegen** de maandbias: 115 trades, +0,73 / +0,34 / +0,41R (t 3,2) -
een weekbreuk tegen een nog niet gedraaide maandstructuur = de vroege omkeer (inverse H&S) van video 4.

## Test 39b (vooraf vastgelegd): weekbreuk tegen de maandbias, controle op de holdout
`hi_bias == -1 & bos` op weekpoten (entry 0,66, `R_m`), gekozen na het zien van de 37 -> controle op de 29 exoten.
Geslaagd als elke periode > 0 met PF >= 1,05 en samen t >= 2,0.

### Uitkomst test 39b: holdout positief in elke periode, t 1,98 (lat 2,0) -> net niet
29 exoten, weekpoten, breuk tegen de maandbias: 88 trades, +0,42 / +0,04 / +0,88R (PF 1,73 / 1,05 / 3,24, t 1,98).
Samen met de 37: ±203 trades (±10 per jaar), alle periodes positief. Klein in aantal, maar de sterkste en meest
consistente regel tot nu toe, samen met test 37 (weekpoot + OB + breuk).

## Grok-"Blueprint tool" (gedeeld door de trader, 2026-10-30) en test 40 (vooraf vastgelegd)
De tekst zegt zelf dat Grok de video's niet kon bekijken ("standard interpretations ... direct video content access
yielded insufficient details"); de voorbeelden (EUR/CHF 0,9540 -> 0,9840, "YouTube link 6/7") en de "3-candle
Bullish N" zijn verzonnen en wijken af van de video's (video 4: N = impuls, correctie naar de golden pocket, nieuwe
poot; video 3/12: fib body -> wick, doelen -0,25 / -0,65, geen 1,272 / 1,618). Bruikbaar en toetsbaar is de
**volgorde / piramide**: maand-S/R -> maand- en weekstructuur in dezelfde richting -> fib op de week-impuls, dagprijs in
0,618-0,786 -> dag-framework (OB / geflipte S/R in die zone) -> bevestigingscandle op de dag in de richting van de bias
-> instap.
**Test 40**: weekpoten (test 37: breuk van het key level), `test36.py --tf W1 --confirm`: na de aanraking van de
golden pocket instap op het slot van een bevestigingscandle op de dag (in de richting van de poot, slot voorbij de
vorige high/low, nog op of onder fib 0,382). SL 0,1 ATR voorbij de wick van fib 1 (video 3, niet onder de sweep:
test 32). Uit: half -0,25, stop naar de oude top, rest -0,65.
**Beslissend: `htf_sup & hi_struct == 1 & bos & has_ob` (alles in confluentie), `R_m`, één positie per richting, 37
instrumenten.** Geslaagd als elke periode > 0 met PF >= 1,05 en t >= 2,0, én op de 29 holdout-exoten elke periode > 0.
Gerapporteerd: zonder maandstructuur, zonder OB, test 37 met bevestiging i.p.v. limiet.

### Uitkomst test 40: piramide verworpen; test 37 + dagbevestiging is de beste kandidaat
Volledige piramide (S/R + maand- én weekstructuur + fib + OB + bevestiging): 73 trades (3 per jaar), +0,50 / -0,15 /
-0,34R (t 0,85) -> verworpen; de eis "maandstructuur mee" maakt het slechter (zelfde les als test 39: een weekbreuk
tegen een nog niet gedraaide maand is juist de vroege omkeer). Zonder maandstructuur: +0,13 / +0,19 / +0,17R (t 1,5).
**Test 37-regel (weekpoot + breuk + OB) met instap op de dagbevestiging i.p.v. de limiet** (gerapporteerde variant):
37 instrumenten 264 trades (13 per jaar), +0,27 / +0,20 / +0,15R (PF 1,44 / 1,35 / 1,27, t 2,28); holdout 194 trades,
+0,31 / +0,06 / +0,08R (PF 1,53 / 1,09 / 1,13, t 1,83). Dit is de eerste versie die op de 37 de lat haalt én op de
holdout in elke periode positief is - maar het is een variant, niet de vooraf beslissende regel van test 40, dus eerst
vooruit volgen (scanner) vóór geld.

## Screenshots van de trader opnieuw bekeken (2026-10-30) en test 41 (vooraf vastgelegd)
De trader: "Dit is absurd: ±13 per jaar ... Kijk terug naar al mijn setups screenshots." Alle beelden uit het gesprek
opnieuw bekeken (TradingView, 1D): GBPNZD 2026 (2 longs: poot feb-mrt en jun-jul, +2,82R / +3,26R), NZDCAD okt-23
long, feb-24 short, jun-24 long. Gemeenschappelijk:
1. een **dagpoot die een BoS-lijn breekt** (de vorige swing aan dezelfde kant, door de trader als "BoS" getekend);
2. fib body -> wick op die poot, **limiet op 0,66** (oranje lijn; NZDCAD okt-23: 0,8215 - 0,66 x 0,025 = 0,8050 =
   instap 0,80537), SL net voorbij fib 1, **TP -0,2** (soms -0,25 / -0,65);
3. een **weekly S/R-lijn** (horizontaal, meerdere week-reacties) tussen fib 1 en de instap (NZDCAD 0,80772 /
   0,83221).
Frequentie in de screenshots: ±2-3 per paar per jaar, op de **dag** (poten van 3-9 dag-ATR).
**Test 41**: `test36.py --tf D1 --entry 0.66` (dagpoten 2 / 4, breuk `bos`, limiet 0,66 of OB, SL 0,1 ATR voorbij de
wick van fib 1); weekly S/R = cluster van >= 2 week-swingpunten binnen 0,25 week-ATR uit de laatste 2 jaar (beste
S/R-definitie uit `sr_quality.py`), tussen de wick van fib 1 en de instap (`wk_sr`).
**Beslissend: `bos & wk_sr`, `R_t020` (vol op -0,2, zoals in de screenshots), één positie per richting, 37
instrumenten.** Geslaagd als elke periode > 0 met PF >= 1,05 en t >= 2,0, én op de holdout elke periode > 0.
Gerapporteerd: trades per week, met weekbias, beheer `R_m`, en of de 5 screenshot-trades gevonden worden.

### Uitkomst test 41: verworpen
`bos & wk_sr`, `R_t020`: 1116 trades (53 per jaar, 1,0 per week), +0,08 / +0,00 / -0,10R (t 0,3); holdout -0,02 /
+0,06 / -0,09R. Met weekbias: +0,22 / +0,02 / -0,05R.
Naast de screenshots (NZDCAD 2023-24): de engine vindt de poot van de trader in jun-24 (0,8098 -> 0,8496, instap
0,8224), maar schrapt hem omdat de prijs vóór de instap nog een hogere top maakt (0,8519); **de trader verlegt fib 0
naar die nieuwe top** (zijn 0 = 0,8515) en wacht opnieuw op 0,66. Omgekeerd neemt de engine setups die de trader niet
toont (nov-23 short, dec-23 long, apr-24 short: alle -1R).

## Test 42 (vooraf vastgelegd): fib 0 verleggen bij een nieuwe extreme vóór de instap
`test36.py --tf D1 --entry 0.66 --reanchor`: maakt de prijs vóór de instap een nieuwe top (long), dan wordt dat fib 0;
limiet opnieuw op 0,66 van de nieuwe poot (OB vervalt), verlooptijd opnieuw. Verder test 41.
**Beslissend: `bos & wk_sr`, `R_t020`, één positie per richting, 37 instrumenten**; zelfde lat (elke periode > 0, PF
>= 1,05, t >= 2,0; holdout elke periode > 0). Gerapporteerd: alle setups, met weekbias, `R_m`.
