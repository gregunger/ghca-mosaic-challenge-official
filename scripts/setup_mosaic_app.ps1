# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
<#
.SYNOPSIS
Bootstrap a fresh Windows MOSAIC checkout for GitHub Copilot App.
.DESCRIPTION
Installs missing Python and Copilot CLI prerequisites through WinGet, configures
this checkout's local MCP server and isolated MOSAIC worker, then runs offline
validation. App installation, sign-in, policy approval and in-App MCP verification
remain explicit human checkpoints.
.PARAMETER OfflineOnly
Skip Copilot CLI installation, authentication, and model-backed worker configuration.
.EXAMPLE
.\scripts\setup_mosaic_app.ps1
.EXAMPLE
.\scripts\setup_mosaic_app.ps1 -OfflineOnly
#>
[CmdletBinding()]
param(
    [switch]$OfflineOnly
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$Purpose
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$Purpose failed with exit code $LASTEXITCODE."
    }
}

function Refresh-ProcessPath {
    $extraPaths = @(
        [Environment]::GetEnvironmentVariable("Path", "Machine"),
        [Environment]::GetEnvironmentVariable("Path", "User")
    ) -join ";"

    $segments = @($env:Path -split ";") + @($extraPaths -split ";")
    $uniqueSegments = [System.Collections.Generic.List[string]]::new()
    foreach ($segment in $segments) {
        if (-not [string]::IsNullOrWhiteSpace($segment) -and
            -not $uniqueSegments.Contains($segment)) {
            $uniqueSegments.Add($segment)
        }
    }
    $env:Path = $uniqueSegments -join ";"
}

function Install-WinGetPackage {
    param(
        [Parameter(Mandatory = $true)][string]$PackageId,
        [Parameter(Mandatory = $true)][string]$Purpose
    )

    $winget = Get-Command winget.exe -CommandType Application -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw @"
WinGet is not available, so $Purpose cannot be installed automatically.
Use the official installer, reopen PowerShell, and rerun this script:
  Python: https://www.python.org/downloads/windows/
  Copilot CLI: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli
"@
    }

    Write-Host "Installing $Purpose using the official WinGet package $PackageId ..."
    Invoke-CheckedCommand -FilePath $winget.Source -ArgumentList @(
        "install", "--id", $PackageId, "--exact", "--source", "winget",
        "--accept-source-agreements", "--accept-package-agreements"
    ) -Purpose "WinGet installation of $Purpose"
    Refresh-ProcessPath
}

function Test-McpConfiguration {
    param(
        [Parameter(Mandatory = $true)]$Configuration,
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$SourcePath
    )

    if (-not $Configuration.mcpServers -or
        @($Configuration.mcpServers.PSObject.Properties).Count -ne 1) {
        return $false
    }
    $server = $Configuration.mcpServers.'mosaic-synthetic-evidence'
    if (-not $server) {
        return $false
    }

    $expectedTools = @("list_approved_sources", "read_approved_source")
    $actualTools = @($server.tools)
    return (
        $server.type -eq "stdio" -and
        $server.command -eq $PythonPath -and
        @($server.args).Count -eq 2 -and
        $server.args[0] -eq "-m" -and
        $server.args[1] -eq "mosaic.mcp_server" -and
        $server.env.PYTHONPATH -eq $SourcePath -and
        $server.env.PYTHONNOUSERSITE -eq "1" -and
        $actualTools.Count -eq $expectedTools.Count -and
        $actualTools[0] -eq $expectedTools[0] -and
        $actualTools[1] -eq $expectedTools[1]
    )
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$git = Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $git) {
    throw "Git is required to clone this repository. Install Git for Windows and reopen PowerShell: https://gitforwindows.org/"
}
Invoke-CheckedCommand -FilePath $git.Source -ArgumentList @(
    "-C", $projectRoot, "rev-parse", "--show-toplevel"
) -Purpose "Repository checkout verification"

$architecture = $env:PROCESSOR_ARCHITEW6432
if ([string]::IsNullOrWhiteSpace($architecture)) {
    $architecture = $env:PROCESSOR_ARCHITECTURE
}
if ($architecture -notin @("AMD64", "ARM64")) {
    throw "This bootstrap supports Windows x64 and ARM64 only; detected $architecture."
}

$appDownload = "https://github.com/features/ai/github-app"
Write-Host ""
Write-Host "This will prepare the current checkout at $projectRoot."
Write-Host "It will not change system-wide execution policy, install optional WorkIQ,"
Write-Host "access customer systems, or run paid model inference."
Write-Host "The GitHub Copilot App itself must be downloaded and signed into by you."
Write-Host ""

$pythonLauncher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
if ($pythonLauncher) {
    & $pythonLauncher.Source -3.12 --version *> $null
}
if (-not $pythonLauncher -or $LASTEXITCODE -ne 0) {
    Install-WinGetPackage -PackageId "Python.Python.3.12" -Purpose "Python 3.12"
    $pythonLauncher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
}
if (-not $pythonLauncher) {
    throw "Python 3.12 launcher was not found after installation. Reopen PowerShell and rerun this script."
}
& $pythonLauncher.Source -3.12 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 is not available to the launcher. Reopen PowerShell and rerun this script."
}

$pythonVersionText = & $pythonLauncher.Source -3.12 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $pythonVersionText.Trim() -ne "3.12") {
    throw "Expected Python 3.12 from the launcher; found '$pythonVersionText'."
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating the repository-local Python environment ..."
    Invoke-CheckedCommand -FilePath $pythonLauncher.Source -ArgumentList @(
        "-3.12", "-m", "venv", (Join-Path $projectRoot ".venv")
    ) -Purpose "Python virtual environment creation"
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "The repository virtual environment was not created at $venvPython."
}

Push-Location -LiteralPath $projectRoot
try {
    Write-Host "Installing the repository's declared development and MCP dependencies ..."
    Invoke-CheckedCommand -FilePath $venvPython -ArgumentList @(
        "-m", "pip", "install", "-e", ".[dev,mcp]"
    ) -Purpose "MOSAIC Python dependency installation"

    $sharedMcpPath = Join-Path $projectRoot ".github\mcp.json"
    if (-not (Test-Path -LiteralPath $sharedMcpPath)) {
        throw "The shared MCP configuration is missing: $sharedMcpPath"
    }
    $sharedConfiguration = Get-Content -LiteralPath $sharedMcpPath -Raw |
        ConvertFrom-Json -ErrorAction Stop
    $expectedServer = $sharedConfiguration.mcpServers.'mosaic-synthetic-evidence'
    if (@($sharedConfiguration.mcpServers.PSObject.Properties).Count -ne 1 -or
        -not $expectedServer -or
        $expectedServer.type -ne "stdio" -or
        @($expectedServer.tools).Count -ne 2 -or
        $expectedServer.tools[0] -ne "list_approved_sources" -or
        $expectedServer.tools[1] -ne "read_approved_source") {
        throw "The shared MCP configuration does not match the expected two-tool allowlist. Stop for review."
    }

    $localMcpPath = Join-Path $projectRoot ".mcp.json"
    $sourcePath = Join-Path $projectRoot "src"
    $resolvedPythonPath = (Resolve-Path -LiteralPath $venvPython).Path
    if (Test-Path -LiteralPath $localMcpPath) {
        $localConfiguration = Get-Content -LiteralPath $localMcpPath -Raw |
            ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-McpConfiguration -Configuration $localConfiguration `
            -PythonPath $resolvedPythonPath -SourcePath $sourcePath)) {
            throw "An existing .mcp.json differs from this setup's expected MCP configuration. It was not changed; review it manually."
        }
        Write-Host "Existing local MCP configuration matches; leaving it unchanged."
    }
    else {
        $localConfiguration = $sharedConfiguration | ConvertTo-Json -Depth 10 |
            ConvertFrom-Json -ErrorAction Stop
        $localServer = $localConfiguration.mcpServers.'mosaic-synthetic-evidence'
        $localServer.command = $resolvedPythonPath
        $localServer.env.PYTHONPATH = $sourcePath

        $temporaryDirectory = Join-Path $projectRoot "build\setup-check"
        New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null
        $temporaryMcpPath = Join-Path $temporaryDirectory ".mcp.json.setup-tmp"
        $localConfiguration | ConvertTo-Json -Depth 10 |
            Set-Content -LiteralPath $temporaryMcpPath -Encoding UTF8
        if (Test-Path -LiteralPath $localMcpPath) {
            Remove-Item -LiteralPath $temporaryMcpPath -Force
            throw "A .mcp.json appeared during setup. It was not overwritten; review the existing file."
        }
        Move-Item -LiteralPath $temporaryMcpPath -Destination $localMcpPath
        Write-Host "Created the ignored, checkout-local MCP override."
    }

    $ignoredMcp = & $git.Source -C $projectRoot check-ignore --quiet .mcp.json
    if ($LASTEXITCODE -ne 0) {
        throw ".mcp.json is not ignored by Git. Stop before putting local configuration in the checkout."
    }

    if (-not $OfflineOnly) {
        $copilot = Get-Command copilot.exe -CommandType Application -ErrorAction SilentlyContinue
        if (-not $copilot) {
            Install-WinGetPackage -PackageId "GitHub.Copilot" -Purpose "GitHub Copilot CLI"
            $copilot = Get-Command copilot.exe -CommandType Application -ErrorAction SilentlyContinue
        }
        if (-not $copilot) {
            throw "The native copilot.exe was not found after installation. Reopen PowerShell and rerun this script."
        }

        $workerConfigurationPath = Join-Path $projectRoot "build\intake\copilot-worker.json"
        $workerProfilePath = Join-Path $projectRoot "build\intake\.copilot-cli"
        if (Test-Path -LiteralPath $workerConfigurationPath) {
            Write-Host "Existing worker settings found; validating without replacing them."
            Invoke-CheckedCommand -FilePath $venvPython -ArgumentList @(
                "-m", "mosaic.jobs", "copilot-settings"
            ) -Purpose "Existing Copilot worker settings validation"
        }
        else {
            if (Test-Path -LiteralPath $workerProfilePath) {
                throw "A worker profile exists without its settings file. Review $workerProfilePath manually; it was not changed."
            }
            $environmentOverride = @(
                Get-ChildItem Env: | Where-Object {
                    ($_.Name -in @(
                        "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
                        "COPILOT_OFFLINE"
                    ) -or $_.Name -like "COPILOT_PROVIDER_*") -and
                    -not [string]::IsNullOrEmpty($_.Value)
                } | ForEach-Object { $_.Name }
            )
            if ($environmentOverride.Count -gt 0) {
                throw "Remove or resolve inherited Copilot token/provider overrides under your organization's credential policy before OAuth setup. Variable names: $($environmentOverride -join ', ')"
            }

            Write-Host ""
            Write-Host "Copilot CLI sign-in and model selection require your input."
            Write-Host "Use the authorized account. Do not accept plaintext credential storage."
            Write-Host "When the CLI opens, use /user and /model, then /exit. Do not enter a business prompt."
            Write-Host ""

            New-Item -ItemType Directory -Path $workerProfilePath -Force | Out-Null
            $profileEnvironment = @{
                COPILOT_HOME = $workerProfilePath
                HOME = $workerProfilePath
                USERPROFILE = $workerProfilePath
                GH_CONFIG_DIR = Join-Path $workerProfilePath "gh"
                XDG_CONFIG_HOME = Join-Path $workerProfilePath ".config"
                COPILOT_ALLOW_ALL = "false"
            }
            $previousEnvironment = @{}
            foreach ($name in $profileEnvironment.Keys) {
                $previousEnvironment[$name] =
                    [Environment]::GetEnvironmentVariable($name, "Process")
            }

            Push-Location -LiteralPath $workerProfilePath
            try {
                foreach ($name in $profileEnvironment.Keys) {
                    [Environment]::SetEnvironmentVariable(
                        $name, $profileEnvironment[$name], "Process"
                    )
                }
                Invoke-CheckedCommand -FilePath $copilot.Source `
                    -ArgumentList @("login") -Purpose "Copilot CLI OAuth sign-in"
                Invoke-CheckedCommand -FilePath $copilot.Source -ArgumentList @(
                    "--no-custom-instructions", "--disable-builtin-mcps",
                    "--available-tools=__mosaic_no_tools__", "--no-auto-update",
                    "--no-remote-export"
                ) -Purpose "Restricted Copilot CLI account and model inspection"
            }
            finally {
                Pop-Location
                foreach ($name in $previousEnvironment.Keys) {
                    [Environment]::SetEnvironmentVariable(
                        $name, $previousEnvironment[$name], "Process"
                    )
                }
            }

            $modelId = Read-Host "Enter the exact approved Copilot CLI model ID shown by /model (not auto)"
            if ([string]::IsNullOrWhiteSpace($modelId) -or $modelId -eq "auto") {
                throw "An explicit, approved model ID is required. No worker settings were written."
            }
            $creditLimitText = Read-Host "Maximum AI credits for one analysis call (30-300; default 30)"
            if ([string]::IsNullOrWhiteSpace($creditLimitText)) { $creditLimitText = "30" }
            $creditLimit = 0
            if (-not [int]::TryParse($creditLimitText, [ref]$creditLimit) -or
                $creditLimit -lt 30 -or $creditLimit -gt 300) {
                throw "The credit limit must be an integer from 30 through 300."
            }
            $timeoutText = Read-Host "Analysis deadline in seconds (1-1800; default 600)"
            if ([string]::IsNullOrWhiteSpace($timeoutText)) { $timeoutText = "600" }
            $timeout = 0
            if (-not [int]::TryParse($timeoutText, [ref]$timeout) -or
                $timeout -lt 1 -or $timeout -gt 1800) {
                throw "The model deadline must be an integer from 1 through 1800 seconds."
            }

            Invoke-CheckedCommand -FilePath $venvPython -ArgumentList @(
                "-m", "mosaic.jobs", "configure-copilot",
                "--copilot-executable", $copilot.Source,
                "--model", $modelId,
                "--max-ai-credits", "$creditLimit",
                "--model-timeout", "$timeout"
            ) -Purpose "MOSAIC worker configuration"
        }
    }

    Write-Host ""
    Write-Host "Running the offline synthetic generation and test suite ..."
    $runId = Get-Date -Format "yyyyMMdd-HHmmss"
    $outputDirectory = Join-Path $projectRoot "build\setup-check\$runId\reference"
    Invoke-CheckedCommand -FilePath $venvPython -ArgumentList @(
        "-m", "mosaic.cli", "--output", $outputDirectory
    ) -Purpose "Offline synthetic MOSAIC generation"
    Invoke-CheckedCommand -FilePath $venvPython -ArgumentList @(
        "-m", "pytest"
    ) -Purpose "MOSAIC test suite"

    Write-Host ""
    Write-Host "Opening the official GitHub Copilot App download page."
    try {
        Start-Process $appDownload
    }
    catch {
        Write-Warning "Could not open the browser automatically. Open the official App download page: $appDownload"
    }
    Write-Host "Install GitHub Copilot App if needed, sign in, and open this checkout as a trusted local project."
    Write-Host "In Customize > MCP > Installed, verify mosaic-synthetic-evidence."
    Write-Host "In a new MOSAIC Orchestrator session, call list_approved_sources and read_approved_source for EVD-002."
    Write-Host ""

    $runDirectory = Split-Path -Parent $outputDirectory
    $readinessPath = Join-Path $runDirectory "setup-status.json"
    $readiness = [ordered]@{
        checkedAt = [DateTime]::UtcNow.ToString("o")
        repository = $projectRoot
        offlineGeneration = "passed"
        pythonTests = "passed"
        localMcpConfiguration = "passed"
        workerConfiguration = if ($OfflineOnly) { "skipped_offline_only" } else { "configured_or_previously_validated" }
        copilotAppSignIn = "requires_user_confirmation"
        inAppMcpToolCalls = "requires_user_verification"
        overall = "awaiting_in_app_verification"
    }
    $readiness | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $readinessPath -Encoding UTF8

    Write-Host "Local setup checks passed. In-App sign-in, project trust and both MCP tool calls are still required."
    Write-Host "Readiness record: $readinessPath"
    Write-Host "Do not treat this local validation as customer approval or deployment authorization."
}
finally {
    Pop-Location
}
