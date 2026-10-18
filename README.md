# antigravity-coding-team

An Antigravity plugin that bundles the plan-and-execute agent team.

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

> Requires the `code-review-graph` MCP server to be configured globally on the
> target machine — several agent prompts call its tools. MCP servers are
> deliberately *not* bundled here; see "Deliberately excluded" below.

## What's inside

```
plugin.json                 manifest
agents/                     orchestrator, planner (main) + implementer,
                            researcher, plan-critic, code-reviewer, verifier
rules/AGENTS.md             merged operating rules (always on)
skills/                     the 8 skills the agents reference
permissions.sample.json     project-agnostic permission grants (not auto-loaded)
```

| Agent | Role | Dispatches |
|---|---|---|
| `orchestrator` | runs a written plan end to end; the only agent that commits | `implementer`, `code-reviewer`, `verifier` |
| `planner` | researches, writes spec + plan; never edits source | `researcher`, `plan-critic` |
| `implementer` | one plan task, write tools, never commits | — |
| `researcher` | read-only, graph-first, cited facts | — |
| `plan-critic` | red-teams a plan, findings only | — |
| `code-reviewer` | five-axis review + verdict | — |
| `verifier` | runs tests/lint/build, reports evidence | — |

Bundled skills: `subagent-driven-development`, `grilling`, `writing-plans`,
`executing-plans`, `ponytail`, `verification-before-completion`,
`finishing-a-development-branch`, `code-review-and-quality`.

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

- **MCP servers.** The source setup's servers are not portable: `context7` carries
  a bearer token, `daas-cd` and `code-review-graph` hardcode absolute paths, and
  `undermind` needs OAuth. Configure them globally per machine. Adding an
  `mcp_config.json` here would also tie their lifecycle to this plugin.
- **`grill-me`, `graphify`, `archify`, `frontend-design`, `systematic-debugging`,
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
