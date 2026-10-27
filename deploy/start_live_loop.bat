@echo off
REM Start de bot en start hem na een crash na 60 seconden opnieuw.
REM Stopt NIET opnieuw als de controle voor de start mislukt (afsluitcode 3).
REM Volledig stoppen: Ctrl+C en daarna J/Y, of sluit het venster.
set NO_PAUSE=1
:again
call "%~dp0start_live.bat" %*
if %errorlevel%==3 (
  echo [GESTOPT] Controle voor de start mislukt; niet opnieuw proberen.
  pause
  exit /b 3
)
echo.
echo [%date% %time%] Bot gestopt. Opnieuw starten over 60 seconden... (Ctrl+C = stoppen)
timeout /t 60
goto again
