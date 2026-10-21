# Coding Team

A plan-and-execute agent team for **Antigravity** and **Codex desktop / CLI**.
Each platform has an independent plugin, agent definitions, skills and installer.

```text
antigravity/              Antigravity plugin, agents, rules and eight skills
  install.bat/.ps1/.sh    Install or update using agy
codex/                   Codex plugin, seven TOML agents and nine skills
  install.bat/.ps1        Install or update using Codex
  scripts/               Configuration validation
.agents/plugins/         Local Codex marketplace pointing to ./codex
```

## Common workflow

The planner clarifies requirements, delegates research and writes a design spec.
After spec approval it writes a plan, checked by the plan critic. After plan
approval the orchestrator delegates implementation in dependency-ordered waves,
with disjoint file ownership. Review and verification follow; only the
orchestrator commits task changes.

| Agent | Responsibility | Codex model / effort |
|---|---|---|
| planner | Requirements, spec and plan | GPT-6 Sol / high |
| plan-critic | Critique plan against spec | GPT-6 Sol / high |
| researcher | Scoped read-only exploration | GPT-6 Luna / low |
| orchestrator | Dispatch, progress and commits | GPT-6 Sol / low |
| implementer | One scoped implementation task | GPT-6 Sol / medium |
| code-reviewer | Diff review and verdict | GPT-6 Sol / high |
| verifier | Tests, lint, typecheck and build evidence | GPT-6 Luna / low |

Both plugins bundle `code-review-graph` MCP configuration. Its executable must
be installed and available on PATH to use graph tools. Codex falls back to source
inspection when graph tools are unavailable. All roles respect session permissions.

## Run with Antigravity

Requires the `agy` CLI. On Windows, double-click **antigravity/install.bat**, or
run from this repository's root:

```powershell
.\antigravity\install.ps1
# Validate without installing:
.\antigravity\install.ps1 -ValidateOnly
```

On Linux, macOS or Git Bash:

```bash
bash antigravity/install.sh
```

Restart Antigravity after installing. Use `/agents` to choose `planner` or
`orchestrator`, and `/plugin` to inspect the bundle. Manual installation:
`agy plugin install ./antigravity`.

See [Antigravity details](antigravity/README.md) for permissions and packaging.

## Run with Codex

Requires Codex desktop / CLI with `codex` on PATH, **PowerShell 7** (`pwsh`), and
access to the configured OpenAI models. On Windows, double-click
**codex/install.bat**, or run from this repository's root:

```powershell
pwsh -NoProfile -File .\codex\install.ps1
# Validate structure without installing:
pwsh -NoProfile -File .\codex\install.ps1 -ValidateOnly
```

The installer registers this repository's marketplace, installs/enables
`coding-team`, copies seven agents into `~/.codex/agents/`, and installs planner
and orchestrator CLI profiles. Differing existing agent files and existing
profiles are backed up. Run the same installer after edits to refresh the cache.

Start a new chat after installation; restart Codex if the skill list is stale.
The `$` picker lists **skills**, while agents are delegation targets.
For planning, select **GPT-6 Sol / High** in the desktop composer and send:

```text
$coding-team Act as the planner. Plan this feature: [your requirements].
Delegate exploration to researcher and plan critique to plan-critic.
```

After approving the plan, start a fresh chat with **GPT-6 Sol / Low** and send:

```text
$coding-team Act as the orchestrator. Execute the approved plan at [plan path].
Use implementer, code-reviewer and verifier for their assigned roles.
```

The main chat model is selected separately; spawned agents use their TOML model
settings. CLI profiles select the main role and model together:

```powershell
codex -p coding-team-planner -C <your-project-folder>
codex -p coding-team-orchestrator -C <your-project-folder>
```

See [Codex details](codex/README.md) for configuration notes and recommendations.

## Maintain and validate

Edit `antigravity/` for Antigravity changes and `codex/` for Codex changes.
Installing Codex does not regenerate its files from Antigravity. Keep shared
workflow changes consistent across both where appropriate.

```powershell
agy plugin validate .\antigravity --strict
pwsh -NoProfile -File .\codex\install.ps1 -ValidateOnly
# Deeper checks including installed-file parity (Python 3.11+; after installation):
python .\codex\scripts\validate.py
```
