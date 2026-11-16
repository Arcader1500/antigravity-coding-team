# Coding Team

A plan-and-execute agent team for **Antigravity** and **Codex desktop / CLI**.
Each platform has an independent plugin, agent definitions, skills and installer.

```text
antigravity/              Antigravity plugin, agents, rules and eight skills
  install.bat/.ps1/.sh    Install or update using agy
codex/                   Codex plugin, nine TOML agents and twelve skills
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

| Agent | Responsibility | Codex source model / effort |
|---|---|---|
| planner | Requirements, spec and plan | GPT-6 Luna / high |
| plan-critic | Critique plan against spec | GPT-6.1 Sol / medium |
| researcher | Scoped read-only exploration | GPT-6 Luna / low |
| orchestrator | Dispatch, progress and commits | GPT-6.1 Sol / low |
| implementer | One scoped implementation task | GPT-6 Luna / medium |
| code-reviewer | Diff review and verdict | GPT-6.1 Sol / medium |
| verifier | Tests, lint, typecheck and build evidence | GPT-6 Luna / low |
| devops-expert | Kubernetes, Terraform, CI/CD and cloud specialist | GPT-6 Luna / medium |
| risk-estimator | Advisory implementation-risk and AI-agent time forecasts | GPT-6.1 Sol / medium |

The planner's native source role is GPT-6 Luna / high. Its separate CLI launch
profile selects GPT-6.1 Sol / medium for the main chat; changing that profile
does not rewrite the source agent model.

Both plugins bundle `code-review-graph` MCP configuration. Its executable must
be installed and available on PATH to use graph tools. Graph readiness is required before worker dispatch; the orchestrator repairs
missing setup. Source inspection confirms critical claims and covers unindexed content. All roles respect session permissions.

Both plugins also bundle `context7` for current library documentation. It
answers anonymously (rate-limited), so no key is required; see each plugin's
README for the optional key setup.

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

Restart Antigravity after installing. Close the running `agy` process *before*
installing: it locks the installed plugin directory and the copy fails with
`The process cannot access the file because it is being used by another process`.
Use `/agents` to choose `planner` or
`orchestrator`, and `/plugin` to inspect the bundle. Manual installation:
`agy plugin install ./antigravity`.

See [Antigravity details](antigravity/README.md) for permissions and packaging.

## Run with Codex

Requires Codex desktop / CLI with `codex` on PATH, **Windows PowerShell 5.1**
(`powershell`, the default on Windows), and access to the configured OpenAI
models. On Windows, double-click **codex/install.bat**, or run from this
repository's root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1
# Validate structure without installing:
powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1 -ValidateOnly
```

The installer registers this repository's marketplace, installs/enables
`coding-team`, copies nine agents into `~/.codex/agents/`, and installs planner
and orchestrator CLI profiles. Differing existing agent files and existing
profiles are backed up. Run the same installer after edits to refresh the cache.

Start a new chat after installation; restart Codex if the skill list is stale.
The `$` picker lists **skills**, while agents are delegation targets.
For planning, select **GPT-6.1 Sol / Medium** in the desktop composer and send:

```text
$team-plan Plan this feature: [your requirements].
```

After approving the plan, start a fresh chat with **GPT-6.1 Sol / Low** and send:

```text
$team-run Execute the approved plan at [plan path].
```

For an independent review, use `$team-review Review my current diff`.
`$coding-team` remains available and routes to these workflows.

The main chat model is selected separately; spawned agents use their TOML model
settings. CLI profiles select the main role and model together:

```powershell
codex -p coding-team-planner -C <your-project-folder>
codex -p coding-team-orchestrator -C <your-project-folder>
```

See [Codex details](codex/README.md) for configuration notes and recommendations.

### Codex review and verification flow

```text
Planner -> spec checkpoint -> create plan -> plan-critic
  -> planner fixes -> critic rechecks until READY
  -> manual handoff to orchestrator
  -> implementers execute tasks and waves with focused checks
  -> code-reviewer -> orchestrator dispatches implementer fixes
  -> reviewer rechecks until all required findings are resolved and approved
  -> verifier -> complete
```

Waves organize implementation and dependencies; they do not automatically trigger
verifier runs or early risk-based review gates. Only after review approval does
verifier run the full relevant project checks. If verification fails, orchestrator
dispatches implementer fixes, reviewer approves the changes, then verifier checks
again. Completion requires both review approval and passing required verification.
Earlier task checks cannot replace the post-review verifier stage. Matching final
verifier evidence may be reused only for unchanged code, commands and environment.

### Risk forecasts and execution history

After the plan critic returns READY, the planner may consult the risk-estimator
for an advisory forecast and targeted evidence questions. The planner retains
answers and the baseline prediction with the approved-plan handoff. During
execution the orchestrator records task attempts, review and verification
results, incidents and later human/live acceptance through the packaged SQLite
helper. Forecasts do not change the critic verdict or add approval gates.

Risk logging requires Python 3.11+ and stores project-local history in
`.coding-team/risk.sqlite3`, outside the installed plugin cache. Before the
helper is ready, the controller records ordered JSONL operations in
`.coding-team/task-timings.jsonl` from system-clock dispatch/result observations;
the helper can replay the file idempotently. The legacy `run_start` entry is
preserved and reported. Controller dispatch-to-result time includes result
delivery and any unobserved waits, so it is not labeled active agent effort.
Missing phase measurements stay null; human pauses, external waits and
human/live acceptance remain distinct from agent timing.

Estimates are heuristic and history does not update the rubric automatically.
Rubric inspection or revision is outside the workflow and happens only when
the user chooses; earlier predictions remain available for comparison.

## Maintain and validate

Edit `antigravity/` for Antigravity changes and `codex/` for Codex changes.
Installing Codex does not regenerate its files from Antigravity. Keep shared
workflow changes consistent across both where appropriate.

```powershell
agy plugin validate .\antigravity --strict
powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1 -ValidateOnly
# Source-only checks (Python 3.11+; do not read global install state):
py -3 .\codex\scripts\validate.py --source-only
# Explicit installed-file parity check, after installation:
py -3 .\codex\scripts\validate.py --installed-parity
```
