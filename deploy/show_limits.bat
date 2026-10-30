@echo off
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
python deploy\check_limits.py %*
echo.
pause
