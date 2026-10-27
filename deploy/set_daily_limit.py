#!/usr/bin/env python3
"""
Past de dagstop 'geen nieuwe trades' van de bot aan in .env (CFG_DAILY_HALT_PCT).

    python deploy\\set_daily_limit.py 2.0     zet op 2.0%
    python deploy\\set_daily_limit.py reset   terug naar de geteste standaard (2.5%)

Gevolgen:
  - Eerst de bot stoppen (Ctrl+C) en daarna opnieuw starten; lopende bot leest niet opnieuw in.
  - Alleen deze poort verandert. De noodstop 'alles sluiten' (3.2%) staat vast in de code.
  - Geteste waarden: 2.0 t/m 3.5. Daarbuiten kan de bot ofwel nauwelijks nog handelen (<2.0),
    ofwel te dicht bij de 5ers-grens van 5% komen (>3.5). Meer dan 4.0 wordt geweigerd.
"""
import re
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"
KEY = "CFG_DAILY_HALT_PCT"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    arg = sys.argv[1].strip().replace(",", ".")
    if not ENV.exists():
        print(f"[FOUT] {ENV} bestaat niet. Maak eerst .env aan (zie deploy\\.env.example).")
        sys.exit(1)
    lines = ENV.read_text(encoding="utf-8").splitlines()
    pat = re.compile(rf"^\s*#?\s*{KEY}\s*=")
    if arg.lower() == "reset":
        new = None
    else:
        try:
            v = float(arg)
        except ValueError:
            print(f"[FOUT] '{arg}' is geen getal. Voorbeeld: set_daily_limit.bat 2.0")
            sys.exit(1)
        if not 1.0 <= v <= 4.0:
            print(f"[FOUT] {v}% is buiten het toegestane bereik 1.0 t/m 4.0 (5ers-grens is 5%).")
            sys.exit(1)
        if not 2.0 <= v <= 3.5:
            print(f"[LET OP] {v}% ligt buiten het geteste bereik 2.0-3.5.")
        new = f"{KEY}={v:g}"
    out, done = [], False
    for ln in lines:
        if pat.match(ln):
            if not done and new:
                out.append(new)
            done = True
            continue
        out.append(ln)
    if new and not done:
        out.append(new)
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[OK] {'terug naar standaard 2.5%' if not new else new} opgeslagen in {ENV}")
    print("     Stop de bot (Ctrl+C) en start hem opnieuw om het te laten ingaan.")
    print("     Controleer met: deploy\\show_limits.bat")


if __name__ == "__main__":
    main()
