$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path $PSScriptRoot -Parent
$manifest = Get-Content "$pluginRoot/.codex-plugin/plugin.json" -Raw | ConvertFrom-Json
if ($manifest.name -ne 'coding-team') { throw 'Unexpected plugin name.' }
$catalog = Get-Content "$(Split-Path $pluginRoot -Parent)/.agents/plugins/marketplace.json" -Raw | ConvertFrom-Json
$entry = @($catalog.plugins | Where-Object name -EQ $manifest.name)
if ($entry.Count -ne 1 -or $entry[0].source.path -ne './codex') { throw 'Marketplace must point coding-team to ./codex.' }
Get-Content "$pluginRoot/.mcp.json" -Raw | ConvertFrom-Json | Out-Null
if (@(Get-ChildItem "$pluginRoot/agents" -Filter '*.toml').Count -ne 8) { throw 'Expected eight agent definitions.' }
if (@(Get-ChildItem "$pluginRoot/skills" -Directory).Count -ne 12) { throw 'Expected twelve skills.' }
foreach ($entrySkill in @('team-plan', 'team-run', 'team-review')) {
    if (-not (Test-Path "$pluginRoot/skills/$entrySkill/SKILL.md")) { throw "Missing entry skill: $entrySkill" }
}
foreach ($role in @('planner', 'orchestrator', 'researcher', 'plan-critic', 'implementer', 'code-reviewer', 'verifier', 'devops-expert')) {
    if (-not (Select-String -LiteralPath "$pluginRoot/agents/$role.toml" -Pattern '^developer_instructions = ' -Quiet)) { throw "Missing instructions for $role" }
}
Write-Host 'Codex plugin structure validated.'
