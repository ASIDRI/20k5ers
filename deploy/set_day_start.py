#!/usr/bin/env python3
"""
Zet de dagbasis van de bot gelijk aan die van 5ers.

De bot rekent zijn dagelijkse verlieslimiet uit de "day start equity": de hoogste van
equity en saldo bij de dagreset. Als jouw bot een andere limiet toont dan het 5ers-dashboard
(bijvoorbeeld bot 48.700, 5ers 47.679), dan staat de basis van de bot verkeerd. Hier corrigeer je dat.

    python deploy\\set_day_start.py --floor 47679   de limiet van het 5ers-dashboard (aanrader)
    python deploy\\set_day_start.py --start 50188   of de dagbasis zelf
    python deploy\\set_day_start.py --show          alleen tonen wat er nu staat

Bij --floor geldt: dagbasis = limiet / 0.95 (5ers houdt 5% dagverlies aan).

BELANGRIJK: stop de bot eerst (Ctrl+C) en start hem hierna opnieuw. Een draaiende bot leest
dit bestand niet opnieuw in en zou je wijziging terugschrijven. De waarde blijft staan tot
de volgende dagreset; daarna rekent de bot weer zelf (hoogste van equity en saldo).
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "challenge_risk_state.json"


def server_date():
    """Serverdatum zoals de bot die telt (New York + 7 uur)."""
    now = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        ny = now.astimezone(ZoneInfo("America/New_York"))
        return (ny + timedelta(hours=7)).date()
    except Exception:
        return (now + timedelta(hours=2)).date()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if not STATE.exists():
        print(f"[FOUT] {STATE.name} bestaat nog niet. Start de bot eerst een keer; hij maakt dit bestand zelf aan.")
        sys.exit(1)
    st = json.loads(STATE.read_text(encoding="utf-8"))
    cur = float(st.get("day_start_equity", 0))
    print(f"Nu in de bot : dagbasis ${cur:,.2f}  ->  dagelijkse limiet (5%) ${cur * 0.95:,.2f}")
    print(f"               datum in bestand: {st.get('current_date')}, handmatig gezet: {st.get('day_start_equity_manually_set_date') or 'nee'}")
    if args[0] == "--show":
        return
    try:
        val = float(args[1].replace(",", ".").replace("$", ""))
    except (IndexError, ValueError):
        print("[FOUT] Geef een getal op, bijvoorbeeld: --floor 47679")
        sys.exit(1)
    if args[0] == "--floor":
        new = val / 0.95
    elif args[0] == "--start":
        new = val
    else:
        print(__doc__)
        sys.exit(1)
    start = float(st.get("starting_balance", 50000))
    if not (0.5 * start <= new <= 2.0 * start):
        print(f"[FOUT] Dagbasis ${new:,.2f} is onwaarschijnlijk (verwacht tussen ${0.5*start:,.0f} en ${2*start:,.0f}). Niets aangepast.")
        sys.exit(1)
    today = server_date().isoformat()
    backup = STATE.with_suffix(".json.bak")
    backup.write_text(STATE.read_text(encoding="utf-8"), encoding="utf-8")
    st["day_start_equity"] = round(new, 2)
    st["ddd_limit"] = round(new * 0.95, 2)
    st["day_start_equity_manually_set_date"] = today
    st["current_date"] = today
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(f"Nieuw        : dagbasis ${new:,.2f}  ->  dagelijkse limiet (5%) ${new * 0.95:,.2f}   (vastgezet voor {today})")
    print(f"Reserve      : {backup.name}")
    print("Start de bot nu opnieuw en controleer met deploy\\show_limits.bat dat 'Day Start' klopt.")


if __name__ == "__main__":
    main()
