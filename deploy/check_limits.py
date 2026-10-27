#!/usr/bin/env python3
"""
Toont welke verlieslimieten de bot NU gebruikt, zodat je ze naast 5ers kunt leggen.

    python deploy\\check_limits.py            (of dubbelklik deploy\\show_limits.bat)
    python deploy\\check_limits.py --no-mt5   zonder verbinding met MetaTrader

Leest .env en de code, de laatste statusregel uit logs\\tradr_live.log en
(als MT5 open staat) saldo en equity van het account. Past niets aan.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))
try:
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
except Exception:
    pass

BASELINE = {"CFG_DAILY_HALT_PCT": 2.5}


def getf(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return float(default)


def main():
    from ftmo_config import FIVEERS_CONFIG as C
    halt_env = os.getenv("CFG_DAILY_HALT_PCT")
    gate = getf("CFG_DAILY_HALT_PCT", "2.50")
    print("=" * 72)
    print(f" VERLIESLIMIETEN  --  {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 72)
    print("\n 5ers (de regels van de prop firm)")
    print("   Dagelijks verlies  : 5%   -> account dicht als je er doorheen gaat")
    print("   Totaal verlies     : 10%  van het startbedrag")
    print("   Controleer altijd je eigen 5ers-dashboard: dat is leidend.")

    print("\n Bot, DAGELIJKS verlies (t.o.v. equity aan het begin van de dag)")
    src = f"uit .env ({halt_env})" if halt_env else "standaard"
    flag = "" if abs(gate - BASELINE["CFG_DAILY_HALT_PCT"]) < 1e-9 else "   <-- AFWIJKEND van de geteste 2.5"
    print(f"   Waarschuwing                    : {C.daily_loss_warning_pct:.2f}%  (risico max 0.25%)")
    print(f"   Reduceren                       : {C.daily_loss_reduce_pct:.2f}%  (risico max 0.15%)")
    print(f"   Dagstop (CFG_DAILY_HALT_PCT)    : {gate:.2f}%  ({src}){flag}")
    print(f"      = geen nieuwe trades EN alles sluiten, dezelfde instelling als in de backtest")
    print(f"      bij meer dan 5 open posities : {gate - 0.4:.2f}%")
    print(f"      rond de rollover (22:00 UTC / 21:00 in de zomer): max 2.50%")
    print(f"   Marge tot 5ers-grens            : {5 - gate:.2f} procentpunt")

    sf0 = REPO / "challenge_risk_state.json"
    if sf0.exists():
        try:
            stt = json.loads(sf0.read_text(encoding="utf-8"))
            ds = float(stt.get("day_start_equity", 0))
            print("\n Dagbasis van de bot (challenge_risk_state.json) -> vergelijk met het 5ers-dashboard")
            print(f"   Dagbasis (day start equity)     : ${ds:,.2f}   datum {stt.get('current_date')}"
                  f"{'  (handmatig gezet)' if stt.get('day_start_equity_manually_set_date') else ''}")
            print(f"   Dagelijkse 5%-limiet in de bot  : ${ds * 0.95:,.2f}   <-- moet gelijk zijn aan de limiet op 5ers")
            print(f"   Bot stopt bij {gate:.2f}% verlies  : equity ${ds * (1 - gate / 100):,.2f}")
            print("   Staat het anders dan 5ers?  deploy\\set_day_start.bat --floor <limiet van 5ers>")
        except Exception as e:
            print(f"\n (dagbasis niet te lezen: {e})")

    print("\n Bot, TOTAAL verlies (t.o.v. het startbedrag)")
    print(f"   Trap 1 vanaf {getf('CFG_TDD_CAUTION_PCT', '1.5'):.1f}%   : risico max {getf('CFG_RISK_CAUTIOUS', '0.4'):.2f}%")
    print(f"   Trap 2 vanaf {getf('CFG_TDD_WARNING_PCT', '2.5'):.1f}%   : risico max {getf('CFG_RISK_CONSERVATIVE', '0.25'):.2f}%")
    print(f"   Trap 3 vanaf {getf('CFG_TDD_EMERGENCY_PCT', '5.5'):.1f}%   : risico max {getf('CFG_RISK_ULTRASAFE', '0.15'):.2f}%, plus muurbewaking")
    print(f"   5ers-grens                      : 10.00%")

    print("\n Risico per trade")
    try:
        prm = json.loads((REPO / "params" / "current_params.json").read_text())["parameters"]
        print(f"   Basis (parameters, daalt per fase): {prm.get('risk_per_trade_pct')}%")
    except Exception:
        pass
    print(f"   Challenge stap 1                : {getf('STEP1_RISK_PCT', '1.8'):.2f}%")
    print(f"   Challenge stap 2                : {getf('STEP2_RISK_PCT', '1.8'):.2f}%")
    print(f"   Gefund onder $300k (klimlimiet) : {getf('FUNDED_CLIMB_RISK_PCT', '1.8'):.2f}%")
    print(f"   Gefund vanaf $300k              : 0.60%")
    sf = REPO / "challenge_steps.json"
    forced = os.getenv("CHALLENGE_STEP")
    step = None
    if sf.exists():
        try:
            step = json.loads(sf.read_text())
        except Exception:
            pass
    print(f"   Huidige fase                    : {forced or (step if step else 'wordt bepaald bij de start')}"
          f"{'  (CHALLENGE_STEP in .env)' if forced else ''}")

    print("\n Laatste statusregel van de bot (logs\\tradr_live.log)")
    lg = REPO / "logs" / "tradr_live.log"
    if lg.exists():
        last = None
        with open(lg, "r", encoding="utf-8", errors="replace") as f:
            for line in f.readlines()[-4000:]:
                if "[DDD/TDD Protection]" in line:
                    last = line.strip()
        if last:
            print("   " + last)
            m = re.search(r"DDD: ([\d.]+)%.*?halt: ([\d.]+)%", last)
            if m:
                print(f"   -> dagverlies nu {m.group(1)}%, noodstop op {m.group(2)}%")
        else:
            print("   (nog geen DDD/TDD-regel in het logboek)")
    else:
        print("   (nog geen logboek: de bot heeft nog niet gedraaid)")

    if "--no-mt5" not in sys.argv:
        print("\n Account in MetaTrader 5")
        try:
            import MetaTrader5 as mt5
            kw = {}
            if os.getenv("MT5_PATH") and Path(os.getenv("MT5_PATH")).exists():
                kw["path"] = os.getenv("MT5_PATH")
            if (os.getenv("MT5_LOGIN") or "").isdigit():
                kw.update(login=int(os.getenv("MT5_LOGIN")), password=os.getenv("MT5_PASSWORD", ""),
                          server=os.getenv("MT5_SERVER", ""))
            if not mt5.initialize(**kw):
                print(f"   geen verbinding: {mt5.last_error()}")
            else:
                a = mt5.account_info()
                print(f"   Account {a.login}  |  saldo ${a.balance:,.2f}  |  equity ${a.equity:,.2f}")
                start = getf("ACCOUNT_SIZE", "50000")
                print(f"   Totaal t.o.v. start ${start:,.0f}: {(a.equity - start) / start * 100:+.2f}%  "
                      f"(bodem 5ers: ${start * 0.9:,.0f})")
                print(f"   Zwevend resultaat nu: ${a.equity - a.balance:+,.2f}")
                mt5.shutdown()
        except ImportError:
            print("   MetaTrader5-pakket niet gevonden (alleen beschikbaar op de Windows-VM)")
        except Exception as e:
            print(f"   fout: {type(e).__name__}: {e}")
    print()


if __name__ == "__main__":
    main()
