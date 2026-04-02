$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $root "backend"
$frontendPath = Join-Path $root "frontend"
$bridgeScript = Join-Path $root "run_whatsapp_bridge.ps1"

if (-not (Test-Path $backendPath)) { throw "Backend folder not found: $backendPath" }
if (-not (Test-Path $frontendPath)) { throw "Frontend folder not found: $frontendPath" }
if (-not (Test-Path $bridgeScript)) { throw "Bridge launcher not found: $bridgeScript" }

Write-Host "Starting OmniVoice demo stack..." -ForegroundColor Cyan

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
  $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $pythonCmd = "py -3"
} else {
  throw "Python was not found in PATH."
}

if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
  Push-Location $frontendPath
  npm install
  Pop-Location
}

$backendRequirements = Join-Path $backendPath "requirements.txt"
if (Test-Path $backendRequirements) {
  Push-Location $backendPath
  & $pythonCmd -m pip install -r "$backendRequirements"
  Pop-Location
}

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "Set-Location '$backendPath'; $pythonCmd -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "Set-Location '$frontendPath'; npm run dev -- --host 0.0.0.0 --port 5173"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "'$bridgeScript'"

Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: check terminal for exact localhost port (5173/5174/5175...)" -ForegroundColor Green
Write-Host "WhatsApp bridge API: http://localhost:8080" -ForegroundColor Green
Write-Host "Three PowerShell windows were opened (backend/frontend/bridge)." -ForegroundColor Cyan
