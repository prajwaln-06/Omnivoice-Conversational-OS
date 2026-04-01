$ErrorActionPreference = "Stop"
$py = "C:/ProgramData/miniconda3/python.exe"
$script = Join-Path $PSScriptRoot "live_demo.py"
Write-Host "Using Python:" $py
& $py $script
