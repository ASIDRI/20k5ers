@echo off
REM ===================================================================
REM  5ers live bot - W5 baseline (t65 + TDD tiers)
REM  GEGENEREERD door backtest/src/w5_gen_env.py - niet met de hand
REM  aanpassen; draai het script opnieuw als de config verandert.
REM ===================================================================

REM --- broker ---
REM getest op 22, maar 22:00 UTC valt in het rollover-venster (21:30-22:30) waar spreads 5-50x uitlopen
set NIGHTLY_DERISK_HOUR=21

REM KRITIEK: ongezet = forexcom_demo
set BROKER_TYPE=fiveers_live

REM --- gevalideerde strategie-instellingen ---
set CFG_MAX_CUM_RISK=7.0
set CORR_GROUP_CAP=6
set MAX_TOTAL_POSITIONS=20
set EXCLUDE_SYMBOLS=XRP_USD,ADA_USD,BTC_USD,ETH_USD,NAS100_USD,XAG_USD,XAU_USD,CAD_JPY
set OIL_ENABLE=1
set SPX500_ENABLE=0
set CFG_TDD_CAUTION_PCT=1.5
set CFG_RISK_CAUTIOUS=0.4
set CFG_TDD_EMERGENCY_PCT=5.5
set TDD_WALL_SAFETY=5.5
set TDD_EMERGENCY_HALT=0
set NIGHTLY_DERISK=1
set NIGHTLY_MAX_PER_GROUP=0
set NIGHTLY_MAX_TOTAL=0
set NIGHTLY_R_CLOSE_LOSING=0.25
set NIGHTLY_R_NEW=0.5
set NIGHTLY_REDUCE_PCT=0.75
set RISK_REGIME_ENABLE=1
set RISK_CALM_MULT=1.45
set RISK_VOLATILE_MULT=1.0
set VOL_REGIME_DD_OFF=5.0
set VOL_REGIME_DD_MULT=1.0

REM --- dagstop: CFG_DAILY_HALT_PCT bewust NIET hier gezet. Standaard 2.5; wijzigen
REM     met deploy\set_daily_limit.bat <procent> (schrijft naar .env) ---

REM --- credentials staan in .env (niet in git) ---

REM --- console: UTF-8 zodat alle meldingen leesbaar zijn, en direct tonen ---
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

cd /d "%~dp0.."
title 20k5ers live bot

where python >nul 2>&1
if errorlevel 1 (
  echo [FOUT] Python is niet gevonden. Installeer Python 3.11 of 3.12 en vink 'Add to PATH' aan.
  goto :fail
)

echo.
echo ============ STAP 1: controle voor de start ============
python deploy\preflight.py
if errorlevel 1 goto :fail

echo.
echo ============ STAP 2: bot draait (Ctrl+C om te stoppen) ============
python -u main_live_bot.py %*
set EXITCODE=%errorlevel%
echo.
echo [BOT GESTOPT] afsluitcode %EXITCODE%. Details: logs\tradr_live.log
if not defined NO_PAUSE pause
exit /b %EXITCODE%

:fail
echo.
echo [AFGEBROKEN] De controle voor de start is mislukt. De bot is NIET gestart.
echo Los de [FOUT]-regels hierboven op en start opnieuw.
if not defined NO_PAUSE pause
exit /b 3
