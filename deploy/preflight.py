#!/usr/bin/env python3
"""
Controle VOOR de bot start. Draai op de Windows-VM:

    python deploy\\preflight.py            alles controleren, ook de MT5-verbinding
    python deploy\\preflight.py --no-mt5   zonder verbinding (bijvoorbeeld zonder MT5 open)

Wat er gecontroleerd wordt, in volgorde:
  1  Python-versie
  2  pakketten (pandas, numpy, requests, dotenv, tzdata, MetaTrader5)
  3  tijdzonedatabase (New York) -- zonder die staat de daglimiet-reset in de zomer fout
  4  .env: MT5_LOGIN / MT5_PASSWORD / MT5_SERVER aanwezig en niet nog een voorbeeldwaarde
  5  systeemklok (tijd en tijdzone, zodat je ziet of Windows goed loopt)
  6  verbinding met MetaTrader 5: account, saldo, algo-trading aan
  7  configuratie: backtest/src/w5_acceptance.py (bot weigert te starten bij afwijking)

Geeft afsluitcode 0 als alles klopt, anders 1. Er wordt NIETS getraden.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

problems = []
warnings = []


def ok(msg):
    print(f"  [ OK  ] {msg}")


def bad(msg, fix=""):
    print(f"  [FOUT ] {msg}")
    if fix:
        print(f"          -> {fix}")
    problems.append(msg)


def warn(msg):
    print(f"  [LET OP] {msg}")
    warnings.append(msg)


def section(t):
    print(f"\n{t}")


def main():
    use_mt5 = "--no-mt5" not in sys.argv
    print("=" * 70)
    print(" 20k5ers bot -- controle voor de start")
    print("=" * 70)

    # 1 -- Python
    section("1. Python")
    v = sys.version_info
    exe = sys.executable
    if v < (3, 11):
        bad(f"Python {v.major}.{v.minor} is te oud (nodig: 3.11 of 3.12)",
            "installeer Python 3.11/3.12 van python.org en vink 'Add to PATH' aan")
    elif v >= (3, 13):
        warn(f"Python {v.major}.{v.minor}: getest is 3.11/3.12. Lukt het installeren van MetaTrader5 niet, gebruik 3.12")
        ok(f"Python {v.major}.{v.minor}.{v.micro} ({exe})")
    else:
        ok(f"Python {v.major}.{v.minor}.{v.micro} ({exe})")
    if sys.maxsize <= 2 ** 32:
        bad("32-bit Python; MetaTrader5 vraagt 64-bit", "installeer de 64-bit versie")

    # 2 -- pakketten
    section("2. Pakketten")
    need = [("pandas", "pandas"), ("numpy", "numpy"), ("requests", "requests"),
            ("dotenv", "python-dotenv"), ("tzdata", "tzdata")]
    if os.name == "nt":
        need.append(("MetaTrader5", "MetaTrader5"))
    missing = []
    for mod, pipname in need:
        try:
            m = __import__(mod)
            ok(f"{pipname} {getattr(m, '__version__', '')}".rstrip())
        except Exception as e:
            bad(f"{pipname} ontbreekt ({type(e).__name__})", f"python -m pip install {pipname}")
            missing.append(pipname)
    if os.name != "nt":
        warn("Geen Windows: MetaTrader5 wordt hier niet gecontroleerd (alleen op de VM)")
    if missing:
        print("          Alles in een keer: python -m pip install -r requirements-live.txt")

    # 3 -- tijdzones
    section("3. Tijdzonedatabase")
    try:
        from zoneinfo import ZoneInfo
        ny = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
        ok(f"New York werkt (nu {ny:%H:%M}, UTC{ny.strftime('%z')[:3]}:{ny.strftime('%z')[3:]})")
    except Exception as e:
        bad(f"tijdzone New York niet beschikbaar ({type(e).__name__})",
            "python -m pip install tzdata   (zonder dit loopt de dagreset in de zomer een uur fout)")

    # 4 -- .env
    section("4. Inloggegevens (.env)")
    env_path = REPO / ".env"
    if not env_path.exists():
        bad(".env ontbreekt in " + str(REPO),
            "kopieer deploy\\.env.example naar .env in de hoofdmap en vul je gegevens in")
    else:
        ok(f".env gevonden ({env_path})")
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except Exception:
        pass
    login = os.getenv("MT5_LOGIN", "")
    pw = os.getenv("MT5_PASSWORD", "")
    srv = os.getenv("MT5_SERVER", "")
    for name, val in (("MT5_LOGIN", login), ("MT5_PASSWORD", pw), ("MT5_SERVER", srv)):
        if not val:
            bad(f"{name} is leeg of ontbreekt in .env")
        elif val.upper().startswith(("YOUR_", "ZET_HIER", "JOUW_")) or val in ("12345678", "jouw_wachtwoord"):
            bad(f"{name} staat nog op de voorbeeldwaarde", "vul je echte waarde in .env in")
        else:
            shown = val if name != "MT5_PASSWORD" else "*" * len(val)
            ok(f"{name} = {shown}")
    if login and not login.isdigit():
        bad("MT5_LOGIN moet een getal zijn (je 5ers-accountnummer)")
    path = os.getenv("MT5_PATH", "")
    if path:
        if Path(path).exists():
            ok(f"MT5_PATH bestaat ({path})")
        else:
            bad(f"MT5_PATH wijst naar een bestand dat er niet is: {path}",
                "verwijder de regel uit .env of zet het juiste pad naar terminal64.exe")

    # 5 -- klok
    section("5. Systeemklok")
    now = datetime.now().astimezone()
    ok(f"Windows-tijd {now:%Y-%m-%d %H:%M:%S} (UTC{now.strftime('%z')[:3]}:{now.strftime('%z')[3:]})")
    print("          Loopt de klok fout? Als beheerder: w32tm /resync")

    # 6 -- MT5
    section("6. MetaTrader 5")
    if not use_mt5:
        warn("MT5-verbinding overgeslagen (--no-mt5)")
    elif os.name != "nt" and "MetaTrader5" not in sys.modules:
        try:
            import MetaTrader5  # noqa: F401  (testomgeving)
        except Exception:
            warn("MT5 kan hier niet draaien; draai deze controle op de Windows-VM")
    if use_mt5 and (os.name == "nt" or "MetaTrader5" in sys.modules):
        try:
            import MetaTrader5 as mt5
            kw = {}
            if path and Path(path).exists():
                kw["path"] = path
            if login.isdigit() and pw and srv:
                kw.update(login=int(login), password=pw, server=srv)
            if not mt5.initialize(**kw):
                bad(f"MT5 verbinden mislukt: {mt5.last_error()}",
                    "staat MetaTrader 5 open en ben je er ingelogd? Server-naam exact zoals in MT5 "
                    "(Bestand > Inloggen). Zet in MT5: Extra > Opties > Expert Advisors > 'Algoritmische handel toestaan'")
            else:
                info = mt5.account_info()
                term = mt5.terminal_info()
                if info is None:
                    bad("Verbonden, maar geen account-info", "log in MT5 in met je 5ers-account")
                else:
                    ok(f"Account {info.login} bij {info.company} (server {info.server})")
                    ok(f"Saldo ${info.balance:,.2f} | Equity ${info.equity:,.2f} | hefboom 1:{info.leverage}")
                    if info.login and login.isdigit() and int(login) != int(info.login):
                        warn(f"Ingelogd account {info.login} wijkt af van MT5_LOGIN {login}")
                    if not info.trade_allowed:
                        bad("Handelen is voor dit account niet toegestaan (trade_allowed=False)",
                            "is het account actief bij 5ers, en geen investor-wachtwoord?")
                    else:
                        ok("Handelen toegestaan voor dit account")
                if term is not None:
                    if not term.trade_allowed:
                        bad("Algoritmische handel staat UIT in de MT5-terminal",
                            "Extra > Opties > Expert Advisors > 'Algoritmische handel toestaan', "
                            "en de knop 'Algo Trading' bovenaan op groen")
                    else:
                        ok("Algoritmische handel staat aan in de terminal")
                    if not term.connected:
                        bad("Terminal heeft geen verbinding met de broker", "check internet en servernaam")
                mt5.shutdown()
        except Exception as e:
            bad(f"MT5-controle crashte: {type(e).__name__}: {e}")

    # 7 -- configuratie
    section("7. Configuratie (acceptatietest)")
    env = dict(os.environ)
    env.setdefault("BROKER_TYPE", "fiveers_live")
    env["PYTHONUTF8"] = "1"
    try:
        p = subprocess.run([sys.executable, str(REPO / "backtest" / "src" / "w5_acceptance.py")],
                           env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = p.stdout.splitlines()
        shown = [ln for ln in out if "FAIL" in ln or ln.startswith("CONFIG:") or ln.startswith("DEPLOYMENT:")]
        for ln in shown:
            print("          " + ln.strip())
        if p.returncode == 0:
            ok("configuratie komt overeen met de gevalideerde baseline")
        elif p.returncode == 2:
            warn("configuratie klopt; de acceptatietest mist alleen omgevingsitems (zie boven)")
        else:
            bad("configuratie wijkt af van de gevalideerde baseline", "bot start niet; zie de FAIL-regels hierboven")
    except Exception as e:
        bad(f"acceptatietest kon niet draaien: {e}")

    # Samenvatting
    print("\n" + "=" * 70)
    if problems:
        print(f" NIET KLAAR: {len(problems)} probleem(en). De bot start niet.")
        for pr in problems:
            print(f"   - {pr}")
        sys.exit(1)
    print(" ALLES IN ORDE." + (f" ({len(warnings)} aandachtspunt(en))" if warnings else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
