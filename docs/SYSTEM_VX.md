# Systeem VX: VectorVest vertaald naar forex, metalen en olie

Opdracht van de trader: "volledig systeem ontwikkelen voor forex, metals en oil op basis van wat VectorVest doet, maar
dan wat anders, want je bent niet met stocks bezig". Achtergrond over VectorVest: `docs/EDGE_SEARCH.md`.

## Wat VectorVest doet, en de vertaling

| VectorVest (aandelen) | VX (forex, metalen, olie) | Waarom |
|---|---|---|
| **VVC**: de prijs van het gemiddelde aandeel | **Sterkte-index per valuta** (EUR, GBP, AUD, NZD, USD, CAD, CHF, JPY): het gemiddelde van haar 7 paren | Forex heeft geen markt die als geheel stijgt; elke valuta heeft wel haar eigen "markt" tegenover de rest |
| **RT** (Relative Timing): richting, grootte en dynamiek van de koers over meerdere periodes | **Momentum** over 1, 3, 6 en 12 maanden, elk gedeeld door de volatiliteit, en daarvan het gemiddelde | Momentum bestaat in valuta's en grondstoffen (Moskowitz, Ooi & Pedersen 2012; Menkhoff e.a. 2012) |
| **Value** (koers tegenover winst en rente) | **5-jaars terugkeer**: hoe ver de index onder (+) of boven (-) haar gemiddelde van 5 jaar staat | Valuta-"value" in Asness, Moskowitz & Pedersen (2013) |
| **Safety** (stabiliteit) | **Lage volatiliteit** (63 dagen) | |
| **VST** (Value + Safety + Timing) | **VST**: het gemiddelde van de drie rangen (z-scores over de 8 valuta's) | |
| **DEW** (koers boven 30-WMA én DPO(20) > 0) | **Dezelfde DEW**, op elke valuta-index en op goud, zilver en olie | De gepubliceerde regel |
| Koop de best gerangschikte aandelen als de markt Up staat | **Long de sterkste valuta's** (hoogste VST) met DEW Up, **short de zwakste** met DEW Down, via hun paren | |
| Verkoop als de rating zakt / onder de stop | **Uit zodra de DEW van die valuta omdraait** | DEW als stop |

## Test VX1 (vooraf vastgelegd, 2026-10-30)

Code: `research/vx/vx.py`. Dagdata, alles op het moment dat de dagcandle **gesloten** is (`complete_times`). Een
beslissing bij het slot van dag t geldt van dat slot tot het volgende.

**Universum:**
- de 28 paren van de 8 valuta's (2003-2025);
- goud en zilver (XAUUSD, XAGUSD, 2005-2025);
- olie (XTI_USD, 2015-2026).

**Ratings** (elke dag; de index in log, σ = het dagelijkse risico over 252 dagen):
- `RT` = het gemiddelde van (L[t] - L[t-n]) / (σ·√n) over n = 21, 63, 126, 252.
- `VAL` = -(L[t] - het gemiddelde van L over 1.260 dagen) / (σ·√252). Het gemiddelde loopt over hoogstens 1.260
  dagen en telt vanaf 252 dagen data mee.
- `SAFE` = -de volatiliteit over 63 dagen.
- `VST` = het gemiddelde van de z-scores van RT, VAL en SAFE over de 8 valuta's.

**DEW** op elke valuta-index en grondstof:
- Up: slot boven de 30-daagse gewogen MA én DPO(20) > 0.
- Down: slot onder de 30-WMA én DPO(20) < 0.
- Zonder nieuw signaal blijft de stand.
- DPO(20) = het slot van 11 dagen geleden min het SMA van 20 dagen.

**Portefeuille** (instap bij het weekslot, op de laatste forexdag van de week; uitstap dagelijks):
- **Forex:**
  - Long de 2 valuta's met de hoogste VST uit de top 3 die DEW Up hebben.
  - Short de 2 met de laagste VST uit de onderste 3 die DEW Down hebben.
  - Elke long-short-combinatie wordt een paar (maximaal 4).
  - Draait de DEW van een valuta om, dan gaan haar paren dicht bij dat slot.
- **Goud, zilver, olie:**
  - Long als DEW Up en RT > 0; short als DEW Down en RT < 0.
  - Uit als de DEW omdraait.
- **Grootte:**
  - Elke positie mikt op 10% volatiliteit per jaar (63-daags risico van het instrument, bepaald bij de instap).
  - De portefeuille deelt door 7 vaste plaatsen (4 forex + 3 grondstoffen); een lege plaats staat in cash.
- **Kosten:** elke verandering in positie kost de spread + slippage van het instrument (`test2.cost_price`).
  Swaps en rente (carry) zijn niet meegeteld.

**Lat (beslissend, het hele systeem):**
- elke periode (2005-14, 2015-20, 2021-25) heeft na kosten een positief rendement;
- over 2005-2025 heeft het gemiddelde dagrendement t >= 2,0 (≈ Sharpe >= 0,45).

**Gerapporteerd, niet beslissend:**
- alleen forex; alleen grondstoffen;
- zonder de DEW (alleen de VST-rangen, wekelijks);
- alleen de DEW (long Up / short Down zonder VST);
- als vergelijking: goud kopen en houden.

**Bij slagen:** een eigen vastlegging met (1) de 5ers-challenge op het 15-minutenpad en (2) swaps.
