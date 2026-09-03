@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose (see start.bat for why).
REM Registers auto-start for the current user (no admin, no registry).
REM It writes a silent launcher into the Windows Startup folder; delete that
REM file (or run uninstall-autostart.bat) to disable it.
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" install-autostart
pause
exit /b 0
