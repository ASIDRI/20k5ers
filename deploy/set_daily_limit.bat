@echo off
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
if "%~1"=="" (
  echo Gebruik: deploy\set_daily_limit.bat 2.0    ^(of "reset" voor terug naar 2.5^)
  exit /b 1
)
python deploy\set_daily_limit.py %1
echo.
pause
