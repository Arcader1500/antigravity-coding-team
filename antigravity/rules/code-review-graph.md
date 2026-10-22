---
trigger: always_on
description: Standard operating rules for code-review-graph MCP and automated git post-commit graph updates.
---

# code-review-graph

This project uses `code-review-graph` for persistent structural code intelligence, caller/callee graphs, and impact radius analysis.

## Operating Rules

### 1. Mandatory Graph Use for Discovery & Review
- **Trigger:** You MUST use the `code-review-graph` MCP before any broad file scan or raw `grep` whenever the task does not enumerate the files and symbols involved. Nothing in the prompt tells you which files matter — the graph is how you find out.
- **Who it binds:** `planner`, `orchestrator`, `researcher`, `plan-critic` and `code-reviewer` always. `implementer` and `verifier` may use it: the controller gives the implementer its file list, so the graph is optional there, but use it when the task references a symbol or file it does not name.
- Tools by question:
  - Locate code entities and symbols: `semantic_search_nodes_tool`
  - Inspect callers, callees, and test mappings: `query_graph_tool` (`tests_for`, `callers`, `callees`)
  - Measure blast radius and affected execution paths: `get_impact_radius_tool`, `detect_changes_tool`, and `get_affected_flows_tool`
  - Retrieve risk-scored context: `get_review_context_tool`
- State in your report which graph tools you called. Skipping the graph silently on a task that triggers the rule is a defect.
- When the graph and the on-disk source disagree, the on-disk source code wins. An empty graph result means "not indexed", not "does not exist" — verify with `view_file`.

### 2. No Manual Mid-Wave Graph Rebuilds by Subagents
- Subagents (`implementer`, `researcher`, `code-reviewer`, `plan-critic`, `verifier`) must **NEVER** run shell commands to manually rebuild or update the graph during a task wave (e.g. `code-review-graph build` or `code-review-graph update`).
- Running manual graph updates during wave execution causes parallel wave collisions, lock contention on `.code-review-graph/graph.db`, and dirty working tree errors.

### 3. Automatic Updates via Git `post-commit` Hook
- The knowledge graph is updated automatically whenever `orchestrator` creates a commit via the repository's `.git/hooks/post-commit` hook.
- The post-commit hook triggers incremental updates in the background without blocking the development cycle or dirtying `git status`.
- Ensure `.code-review-graph/` is ignored in the project's `.gitignore` and global git configuration.
