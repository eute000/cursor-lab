@echo off
chcp 65001 >nul
rem 取消开机自启并结束正在运行的点击特效进程
cd /d "%~dp0"
set "PY=C:\Users\17954\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "tools\click_fx.py" --autostart-remove
echo 正在结束已运行的点击特效进程...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*click_fx.py*' -and $_.Name -like 'python*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
powershell -NoProfile -Command "Add-Type -Namespace W -Name N -MemberDefinition '[System.Runtime.InteropServices.DllImport(\"user32.dll\")]public static extern bool SystemParametersInfo(uint a,uint b,System.IntPtr c,uint d);'; [void][W.N]::SystemParametersInfo(0x57, 0, [IntPtr]::Zero, 3)"
echo 已取消（指针已恢复）
pause
