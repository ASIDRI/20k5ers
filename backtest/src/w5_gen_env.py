#!/usr/bin/env python3
"""
Genereert het Windows-startbestand uit BASELINE_t65_tdd_FROZEN.json.

Waarom genereren en niet met de hand schrijven: een handgeschreven .bat loopt
uit de pas zodra de config verandert, en niemand merkt dat. Dit leest de frozen
config en zet er precies die variabelen in die de LIVE bot leest — niet de
backtest-only vlaggen (TDD_WORST_CASE, TERMINAL_ON_BREACH), want die hebben
live geen betekenis en zouden alleen verwarren.

Eén bewuste afwijking wordt expliciet gezet in plaats van overgenomen:
NIGHTLY_DERISK_HOUR staat in de frozen config op 22 (wat getest is) maar moet
live op 21, omdat 22:00 UTC midden in het rollover-venster valt waar spreads
5-50x uitlopen — kosten die de vlakke-spread simulator niet ziet.

Credentials worden NIET in het bestand gezet. Die staan in .env (niet in git);
deploy/preflight.py controleert ze voor de start.

Draaien:  uv run python3 backtest/src/w5_gen_env.py
"""
import importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
_w = importlib.util.spec_from_file_location("w5", str(HERE / "w5_common.py"))
w5 = importlib.util.module_from_spec(_w); _w.loader.exec_module(w5)

# Alleen wat main_live_bot.py daadwerkelijk uitleest.
LIVE_KEYS = [
    "CFG_MAX_CUM_RISK", "CORR_GROUP_CAP", "MAX_TOTAL_POSITIONS", "EXCLUDE_SYMBOLS",
    # Expliciet vastzetten, ook al staat de standaard nu op aan: het
    # deploybestand hoort te zeggen wat er gehandeld wordt en niet af te
    # hangen van een standaard die later kan verschuiven.
    "OIL_ENABLE", "SPX500_ENABLE",
    "CFG_TDD_CAUTION_PCT", "CFG_RISK_CAUTIOUS", "CFG_TDD_EMERGENCY_PCT",
    "TDD_WALL_SAFETY", "CFG_DAILY_HALT_PCT", "TDD_EMERGENCY_HALT",
    "NIGHTLY_DERISK", "NIGHTLY_DERISK_HOUR", "NIGHTLY_MAX_PER_GROUP",
    "NIGHTLY_MAX_TOTAL", "NIGHTLY_R_CLOSE_LOSING", "NIGHTLY_R_NEW",
    "NIGHTLY_REDUCE_PCT", "RISK_REGIME_ENABLE", "RISK_CALM_MULT",
    "RISK_VOLATILE_MULT", "VOL_REGIME_DD_OFF", "VOL_REGIME_DD_MULT",
]
OVERRIDES = {
    "NIGHTLY_DERISK_HOUR": ("21", "getest op 22, maar 22:00 UTC valt in het "
                                  "rollover-venster (21:30-22:30) waar spreads "
                                  "5-50x uitlopen"),
    "BROKER_TYPE": ("fiveers_live", "KRITIEK: ongezet = forexcom_demo"),
}


def main():
    frozen = json.loads((w5.W5_DIR / "BASELINE_t65_tdd_FROZEN.json").read_text())
    eff = {**w5.cs.dh.BASE_ENV, **w5.BASE_ENV, **frozen["env"]}
    lines = [
        "@echo off",
        "REM ===================================================================",
        "REM  5ers live bot — W5 baseline (t65 + TDD tiers)",
        "REM  GEGENEREERD door backtest/src/w5_gen_env.py — niet met de hand",
        "REM  aanpassen; draai het script opnieuw als de config verandert.",
        "REM ===================================================================",
        "",
        "REM --- broker ---",
    ]
    for k, (v, why) in OVERRIDES.items():
        lines += [f"REM {why}", f"set {k}={v}", ""]
    lines.append("REM --- gevalideerde strategie-instellingen ---")
    for k in LIVE_KEYS:
        if k in OVERRIDES:
            continue
        if k == "CFG_DAILY_HALT_PCT":
            continue
        v = eff.get(k)
        if v is None:
            continue
        lines.append(f"set {k}={v}")
    lines += [
        "",
        "REM --- dagstop: CFG_DAILY_HALT_PCT bewust NIET hier gezet. Standaard 2.5; wijzigen",
        "REM     met deploy\\set_daily_limit.bat <procent> (schrijft naar .env) ---",
        "",
        "REM --- credentials staan in .env (niet in git) ---",
        "",
        "REM --- console: UTF-8 zodat alle meldingen leesbaar zijn, en direct tonen ---",
        "chcp 65001 >nul",
        "set PYTHONUTF8=1",
        "set PYTHONIOENCODING=utf-8",
        "set PYTHONUNBUFFERED=1",
        "",
        "cd /d \"%~dp0..\"",
        "title 20k5ers live bot",
        "",
        "where python >nul 2>&1",
        "if errorlevel 1 (",
        "  echo [FOUT] Python is niet gevonden. Installeer Python 3.11 of 3.12 en vink 'Add to PATH' aan.",
        "  goto :fail",
        ")",
        "",
        "echo.",
        "echo ============ STAP 1: controle voor de start ============",
        "python deploy\\preflight.py",
        "if errorlevel 1 goto :fail",
        "",
        "echo.",
        "echo ============ STAP 2: bot draait (Ctrl+C om te stoppen) ============",
        "python -u main_live_bot.py %*",
        "set EXITCODE=%errorlevel%",
        "echo.",
        "echo [BOT GESTOPT] afsluitcode %EXITCODE%. Details: logs\\tradr_live.log",
        "if not defined NO_PAUSE pause",
        "exit /b %EXITCODE%",
        "",
        ":fail",
        "echo.",
        "echo [AFGEBROKEN] De controle voor de start is mislukt. De bot is NIET gestart.",
        "echo Los de [FOUT]-regels hierboven op en start opnieuw.",
        "if not defined NO_PAUSE pause",
        "exit /b 3",
    ]
    out = REPO / "deploy" / "start_live.bat"
    out.parent.mkdir(exist_ok=True)
    text = "\r\n".join(lines) + "\r\n"
    # Zuiver ASCII: cmd leest het bestand voor 'chcp 65001' met de tekenset van
    # de machine, dus UTF-8-tekens (zoals een gedachtestreep) kunnen daar rommel geven.
    text = text.replace("\u2014", "-")
    text.encode("ascii")
    out.write_bytes(text.encode("ascii"))
    print(f"geschreven: {out}")
    print(f"  {len([k for k in LIVE_KEYS if eff.get(k) is not None])} strategie-variabelen")
    print(f"  {len(OVERRIDES)} bewuste overrides")


if __name__ == "__main__":
    main()
