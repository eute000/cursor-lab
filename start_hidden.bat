@echo off
chcp 65001 >nul
rem 立刻在后台无窗口启动点击特效（不用重启电脑）
cd /d "%~dp0"
set "PYW=C:\Users\17954\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe"
if not exist "%PYW%" set "PYW=wscript"
if "%PYW%"=="wscript" (
  echo 没找到 pythonw.exe，改用最小化窗口启动
  start "CursorLab click-fx" /min python "tools\click_fx.py"
) else (
  start "" "%PYW%" "tools\click_fx.py"
  echo 已在后台启动（无窗口），按住鼠标试试
)
timeout /t 2 >nul
