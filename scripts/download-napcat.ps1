$ErrorActionPreference = "Stop"

$Target = "D:\napcat"
$Zip = Join-Path $env:TEMP "NapCat.Shell.Windows.OneKey.v4.18.7.zip"
$Urls = @(
  "https://github.com/NapNeko/NapCatQQ/releases/download/v4.18.7/NapCat.Shell.Windows.OneKey.zip",
  "https://gh.llkk.cc/https://github.com/NapNeko/NapCatQQ/releases/download/v4.18.7/NapCat.Shell.Windows.OneKey.zip",
  "https://ghproxy.net/https://github.com/NapNeko/NapCatQQ/releases/download/v4.18.7/NapCat.Shell.Windows.OneKey.zip"
)

if (Test-Path -LiteralPath $Zip) {
  Remove-Item -LiteralPath $Zip -Force
}

$downloaded = $false
foreach ($Url in $Urls) {
  Write-Output "Downloading $Url"
  curl.exe -L --retry 5 --retry-delay 3 --connect-timeout 20 --max-time 300 -o $Zip $Url
  if ((Test-Path -LiteralPath $Zip) -and ((Get-Item -LiteralPath $Zip).Length -gt 100000)) {
    $downloaded = $true
    break
  }
}

if (-not $downloaded) {
  throw "NapCat download failed. Put NapCat.Shell.Windows.OneKey.zip at $Zip and rerun this script."
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Expand-Archive -LiteralPath $Zip -DestinationPath $Target -Force
Write-Output "NapCat extracted to $Target"
