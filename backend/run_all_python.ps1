$ErrorActionPreference = "Stop"

$py = "C:/ProgramData/miniconda3/python.exe"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Using Python:" $py
& $py -V

Write-Host "\nInstalling requirements..."
& $py -m pip install -r "$root/requirements.txt"

Write-Host "\nInstalling runtime extras..."
& $py -m pip install pyaudio groq python-dotenv

Write-Host "\nValidating all Python files..."
& $py "$root/validate_python_stack.py"

Write-Host "\nRunning orchestration test..."
& $py "$root/orchestration_test.py"

Write-Host "\nDone."
