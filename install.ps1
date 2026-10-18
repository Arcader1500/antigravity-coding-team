<#
.SYNOPSIS
    Installs or updates the antigravity-coding-team plugin in Antigravity.
.DESCRIPTION
    Validates the plugin structure using 'agy plugin validate --strict',
    installs/updates it via 'agy plugin install', and checks status with 'agy plugin list'.
.PARAMETER ValidateOnly
    Only validates the plugin without installing.
.EXAMPLE
    .\install.ps1
.EXAMPLE
    .\install.ps1 -ValidateOnly
#>
[CmdletBinding()]
param(
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

$PluginDir = $PSScriptRoot
if (-not $PluginDir) {
    $PluginDir = (Get-Location).Path
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Antigravity Coding Team Plugin Installer  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Plugin Directory: $PluginDir`n" -ForegroundColor DarkGray

# Check if 'agy' CLI is installed and accessible
$AgyCmd = Get-Command "agy" -ErrorAction SilentlyContinue
if (-not $AgyCmd) {
    # Check default install location on Windows
    $DefaultAgy = "$env:LOCALAPPDATA\agy\bin\agy.exe"
    if (Test-Path $DefaultAgy) {
        $AgyPath = $DefaultAgy
    } else {
        Write-Error "The 'agy' CLI command was not found in PATH or at '$DefaultAgy'. Please ensure Antigravity CLI is installed."
        exit 1
    }
} else {
    $AgyPath = $AgyCmd.Source
}

Write-Host "[1/3] Validating plugin with 'agy plugin validate --strict'..." -ForegroundColor Yellow
$validateOutput = & $AgyPath plugin validate "$PluginDir" --strict 2>&1
$validateExitCode = $LASTEXITCODE

if ($validateExitCode -ne 0) {
    Write-Host "`nPlugin validation failed:" -ForegroundColor Red
    Write-Host $validateOutput -ForegroundColor Red
    exit $validateExitCode
} else {
    Write-Host $validateOutput -ForegroundColor DarkGray
    Write-Host "Validation passed successfully!`n" -ForegroundColor Green
}

if ($ValidateOnly) {
    Write-Host "Validate-only mode specified. Skipping installation." -ForegroundColor Yellow
    exit 0
}

Write-Host "[2/3] Installing/Updating plugin in Antigravity..." -ForegroundColor Yellow
$installOutput = & $AgyPath plugin install "$PluginDir" 2>&1
$installExitCode = $LASTEXITCODE

if ($installExitCode -ne 0) {
    Write-Host "`nInstallation failed:" -ForegroundColor Red
    Write-Host $installOutput -ForegroundColor Red
    exit $installExitCode
} else {
    Write-Host $installOutput -ForegroundColor DarkGray
    Write-Host "Plugin installed/updated successfully!`n" -ForegroundColor Green
}

Write-Host "[3/3] Verifying installed plugins..." -ForegroundColor Yellow
& $AgyPath plugin list

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host " Plugin successfully installed / updated!    " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "NOTE: If you have an active 'agy' session or Antigravity IDE running," -ForegroundColor Cyan
Write-Host "please restart it to load any updated plugin files.`n" -ForegroundColor Cyan
