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
