# Required code-review-graph preflight

The orchestrator owns setup before worker dispatch, under existing session
permissions. Other roles report missing setup rather than mutating it. Never
rebuild or repair the graph while wave writers are active.

1. Resolve the absolute target checkout with `git rev-parse --show-toplevel`.
   Check `code-review-graph --version` and MCP connectivity with
   `list_graph_stats_tool(repo_root=<absolute root>)`.
2. If the executable is missing, install it with the available Python tool manager
   (for example, `uv tool install code-review-graph`). The plugin already declares
   `code-review-graph serve` in `.mcp.json`; avoid duplicate registrations. If a
   restart is needed to expose MCP tools, report it and stop before dispatch.
   Do not broaden permissions or install unrelated project dependencies.
   If Codex reports an ignored `mcp_servers.code-review-graph.type` setting in
   user `config.toml`, remove only that unsupported key from the existing table.
   Native TOML stdio configuration uses `command` and `args`; HTTP uses `url`.
   Do not copy JSON transport metadata into native TOML or create a duplicate
   user registration for the plugin-managed server. Check the configured command
   separately if startup still times out; removing `type` does not prove readiness.
3. Ensure `.code-review-graph/` is ignored before building. If the index is missing,
   run `code-review-graph build --repo <absolute root>` and check its exit status.
   Otherwise inspect status/freshness and use
   `code-review-graph update --repo <absolute root>` when stale, outside active waves.
   Confirm the intended repository through MCP afterward. An empty index may be
   valid for documentation-only or unsupported-language repositories; inspect
   uncovered content directly instead of repeatedly rebuilding.
4. Resolve the effective post-commit hook location, respecting `core.hooksPath`
   and worktrees (`git rev-parse --git-path hooks/post-commit`). Create a missing
   hook or add a background incremental graph update without replacing existing
   behavior. Use Git's hook shell and quote paths correctly, including Windows
   paths with spaces. Confirm the hook and ignore entry before dispatch.
5. Failed installation, inaccessible MCP, failed build or unrepairable hook setup
   blocks dispatch. Report the specific failure and required action. Do not
   silently substitute source-only execution for required graph readiness.

For cross-project calls, explicitly pass the intended absolute `repo_root` when
supported. Inspect repository identity and freshness before relying on results.
Use `semantic_search_nodes_tool` for discovery; `query_graph_tool` patterns
`callers_of`, `callees_of`, `tests_for` for relationships; `detect_changes_tool`,
`get_impact_radius_tool` and `get_review_context_tool` for review scope. Confirm
critical claims in source. Empty results mean unindexed or unsupported content,
not proof of absence. Source wins when it disagrees with the graph.

Background post-commit updates may lag; verify relevant source in the working
tree. Native collaboration waits are required before inspecting writer output,
committing wave changes or starting final review/verification gates.
