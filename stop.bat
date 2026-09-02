@echo off
chcp 65001 >nul
setlocal
REM 停止 SolveBase 的全部进程（单进程模式的 8787 + 开发模式的 5173）

set "FOUND="
for %%P in (8787 5173) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
    echo   停止端口 %%P  PID %%a
    taskkill /PID %%a /F /T >nul 2>&1
    set "FOUND=1"
  )
)

if not defined FOUND (
  echo SolveBase 未在运行。
) else (
  echo 已停止。
)
timeout /t 2 >nul
exit /b 0
