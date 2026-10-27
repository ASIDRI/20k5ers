@echo off
REM Toont het logboek live in een tweede venster: elke scan, order en fout.
cd /d "%~dp0.."
powershell -NoProfile -Command "Get-Content logs\tradr_live.log -Wait -Tail 60 -Encoding UTF8"
