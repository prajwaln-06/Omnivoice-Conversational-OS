$ErrorActionPreference = "Stop"

$storePath = Join-Path $PSScriptRoot "whatsapp-mcp\whatsapp-bridge\store"
if (-not (Test-Path $storePath)) {
  throw "Store path not found: $storePath"
}

Write-Host "Stopping running bridge processes if any..." -ForegroundColor Yellow
Get-Process go -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Removing WhatsApp session DB for clean re-login..." -ForegroundColor Yellow
$waDb = Join-Path $storePath "whatsapp.db"
if (Test-Path $waDb) {
  Remove-Item $waDb -Force
}

Write-Host "Session reset complete. Start bridge again and scan QR." -ForegroundColor Green
