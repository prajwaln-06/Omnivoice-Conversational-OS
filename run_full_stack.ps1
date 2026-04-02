$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $root "backend"
$frontendPath = Join-Path $root "frontend"

if (-not (Test-Path $backendPath)) {
  throw "Backend folder not found at $backendPath"
}

if (-not (Test-Path $frontendPath)) {
  throw "Frontend folder not found at $frontendPath"
}

Write-Host "Starting OmniVoice full stack..." -ForegroundColor Cyan

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
  $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $pythonCmd = "py -3"
} else {
  throw "Python was not found in PATH. Install Python or update this script with your interpreter path."
}

if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
  Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
  Push-Location $frontendPath
  npm install
  Pop-Location
}

$backendRequirements = Join-Path $backendPath "requirements.txt"
if (-not (Test-Path $backendRequirements)) {
  throw "Backend requirements file not found at $backendRequirements"
}

Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Push-Location $backendPath
& $pythonCmd -m pip install -r "$backendRequirements"
Pop-Location

$backendCommand = "$pythonCmd -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
$frontendCommand = "npm run dev -- --host 0.0.0.0 --port 5173"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; $backendCommand"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; $frontendCommand"

Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Two new PowerShell windows were opened for backend and frontend." -ForegroundColor Cyan
