param(
  [string]$To = "+918660573165",
  [switch]$PlayConfirmation
)

$ErrorActionPreference = "Stop"
$py = "C:/ProgramData/miniconda3/python.exe"
$script = Join-Path $PSScriptRoot "voice_auto_send.py"
$args = @($script, "--to", $To)
if ($PlayConfirmation) { $args += "--play-confirmation" }

Write-Host "Using Python:" $py
& $py @args
