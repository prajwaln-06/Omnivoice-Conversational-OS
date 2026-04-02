$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridgePath = Join-Path $root "backend\whatsapp-mcp\whatsapp-bridge"

if (-not (Test-Path $bridgePath)) {
  throw "WhatsApp bridge folder not found at $bridgePath"
}

$msysGcc = "C:\msys64\ucrt64\bin\gcc.exe"
if (-not (Test-Path $msysGcc)) {
  throw "MSYS2 UCRT64 GCC not found at $msysGcc. Install MSYS2 and mingw-w64-ucrt-x86_64-gcc first."
}

# Remove old 32-bit MinGW from the current process PATH if present.
$env:Path = ($env:Path -split ';' | Where-Object { $_ -and ($_ -ne 'C:\MinGW\bin') }) -join ';'
$env:Path = "C:\msys64\ucrt64\bin;$env:Path"
$env:CC = "gcc"
$env:CXX = "g++"
$env:CGO_ENABLED = "1"

Write-Host "Using GCC:" (Get-Command gcc).Source -ForegroundColor Cyan
Write-Host "Bridge path:" $bridgePath -ForegroundColor Cyan

Push-Location $bridgePath
go run main.go
Pop-Location
