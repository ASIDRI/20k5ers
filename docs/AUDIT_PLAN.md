# Audit: backtest tegenover live, versie per versie

Doel: voor elke belangrijke versie van de bot vaststellen of zijn backtest hetzelfde doet als de
live-bot van die versie zou doen op MT5, op onze eigen historische data. Pas daarna optimaliseren,
en alleen op een motor die aantoonbaar gelijk loopt met live.

Regels voor de hele audit:
- **Geen tijdslimiet** op scans, backtests of optimalisaties (`backtest/run_job.sh`, losgekoppeld, hervatbaar).
- **Niets aan de live-bot veranderen** tijdens de audit. Oude versies worden apart uitgepakt, nooit over de huidige code heen.
- Elke versie heeft een vaste naam (V1, V2, ...) en een vaste commit. Resultaten worden per versie bewaard.
- Elke uitspraak in een rapport verwijst naar een run (map + commando) die je zelf opnieuw kunt draaien.

## Wat er eerder fout ging

Ik heb eerder gezegd dat de backtestmotor (`main_live_bot_backtest.py` + `csv_mt5_simulator.py`) werkte
zoals live. Dat klopte niet. De simulator gaf de **lopende** dag-, week- en maandcandle mee met de
**eindwaarden** van die candle (filter `time < nu`, terwijl de candle om 22:00 UTC opent). De echte
live-bot vraagt aan MT5 alleen **afgesloten** candles (`copy_rates_from_pos(..., 1, ...)`).
De backtest wist dus de toekomst. Ik heb dat pas op 27 oktober gevonden.

Dezelfde filter staat al in de versie van 3 februari (V3), en de oudste motor van januari (V1) lekt ook
(week/maand vanaf de openingstijd, en vullen op de signaalcandle zelf). Fase 1 bestaat om de
referentie zelf eerst te bewijzen, zodat dit niet opnieuw gebeurt.

## Versies

| Naam | Datum | Commit | Wat |
|---|---|---|---|
| V1  | 2026-01-09 | `912d1a2` | Eerste commit. Backtest: `ftmo_challenge_analyzer.py` + `strategy_core.simulate_trades` (D1) |
| V2  | 2026-01-20 | `97de18e` | PR #7, dagelijkse scan na close, uitlijning live/backtest/simulator |
| V3  | 2026-02-03 | `9e6fc4a` | 5-TP exit + Trial 10 parameters. Eerste versie met `main_live_bot_backtest.py` + `csv_mt5_simulator.py` |
| V4  | 2026-02-11 | `147bd0d` | Risico 0,7% "na 3 JPY-stops op 1 dag" (live in gebruik in februari) |
| V5  | 2026-03-22 | `16023cb` | PR #26, optimalisaties van maart, risico 1,1% |
| V6  | 2026-05-19 | `dcd50b6` | PR #31-#34, 50k-account |
| V7  | 2026-07-03 | `d5a9789` | PR #36 |
| V8  | 2026-10-23 | `befa205` | Climb cap live, rapport met de $4M-backtest |
| V9  | 2026-10-27 | `be58da1` | Pariteitsfixes live/backtest (nog met het candle-lek) |
| V10 | huidig     | branch    | Lek dicht (`HTF_NO_LOOKAHEAD=1`), live timing in de backtest |

## Fases

### Fase 0: Inventaris (klaar te zetten, geen runs)
- Elke versie uitpakken in een eigen map (`backtest/output/audit/V<n>/code`), met de data van die versie.
- Per versie vastleggen: welke backtestmotor, welke parameters, welke live-bot, welke candles de live-bot opvraagt.
- Controleren dat de koersdata gelijk is aan nu (voor V3 gedaan: D1/W1/MN/H4 byte voor byte gelijk).

### Fase 1: De referentie bewijzen ("live op onze data")
De referentie is de echte `main_live_bot.py` van een versie, aangestuurd door een nagebootste MT5
(`live_replay.py`): klok in 15-minutenstappen, MT5 geeft alleen afgesloten candles, orders worden op M15
gevuld met spread, SL/TP zoals een broker. Voor die referentie gebruikt wordt, moet hij slagen voor:
1. **Candle-test:** op elk tijdstip ziet de bot geen enkele candle die nog niet gesloten is (automatische controle op elke opvraging).
2. **Klok-test:** scans op de servertijden van de live-bot (00:15 server, maandag 01:00), rollover en nachtelijke de-risk op de juiste uren.
3. **Broker-test:** bekende scenario's met vooraf berekende uitkomst (limiet gevuld/niet gevuld, SL en TP in dezelfde candle, gaps, gedeeltelijke TP's).
4. **5ers-test:** dagbasis = max(equity, saldo) bij de dagreset, dagverlies en totaalverlies zoals op het dashboard.
5. **Echte live-vergelijking (als er afschriften zijn):** MT5-historie van een periode waarin de bot live draaide, naast de replay van dezelfde versie en periode.

### Fase 2: Elke versie meten
Per versie, op vaste testperiodes (eerst 2023, daarna 2019 en 2024):
- **A:** de backtest van die versie precies zoals hij toen was.
- **B:** dezelfde backtest, met als enige wijziging: alleen afgesloten candles.
- **C:** de live-bot van die versie in de referentie van fase 1.

Vergelijking per versie: rendement, aantal trades, winrate, profit factor, max dagverlies, max totaalverlies,
en **trade per trade** (zelfde symbool, richting, instap binnen 1 candle). A tegenover C zegt of die
versie ooit "zoals live" was; B tegenover C zegt wat er overblijft na het dichten van het lek.

### Fase 3: De backtestmotor die we voortaan gebruiken
- Keuze: de bestaande motor (gerepareerd) of de replay zelf als motor. Doorslaggevend is de meting, niet de verwachting.
- Acceptatie: op minstens 3 testjaren komt minstens 95% van de trades overeen met de referentie, en het verschil in rendement en max verlies is klein (doel: binnen 10% relatief).
- Deze test komt in `w5_acceptance.py`, zodat een toekomstige wijziging die de motor laat afwijken meteen faalt.

### Fase 4: Optimaliseren op de gekeurde motor
- Alleen met de motor uit fase 3, zonder tijdslimiet.
- Optimaliseren op een deel van de jaren, beoordelen op jaren die de optimizer nooit zag (walk-forward).
- Geen parameters meer die op een paar weken data gekozen zijn (V3 was geoptimaliseerd op 1-21 april 2024).

### Fase 5: Rapport
Per versie A/B/C in één tabel, wat de beste versie is na het dichten van het lek, en wat live mag draaien.

## Bevindingen tot nu toe

| # | Bevinding | Gevolg |
|---|---|---|
| B1 | Geen echte live-trades in de repo. `challenge_state.json` van het live-account: $19.951 op 12 januari, 0 trades. Alle `tradr_live.log` in de geschiedenis zijn backtestlogs (datums 2023). | "Werkte live" is uit de repo niet te bewijzen of te weerleggen: MT5-afschriften nodig. |
| B2 | V3 t/m V9 hebben in de simulator hetzelfde filter `time < nu` (lopende candle met eindwaarden). De live-bots van V2 t/m V9 vragen afgesloten candles (`copy_rates_from_pos(..., 1, ...)`). V1 vraagt `..., 0, ...` (de lopende candle zoals hij op dat moment is). | Geen enkele oude backtest was "zoals live". Fase 2 meet hoeveel dat uitmaakt. |
| B3 | Mijn regel van 27/10 voor "afgesloten candle" was fout voor de forex-maandcandles (die staan op de laatste dag van de maand): de bot zag de maand van twee maanden terug. | Vervangen door `candle_avail.py`; oude regel nog op te roepen met `HTF_NO_LOOKAHEAD=crude`. Alle cijfers zonder lek worden opnieuw gemeten. |
| B4 | De data gebruikt drie stempelconventies door elkaar. Goud, zilver en NAS100: D1/W1/MN komen niet overeen met hun eigen M15 (andere bron). Bij forex en goud staan de M15-rijen dubbel. | Datacontrole als vaste stap in fase 1. Deze 3 symbolen apart rapporteren. |
| B5 | `live_replay.py` laadde `backtest/src/strategy_core.py` in plaats van de live `strategy_core.py` (zoekpad-volgorde). | Hersteld, met een controle die faalt als het opnieuw gebeurt. De replay-cijfers van 27/10 worden opnieuw gemeten. |
| B6 | Huidige parameters: TP4 = 2,5R ligt **onder** TP3 = 2,75R. | Na te kijken in fase 2 (C-run van V10). |
| B7 | V3 (de 5-TP "Trial 10") is geoptimaliseerd op 1-21 april 2024: drie weken data. | Geen basis voor live. |

## Gereedschap

| Script | Fase | Wat |
|---|---|---|
| `backtest/src/audit_versions.py` | 0 | `list`, `extract`, `inventory`, `prepare` per versie |
| `backtest/src/candle_avail.py` | 1 | Wanneer een candle gesloten is, per bestand; gedeeld door huidige en oude motoren |
| `backtest/src/audit_referee_tests.py` | 1 | `candles`: geen lek, geen onnodige vertraging, kruiscontrole met M15 |
| `backtest/src/live_replay.py --code-root` | 1/2 | De live-bot van elke versie op de nagebootste MT5 (run C) |
| `backtest/src/audit_run.py` | 2 | Wachtrij A/B/C per versie en jaar, hervatbaar; `table` geeft de vergelijking |

## Voortgang

| Fase | Status |
|---|---|
| 0 | V1 t/m V9 uitgepakt en geïnventariseerd. Koersdata van V3 byte voor byte gelijk aan nu. |
| 1 | Test 1 (candles) geslaagd: 1.200 gevallen, 0 lek, 0 onnodige vertraging; M15-kruiscontrole klopt behalve bij goud/zilver/NAS100 (B4). Tests 2-4 volgen. Test 5 wacht op MT5-afschriften. |
| 2 | Runner klaar; proefruns V3 A/B/C. Daarna V3-V10, 2023, zonder tijdslimiet. |
| 3-5 | Nog niet gestart |
