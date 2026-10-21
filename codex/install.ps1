#Requires -Version 7.0
[CmdletBinding()]
param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot/scripts/validate.ps1"
if ($ValidateOnly) { return }
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) { throw 'Codex CLI was not found. Install Codex desktop and ensure codex is on PATH.' }
# CLI handles installation/cache/config instead of manually imitating its state.
& codex plugin marketplace add $repoRoot
if ($LASTEXITCODE -ne 0) { throw 'Marketplace registration failed.' }
& codex plugin add coding-team@coding-team-local --json
if ($LASTEXITCODE -ne 0) { throw 'Plugin installation failed.' }
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
    $text = "model = `"gpt-6-sol`"`nmodel_reasoning_effort = `"$effort`"`ndeveloper_instructions = '''`n" + (Get-Content "$PSScriptRoot/agents/$role.toml" -Raw).Split("developer_instructions = '''")[1]
    if (Test-Path $profile) { Copy-Item $profile "$profile.backup-$(Get-Date -Format yyyyMMddHHmmss)" }
    Set-Content $profile $text -Encoding utf8NoBOM
}
& codex plugin list --marketplace coding-team-local --json
if ($LASTEXITCODE -ne 0) { throw 'Installation verification failed.' }
Write-Host 'Installed. Start a new Codex chat to load the plugin. CLI: codex -p coding-team-planner or codex -p coding-team-orchestrator.'
