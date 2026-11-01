@echo off
chcp 65001 >nul
rem 注册开机自启：登录后自动在后台无窗口运行点击特效
cd /d "%~dp0"
set "PY=C:\Users\17954\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "tools\click_fx.py" --autostart-install
echo.
echo 已设置。下次登录会自动生效（无窗口、无托盘）。
echo 想立刻生效而不用重启：运行 start_hidden.bat
pause
