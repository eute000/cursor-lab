# CursorLab 安装器
# 仓库内用法: powershell -ExecutionPolicy Bypass -File install.ps1
# 解压包内用法: 双击 安装.bat（或 powershell -ExecutionPolicy Bypass -File install.ps1）
param(
    [string]$Dir = "",
    [string]$Name = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 找指针文件：优先 .\cursors（发行包），其次 .\out\pixel-cat（仓库）
if (-not $Dir) {
    foreach ($cand in @((Join-Path $root "cursors"), (Join-Path $root "out\pixel-cat"))) {
        if (Test-Path $cand) { $Dir = $cand; break }
    }
}
if (-not $Dir -or -not (Test-Path $Dir)) {
    throw "找不到指针目录。先运行 python -m cursorlab.build 生成，或用 -Dir 指定"
}
$Dir = (Resolve-Path $Dir).Path

$map = [ordered]@{
    Arrow       = "arrow.cur"
    Help        = "help.cur"
    AppStarting = "appstarting.ani"
    Wait        = "wait.ani"
    Crosshair   = "crosshair.cur"
    IBeam       = "ibeam.cur"
    NWPen       = "nwpen.cur"
    No          = "no.cur"
    SizeNS      = "sizens.cur"
    SizeWE      = "sizewe.cur"
    SizeNWSE    = "sizenwse.cur"
    SizeNESW    = "sizenesw.cur"
    SizeAll     = "sizeall.cur"
    UpArrow     = "uparrow.cur"
    Hand        = "hand.cur"
    Pin         = "pin.cur"
    Person      = "person.cur"
}

if (-not $Name) { $Name = "CursorLab " + (Split-Path $Dir -Leaf) }

$curKey     = "HKCU:\Control Panel\Cursors"
$schemeKey  = "$curKey\Schemes"
$backupFile = Join-Path $root "backup-cursors.json"

function Read-KeyValues($path) {
    $out = [ordered]@{}
    if (-not (Test-Path $path)) { return $out }
    $item = Get-Item -Path $path
    foreach ($n in $item.GetValueNames()) { $out[$n] = $item.GetValue($n) }
    return $out
}

# 1. 备份（只在第一次装时备份，避免把已经装上的主题当成"原样"）
if (-not (Test-Path $backupFile)) {
    # 注册表默认值的名字是空串，JSON 里存成 __default__，
    # 否则 PS 5.1 的 ConvertFrom-Json 会因为空属性名直接报错
    $cursors = Read-KeyValues $curKey
    if ($cursors.Contains("")) {
        $cursors["__default__"] = $cursors[""]
        $cursors.Remove("")
    }
    $backup = [ordered]@{
        when    = (Get-Date).ToString("s")
        cursors = $cursors
        schemes = Read-KeyValues $schemeKey
    }
    ($backup | ConvertTo-Json -Depth 6) | Set-Content -Path $backupFile -Encoding UTF8
    Write-Host "[1/3] 备份原始指针 -> backup-cursors.json" -ForegroundColor DarkGray
} else {
    Write-Host "[1/3] 备份已存在，跳过" -ForegroundColor DarkGray
}

# 2. 写 HKCU（用户级，不需要管理员）
#    注意：Get-Item 拿到的是只读键，必须用 OpenSubKey(..., $true) / CreateSubKey
$paths = @()
$curW = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Control Panel\Cursors", $true)
if (-not $curW) { throw "打不开 HKCU\Control Panel\Cursors" }
foreach ($role in $map.Keys) {
    $file = Join-Path $Dir $map[$role]
    if (-not (Test-Path $file)) { throw "缺文件: $file" }
    $curW.SetValue($role, $file, [Microsoft.Win32.RegistryValueKind]::String)
    $paths += $file
}
$curW.SetValue("", $Name, [Microsoft.Win32.RegistryValueKind]::String)
$curW.Close()
$schemeW = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Control Panel\Cursors\Schemes")
$schemeW.SetValue($Name, ($paths -join ";"), [Microsoft.Win32.RegistryValueKind]::String)
$schemeW.Close()
Write-Host "[2/3] 已写入 17 个指针，主题名 `"$Name`"" -ForegroundColor DarkGray

# 3. 立刻生效
if (-not ("Win.Native" -as [type])) {
    Add-Type -Namespace Win -Name Native -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError=true)]
public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, System.IntPtr pvParam, uint fWinIni);
'@
}
[void][Win.Native]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 3)
Write-Host "[3/3] 已刷新，指针立刻生效" -ForegroundColor Green
Write-Host ""
Write-Host "当前主题: $Name" -ForegroundColor Cyan
Write-Host "还原: powershell -ExecutionPolicy Bypass -File uninstall.ps1" -ForegroundColor DarkGray
