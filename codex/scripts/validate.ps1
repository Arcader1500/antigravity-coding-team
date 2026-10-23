$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path $PSScriptRoot -Parent
$manifest = Get-Content "$pluginRoot/.codex-plugin/plugin.json" -Raw | ConvertFrom-Json
if ($manifest.name -ne 'coding-team') { throw 'Unexpected plugin name.' }
$catalog = Get-Content "$(Split-Path $pluginRoot -Parent)/.agents/plugins/marketplace.json" -Raw | ConvertFrom-Json
$entry = @($catalog.plugins | Where-Object name -EQ $manifest.name)
if ($entry.Count -ne 1 -or $entry[0].source.path -ne './codex') { throw 'Marketplace must point coding-team to ./codex.' }
Get-Content "$pluginRoot/.mcp.json" -Raw | ConvertFrom-Json | Out-Null
$hooks = Get-Content "$pluginRoot/hooks/graph-hooks.json" -Raw | ConvertFrom-Json
if (-not $hooks.hooks.SessionStart) { throw 'Missing graph SessionStart hook.' }
foreach ($handler in $hooks.hooks.SessionStart.hooks) {
    if (-not $handler.command -or -not $handler.commandWindows) { throw 'Graph hook needs command and commandWindows.' }
    # Codex runs commandWindows as PowerShell code, so a nested powershell -Command
    # would have its variables expanded away by the outer shell and the hook fails.
    if ($handler.commandWindows -match 'powershell') { throw 'commandWindows must be plain PowerShell code, not a nested powershell call.' }
}
if ($hooks.hooks.PostToolUse) { throw 'Graph updates belong to the git post-commit hook, not PostToolUse.' }
if (@(Get-ChildItem "$pluginRoot/agents" -Filter '*.toml').Count -ne 8) { throw 'Expected eight agent definitions.' }
if (@(Get-ChildItem "$pluginRoot/skills" -Directory).Count -ne 12) { throw 'Expected twelve skills.' }
foreach ($entrySkill in @('team-plan', 'team-run', 'team-review')) {
    if (-not (Test-Path "$pluginRoot/skills/$entrySkill/SKILL.md")) { throw "Missing entry skill: $entrySkill" }
}
foreach ($role in @('planner', 'orchestrator', 'researcher', 'plan-critic', 'implementer', 'code-reviewer', 'verifier', 'devops-expert')) {
    if (-not (Select-String -LiteralPath "$pluginRoot/agents/$role.toml" -Pattern '^developer_instructions = ' -Quiet)) { throw "Missing instructions for $role" }
}
Write-Host 'Codex plugin structure validated.'
