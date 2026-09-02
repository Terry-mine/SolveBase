@echo off
chcp 65001 >nul
setlocal
REM ============================================================
REM  SolveBase 开发模式（双进程，前端热更新）
REM    后端 http://127.0.0.1:8787   —— API
REM    前端 http://127.0.0.1:5173   —— 改代码即刷新，/api 代理到 8787
REM
REM  日常记录用 start.bat 就够了；改前端代码时才用这个。
REM ============================================================

cd /d "%~dp0"
set "PY=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
set "NODE_DIR=C:\Users\As40159\.workbuddy\binaries\node\versions\22.22.2"

netstat -ano | findstr ":8787" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
  echo 启动后端 8787 ...
  start "SolveBase-Backend" /min "%PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8787 --reload
) else (
  echo [跳过] 后端 8787 已在运行
)

netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
  echo 启动前端 5173 ...
  start "SolveBase-Frontend" /min cmd /k "cd /d "%~dp0web" && set "PATH=%NODE_DIR%;%PATH%" && npm run dev"
) else (
  echo [跳过] 前端 5173 已在运行
)

timeout /t 6 >nul
start "" "http://127.0.0.1:5173"
exit /b 0
