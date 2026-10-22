[CmdletBinding()]
param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
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
$repoRoot = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot/scripts/validate.ps1"
if ($ValidateOnly) { return }
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) { throw 'Codex CLI was not found. Install Codex desktop and ensure codex is on PATH.' }
# CLI handles installation/cache/config instead of manually imitating its state.
$marketplace = Invoke-NativeCommand { & codex plugin marketplace add $repoRoot }
if ($marketplace.ExitCode -ne 0) { throw "Marketplace registration failed. $($marketplace.Output)" }
$install = Invoke-NativeCommand { & codex plugin add coding-team@coding-team-local --json }
if ($install.ExitCode -ne 0) { throw "Plugin installation failed. $($install.Output)" }
$codexDir = Join-Path $env:USERPROFILE '.codex'
New-Item -ItemType Directory -Force "$codexDir/agents" | Out-Null
foreach ($file in Get-ChildItem "$PSScriptRoot/agents" -Filter '*.toml') {
    $target = Join-Path "$codexDir/agents" $file.Name
    if (Test-Path $target) {
        if ((Get-FileHash $target).Hash -ne (Get-FileHash $file.FullName).Hash) {
            Copy-Item $target "$target.backup-$(Get-Date -Format yyyyMMddHHmmss)"
        }
    }
    Copy-Item $file.FullName $target -Force
}
foreach ($role in @('planner', 'orchestrator')) {
    $effort = if ($role -eq 'planner') { 'high' } else { 'low' }
    $profile = "$codexDir/coding-team-$role.config.toml"
    # Windows PowerShell 5.1 reads without -Encoding UTF8 as ANSI, and binds
    # String.Split to the char[] overload, so split on an explicit offset.
    $marker = "developer_instructions = '''"
    $raw = Get-Content "$PSScriptRoot/agents/$role.toml" -Raw -Encoding UTF8
    $body = $raw.Substring($raw.IndexOf($marker) + $marker.Length)
    $text = "model = `"gpt-6-sol`"`nmodel_reasoning_effort = `"$effort`"`n$marker`n" + $body
    if (Test-Path $profile) { Copy-Item $profile "$profile.backup-$(Get-Date -Format yyyyMMddHHmmss)" }
    # Write UTF-8 without BOM: Set-Content -Encoding utf8NoBOM is PowerShell 7 only.
    [System.IO.File]::WriteAllText($profile, $text, (New-Object System.Text.UTF8Encoding $false))
}
$list = Invoke-NativeCommand { & codex plugin list --marketplace coding-team-local --json }
if ($list.ExitCode -ne 0) { throw "Installation verification failed. $($list.Output)" }
Write-Host $list.Output -ForegroundColor DarkGray
Write-Host 'Installed. Start a new Codex chat to load the plugin. CLI: codex -p coding-team-planner or codex -p coding-team-orchestrator.'
