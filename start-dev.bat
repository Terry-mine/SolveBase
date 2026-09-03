@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose (see start.bat for why).
REM Dev mode (two processes, hot reload):
REM   backend  http://127.0.0.1:8787   API
REM   frontend http://127.0.0.1:5173   hot reload, /api proxied to 8787
REM For daily note-taking use start.bat instead.
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" dev
if errorlevel 1 pause
exit /b 0
