$ErrorActionPreference = "Stop"

$backendPath = $PSScriptRoot
$frontendPath = Join-Path (Split-Path $PSScriptRoot -Parent) "frontend"

if (-not (Test-Path $frontendPath)) {
  throw "Frontend path not found: $frontendPath"
}

$bridgeLauncher = Join-Path $backendPath "start_whatsapp_bridge_window.ps1"
$apiCmd = "Set-Location '$backendPath'; py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
$uiCmd = "Set-Location '$frontendPath'; npm run dev -- --host 0.0.0.0 --port 5173"

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "& '$bridgeLauncher'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd

Write-Host "Started bridge, backend API, and frontend in separate windows." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000/health" -ForegroundColor Cyan
