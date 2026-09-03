@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose (see start.bat for why).
REM Shows port/PID/health + database info + record stats. First stop when
REM something looks wrong.
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" status
pause
exit /b 0
