---
trigger: always_on
description: Standard operating rules for code-review-graph MCP and automated git post-commit graph updates.
---

# code-review-graph

This project uses `code-review-graph` for persistent structural code intelligence, caller/callee graphs, and impact radius analysis.

## Operating Rules

### 1. Read-Only MCP Usage for Discovery & Review
- Specialized agents (`researcher`, `planner`, `plan-critic`, `implementer`, `code-reviewer`) must prioritize the `code-review-graph` MCP tools before falling back to broad file scans or raw `grep`:
  - Locate code entities and symbols: `semantic_search_nodes_tool`
  - Inspect callers, callees, and test mappings: `query_graph_tool` (`tests_for`, `callers`, `callees`)
  - Measure blast radius and affected execution paths: `get_impact_radius_tool`, `detect_changes_tool`, and `get_affected_flows_tool`
  - Retrieve risk-scored context: `get_review_context_tool`
- When the graph and the on-disk source disagree, the on-disk source code wins. An empty graph result means "not indexed", not "does not exist" — verify with `view_file`.

### 2. No Manual Mid-Wave Graph Rebuilds by Subagents
- Subagents (`implementer`, `researcher`, `code-reviewer`, `plan-critic`, `verifier`) must **NEVER** run shell commands to manually rebuild or update the graph during a task wave (e.g. `code-review-graph build` or `code-review-graph update`).
- Running manual graph updates during wave execution causes parallel wave collisions, lock contention on `.code-review-graph/graph.db`, and dirty working tree errors.

### 3. Automatic Updates via Git `post-commit` Hook
- The knowledge graph is updated automatically whenever `orchestrator` creates a commit via the repository's `.git/hooks/post-commit` hook.
- The post-commit hook triggers incremental updates in the background without blocking the development cycle or dirtying `git status`.
- Ensure `.code-review-graph/` is ignored in the project's `.gitignore` and global git configuration.
