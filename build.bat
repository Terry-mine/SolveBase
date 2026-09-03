@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose (see start.bat for why).
REM Rebuilds the frontend into web\dist, which the backend serves directly.
REM Run this after changing anything under web\src.
REM Editing config\vocab.yaml does NOT need a rebuild - just refresh the page.
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" build
pause
exit /b 0
