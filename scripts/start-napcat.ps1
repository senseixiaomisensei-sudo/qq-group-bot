$ErrorActionPreference = "Stop"
$NapCatRoot = "D:\napcat"
$ShellRoot = Get-ChildItem -LiteralPath $NapCatRoot -Directory -Filter "NapCat.*.Shell" |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "QQ.exe") } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $ShellRoot) {
  throw "NapCat Shell QQ.exe not found under $NapCatRoot"
}

$Boot = Join-Path $ShellRoot.FullName "NapCatWinBootMain.exe"
$Hook = Join-Path $ShellRoot.FullName "NapCatWinBootHook.dll"
foreach ($Name in @("NapCatWinBootMain.exe", "NapCatWinBootHook.dll")) {
  $Destination = Join-Path $ShellRoot.FullName $Name
  if (Test-Path -LiteralPath $Destination) {
    continue
  }
  $Source = Join-Path $NapCatRoot $Name
  if (-not (Test-Path -LiteralPath $Source)) {
    $Source = Join-Path $NapCatRoot "bootmain\$Name"
  }
  if (-not (Test-Path -LiteralPath $Source)) {
    throw "NapCat bootstrap file not found: $Name"
  }
  Copy-Item -LiteralPath $Source -Destination $Destination
}

$SourceConfig = Join-Path $NapCatRoot "config"
$TargetConfig = Join-Path $ShellRoot.FullName "config"
if (Test-Path -LiteralPath $SourceConfig) {
  New-Item -ItemType Directory -Path $TargetConfig -Force | Out-Null
  Get-ChildItem -LiteralPath $SourceConfig -Filter "onebot11*.json" |
    ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $TargetConfig $_.Name) -Force
    }
}

Set-Location -LiteralPath $ShellRoot.FullName
$BotQq = [Environment]::GetEnvironmentVariable("BOT_QQ")
if (-not $BotQq) {
  $EnvFile = "D:\数据\qq-group-bot\.env.local"
  if (Test-Path -LiteralPath $EnvFile) {
    $BotQq = (Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match '^BOT_QQ=' } | Select-Object -First 1) -replace '^BOT_QQ=', ''
  }
}

if ($BotQq) {
  & $Boot $BotQq
} else {
  & $Boot
}
