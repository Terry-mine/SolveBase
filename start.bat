@echo off
setlocal
REM SolveBase launcher - ASCII ONLY on purpose.
REM Batch files with UTF-8 Chinese + "chcp 65001" get mangled by cmd.exe
REM (it switches codepage mid-parse and reads the rest at wrong offsets).
REM All text and logic now live in scripts\launcher.py (Python, UTF-8 safe).
REM
REM   start.bat              start service + open browser
REM   start.bat --no-browser start service only
cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0scripts\launcher.py" start %*
if errorlevel 1 pause
exit /b 0
