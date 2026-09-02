@echo off
chcp 65001 >nul
setlocal
REM ============================================================
REM  SolveBase 一键启动（单进程模式）
REM  后端同时托管界面，只开一个端口：http://127.0.0.1:8787
REM  运行期不需要 Node，进程不留黑窗口，日志写在 logs\server.log
REM
REM  用法：
REM    双击 start.bat        启动并自动打开浏览器
REM    start.bat silent      静默启动，不开浏览器（开机自启用）
REM ============================================================

cd /d "%~dp0"
set "PYW=C:\Users\As40159\.workbuddy\binaries\python\envs\default\Scripts\pythonw.exe"
set "PORT=8787"
set "URL=http://127.0.0.1:%PORT%"

if not exist "%PYW%" (
  echo [错误] 找不到 Python 解释器：
  echo        %PYW%
  echo        换过环境的话，改本文件顶部的 PYW 变量即可。
  if not "%1"=="silent" pause
  exit /b 1
)

if not exist "web\dist\index.html" (
  echo [提示] 前端还没构建，界面打不开（API 仍可用）。先运行一次 build.bat。
)

REM 端口已被占用就认为服务在跑，不重复启动
netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [跳过] SolveBase 已在运行： %URL%
  goto :open
)

echo 正在启动 SolveBase ...
start "" "%PYW%" "%~dp0scripts\serve_bg.py"

REM 等服务真正就绪（最多 20 秒）。用 ping 当 sleep：timeout 在无交互环境会报错
set /a tries=0
:wait
set /a tries+=1
ping -n 2 127.0.0.1 >nul
curl -s -m 2 "%URL%/api/v1/health" >nul 2>&1
if not errorlevel 1 goto :ready
if %tries% GEQ 20 (
  echo [警告] 20 秒内没等到服务就绪。
  echo        看一眼日志： %~dp0logs\server.log
  if not "%1"=="silent" pause
  exit /b 1
)
goto :wait

:ready
echo 已就绪： %URL%

:open
if "%1"=="silent" exit /b 0
start "" "%URL%"
exit /b 0
