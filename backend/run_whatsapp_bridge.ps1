$ErrorActionPreference = "Stop"

$bridgePath = Join-Path $PSScriptRoot "whatsapp-mcp\whatsapp-bridge"
if (-not (Test-Path $bridgePath)) {
  throw "Bridge path not found: $bridgePath"
}

# Ensure wrong 32-bit MinGW is not used by cgo.
$env:Path = (($env:Path -split ';') | Where-Object { $_ -ne 'C:\MinGW\bin' }) -join ';'
$env:Path = "C:\msys64\ucrt64\bin;$env:Path"
$env:CC = "gcc"
$env:CXX = "g++"
$env:CGO_ENABLED = "1"

Write-Host "Using GCC:" -ForegroundColor Cyan
& gcc -v | Out-Host

Push-Location $bridgePath
try {
  Write-Host "Starting WhatsApp bridge on :8080 ..." -ForegroundColor Green
  go run main.go
}
finally {
  Pop-Location
}
