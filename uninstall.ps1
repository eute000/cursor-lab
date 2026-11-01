# Cursor Lab 还原器 —— 把指针恢复成安装前的样子
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupFile = Join-Path $root "backup-cursors.json"
$curKey    = "HKCU:\Control Panel\Cursors"
$schemeKey = "$curKey\Schemes"

if (-not (Test-Path $backupFile)) {
    throw "没找到 backup-cursors.json —— 没有可还原的备份"
}

$b = Get-Content -Path $backupFile -Raw -Encoding UTF8 | ConvertFrom-Json

# 1. 恢复每个角色（用可写句柄）
$curW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors", $true)
foreach ($p in $b.cursors.PSObject.Properties) {
    $curW.SetValue([string]$p.Name, [string]$p.Value,
        [Microsoft.Win32.RegistryValueKind]::String)
}
$curW.Close()

# 2. 删掉 Cursor Lab 自己注册的主题
$schemeW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors\Schemes", $true)
if ($schemeW) {
    foreach ($n in $schemeW.GetValueNames()) {
        if ($n -like "CursorLab*") { $schemeW.DeleteValue($n) }
    }
    $schemeW.Close()
}
# 备份里原本没有、现在多出来的值也不要硬留着
$curW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors", $true)
foreach ($extra in @("Scheme Source")) {
    if (($curW.GetValueNames() -contains $extra) -and
        -not ($b.cursors.PSObject.Properties.Name -contains $extra)) {
        $curW.DeleteValue($extra)
    }
}
$curW.Close()

# 3. 刷新
if (-not ("Win.Native" -as [type])) {
    Add-Type -Namespace Win -Name Native -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError=true)]
public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, System.IntPtr pvParam, uint fWinIni);
'@
}
[void][Win.Native]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 3)

Write-Host "已还原成安装前的指针设置" -ForegroundColor Green
Write-Host "（备份文件保留在 backup-cursors.json，删掉它下次安装会重新备份）" -ForegroundColor DarkGray
