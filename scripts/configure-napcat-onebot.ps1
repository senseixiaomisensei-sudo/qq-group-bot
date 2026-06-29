$ErrorActionPreference = "Stop"

$NapCatRoot = "D:\napcat"
$ConfigCandidates = @(
  (Join-Path $NapCatRoot "config\onebot11.json"),
  (Join-Path $NapCatRoot "napcat\config\onebot11.json"),
  (Join-Path $NapCatRoot "NapCat.Shell\config\onebot11.json")
)

$ConfigPath = $ConfigCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $ConfigPath) {
  $ConfigPath = $ConfigCandidates[0]
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ConfigPath) | Out-Null
}

$config = @{
  network = @{
    httpServers = @()
    httpSseServers = @()
    httpClients = @()
    websocketServers = @()
    websocketClients = @(
      @{
        enable = $true
        name = "NoneBot2"
        url = "ws://127.0.0.1:18080/onebot/v11/ws"
        messagePostFormat = "array"
        reportSelfMessage = $false
        reconnectInterval = 5000
        token = ""
        debug = $false
        heartInterval = 30000
      }
    )
    plugins = @()
  }
  musicSignUrl = ""
  enableLocalFile2Url = $false
  parseMultMsg = $false
  imageDownloadProxy = ""
}

$config | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ConfigPath -Encoding UTF8
Write-Output "NapCat OneBot config written: $ConfigPath"
