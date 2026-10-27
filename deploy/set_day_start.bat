@echo off
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
if "%~1"=="" (
  python deploy\set_day_start.py --show
  echo.
  echo Voorbeeld: deploy\set_day_start.py --floor 47679   ^(limiet van het 5ers-dashboard^)
) else (
  python deploy\set_day_start.py %*
)
echo.
pause
