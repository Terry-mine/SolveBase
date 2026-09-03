@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose (see start.bat for why).
REM Removes auto-start. Manual start (start.bat) keeps working.
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" uninstall-autostart
pause
exit /b 0
