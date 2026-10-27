# 20k5ers bot op een Windows-VM zetten

Alles hieronder typ je in de **Opdrachtprompt** (`cmd`), tenzij er "Kladblok" staat.
Op een server zonder `winget`: gebruik de downloadlinks bij stap 1.

## 0. Wat je nodig hebt
- Windows 10/11 of Windows Server 2019/2022, **64-bit**, minstens 4 GB RAM.
- Je 5ers-accountnummer, wachtwoord en servernaam (staan in je 5ers-mail/dashboard).
- Een GitHub-account met toegang tot de (private) repo.

## 1. Programma's installeren
```
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
```
Geen `winget`? Download Python 3.12 (64-bit) op https://www.python.org/downloads/ en vink
**"Add python.exe to PATH"** aan. Git: https://git-scm.com/download/win

**Sluit daarna het venster en open een nieuwe Opdrachtprompt**, en controleer:
```
python --version
git --version
```
(Python 3.11 of 3.12. Niet 3.13: het MetaTrader5-pakket heeft daar niet altijd een versie voor.)

## 2. MetaTrader 5 installeren en inloggen
1. Installeer MT5 via de link in je 5ers-dashboard.
2. Bestand > Inloggen bij handelsaccount: je 5ers-nummer, wachtwoord, server. Wacht tot rechtsonder een verbinding staat.
3. Extra > Opties > tabblad **Expert Advisors** > vink **"Algoritmische handel toestaan"** aan.
4. In de werkbalk moet de knop **Algo Trading** groen zijn.
5. Laat MT5 open staan zolang de bot draait.

## 3. De bot downloaden
Kies een map zonder spaties, bijvoorbeeld `C:\`:
```
cd C:\
git clone --depth 1 https://github.com/NinaFal/20k5ers.git
cd 20k5ers
```
Er opent een inlogscherm van GitHub; log in. (Staat de repo nu onder een andere eigenaar,
dan staat het juiste adres bovenaan je repo-pagina bij de groene knop **Code**.)

Zolang pull request #38 nog niet in `main` zit, haal je de werkbranch op:
```
git clone --depth 1 -b claude/awesome-maxwell-continued-k9zacp https://github.com/NinaFal/20k5ers.git
```

## 4. Pakketten installeren
```
cd C:\20k5ers
python -m pip install --upgrade pip
python -m pip install -r requirements-live.txt
```

## 5. Je inloggegevens (.env)
```
copy deploy\.env.example .env
notepad .env
```
Vul in Kladblok `MT5_LOGIN`, `MT5_PASSWORD` en `MT5_SERVER` in en sla op. Het bestand `.env`
staat in `.gitignore` en gaat nooit naar GitHub. Zet je wachtwoord nergens anders neer.

Staat dit account al in stap 2 of is het al gefund? Voeg dan in `.env` een regel toe:
```
CHALLENGE_STEP=2
```
(`1`, `2` of `funded`). Zonder die regel telt de eerste login als stap 1, een nieuwe login
na een gehaalde stap 1 als stap 2.

## 6. Controleren voor je start (aanrader)
```
python deploy\preflight.py
```
Dit test zonder iets te handelen: Python, pakketten, tijdzone, `.env`, de verbinding met MT5
(account, saldo, algo-trading aan) en de bot-configuratie. Bij een probleem staat er
`[FOUT]` met wat je moet doen. Pas bij **ALLES IN ORDE** verder.

## 7. De bot starten
```
deploy\start_live.bat
```
Het venster blijft open en toont **alles**: de controle voor de start, daarna elke scan,
order, waarschuwing en fout. Bij een crash of een mislukte controle blijft de melding staan
(het venster sluit niet). Stoppen: `Ctrl+C`.

Het oude `python main_live_bot.py` werkt nog steeds, maar dan zijn de strategie-instellingen
en de controle niet actief. Gebruik `start_live.bat`.

**Logboek live in een tweede venster** (aanrader): open een tweede Opdrachtprompt:
```
cd C:\20k5ers
deploy\watch_log.bat
```

**Automatisch herstarten na een crash** (na 60 seconden), in plaats van `start_live.bat`:
```
deploy\start_live_loop.bat
```

## 8. Dagelijkse limieten bekijken en wijzigen
Bekijken (bot-limieten naast die van 5ers, laatste statusregel, saldo en equity):
```
deploy\show_limits.bat
```
Je ziet daar:
- **Dagstop 2,5%** (bij meer dan 5 open posities 2,1%): boven dit dagverlies krijgt de bot geen nieuwe trades en sluit hij alles. Dit is dezelfde instelling als in de backtest en is instelbaar.
- Een trapje dat het risico per trade verlaagt bij dagverlies (2,0% en 2,5%) en bij totaalverlies (1,5%, 2,5% en 5,5%).
- 5ers sluit je account bij **5%** dagverlies en **10%** totaal. Kijk bij twijfel altijd op je 5ers-dashboard.

Wijzigen van de dagstop (geteste waarden 2,0 t/m 3,5; meer dan 4,0 wordt geweigerd):
```
deploy\set_daily_limit.bat 2.0
```
Terug naar de standaard (2,5):
```
deploy\set_daily_limit.bat reset
```
Stop de bot daarna met `Ctrl+C` en start hem opnieuw; een draaiende bot leest dit niet opnieuw in.
Controleer met `deploy\show_limits.bat`; bij een afwijking van de geteste 2,5 staat daar een melding.

### Toont de bot een andere dagelijkse limiet dan 5ers? (bijvoorbeeld 48.700 tegen 47.679)
De bot rekent met zijn dagbasis: de hoogste van equity en saldo bij de dagreset van 5ers. Staat die basis
anders dan bij 5ers, dan klopt ook zijn limiet niet. Corrigeren:
1. Stop de bot met `Ctrl+C`.
2. Zet de limiet van het 5ers-dashboard in de bot (hier: 47.679):
```
deploy\set_day_start.bat --floor 47679
```
   Of geef de dagbasis zelf op: `deploy\set_day_start.bat --start 50188`. Zonder getal toont hij alleen wat er nu staat.
3. Start de bot opnieuw met `deploy\start_live.bat` en controleer met `deploy\show_limits.bat` dat het klopt.

De waarde blijft tot de volgende dagreset staan; daarna rekent de bot weer zelf. Er wordt een reservekopie gemaakt
(`challenge_risk_state.json.bak`). Dit bestand bestaat pas nadat de bot een keer is gestart.

## 9. Updaten
Stop de bot (`Ctrl+C`), dan:
```
cd C:\20k5ers
git pull
python -m pip install -r requirements-live.txt
deploy\start_live.bat
```

## 10. Windows goed zetten (eenmalig, als beheerder)
Geen slaapstand, klok synchroniseren:
```
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
w32tm /resync
```
Zet in Windows Update "Actieve uren" zo dat de VM niet midden in de handelsdag herstart.
Wil je dat de bot na het inloggen vanzelf start:
```
schtasks /create /tn "20k5ers bot" /tr "C:\20k5ers\deploy\start_live_loop.bat" /sc onlogon /rl highest
```

## Problemen
| Melding | Oplossing |
|---|---|
| `'python' is not recognized` | Python niet in PATH; installeer opnieuw met "Add to PATH" en open een nieuw venster |
| `MetaTrader5 ... ontbreekt` | `python -m pip install MetaTrader5` (Python 3.11 of 3.12, 64-bit) |
| `MT5 verbinden mislukt` / `IPC timeout` | MT5 openen en ingelogd laten staan; servernaam exact zoals in MT5; `MT5_PATH` in `.env` leeg laten of juist zetten |
| `Algoritmische handel staat UIT` | MT5: Extra > Opties > Expert Advisors, en de knop Algo Trading op groen |
| `tijdzone New York niet beschikbaar` | `python -m pip install tzdata` |
| `configuratie wijkt af` | Niets handmatig aanpassen; `git pull` en opnieuw proberen, of laat het me weten |
| Vreemde tekens in het venster | Gebruik `start_live.bat` (zet UTF-8 aan) |

## Veiligheid
- `.env` nooit delen of uploaden.
- In deze repo hebben eerder echte sleutels gestaan (OANDA, en een MT5-wachtwoord in
  `.env.forexcom_demo`). Ze zijn uit de bestanden gehaald maar staan nog in de geschiedenis.
  Vernieuw ze: een nieuwe OANDA-sleutel en een nieuw wachtwoord voor dat MT5-account.
- Zet de repo op **Private**.
