# Coding Team for Codex desktop

Installed plugin: `coding-team@coding-team-local`.
The original Antigravity manifest, agents and installer remain intact.
`codex/` contains the independently maintained Codex plugin. From the repository root, reinstall:

```powershell
pwsh -File .\codex\install.ps1
```

Start a new chat after installing; restart Codex if the skills list is stale.
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

All seven native custom agents are installed under `~/.codex/agents/` for use across projects. They inherit session permissions.
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

`code-review-graph serve` is configured as a local MCP server. Install its
executable and make it available on PATH to use it. Source inspection remains
the fallback when graph tools are unavailable or stale.

## Changes made for Codex

- Supported compatibility manifest and local marketplace, installed through the
  Codex CLI rather than manually editing the plugin registry.
- Native TOML agents with explicit OpenAI models and reasoning effort.
- Separate planner and orchestrator launch profiles and workflow skill.
- Native collaboration waits replace Antigravity's end-turn-after-dispatch rule.
- Orchestrator alone stages owned files and commits; existing hooks are preserved.
- Graph tooling is optional and project-defined validation commands take priority.

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
