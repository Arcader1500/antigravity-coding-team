# Coding Team for Codex desktop

Installed plugin: `coding-team@coding-team-local`.
The original Antigravity manifest, agents and installer remain intact.
`codex/` contains the independently maintained Codex plugin. From the repository root, reinstall:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1
```

Start a new chat after installing; restart Codex if the skills list is stale.
The installer uses Codex CLI when `codex` is on `PATH`. Without it, it stages
the plugin under `%USERPROFILE%\.codex\plugins` and registers a personal local
marketplace for the ChatGPT desktop app. Restart ChatGPT, then install Coding
Team from the **Personal** marketplace in the Plugins Directory.
Use `$team-plan` to plan a feature, `$team-run` to execute an approved plan, or
`$team-review` for an independent local diff review. `$coding-team` remains a
compatibility entry point that routes to the appropriate workflow.

| Role | Model | Reasoning |
|---|---|---|
| planner | gpt-6-sol | high |
| plan-critic | gpt-6-sol | high |
| researcher | gpt-6-luna | low |
| orchestrator | gpt-6-sol | low |
| implementer | gpt-6-sol | medium |
| code-reviewer | gpt-6-sol | high |
| verifier | gpt-6-luna | low |
| devops-expert | gpt-6-sol | medium |

All eight native custom agents are installed under `~/.codex/agents/` for use across projects. They inherit session permissions.
Read-only role instructions do not establish a separate read-only sandbox.

For main-chat roles, select GPT-6 Sol and the listed effort in the desktop
composer, then invoke `$team-plan` or `$team-run` respectively.
The skill cannot change the current chat's model. CLI launch profiles:

```powershell
codex -p coding-team-planner -C <your-project-folder>
codex -p coding-team-orchestrator -C <your-project-folder>
```

The profiles contain the role instructions and live in `~/.codex/`.
They do not replace your global default model. The installer backs up differing
existing agent files and existing profiles before replacing them.

`code-review-graph serve` is configured as a required local MCP server. Before
worker dispatch, the orchestrator sets up a missing executable, repository index,
ignore entry and post-commit hook, preserving existing hook behavior. It confirms
MCP access to the intended repository; setup failures block dispatch. Source
inspection confirms critical claims and covers unindexed content. See
[graph preflight](skills/subagent-driven-development/references/code-review-graph.md).

The installer also writes one advisory `SessionStart` hook to
`~/.codex/hooks.json`: it prints graph status only when the checkout has a
`.code-review-graph/graph.db`, and always exits 0, so an unindexed repository
cannot fail session startup. Older per-tool graph hooks are removed; graph
updates stay in the repository's git `post-commit` hook, so Codex never
rebuilds the graph in the middle of a wave. Other user hooks are preserved and
both files are backed up. Windows uses `commandWindows`, macOS/Linux uses the
POSIX `command`. Codex runs `commandWindows` as PowerShell code, so it must be
plain PowerShell: a nested `powershell.exe -Command "..."` gets its variables
expanded by the outer shell and the hook fails. The running app-server daemon
reads `hooks.json` once at startup, so restart Codex (`codex app-server daemon
restart`) after installing. Codex skips changed hooks until you review them:
run `/hooks` after installing, or the hook will not run.

If Codex reports `mcp_servers.code-review-graph` with an invalid transport, or
warns that `mcp_servers.code-review-graph.type` is ignored, remove the complete
`[mcp_servers.code-review-graph]` block from the user `config.toml`, including
any `.tools.*` sub-tables. A partial edit leaves orphaned sub-tables and Codex
then rejects the whole bootstrap config. Native Codex TOML uses `command` and
`args` for stdio, or `url` for HTTP; do not copy transport metadata from a
different client's JSON format. An existing manual stdio entry would use:

```toml
[mcp_servers.code-review-graph]
command = "code-review-graph"
args = ["serve"]
```

The plugin already supplies this server; do not add a second registration just
to fix the warning. The installer removes a stale user block automatically and
backs up the file. An ignored setting and a startup timeout are separate issues:
verify the configured executable and MCP handshake if startup still fails. See
the [official Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

`context7` is configured as a remote MCP server at `https://mcp.context7.com/mcp`
for up-to-date library documentation. It answers anonymously (rate-limited); no
OAuth step is required. To use your own key, add it to your Codex MCP
configuration, for example in `~/.codex/config.toml`:

```toml
[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
bearer_token_env_var = "CONTEXT7_API_KEY"
```

Keep a single `context7` entry so the MCP list has no duplicates.

## Changes made for Codex

- Supported compatibility manifest and local marketplace, installed through the
  Codex CLI rather than manually editing the plugin registry.
- Native TOML agents with explicit OpenAI models and reasoning effort.
- Separate planner and orchestrator launch profiles and workflow skill.
- Native collaboration waits replace Antigravity's end-turn-after-dispatch rule.
- Orchestrator alone stages owned files and commits; existing hooks are preserved.
- Required graph readiness is established before dispatch; project-defined validation commands establish correctness.
- Implementers read the bundled ponytail skill in full mode within assigned scope.
- PowerShell PR descriptions use temporary UTF-8 files with `gh --body-file`.

## Recommended next changes

The first improvement batch is implemented: dedicated entry skills, registered
agent-type dispatch, repository-specific planning commands/dependencies, and
the original execution sequence: tasks/waves with focused checks, then the
code-review/fix loop until approved, then final verifier, then complete.
No automatic per-wave verifier runs or early risk-based review gates are added.
See the root README for examples and evidence-reuse rules. Recommendations below
describe remaining work rather than additional requirements.

1. Replace the remaining long, mechanically adapted supporting skills with short
   native Codex workflows. Several still repeat tool-specific assumptions and
   refer to optional skills outside this bundle. Consolidate contradictory rules
   rather than relying on adaptation notices.
2. Add a durable execution state file recording approved spec/plan revisions,
   completed task IDs, commit SHAs, checks and unresolved risks. This makes a fresh
   execution chat resumable without reading the whole planning conversation.
3. Measure the new review cadence on real projects: check that focused task
   validation, the review/fix loop and independent final verification catch
   regressions while avoiding repeated identical full-suite runs.
4. Replace the planner's broad mandatory question categories with questions only
   for material ambiguity. Reuse decisions the user already gave.
5. Measure actual quota consumption and task quality. Neither a large context
   window nor a lower model tier guarantees negligible quota, and starting a new
   chat does not refund earlier work.

References: [plugin packaging](https://developers.openai.com/plugins/build/plugins)
and [custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
