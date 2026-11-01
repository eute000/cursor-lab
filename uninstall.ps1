# CursorLab 还原器 —— 把指针恢复成安装前的样子
# 注意：备份 JSON 里有注册表"默认值"（空名字）这一项，PS 5.1 的 ConvertFrom-Json
#       遇到空属性名会直接报错，所以这里用 JavaScriptSerializer 读成字典。
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupFile = Join-Path $root "backup-cursors.json"

if (-not (Test-Path $backupFile)) {
    throw "没找到 backup-cursors.json —— 没有可还原的备份"
}

Add-Type -AssemblyName System.Web.Extensions
$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$b = $ser.DeserializeObject((Get-Content -Path $backupFile -Raw -Encoding UTF8))

# 1. 恢复每个角色（用可写句柄；Get-Item 拿到的是只读键）
$curW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors", $true)
if (-not $curW) { throw "打不开 HKCU\Control Panel\Cursors" }
foreach ($kv in $b["cursors"].GetEnumerator()) {
    $name = [string]$kv.Key
    if ($name -eq "__default__") { $name = "" }
    $curW.SetValue($name, [string]$kv.Value, [Microsoft.Win32.RegistryValueKind]::String)
}

# 2. 删掉 CursorLab 自己注册的主题
$schemeW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors\Schemes", $true)
if ($schemeW) {
    foreach ($n in $schemeW.GetValueNames()) {
        if ($n -like "CursorLab*") { $schemeW.DeleteValue($n) }
    }
    $schemeW.Close()
}

# 3. 备份里原本没有、后来多出来的值也清掉
foreach ($extra in @("Scheme Source")) {
    if (($curW.GetValueNames() -contains $extra) -and -not $b["cursors"].ContainsKey($extra)) {
        $curW.DeleteValue($extra)
    }
}
$curW.Close()

# 4. 刷新
if (-not ("Win.Native" -as [type])) {
    Add-Type -Namespace Win -Name Native -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError=true)]
public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, System.IntPtr pvParam, uint fWinIni);
'@
}
[void][Win.Native]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 3)

Write-Host "已还原成安装前的指针设置" -ForegroundColor Green
Write-Host "（备份文件保留在 backup-cursors.json，删掉它下次安装会重新备份）" -ForegroundColor DarkGray
