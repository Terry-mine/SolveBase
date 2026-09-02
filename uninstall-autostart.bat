@echo off
chcp 65001 >nul
setlocal
REM 取消开机自启：删掉启动文件夹里的启动器。不影响手动启动。

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "HIT="

if exist "%STARTUP%\SolveBase.vbs" (
  del /f /q "%STARTUP%\SolveBase.vbs"
  echo 已删除 SolveBase.vbs
  set "HIT=1"
)
if exist "%STARTUP%\SolveBase.lnk" (
  del /f /q "%STARTUP%\SolveBase.lnk"
  echo 已删除 SolveBase.lnk
  set "HIT=1"
)

if not defined HIT (
  echo 没有找到自启项，当前本来就没开机自启。
) else (
  echo 开机自启已取消。手动启动仍然可用：双击 start.bat
)
pause
exit /b 0
