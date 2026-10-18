# Coding team operating rules

Plugin rules are always on while this plugin is enabled, so the five
context-triggered rules this bundle was extracted from are merged here.

## Code-review graph
- Locate code with `semantic_search_nodes_tool`; callers, callees and tests with `query_graph_tool`; what a diff affects with `detect_changes_tool` and `get_impact_radius_tool`; impacted execution paths with `get_affected_flows_tool`.
- Fall back to `grep_search` and `view_file` when the graph does not cover what you need, or to verify a claim.
- The graph auto-updates via a pre-commit hook but can lag, and it never replaces source: the source wins on disagreement. An empty result means "not indexed", not "does not exist".

## Planning
- Sequence: clarify (`grilling`), explore (read the codebase with `view_file`/`grep_search`), write spec doc, **checkpoint 1: user/supervisor approves spec**, break into tasks (`writing-plans`), critique (`plan-critic` agent against approved spec until READY), **checkpoint 2: handoff plan**, execute (`orchestrator` / `subagent-driven-development`).
- Never combine spec writing and task planning into one unpaused step: the spec must be approved before planning tasks. Hard gate: stop and end turn after writing spec.
- No "coding in markdown": plans specify interface contracts, schemas, and verification commands; code blocks must remain under 40% of plan lines.
- Grounded symbols: cite verified `file:line` for existing repo functions; never hallucinate or invent helpers.
- Every plan includes a sequential `## Execution Waves` matrix with disjoint files per wave and Red-before-Green TDD steps.
- Flag unverified assumptions; verify them before relying on them.
- Do not implement until the user/supervisor approves the plan.

## Coding standards
- Delete before adding. Reuse existing helpers and patterns before writing new ones.
- Never wrap missing or hallucinated symbols in `getattr()` fallback shims; use verified module signatures.
- No speculative abstraction: generalize on the third use, not the first.
- Names say what a thing is; no `data`, `tmp`, `result` without context.
- Handle errors at trust boundaries; never swallow exceptions; no defensive code for impossible states.
- Comments explain why, never what.
- Touch only files the task needs; do not reformat unrelated code.
- New non-trivial logic ships with a test.

## Review bar
- Approve when the change clearly improves code health, even if imperfect; do not block on style preference.
- Axes in order: correctness, security, design fit, readability/simplicity, performance, tests.
- Label every finding Blocker, Important, or Nit; cite file:line and give a concrete fix.
- End with a verdict: Approve / Approve with comments / Request changes.

## Security
- No hardcoded secrets or tokens; use environment variables or a secret store.
- Validate external input at the boundary; parameterize queries.
- Least privilege for IAM roles, container users, and file permissions.
- Do not log secrets or personal data.
