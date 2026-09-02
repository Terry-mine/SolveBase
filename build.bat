@echo off
chcp 65001 >nul
setlocal
REM ============================================================
REM  重新构建前端，产物进 web\dist，由后端直接托管。
REM  什么时候需要跑：改过 web\src 里的代码之后。
REM  只改 config\vocab.yaml 不用构建，刷新页面即可生效。
REM ============================================================

cd /d "%~dp0web"
set "PATH=C:\Users\As40159\.workbuddy\binaries\node\versions\22.22.2;%PATH%"

if not exist "node_modules" (
  echo 首次构建，先安装依赖 ...
  call npm install --no-audit --no-fund
  if errorlevel 1 goto :fail
)

echo 清理旧产物 ...
if exist "dist" rmdir /s /q "dist"

echo 构建中 ...
call npm run build
if errorlevel 1 goto :fail

echo.
echo 构建完成。重启 SolveBase（stop.bat 再 start.bat）即生效。
timeout /t 3 >nul
exit /b 0

:fail
echo.
echo [失败] 构建没通过，看上面的报错。
pause
exit /b 1
