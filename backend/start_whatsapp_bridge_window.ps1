$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "run_whatsapp_bridge.ps1"
if (-not (Test-Path $scriptPath)) {
  throw "Script not found: $scriptPath"
}

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`""
Write-Host "Started WhatsApp bridge in a dedicated PowerShell window." -ForegroundColor Green
