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
