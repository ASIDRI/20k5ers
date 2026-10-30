# Neely Elliott Wave: botstrategie en bouwplan

Bron: "Mastering Elliott Wave" van Glenn Neely (versie 2.0, 1990), de scan die je in Drive hebt staan (hoofdstuk 1 t/m 5 zijn aanwezig). Paginanummers hieronder (bijv. 3-22) verwijzen naar de boekpagina's.

Dit document is geschreven zodat (a) een LLM-agent of ontwikkelaar het als specificatie kan gebruiken en (b) jij er stap voor stap een geautomatiseerde bot van kunt bouwen. Bij elke regel staat of het **uit het boek komt** of een **ontwerpkeuze van mij** is. Ontwerpkeuzes zijn bedoeld om te testen en aan te passen, niet als waarheid.

---

## 0. Kort en eerlijk

1. **Het boek zegt zelf dat volledig automatiseren moeilijk is** (hoofdstuk 1, "Difficulty", blz. 1-6). Sommige situaties vragen om "abstract denken" of gewoon afwachten tot een telling zichzelf onthult. Een bot kan dus niet alles tellen. Het ontwerp hieronder lost dat op met een **hypotheselijst**: de bot handelt alleen als er genoeg bewijs is voor precies één lezing, en blijft anders buiten de markt. Veel "geen trade" is hier een feature.
2. **Hoofdstuk 6 t/m 12 zitten niet in je pdf.** Daar staan de bevestigingsregels (Post-Constructive Rules of Logic), Compaction, Degree, complexe correcties (dubbele/driedubbele), Power Ratings, geavanceerde Fibonacci en "Missing Waves". Zonder die hoofdstukken kan de bot de **standaardpatronen** (impuls, zigzag, flat, triangle) herkennen en verhandelen, maar niet de complexe. Zie sectie 12.
3. **De scan heeft OCR-fouten** (bijv. "e3" i.p.v. "c3", "13" i.p.v. "L3", "ml" i.p.v. "m1", "251.8%" dat waarschijnlijk 261.8% is). Elke tabel die je in code zet moet je naast het originele boek leggen.
4. **Geen rendementsbelofte.** Het boek bevat geen backtests. Alles wat Neely over nauwkeurigheid zegt is zijn eigen claim. Behandel dit als een hypothese die je zelf moet bewijzen met walk-forward tests en papertrading. Dit is geen financieel advies.
5. Ik heb de meest hard-codeerbare delen al in Python gezet en getest: `neely_core.py` + `test_neely_core.py` (9 tests, allemaal groen). Dat is laag 1 tot 5 van de architectuur hieronder, zonder de grote opzoektabel van sectie 6.

---

## 1. Architectuur in lagen

```
Laag 0  Data           1 prijs per tijdseenheid, juiste bron, sessiegrenzen
Laag 1  Monowaves      pivots, Rule of Proportion, Rule of Neutrality
Laag 2  Retracement    m0, m2 bepalen, Rule (1-7) + Conditie (a-f) + Categorie (i-iii)
Laag 3  Structure      Pre-Constructive Rules of Logic -> lijst Structure labels per monowave
Laag 4  Positionering  Position Indicators reduceren de lijst tot 1 label, Pattern Isolation
Laag 5  Series         Structure Series -> Similarity and Balance -> kandidaat-patroon
Laag 6  Validatie      Impulse / Flat / Zigzag / Triangle regels, conditionele regels, scoring
Laag 7  Hypotheses     meerdere lezingen tegelijk, kiezen of niet handelen
Laag 8  Strategie      setups, entry, stop, targets
Laag 9  Risico/uitvoer positiegrootte, kill-switch, orderafhandeling
```

Rolverdeling: **laag 0 t/m 7 is deterministische code.** Een LLM mag er hooguit (a) de opzoektabel van laag 3 helpen coderen en (b) achteraf een telling in gewone taal uitleggen. Laat een LLM nooit zelf getallen toetsen of een telling "voelen"; dat is waar hallucinaties de strategie stilletjes kapotmaken.

---

## 2. Laag 0: data (boek blz. 2-6 t/m 2-12)

Boekregels:
- Gebruik **geen slotkoersen** en geen bar-charts met high en low tegelijk. Per tijdseenheid mag er maar **één** prijs zijn, zodat je weet in welke volgorde dingen gebeurden.
- Opties: (a) één prijs = (high + low) / 2 per periode, of (b) twee prijzen per periode (high en low) **in de volgorde waarin ze optraden**. Optie (b) is volgens het boek de beste.
- Gebruik **cash-data** (spot/index), geen futures: futures hebben "deterioration" door carry en zijn manipuleerbaarder.
- Volg elke markt in **één land/sessie**. Voor 24-uursmarkten (FX, goud) werkte alleen een vast sessievenster goed, niet het samenvoegen van wereldsessies.
- Voor indices: laat de eerste 10 tot 15 minuten weg zodat alle aandelen open zijn.
- Het boek verwacht minimaal drie grafieken per markt: dagelijks, wekelijks, maandelijks.
- Geschikte markten: breed gedragen (brede indices, goud, grote valuta). Slecht: losse aandelen en weergevoelige grondstoffen.

Implementatie:
- `midpoint_series()` en `ordered_series()` staan in `neely_core.py`.
- **Ontwerpkeuze:** haal tick- of 1-minuutdata op, bouw daar zelf de gekozen tijdseenheid uit (bijv. H1 of H4) in optie (b). Config: `session_utc_window`, `drop_first_minutes`, `timeframes = [base, higher, highest]`.
- **Ontwerpkeuze:** gebruik een rollend venster van maximaal **20 monowaves** (blz. 3-22 adviseert dit expliciet) en start het venster niet op een historisch hoogste of laagste punt (blz. 3-1: grote keerpunten gedragen zich abnormaal).

---

## 3. Laag 1: monowaves

**Definitie (blz. 2-2):** een monowave loopt van een richtingsverandering tot de volgende. Zodra één datapunt lager (bij stijging) of hoger (bij daling) is dan het vorige, is de monowave klaar, hoe klein ook. Absoluut verticale beweging bestaat niet (er is altijd minstens één tijdseenheid).

Code: `find_monowaves(prices)`. Gelijke opeenvolgende punten tellen als doorlopen van de huidige golf; de "dot" komt op het laatste punt.

### 3.1 Rule of Proportion (blz. 3-3 t/m 3-9)
Het boek schaalt de grafiek zo dat een **Directional** beweging van linksonder naar rechtsboven een vierkant vult (ongeveer 45 graden, marge 25% per kant). **Non-Directional** beweging (zijwaarts) vult ongeveer de helft van het vierkant.
- Directional: de eerste monowave wordt meestal niet meer dan 61.8% teruggenomen; de periode eindigt als een monowave in de richting van de centrale lijn voor meer dan 100% wordt teruggenomen.
- Non-Directional: de eerste monowave wordt altijd meer dan 61.8% teruggenomen; elke fase (op hooguit één uitzondering na) minstens 61.8%; de periode eindigt als de prijs de hele range met 161.8% of meer overschrijdt.
- **Voor de bot:** je tekent niet, dus normaliseer. Schaal prijs en tijd van het venster zodat de range van het venster en de tijdsduur van het venster allebei 1 zijn (`price_scale = max - min`, `time_scale = aantal punten`). Gebruik die schaal voor de hoek in 3.2. Dit is een vertaling van mij; het boek gaat uit van handmatige schaling.

### 3.2 Rule of Neutrality (blz. 3-9 t/m 3-13)
Probleem: sommige monowaves lopen bijna horizontaal. Dan kan het eindpunt van de vorige golf verschuiven (Aspect 1) of kan één lange golf in drie worden gesplitst (Aspect 2).

Kandidaat: na schaling is de hoek van de golf **kleiner dan 45 graden** (`apply_neutrality_flags()`). Hoe dichter bij horizontaal, hoe waarschijnlijker.

**Aspect 1** (horizontale actie tussen twee tegengestelde golven; één cirkel past eromheen):
- Beëindig de eerste golf aan de **verre rechterkant** van de horizontale actie, dus de dot schuift naar rechts, ook als dat iets onder de hoogste of boven de laagste prijs is.
- Niet toepassen als de golf, waarvan de dot zou verschuiven, minder dan 61.8% wordt teruggenomen en de markt daarna het eind van die golf overschrijdt.
- Niet toepassen als het nieuwe eindpunt meer dan 38.2% van die golf van het oorspronkelijke eind af zou liggen.

**Aspect 2** (horizontale actie tussen twee golven in dezelfde richting; twee cirkels nodig):
- Alleen als de horizontale actie in dezelfde richting drijft. Als ook maar één datapunt in tegengestelde richting beweegt (lager dan het vorige bij een stijging), mag Aspect 2 niet.
- Duurt de horizontale periode **meer dan één tijdseenheid**, dan **moet** Aspect 2 worden toegepast: split in drie monowaves.
- Duurt het precies één tijdseenheid, dan is het optioneel. Gebruik de variant waarbij alternation van Intricacy verbetert, het Complexity-niveau tussen patronen verbetert of een "missing wave" verdwijnt; anders negeren.
- Zolang je die laatste afweging nog niet kunt maken: behandel **beide** versies als aparte hypotheses (sectie 9).

---

## 4. Laag 2: Rules of Observation en Retracement Rules (blz. 3-14 t/m 3-31)

Elke monowave wordt tijdelijk **m1** genoemd; daarvoor komt **m0**, daarna **m2** (en m3, m4, m(-1), m(-2) enzovoort).

**m2** is alle actie na m1 tot de high of low van m1 doorbroken wordt:
- Als de high (bij een stijgende m1) wordt doorbroken: m2 eindigt op het laagste punt tussen het eind van m1 en die nieuwe high.
- Als de low van m1 wordt doorbroken tijdens m2: m2 eindigt bij de eerste omkering omhoog na die doorbraak.
- m2 mag dus uit 1, 3, 5 of meer monowaves bestaan. m1 zelf moet een monowave zijn (of een gecompacteerd patroon).

**m0** wordt op dezelfde manier achterwaarts in de tijd bepaald (spiegelbeeld). De figuren 3-20b en 3-22 zijn in de scan slecht leesbaar; mijn implementatie (`_m0_start`) is een logisch spiegelbeeld en staat gemarkeerd als **te verifiëren**. Is er te weinig data, dan is m0 onvolledig en zijn Rule en Conditie "voorlopig".

Alle metingen gaan van dot tot dot. Meet **prijs**, tenzij de tekst expliciet tijd noemt.

### 4.1 Rule-identificatie (m2 / m1)

| Rule | m2 als % van m1 |
|------|-----------------|
| 1 | onder 38.2% |
| 2 | 38.2% tot onder 61.8% |
| 3 | precies 61.8% (met marge, zie 4.3) |
| 4 | boven 61.8% tot onder 100% |
| 5 | 100% tot onder 161.8% |
| 6 | 161.8% tot en met 261.8% |
| 7 | boven 261.8% |

### 4.2 Conditie-identificatie (m0 / m1)

| Rule | a | b | c | d | e | f |
|------|---|---|---|---|---|---|
| 1 | < 61.8% | 61.8% tot < 100% | 100% tot en met 161.8% | > 161.8% | | |
| 2 | < 38.2% | 38.2% tot < 61.8% | 61.8% tot < 100% | 100% tot en met 161.8% | > 161.8% | |
| 3 | < 38.2% | 38.2% tot < 61.8% | 61.8% tot < 100% | 100% tot < 161.8% | 161.8% tot en met 261.8% | > 261.8% |
| 4 | < 38.2% | 38.2% tot < 100% | 100% tot < 161.8% | 161.8% tot en met 261.8% | > 261.8% | |
| 5, 6, 7 | < 100% | 100% tot < 161.8% | 161.8% tot en met 261.8% | > 261.8% | | |

**Rule 4 heeft daarnaast een Categorie** op basis van m3 / m2: `i` = 100% tot < 161.8%, `ii` = 161.8% tot en met 261.8%, `iii` = boven 261.8%.

Notatie: `R-4b-ii` = Rule 4, Conditie b, Categorie ii.

Code: `rule_id`, `condition_id`, `category_id`, `classify_monowave` (getest, inclusief de grensgevallen "inclusive").

### 4.3 Tolerantie (blz. 3-34)
- "Ongeveer 61.8%" betekent in de praktijk ongeveer **58% tot 66%** (ongeveer 4 procentpunt marge).
- "Bijna" of "dichtbij" in de tekst betekent **binnen 10%** van de genoemde verhouding.
- Als alle voorwaarden van een regel kloppen op één na, en die ene wijkt maar een klein beetje af, dan geldt de regel toch (Exception Rule, hoofdstuk 9, niet in je pdf). Implementeer dit als een score-aftrek, geen harde uitsluiting.
- **Tijdsvergelijkingen zijn letterlijk.** "m1 (plus één tijdseenheid) wordt in dezelfde tijd of minder volledig teruggenomen" betekent: `tijd(terugname) <= tijd(m1) + 1`. Geen marge.
- In de code is `TOL_FIB = 0.04` configureerbaar en wordt alleen op de 61.8%-grens (Rule 3) toegepast. Breid dat uit naar de andere grenzen als je dat wilt, maar test het.

---

## 5. Laag 3: Pre-Constructive Rules of Logic (blz. 3-32 t/m 3-60)

Dit is de **grote opzoektabel**: ongeveer 26 pagina's die per Rule, Conditie (en Categorie) vertellen welke **Structure labels** een monowave krijgt. Het boek wil dat je dit met de hand per golf doorloopt; een bot kan dit als data-gedreven regelmotor.

### 5.1 De labels
- `:5` = impulsief (met de trend van één groter niveau), `:3` = corrigerend.
- Met positie-indicator: `:F3` (first three), `:c3` (center three), `x:c3` (center three als x-wave), `:sL3` (second to last three), `:L3` (last three), `:5` (vijf), `:s5` (special five), `:L5` (last five).
- Haakjes: `(...)` = lagere waarschijnlijkheid, `[...]` = zeldzaam of zeer onwaarschijnlijk.

### 5.2 Startlijst per Rule (blz. 3-34 e.v.)
Als een golf geen context heeft (eerste golf op de grafiek) of er geen conditie van toepassing is, zet je de hele lijst:

| Rule | Lijst |
|------|-------|
| 1 | `:5 / (:c3) / (x:c3) / [:sL3] / [:s5]` |
| 2 | `:5 / (:sL3) / [:c3] / [:s5]` |
| 3 | `:F3 / :c3 / :s5 / :5 / (:sL3) / [:L5]` |
| 4a | `:F3 / :c3 / :s5 / [:sL3]` |
| 4b | `:F3 / :c3 / :s5 / (:sL3) / (x:c3) / [:L5]` |
| 4c | `:c3 / (:F3) / (x:c3)` |
| 4d | `:F3 / (:c3) / (x:c3)` |
| 4e | `:F3 / (x:c3) / [..]` (laatste item onleesbaar in de scan, verifiëren) |
| 5 | `:F3 / :c3 / :5 / :L5 / (:L3)` |
| 6, 7 | elke Structure is mogelijk; gebruik de beschreven voorwaarden of val terug op de Position Indicator-reeksen |

(Deze kopregels zijn uit de scan gelezen; "c3" staat in de OCR vaak als "e3". Controleer ze tegen het boek.)

### 5.3 Hoe de regels per Conditie werken
Onder elke Conditie staan alinea's die allemaal dezelfde vorm hebben:
`ALS <voorwaarden op prijs, tijd, vorm van omliggende golven> DAN <label toevoegen / label schrappen / markering op m0, m2 of midden van m1 zetten>`.

De eerste zin van een alinea is de belangrijkste; klopt die niet, ga naar de volgende alinea. Alle voorwaarden binnen één zin moeten gelden. Soms plaatst de regel labels aan het einde van m0, m2 of op een "verborgen" punt in het midden van m1 (een missing x-wave). Dat zijn geen drukfouten.

### 5.4 Coderen als data (aanbevolen)
Maak een JSON- of YAML-bestand met één object per alinea. Voorbeeld (eigen formulering van één regel, met pagina-verwijzing, geen letterlijke bronzin):

```json
{
  "id": "R1.b.01",
  "source_page": "3-35",
  "rule": 1, "condition": "b",
  "when": [
    {"op": "ratio_between", "a": "m(-1)", "b": "m0", "lo": 1.0, "hi": 1.618},
    {"op": "not_exceeds_end", "wave": "m4", "of": "m0"}
  ],
  "then": [
    {"add_label": {"wave": "m1", "label": ":s5"}},
    {"mark": {"wave": "m2", "label": "x:c3?"}}
  ],
  "base": [{"add_label": {"wave": "m1", "label": ":5"}}]
}
```

Voorgestelde predicaten (de **vocabulaire** waarmee je alle alinea's kunt uitdrukken):

| Predicaat | Betekenis |
|-----------|-----------|
| `ratio(a,b)` | prijslengte a gedeeld door b |
| `time(a)` | aantal tijdseenheden |
| `approx(x,y)` | binnen 10% ("bijna", "dichtbij") of Fibonacci-marge |
| `retraced_fully_within(a, by, plus_one_unit)` | a wordt volledig teruggenomen binnen evenveel of minder tijd dan a kostte (letterlijk, zie 4.3) |
| `retraced_at_least(a, pct)` / `retraced_less_than` | percentage terugname |
| `shares_price_range(a,b)` | prijsbereiken overlappen |
| `longer_and_more_vertical(a,b)` | groter in prijs én steiler (prijs/tijd) |
| `shortest_of(a; set)`, `longest_of(a; set)` | vergelijking binnen drie of meer golven |
| `count(mX)` | aantal monowaves in m0 of m2 (1, 3, 5, meer dan 3) |
| `breaks_trendline(wave, through=[A,B])` | trendlijn door twee eindpunten wordt gebroken |
| `returns_to_start_within(frac_time)` | markt keert terug naar begin van een reeks binnen x% van de tijd |
| `first_three_monowaves_retrace(m2, pct)` | voor m2 uit meer dan drie monowaves |

Elke regel krijgt: `id`, `source_page`, `when` (alle voorwaarden = AND), `then` (acties), en optioneel `base` (het standaardlabel dat vooraf wordt geplaatst). De motor loopt in boekvolgorde per alinea; schrap- en toevoeg-acties werken op een kopie van de labellijst.

**Aanpak om dit werk te beperken:** codeer eerst Rules 1 t/m 5 (de meeste echte monowaves vallen daar in), laat 6 en 7 eerst op de volledige lijst vallen en finaliseer ze met de Position Indicator-reeksen. Ik kan dit voor je uitschrijven, regel voor regel, met jou als controleur tegen het boek.

### 5.5 Reassessment van gecompacteerde patronen
Na Compaction (hoofdstuk 7, niet in je pdf) wordt een patroon opnieuw als één golf behandeld, om "missing waves" op te sporen. Bevat een gecompacteerd patroon zijn eigen beginpunt-overschrijding (blz. 3-68, fig. 3-36), dan is de basisstructuur altijd `:3`, wat de Pre-Constructive regels ook zeggen.

---

## 6. Laag 4: Position Indicators en Pattern Isolation (blz. 3-60 t/m 3-68)

Doel: per monowave de lijst terugbrengen tot **één** label, daarna de grenzen van patronen vinden.

### 6.1 Eigenschappen per label
- **`:F3`**: begint een reeks, volgt op een `x:c3`, of staat tussen twee `:5`'s. Twee `:F3` naast elkaar betekent dat bij de tweede een nieuw (kleiner) patroon begint.
- **`:c3`**: nooit begin of eind van een reeks. Toegestane reeksen o.a. `F3-c3-c3-c3`, `F3-c3-5`, `F3-c3-L5`. Kan `x:c3` worden, andersom niet.
- **`x:c3`**: verbindt standaardcorrecties tot een complexe correctie. Nooit begin of eind. Komt na een voltooid standaardpatroon en voor een volgend.
- **`:sL3` / `:L3`**: horen bij Terminal of Triangle. `:sL3` heeft altijd een `:L3` direct erna; samen zijn ze de laatste twee van vijf opeenvolgende `:3`'s. Een `:L3` mag klein zijn en moet dan snel worden teruggenomen.
- **`:5`**: eerste `:5` van een reeks mag niet meer dan 61.8% worden teruggenomen en de markt moet daarna het einde overschrijden.
- **`:s5`**: werkt als een `:L5` maar zonder de omkeerbevestiging; komt vooral in complexe correcties voor; vereist `5-F3` of `F3-c3` ervoor.
- **`:L5`**: einde van een groter patroon (kan meerdere graden tegelijk beëindigen). Minimale bevestiging: de trendlijn door het eind van m(-2) en m0 wordt gebroken binnen de tijd van de `:L5` plus één tijdseenheid of minder. Het label ervoor moet `:F3` of `:c3` zijn.
- Verbinder-notatie: `-` = zelfde standaardpatroon, `++` = x-wave tussen twee standaardpatronen.

De volledige "toegestane buren"-reeksen staan op blz. 3-61 t/m 3-64; ze zijn in de scan leesbaar maar met ruis. Codeer ze als een tabel `allowed_neighbors[label] = [(voor, na, voorwaarde)]`.

### 6.2 Pattern Isolation (blz. 3-65)
1. Loop van links naar rechts; zoek de eerste golf met **alleen** `:L5` of `:L3` (of beide) als label. Omcirkel het eind (een patroon eindigt hier waarschijnlijk, vaak gevolgd door een scherpe beweging).
2. Tel **drie** Structure labels terug. Is dat een golf met één label in `{:F3, x:c3, :L3, :s5, :L5}`: stop, mogelijk begin. Anders verder terug tot je er een vindt.
3. Tel de golven tussen de twee omcirkelde punten. Even aantal: verder terug zoeken. Oneven: ga door naar Series.
4. Raak je onderweg een eerder gedoteerd (bevestigd) punt, dan begon het patroon daar, óf dat punt is het eind van een gecompacteerd patroon van gelijke Degree.
5. Er moeten minstens **drie** golven (of golfgroepen) tussen twee punten zitten, anders integreer je de basis-structuur van het eerdere punt.
6. Herhaal vanaf de volgende `:L5`/`:L3`.

---

## 7. Laag 5: Structure Series en Similarity (blz. 4-1 t/m 4-8)

### 7.1 Toegestane reeksen (figuur 4-3)
Standaard (voor beginners):

| Patroon | Reeks |
|---------|-------|
| Impulsion (trending) | `:5 - :F3 - :5 - :F3 - :L5` |
| Zigzag | `:5 - :F3 - :L5` |
| Flat | `:F3 - :c3 - :L5` |
| Triangle | `:F3 - :c3 - :c3 - :sL3 - :L3` |
| Terminal | dezelfde reeks als Triangle |

De Triangle-reeks is dubbelzinnig: of het een Triangle of een Terminal Impulse is volgt uit de **Essential Impulse Construction Rules** (sectie 8.1): voldoet de actie daaraan, dan is het een Terminal; zo niet, een Triangle.

Niet-standaard (complex): `:3 ++ x:c3 ++ :3` (dubbel), `:3 ++ x:c3 ++ :3 ++ x:c3 ++ :3` (driedubbel), met regels voor de grootte van de x-wave. Dat hoort bij hoofdstuk 8 en valt in de MVP buiten scope (zie sectie 12).

Een gecompacteerd patroon (alleen basislabel `:3` of `:5`) mag elk wettig gepositioneerd label van dezelfde Class vertegenwoordigen.

Werk volgorde: begin met de groep die de **minste prijs en tijd** kost.

### 7.2 Rule of Similarity and Balance (blz. 4-3)
Twee aangrenzende golven zijn kandidaat voor dezelfde Degree als de kleinste **minstens 1/3 van de grootste** is in **prijs of in tijd** (één van de twee volstaat). Voldoen ze aan geen van beide, dan kunnen ze niet direct tot één patroon worden verbonden; eerst moeten kleinere golven eromheen worden gegroepeerd. Code: `similar(w_a, w_b)`. Let op: voldoen aan de regel bewijst niet dat de Degree gelijk is.

### 7.3 Zigzag "DETOUR" test (blz. 4-8)
Zie je een zigzag-reeks, controleer dan altijd of de twee labels ervoor er samen met de zigzag een **impuls** van kunnen maken. Is dat zo, test dan eerst de impuls. Voldoet die niet aan alle regels, laat die twee labels vallen en test de zigzag. Voldoet die ook niet, sla dat stuk over tot de omgeving duidelijker is.

### 7.4 Complexity-regel (blz. 3-69)
Aangrenzende patronen mogen niet meer dan **één Complexity Level** uit elkaar liggen (bijv. Level 1, 2, 1 mag; 1, 2, 4 niet). Zonder hoofdstuk 7 kun je dit alleen benaderen via het aantal compacties in een patroon.

---

## 8. Laag 6: Patroonvalidatie (hoofdstuk 5)

### 8.1 Impulse: Essential Construction Rules (blz. 5-2, absoluut)
Een groep van vijf segmenten is alleen impulsief als **alle** volgende gelden:

1. Vijf aangrenzende segmenten die aan een Trending- of Terminal-reeks voldoen.
2. Drie ervan (1, 3, 5) bewegen in dezelfde richting.
3. Golf 2 neemt golf 1 nooit volledig terug.
4. Golf 3 is langer dan golf 2.
5. Golf 4 neemt golf 3 nooit volledig terug.
6. Golf 5 is minstens **38.2%** van golf 4 (korter dan golf 4 = "5th wave failure").
7. Golf 3 is nooit de kortste van 1, 3 en 5.

**Extension Rule (litmus test, blz. 5-4):** de langste van 1, 3, 5 moet minstens **161.8%** van de op één na langste zijn. Twee zeldzame uitzonderingen: (1) golf 1 is de langste, net onder 161.8% van golf 3, en golf 3 eindigt niet meer dan 61.8% voorbij het eind van golf 1; (2) golf 3 is de langste maar onder 161.8% van golf 1 en golf 5 is korter dan golf 3 (zeldzame Terminal). In `impulse_check` staat uitzondering 1 achter de vlag `allow_exceptions`, uitzondering 2 vraagt interne Terminal-structuur en zit er niet in.

Voldoet het niet aan één regel: de actie is een correctie (of je telling begint verkeerd, of de golven hebben niet dezelfde Degree).

**Conditionele regels** (blz. 5-5 t/m 5-12), dienen als score, niet als harde uitsluiting:
- **Alternation** tussen golf 2 en 4: minstens één van prijs, tijd, severity (hoeveel van de vorige golf wordt teruggenomen), intricacy (aantal onderdelen), constructie (flat, zigzag, triangle enz.). Ontbreekt alternation helemaal, dan is dit meestal een complexe correctie met een verborgen x-wave in golf 3.
- **Rule of Equality:** de twee niet-verlengde van 1, 3, 5 neigen naar gelijkheid in prijs en/of tijd of een 61.8%-verhouding. Prijs weegt zwaarder; vooral bij golf-3-extensie.
- **Overlap Rule:** *Trending*: golf 4 komt niet in het prijsbereik van golf 2. *Terminal*: golf 4 **moet** gedeeltelijk in het bereik van golf 2 komen (en de actie is 3-3-3-3-3).
- **Channeling:** de 0-2 trendlijn mag door geen enkel deel van golf 1 of 3 worden gebroken (golf 2 mag hem even raken). Wordt hij verbroken terwijl de prijs nog in de golf-2-zone zit, dan is golf 2 nog niet klaar (het eerste punt was slechts golf a van golf 2). Daarna de 2-4 trendlijn: nieuwe high zonder breuk van de 2-4 lijn = vijfde golf bezig; breuk vóór een nieuwe high = golf 4 is nog bezig.
- **Fibonacci-verwachting** per extensie:
  - Golf 1 verlengd: golf 3 = 61.8% van golf 1 en golf 5 = 38.2% van golf 3 (meest voorkomend), of omgekeerd.
  - Golf 3 verlengd: golf 1 is gelijk aan, 61.8% of 161.8% van golf 5; golf 3 is meer dan 161.8% van golf 1.
  - Golf 5 verlengd: golf 3 is meestal 161.8% van golf 1; golf 5 is vaak 161.8% van de beweging van het begin van golf 1 tot het eind van golf 3, gerekend vanaf het eind van golf 3 of golf 4.

### 8.2 Flats (3-3-5) (blz. 5-16 t/m 5-19)
Minimum: golf b neemt minstens **61.8%** van a terug; golf c is minstens **38.2%** van a.

Classificatie op de b-golf, gemeten tegen de high en low van a:

| b als % van a | Naam b | Variant |
|---------------|--------|---------|
| 61.8% tot 80% | Weak | c < 100% van b: Double Failure; 100% tot 138.2% van b: B-Failure; > 138.2%: Elongated |
| 81% tot 100% | Normal | c < 100% van b: C-Failure (OCR geeft "10%", verifieer); 100% tot 138.2%: Common; > 138.2%: Elongated |
| 101% tot 123.6% | Strong | c ≥ 100% van b en c ≤ 161.8% van a: Irregular; c > 161.8% van a: Elongated |
| > 123.6% | Strong | neemt c b nog volledig terug (alleen tot b ≈ 138.2%): Irregular; neemt c b niet volledig terug maar komt c deels binnen het prijsbereik van a: Irregular Failure; komt c er niet in: Running |

Code: `abc_classify`.

### 8.3 Zigzags (5-3-5) (blz. 5-19 t/m 5-22)
Minimum: a is niet meer dan 61.8% van de voorgaande impuls (één Degree hoger); b neemt minstens 1% en **maximaal 61.8%** van a terug (gaat een deel verder, dan was dat slechts het eerste stuk van een complexere b); c eindigt voorbij het eind van a.
- **Normal:** c is 61.8% tot 161.8% van a.
- **Truncated:** c is 38.2% tot < 61.8% van a. Alleen geldig als de markt daarna minstens **81%** (liefst 100% of meer) van de hele zigzag teruggeeft. Meestal één van de vijf poten van een Triangle.
- **Elongated:** c is meer dan 161.8% van a. Lijkt op een impuls. Pas geldig als de markt na afloop meer dan 61.8% van golf c terugneemt voordat het eind van c wordt overschreden; anders is het een impuls (DETOUR-test).

### 8.4 Triangles (3-3-3-3-3) (blz. 5-22 t/m 5-33)
Minimumregels alle triangles:
1. Precies vijf segmenten a-e, elk een volledige correctie (`:3`).
2. De segmenten overlappen in dezelfde prijszone (geen trend); kleine drift is toegestaan.
3. b is 38.2% tot 261.8% van a, en vermijdt meestal een exacte 100%. Is b ongeveer 61.8% van a, dan is het waarschijnlijk geen triangle.
4. Van de vier terugnames (b, c, d, e) zijn er minstens **drie** ≥ 50% van de vorige golf (uitzondering: Running).
5. Slechts **vier** van de zes eindpunten (0, a, b, c, d, e) raken de convergerende trendlijnen.
6. De b-d trendlijn mag door c en e niet worden gebroken; breuk ná e betekent einde triangle.

**Contracting:**
- De **thrust** erna is minstens **75%** van de breedste golf (normaal niet meer dan 125%) en moet de hoogste of laagste prijs van de triangle overschrijden.
- Limiting (komt in 4e golven en b-golven voor): e is de kortste (in prijs), apex valt binnen het bereik van 61.8% van de langste golf, gecentreerd in die golf, en golf e eindigt zo dat de apex ongeveer **20% tot 40%** van de triangle-duur ná het eind van e ligt.
  - *Horizontal:* trendlijnen in tegengestelde richting; d < c; e < d.
  - *Irregular:* b > a (hooguit 261.8%, meestal < 161.8%); c, d, e elk kleiner dan de vorige.
  - *Running:* b langste en > a; c < b; d > c; e < d; beide trendlijnen helling in dezelfde richting; thrust veel groter dan de breedste poot, tot ca. 261.8% (de scan zegt 251.8%).
- Non-Limiting: apex binnen 20% of na 40% van de duur (gerekend vanaf het eind van e), of een post-thrust correctie die terugloopt tot in de apex-tijdzone. De thrust heeft hier geen vaste limiet.

**Expanding:** a of b is de kleinste; e is bijna altijd de grootste en breekt door de trendlijn over a en c; minstens drie van de voorgaande golven zijn ≥ 50% van de golf rechts; kan niet als b-golf in een zigzag of d-golf van een grotere triangle; thrust is kleiner dan de breedste golf (e).

**Fibonacci in triangles:** a, c, e verhouden zich meestal 61.8% of 38.2%; b en d 61.8%; d tot c ongeveer 61.8%. Een Contracting Triangle zonder Fibonacci-relaties wordt als onmogelijk beschouwd.

Code: `triangle_check` dekt de minimumregels en de varianten; de apex-/tijdtoetsen en de trendlijn-geometrie moeten er nog bij.

### 8.5 Correcties: conditionele regels (blz. 5-34 t/m 5-37)
- **Time alternation** in correcties: drie aangrenzende fasen. De eerste twee verschillen meestal sterk in duur (de tweede is ≥ 161.8× of ≤ 61.8× de eerste). De derde is gelijk aan één van de twee, 61.8% of 161.8% ervan, of gelijk aan de som. Bij patronen van maar drie tijdseenheden is dit onmogelijk.
- **Channeling:** trek een lijn van het begin van a tot het eind van b (0-B) en een parallel door het eind van a. Bij een zigzag mag c voorbij die parallel eindigen maar hem niet raken (raakt hij, dan is het onderdeel van een complexe correctie). Breekt de 0-B lijn, dan is c (en het grotere patroon) waarschijnlijk voorbij.
- **Fibonacci:** flats zijn het minst Fibonacci-achtig; zigzags relateren vooral a en c (61.8%, 100%, 161.8%); triangles relateren veel.

---

## 9. Laag 7: hypothesebeheer (ontwerpkeuze, hier moet de bot slim zijn)

Neely zegt zelf (blz. 1-6) dat de eindpunten pas bij bijna voltooide patronen betrouwbaar zijn en dat echte analisten bij onduidelijkheid verschillen. De bot hoort dat niet te verbergen.

Datastructuur per hypothese:

```
Hypothesis {
  id, window_start, window_end,
  neutrality_choices: {wave_id: "aspect1"|"aspect2_split"|"aspect2_merge"|"ignore"},
  labels: {wave_id: "F3"|"c3"|...},
  pattern: "impulse_trending"|"impulse_terminal"|"zigzag"|"flat"|"triangle"|None,
  progress_labels: {...},
  hard_pass: bool,            # alle absolute regels
  soft_score: float,          # 0..1 uit conditionele regels
  confirmation_state: "none"|"minimal"|"full",
  invalidation_price: float,  # prijs waarbij de lezing fout is
  invalidation_time: int|None
}
```

Beslisregels:
1. Genereer hypotheses door de onzekerheid te vertakken: Neutrality-keuzes, resterende labelkeuzes na Position Indicators, `Series`-dubbelzinnigheid (Triangle vs Terminal, Zigzag vs Impuls).
2. Gooi alles weg wat een harde regel schendt (Essential Impulse Rules, flat/zigzag minima, triangle minima, Similarity, Complexity).
3. Score de rest met de conditionele regels (Alternation, Equality, Overlap, Channeling, Fibonacci, tijdsalternation). Voorgestelde gewichten: harde-regel-bijna-voldaan = aftrek (zie Exception Rule), Fibonacci-treffer = + klein, Channeling-conflict = − groot. **Dit zijn startwaarden die je met walk-forward testen kalibreert.**
4. **Alleen handelen** als: er precies één hypothese `hard_pass` is, of de beste `soft_score >= S_min` en het verschil met de nummer twee minstens `margin` is, én de bevestiging van sectie 10 is gehaald.
5. Elke nieuwe bar vernietigt hypotheses die hun `invalidation_price` raken, en ze worden bijgewerkt of opnieuw geboren (patronen zijn pas "klaar" als de volgende golf ze bevestigt).
6. Een hypothese die niet altijd een enkele lezing oplevert na `N` bars: markeer "geen trade". Dit is Neely's "wacht tot de telling zichzelf toont".

---

## 10. Laag 8: handelsstrategie

> Let op: het boek is een analysemethode, geen volledig systeem. De boekregels hieronder zijn expliciet gemarkeerd. Alles wat "Ontwerp" heet is mijn voorstel en ongetest.

### 10.1 Principes uit het boek
- Handel **na** een voltooid patroon, niet erin. De grootste voorspelbaarheid is vlak na een afgeronde beweging (blz. 1-2).
- Mik niet op top of bodem. Wacht op **minimale bevestiging** dat de trend is gekeerd of hervat (blz. 2-10, voetnoot); dat verkleint ook het gap-risico.
- Plaats stops waar de interpretatie aantoonbaar fout is (blz. 1-4).
- Wees terughoudend: signalen zijn zeldzaam maar betrouwbaarder.
- Overnight/gap: vanwege wereldwijde markten raadt het boek een nachtbureau/stop aan of alleen daghandel of alleen middellang/lang termijn. De bot moet **server-side stops** gebruiken.
- Geschikte timeframes: de bot kijkt altijd minstens drie niveaus (laag, midden, hoog). Het hoogste niveau levert de **richtingsfilter**.

### 10.2 Setups

**Setup A: Triangle thrust (best gespecificeerd door het boek).** Ontwerp: dit is je MVP-handelsregel.
- Voorwaarde: `triangle_check` is OK voor een Contracting Triangle (Limiting of Non-Limiting), alle zes eindpunten gevonden, e is voltooid, richting van de verwachte thrust is gelijk aan de trend die voor de triangle liep (4e golf of b-golf in het bevestigde grotere patroon) of, bij ontbreken daarvan, aan de richting van het hogere timeframe.
- Bevestiging: een monowave breekt de b-d trendlijn **in de thrustrichting** én overschrijdt het einde van golf d.
- Entry: marktorder of stop-entry net voorbij de bevestigende prijs.
- Stop: voorbij het eind van golf e (dat is waar de triangle-lezing fout is).
- Target 1: **75%** van de breedste golf vanaf het eind van e. Target 2: **100% tot 125%** van de breedste golf. Limiting: sluit uiterlijk rond de apex-tijdzone af. Non-Limiting: geen vaste limiet; trail met het laagste punt van elke nieuwe monowave tegen de trend.
- Running Triangle: target tot ca. 261.8% van de breedste poot (OCR-onzeker, verifieer).
- Overslaan als: de thrust het uiterste van de triangle niet overschrijdt, of de apex-geometrie niet klopt, of de tijd voorbij is.

**Setup B: hervatting na een voltooide standaardcorrectie** (zigzag of flat) tegen de hogere-timeframe trend in. Ontwerp.
- Voorwaarde: `abc_classify` levert zigzag of flat; c is voltooid; geen complexe reeksen (`x:c3`) in de buurt.
- Bevestiging: de **0-B trendlijn wordt gebroken** in de richting van de trend (boek blz. 5-35). Voor Truncated Zigzag: markt heeft minstens 81% van de zigzag teruggenomen; voor Elongated Zigzag: meer dan 61.8% van c is teruggenomen terwijl het eind van c intact blijft.
- Entry na bevestiging, stop voorbij het uiterste van c, target 1 = begin van golf a (volledige terugname), target 2 = 161.8% van golf a gerekend vanaf het eind van c. Daarna trailen.

**Setup C: einde van een impuls (tegen de impuls in).** Ontwerp; **niet in de MVP.**
- De bevestiging van een `:L5` vereist de Post-Constructive Rules (hoofdstuk 6, ontbreekt). Gebruik tot dan alleen als **uitstapsignaal** voor bestaande posities: sluit af of trail dicht als een geldige impuls zijn Overlap- en Channeling-bevestiging krijgt.

**Setup D: instap in golf 3 of 5** (na het vaststellen van golf 2 of 4). Ontwerp; later. Vereist stabiele Degree-/Progress-label-toewijzing (hoofdstuk 7 en 12).

### 10.3 Wat de bot nooit doet
- Handelen in een "geen trade"-toestand (geen enkele hypothese met genoeg bewijs).
- Een positie aanhouden nadat de invalidatieprijs is geraakt.
- Handelen op een telling die alleen werkt door een Neutrality-keuze die de bot niet kon verdedigen (los beide versies als aparte hypotheses op).
- Tellen op slotkoersen of op futures-contractwissels.

---

## 11. Laag 9: risico en uitvoering

Ontwerp, standaard voor elke bot:
- **Risico per trade:** vast percentage van het saldo (bijv. 0.25% tot 1%). Positiegrootte = risicobedrag / afstand entry tot invalidatieprijs. Is die afstand groter dan `max_stop_atr`, sla de trade over.
- **Eén positie per markt**, en een maximum van gelijktijdige posities over alle markten.
- **Harde kill-switch:** dagelijks verlies, totale drawdown en maximaal aantal verliezende trades op een rij. Draai je dit op een prop-firm-account, neem hun daily-loss- en max-drawdown-regels als harde limieten met een buffer.
- **Orders:** altijd met server-side stop en target. Geen posities via weekend of grote nieuws zonder bewuste keuze. Rekening houden met spread, slippage en commissie in backtests.
- **Nieuwsfilter:** pauzeer rond grote economische releases; het boek erkent dat plotselinge nieuwsgaps patronen breken.
- **Logging:** bewaar bij elke trade de volledige hypothese (labels, regels die vuurden, scores, invalidatieprijs), zodat je later kunt zien waarom de bot instapte.

---

## 12. Wat de pdf mist (en wat dat betekent)

Je scan bevat hoofdstuk 1 t/m 5. De inhoudsopgave in dezelfde pdf toont wat er verder is:

| Hoofdstuk | Inhoud | Gevolg voor de bot |
|-----------|--------|--------------------|
| 6 Post-Constructive Rules of Logic | Twee stadia van patroonbevestiging per impuls- en correctietype | Zonder dit kan de bot een `:L5` niet formeel bevestigen. Setup C en D wachten hierop. |
| 7 Conclusions | Compaction, Complexity, Degree, "Progress Labels revisited" | Nodig om patronen op te tellen tot grotere graden en richting te bepalen. |
| 8 Construction of Complex Polywaves | Dubbele en driedubbele correcties, x-waves, multiwaves, Alternation (uitgebreid), Intricacy | Zonder dit sla je alle `x:c3`-reeksen over. |
| 9 Basic Neely Extensions | Trendline touch points, Time Rule, Independent Rule, Exception Rule | De Exception Rule is nodig voor het "bijna voldaan"-gedrag. |
| 10 Advanced Logic Rules | Retracement op basis van Power Ratings | Verfijnt de keuze tussen patroonvarianten. |
| 11 Advanced Progress Label Application | Wat er per golf precies moet gelden | Maakt de impuls- en correctielabels strikt. |
| 12 Advanced Neely Extensions | Speciale channeling, Missing Waves, Emulation, "Expansion of Possibilities", geavanceerde Fibonacci | Cruciaal voor de ambiguïteit die de bot moet beheren. |

**MVP-keuze:** bouw alles met de standaardpatronen, markeer elke x-wave-situatie als "geen trade" en laat Setups C en D weg tot je hoofdstuk 6 t/m 12 hebt. Als je mij die hoofdstukken geeft (of aangeeft waar ze staan), werk ik dit document en `neely_core.py` bij.

---

## 13. Bouwvolgorde en testplan

**Fase 1: kern (grotendeels klaar)**
1. Data-laag + `find_monowaves` + Neutrality-flags.
2. m0/m2 + `classify_monowave`. Testcase: laat de bot de voorbeeldgrafieken uit hoofdstuk 3 (fig. 3-2b, 3-12, 3-17 en 3-18) overnemen en vergelijk de dots en Rule-labels met het boek.
3. `impulse_check` met de figuur 5-2 gevallen A t/m K (A faalt regel 3, E faalt regel 7, G regel 5, K regel 4, J is een 5th-wave failure, D heeft vier segmenten).

**Fase 2: opzoektabel**
4. Codeer Rules 1 t/m 5 uit sectie 5 als data, per alinea met pagina-verwijzing. Schrijf voor elke alinea één unit-test met een kunstmatige monowave-reeks.
5. Codeer de Position Indicator-buurtabellen (blz. 3-61 t/m 3-64) en Pattern Isolation.

**Fase 3: patronen**
6. Series + Similarity + DETOUR.
7. Flats, Zigzags, Triangles volledig (inclusief apex-geometrie en trendlijnen).
8. Hypothese-engine met scoring.

**Fase 4: strategie**
9. Setup A in een backtester (event-driven, geen look-ahead). **Cruciaal:** de bot mag een monowave pas gebruiken wanneer die volgens de regels van sectie 3 werkelijk is afgerond; de laatste, nog lopende golf is altijd voorlopig. Dit is de meest voorkomende reden dat Elliott-backtests te mooi uitvallen.
10. Walk-forward test over meerdere markten en perioden, met kosten. Neely zelf waarschuwt dat mechanische systemen die op historie zijn gefit falen zodra de omgeving verandert (blz. 1-2/1-4); houd het aantal vrije parameters klein en test op data die je nooit tijdens ontwikkeling hebt gezien.
11. Papertrading minstens enkele maanden vóór echt geld.

**Fase 5: aanvullen** met hoofdstuk 6 t/m 12 en Setups B, C, D.

Succescriteria (ontwerp): de pijplijn herhaalt de boekvoorbeelden exact; de bot geeft over een lange reeks data in verreweg de meeste periodes "geen trade"; elke trade is reconstrueerbaar uit het log.

---

## 14. Parametertabel (configbestand)

| Parameter | Start | Bron |
|-----------|-------|------|
| `TOL_FIB` | 0.04 | boek blz. 3-34 |
| `NEAR_TOL` ("bijna") | 0.10 | boek blz. 3-34 |
| `similarity_min` | 1/3 | boek blz. 4-3 |
| `max_monowaves_window` | 20 | boek blz. 3-22 |
| `neutrality_angle_deg` | 45 | boek blz. 3-10 |
| `neutrality_aspect1_max_shift` | 0.382 | boek blz. 3-12 |
| `impulse_w5_min_of_w4` | 0.382 | boek blz. 5-2 |
| `extension_min` | 1.618 | boek blz. 5-4 |
| `flat_b_min`, `flat_c_min` | 0.618, 0.382 | boek blz. 5-16 |
| `zigzag_b_max` | 0.618 | boek blz. 5-19 |
| `truncated_retrace_min` | 0.81 | boek blz. 5-21 |
| `triangle_thrust_min` | 0.75 | boek blz. 5-27 |
| `S_min`, `margin`, `N_wait_bars` | te kalibreren | ontwerp |
| `risk_per_trade`, `max_stop_atr` | 0.5%, te kalibreren | ontwerp |

---

## 15. Bijgeleverde code

- `neely_core.py`: `find_monowaves`, `apply_neutrality_flags`, `retracement_ratios`, `rule_id`, `condition_id`, `category_id`, `classify_monowave`, `impulse_check`, `abc_classify`, `triangle_check`, `similar`.
- `test_neely_core.py`: 9 tests (monowaves, gelijke punten, Rules, Condities, classificatie, impulscases uit fig. 5-2, flats/zigzags, triangle, similarity). Run: `python -m pytest -q`.

Bekende beperkingen van de code: `_m0_start` is een spiegelbeeld-aanname; Neutrality Aspect 1/2 wordt alleen gemarkeerd, niet uitgevoerd; `triangle_check` mist apex-geometrie; er is geen Terminal-interne 3-3-3-3-3 controle en geen Compaction.
