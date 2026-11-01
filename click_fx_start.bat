@echo off
chcp 65001 >nul
rem CursorLab click-fx: hold mouse -> cat bows head and grips paws
rem Close this window to stop and restore
cd /d "%~dp0"
set "PY=C:\Users\17954\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
echo ============================================
echo   CursorLab 点击特效
echo   按住鼠标左/右键  =^>  猫低头眯眼握爪
echo   松开            =^>  恢复
echo   关掉本窗口即停止
echo ============================================
echo.
"%PY%" "tools\click_fx.py"
echo.
echo 已退出（若上面有报错，截图发我）
pause
