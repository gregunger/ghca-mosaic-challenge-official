# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
<#
.SYNOPSIS
Generate the offline synthetic MOSAIC reference package.
.DESCRIPTION
Uses the repository virtual environment when available and stops at human review.
This entry point performs no model inference, sign-in or customer-system access.
.PARAMETER OutputDirectory
Optional report destination; defaults to demo-output/SYN-001 in the repository.
.EXAMPLE
./scripts/run_demo.ps1 -OutputDirectory build/validation/reference
#>
param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExecutable = if (Test-Path $localPython) { $localPython } else { "python" }

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $projectRoot "demo-output\SYN-001"
}

$env:PYTHONPATH = Join-Path $projectRoot "src"
Push-Location $projectRoot
try {
    & $pythonExecutable -m mosaic.cli --output $OutputDirectory
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
