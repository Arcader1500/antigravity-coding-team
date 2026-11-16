# antigravity-coding-team

An Antigravity plugin that bundles the plan-and-execute agent team.

For Codex installation, see the [root README](../README.md).
## Quick Installation / Update

Run the included install script to validate, install, or update the plugin:

**PowerShell (Windows):**
```powershell
.\install.ps1
```

**Command Prompt (Windows):**
```cmd
install.bat
```

Close Antigravity (or stop the running `agy` process) before installing: it
holds the installed plugin directory open, and the copy then fails with
`The process cannot access the file because it is being used by another process`.

**Bash (Linux / macOS / Git Bash):**
```bash
./install.sh
```

Or manually with the CLI:
```powershell
agy plugin install <path-to-this-folder>     # local directory install
# or, if you publish it: agy plugin install antigravity-coding-team@<marketplace>
```

Then **restart `agy`** (or your Antigravity IDE session) — a newly installed or updated plugin directory is only discovered on startup. Confirm with `/agents` (main agents) and `/plugin` (the bundle).

> Bundles the `code-review-graph` MCP server out of the box via `mcp_config.json`,
> providing persistent structural code intelligence, impact analysis, and callers/callees tracking.
>
> Also bundles `context7` for up-to-date library documentation via `mcp_config.json`,
> pointed at `https://mcp.context7.com/mcp` — **no OAuth step**, the server answers
> anonymously (rate-limited). To use your own key, put it in `mcp_config.local.json`
> next to `mcp_config.json` (git-ignored, never committed):
>
> ```json
> { "mcpServers": { "context7": { "serverUrl": "https://mcp.context7.com/mcp",
>   "headers": { "Authorization": "Bearer YOUR_CONTEXT7_API_KEY" } } } }
> ```
>
> `install.ps1` merges that file into the installed plugin
> (`~/.gemini/config/plugins/antigravity-coding-team/mcp_config.json`) on every
> install, so the key survives reinstalls without ever entering git. Get a key at
> <https://context7.com/dashboard>. Keep only one `context7` — the plugin's — so the
> MCP list has no duplicates.
>
> Do **not** point it at `https://mcp.context7.com/mcp/oauth`: that endpoint needs a
> browser token exchange, and Antigravity currently fails it with `invalid_grant`
> ("PKCE code verifier was provided but the code challenge was absent from the
> authorization request"). The plain endpoint needs neither.
>
> Agents whose scope is not enumerated in their instructions — `planner`, `orchestrator`,
> `researcher`, `plan-critic`, `code-reviewer` — must call it before scanning files.
> `implementer` receives its file list from the controller, so the graph is optional there
> (it stays available for grounding checks).
> Graph readiness is required: the orchestrator sets up a missing executable, index,
> ignore entry and post-commit hook before dispatch. If setup or MCP access fails,
> execution is blocked until repaired. See [graph rules](rules/code-review-graph.md).

## What's inside

```
plugin.json                 manifest
agents/                     orchestrator, planner (main) + implementer,
                            researcher, plan-critic, code-reviewer, verifier,
                            devops-expert, risk-estimator
rules/AGENTS.md             merged operating rules (always on)
skills/                     the 8 skills the agents reference
scripts/risk_store.py       project-local SQLite history helper (Python 3.11+)
permissions.sample.json     project-agnostic permission grants (not auto-loaded)
```

| Agent | Role | Dispatches |
|---|---|---|
| `orchestrator` | runs a written plan end to end; the only agent that commits | `implementer`, `code-reviewer`, `verifier` |
| `planner` | researches, writes spec, pauses for spec approval, then writes plan + critic loop; never edits source | `researcher`, `plan-critic`, `devops-expert` |
| `implementer` | one plan task, ponytail full mode, write tools, never commits | — |
| `researcher` | read-only, graph-first, cited facts | — |
| `plan-critic` | red-teams a plan, findings only | — |
| `code-reviewer` | five-axis review + verdict | — |
| `verifier` | runs tests/lint/build, reports evidence | — |
| `devops-expert` | K8s/Helm/Terraform/CI-CD/cloud specialist; usable directly or as a subagent | — |
| `risk-estimator` | advisory complexity, risk and AI-agent execution-time estimates | — |

Bundled skills: `subagent-driven-development`, `grill-me`, `writing-plans`,
`executing-plans`, `ponytail`, `verification-before-completion`,
`finishing-a-development-branch`, `code-review-and-quality`.

Requested subagent models and currently loadable frontmatter settings:

| Agents | Requested model slug | Current `model` tier |
|---|---|---|
| `implementer`, `researcher`, `code-reviewer`, `verifier`, `risk-estimator` | `gemini-4-hydrogen-medium` | `flash` |
| `plan-critic` | `gemini-4-argon-high` | `pro` |

These slugs were verified with `agy models` and the
[Antigravity CLI model reference](https://antigravity.google/docs/cli/headless/#select-a-model-effort-or-agent).
However, `agy` 1.5.8 rejects full model slugs in custom-agent frontmatter with
`Invalid model tier` and skips those agents. The
[plugin frontmatter schema](https://antigravity.google/docs/build-plugins/#subagents)
accepts tier names (`inherit`, `flash_lite`, `flash`, `pro`). The current settings
keep the plugin loadable; they do not enforce the requested model/effort pins.
Exact subagent pinning remains blocked by the loader's tier-only support.
The `risk-estimator` uses the supported `flash` tier; this does not guarantee
Hydrogen Medium or an exact reasoning-effort setting.
Reinstall the plugin and restart Antigravity to load agent definition changes.

## Risk estimates and project history

After a READY plan critique, the planner can ask the risk-estimator for
agent-time scenarios, evidence and focused questions. The planner keeps the
answers and baseline prediction with the existing handoff. During execution the
orchestrator resumes the linked run and records attempts, incidents, checks and
later human/live acceptance. These forecasts are advisory and do not add an
approval gate.

Risk logging requires Python 3.11+ and uses the packaged standard-library
`scripts/risk_store.py`. The database lives in the target project at
`.coding-team/risk.sqlite3`, not in Antigravity's installed plugin directory.
Before the helper is ready, the controller appends ordered system-clock
create-run and record operations to `.coding-team/task-timings.jsonl`; the
helper replays them idempotently and reports the legacy `run_start` entry.
Controller dispatch-to-result time is elapsed wall time and may include
unobserved waits; it is not labeled active agent effort. Unknown timing and
human/external waits remain null or separately recorded. Human/live acceptance
can be added later without replacing the implementation outcome.

History does not automatically calibrate or revise the rubric. Rubric review is
outside the execution workflow and happens only when the user chooses.

## Permissions

`permissions.sample.json` holds only the project-agnostic grants: pytest/python/uv,
npm/npx, docker, read-only `gh` and `git` commands, plus `git commit` and delete
commands in `ask`, and all `.env*` reads/writes in `deny`.

It is **not** loaded by the plugin system — plugins cannot ship permissions. Merge
the three arrays into `userSettings.globalPermissionGrants` in
`~/.gemini/config/config.json`, or paste them into the `/permissions` panel (that
path merges correctly and hot-reloads, and is the safer choice).

Removed from the source setup as machine/project-specific: `mcp(daas-cd/*)`,
`mcp(code-review-graph/*)` (belongs to the MCP server's own install) and
`read_url(raw.githubusercontent.com)`.

## Deliberately excluded

- **External API MCP servers.** Cloud-dependent servers requiring external credentials (like `undermind`) should be configured globally per machine. `context7` is the exception — it answers anonymously, so it ships here with no key.
- **`archify`, `frontend-design`, `systematic-debugging`,
  `test-driven-development`, `receiving-code-review`, `using-git-worktrees`,
  `context7-mcp`.** Not referenced by any bundled agent. Copy the ones you want
  into `skills/` and re-validate.
- **Triggered rules.** Plugin rules are always on; the source's
  `trigger: model_decision` / `trigger: glob` scoping (and the `security` glob)
  is lost in the merge into `rules/AGENTS.md`.

## Publishing (optional)

`agy plugin install name@marketplace` needs a Marketplace entry; a local directory
path needs nothing. To publish, `git init` this folder, push it, and hook it to a
marketplace with `agy plugin link <marketplace> <target>`.

Validate any edit before installing:

```powershell
agy plugin validate <path> --strict
```
