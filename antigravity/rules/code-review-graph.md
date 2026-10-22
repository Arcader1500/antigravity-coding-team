---
trigger: always_on
description: Standard operating rules for code-review-graph MCP and automated git post-commit graph updates.
---

# code-review-graph

This project uses `code-review-graph` for persistent structural code intelligence, caller/callee graphs, and impact radius analysis.

## Required orchestrator preflight

Before dispatching workers, the orchestrator owns graph setup for the target checkout:

1. Resolve the absolute repository root with `git rev-parse --show-toplevel`.
   Check `code-review-graph --version` and MCP connectivity with
   `list_graph_stats_tool(repo_root=<absolute root>)`.
2. If the executable is missing, install `code-review-graph` with the available
   Python tool manager (for example, `uv tool install code-review-graph`) under
   session permissions. The plugin already declares its MCP server in
   `mcp_config.json`; avoid duplicate registrations. If a restart is needed to
   expose the server, report the required restart and stop before dispatch.
3. Ensure `.code-review-graph/` is ignored in the target repository before creating
   an index. If no graph exists, run `code-review-graph build --repo <absolute root>`
   and check its exit status; otherwise inspect status and run an incremental
   `code-review-graph update --repo <absolute root>` when stale, with no active writers.
   Confirm the intended repository through MCP afterward. An empty index can be
   valid for documentation-only or unsupported-language repositories; inspect
   source for uncovered content rather than repeatedly rebuilding.
4. Resolve the effective hook location, respecting `core.hooksPath` and worktrees
   (`git rev-parse --git-path hooks/post-commit`). Create a missing post-commit hook
   or add the graph update to an existing one without replacing its other behavior.
   It must run an incremental update for this checkout in the background. Use Git's
   hook shell and quote paths correctly, including Windows paths with spaces.
   Confirm the hook and `.gitignore` entry before dispatch.
5. Missing executable, inaccessible MCP, failed build or unrepairable hook setup
   blocks dispatch. Report the specific failure and required action; do not silently
   downgrade to source-only execution or broaden permissions. Read-only source
   inspection remains necessary for unsupported content and critical claims.

Only the controller performs initial setup or repairs, outside active waves.
Read-only roles report missing graph setup to the controller instead of mutating it.

## Operating Rules

### 1. Mandatory Graph Use for Discovery & Review
- **Trigger:** You MUST use the `code-review-graph` MCP before any broad file scan or raw `grep` whenever the task does not enumerate the files and symbols involved. Nothing in the prompt tells you which files matter — the graph is how you find out.
- **Who it binds:** `planner`, `orchestrator`, `researcher`, `plan-critic` and `code-reviewer` always. `implementer` and `verifier` may use it: the controller gives the implementer its file list, so the graph is optional there, but use it when the task references a symbol or file it does not name.
- Tools by question:
  - Locate code entities and symbols: `semantic_search_nodes_tool`
  - Inspect callers, callees, and test mappings: `query_graph_tool` (`tests_for`, `callers_of`, `callees_of`)
  - Measure blast radius and affected execution paths: `get_impact_radius_tool`, `detect_changes_tool`, and `get_affected_flows_tool`
  - Retrieve risk-scored context: `get_review_context_tool`
- State in your report which graph tools you called. Skipping the graph silently on a task that triggers the rule is a defect.
- When the graph and the on-disk source disagree, the on-disk source code wins. An empty graph result means "not indexed", not "does not exist" — verify with `view_file`.

- For cross-project work, pass the target repository's absolute `repo_root` on graph calls that support it. Check repository identity and freshness; the startup default may refer to another checkout. Confirm critical claims in source.

### 2. No Manual Mid-Wave Graph Rebuilds by Subagents
- Subagents (`implementer`, `researcher`, `code-reviewer`, `plan-critic`, `verifier`) must **NEVER** run shell commands to manually rebuild or update the graph during a task wave (e.g. `code-review-graph build` or `code-review-graph update`).
- Running manual graph updates during wave execution causes parallel wave collisions, lock contention on `.code-review-graph/graph.db`, and dirty working tree errors.

### 3. Automatic Updates via Git `post-commit` Hook
- The knowledge graph is updated automatically whenever `orchestrator` creates a commit via the repository's `.git/hooks/post-commit` hook.
- The post-commit hook triggers incremental updates in the background without blocking the development cycle or dirtying `git status`.
- Ensure `.code-review-graph/` is ignored in the project's `.gitignore` and global git configuration.
