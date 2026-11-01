@echo off
rem 启动「按下变握爪」小助手（最小化窗口，关掉窗口即停止并恢复指针）
cd /d "%~dp0.."
set PY=C:\Users\17954\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
if not exist "%PY%" set PY=python
start "CursorLab click-fx" /min "%PY%" "tools\click_fx.py"
