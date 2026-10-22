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

function Invoke-NativeCommand {
    # Windows PowerShell 5.1 turns native stderr into a terminating error when it
    # is merged with 2>&1 under ErrorActionPreference=Stop; PowerShell 7 does not.
    # Capture it as text on both and let the caller decide on the exit code.
    param([scriptblock]$Command)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $output = & $Command 2>&1 } finally { $ErrorActionPreference = $previous }
    [pscustomobject]@{ Output = @($output | ForEach-Object { "$_" }); ExitCode = $LASTEXITCODE }
}

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

Write-Host "[1/4] Validating plugin with 'agy plugin validate --strict'..." -ForegroundColor Yellow
$validate = Invoke-NativeCommand { & $AgyPath plugin validate "$PluginDir" --strict }
$validateOutput = $validate.Output
$validateExitCode = $validate.ExitCode

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

Write-Host "[2/4] Installing/Updating plugin in Antigravity..." -ForegroundColor Yellow
$install = Invoke-NativeCommand { & $AgyPath plugin install "$PluginDir" }
$installOutput = $install.Output
$installExitCode = $install.ExitCode

if ($installExitCode -ne 0) {
    Write-Host "`nInstallation failed:" -ForegroundColor Red
    Write-Host $installOutput -ForegroundColor Red
    exit $installExitCode
} else {
    Write-Host $installOutput -ForegroundColor DarkGray
    Write-Host "Plugin installed/updated successfully!`n" -ForegroundColor Green
}

# Apply machine-local MCP overrides (e.g. context7 API key) on top of the
# installed plugin's mcp_config.json. The override file is git-ignored.
$PluginName = (Get-Content (Join-Path $PluginDir "plugin.json") -Raw | ConvertFrom-Json).name
$InstalledConfig = Join-Path $env:USERPROFILE ".gemini\config\plugins\$PluginName\mcp_config.json"
$LocalOverride = Join-Path $PluginDir "mcp_config.local.json"

Write-Host "[3/4] Applying local MCP overrides (mcp_config.local.json)..." -ForegroundColor Yellow
if ((Test-Path $LocalOverride) -and (Test-Path $InstalledConfig)) {
    $base = Get-Content $InstalledConfig -Raw | ConvertFrom-Json
    $local = Get-Content $LocalOverride -Raw | ConvertFrom-Json
    foreach ($entry in $local.mcpServers.PSObject.Properties) {
        $base.mcpServers | Add-Member -NotePropertyName $entry.Name -NotePropertyValue $entry.Value -Force
    }
    $merged = $base | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($InstalledConfig, $merged, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "Applied: $($local.mcpServers.PSObject.Properties.Name -join ', ')`n" -ForegroundColor Green
} else {
    Write-Host "No local overrides to apply (mcp_config.local.json missing or plugin not installed).`n" -ForegroundColor DarkGray
}

Write-Host "[4/4] Verifying installed plugins..." -ForegroundColor Yellow
& $AgyPath plugin list

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host " Plugin successfully installed / updated!    " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "NOTE: If you have an active 'agy' session or Antigravity IDE running," -ForegroundColor Cyan
Write-Host "please restart it to load any updated plugin files.`n" -ForegroundColor Cyan
