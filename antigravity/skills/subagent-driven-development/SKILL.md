---
name: subagent-driven-development
description: Execute approved AGY plans through implementer waves, controller-owned commits, independent review and final verification.
---

# Subagent-Driven Development

The orchestrator coordinates execution. A fresh implementer owns each task;
workers implement, check and self-review. Only the controller commits. Independent
code-reviewer review follows the final wave, then verifier checks the result.

## Prepare

1. Read the approved plan once. Extract full task text, context, wave,
   dependencies and exact file ownership. Track completion in the plan or an
   available tracker; no particular tracking tool is required.
2. Confirm branch and working tree. Never start on main/master without explicit
   consent. Preserve unrelated changes. Workspace setup belongs to the controller.
3. Complete the orchestrator's required graph preflight before dispatch. Follow
   [graph rules](../../rules/code-review-graph.md); the controller sets up missing
   graphs and hooks before any workers start. Subagents never rebuild mid-wave.
4. When affected files are not fully enumerated, use `get_impact_radius_tool` and
   `query_graph_tool` to confirm scope and resolve ownership collisions. Verify
   critical graph claims against source.

## Execute waves

- Follow `## Execution Waves` and `**Depends on:**` exactly. Dispatch concurrently
  only within the current wave, with disjoint file ownership and all dependencies
  complete. Serialize overlapping tasks; disjoint paths do not override dependencies.
- Use `invoke_subagent` with the implementer role and
  [implementer-prompt.md](implementer-prompt.md). Paste full task text and context
  inline, including working directory, ownership, dependencies and required checks.
  Workers must preserve others' edits and leave changes uncommitted.
- `invoke_subagent` is asynchronous. Dispatch eligible disjoint tasks in the wave,
  then end the turn and resume on completion messages. The immediate return is
  not completion. Never poll with `manage_task`, timers or Git commands.
- Wait for all writers in the wave before inspecting or committing their output
  or advancing. Confirm actual end-state and check results, rather than relying
  only on reports or `git status`. Never set `MatchPerLine` on `grep_search`;
  confirm empty results with `view_file`.
- The controller stages only intended files and commits completed task changes
  with conventional messages. Post one line per completed task:
  `[wave/track task] DONE — one sentence`.

## Worker status

- DONE: Check end-state and required check results; commit after all wave writers finish.
- DONE_WITH_CONCERNS: Resolve correctness or scope concerns before advancing;
  record non-blocking observations and continue.
- NEEDS_CONTEXT: Supply missing context and re-dispatch.
- BLOCKED: Resolve the cause or report the blocker. Never retry unchanged.

If a task names a nonexistent repository function or attribute, inspect the module
for its real signature and report the discrepancy under DONE_WITH_CONCERNS.
Never mask a missing symbol with a `getattr` fallback shim. Changes beyond assigned
ownership require controller coordination.

## Final gates

1. After all waves and writers finish, dispatch code-reviewer on the full diff
   against approved requirements. Use
   [code-quality-reviewer-prompt.md](code-quality-reviewer-prompt.md). Review covers
   spec compliance and code quality. Reviewer pairs per task are not required.
   [spec-reviewer-prompt.md](spec-reviewer-prompt.md) is an optional focused follow-up
   for a particular compliance question using the existing code-reviewer role.
2. Dispatch implementer fixes for required findings, wait for completion, inspect
   and commit changes, then have the reviewer recheck until approved.
3. Only after approval, dispatch verifier on required project checks. Worker checks
   and self-review do not replace these independent final gates.
4. Failed verification returns to fixes, writer completion, commit, review approval
   and verification. Do not claim completion until both gates pass.
5. Use bundled `finishing-a-development-branch` for branch disposition. Publishing,
   merging and deletion still require user authorization.

Use configured role models; this skill does not change model allocation. Continue
through the approved plan without routine check-ins; stop for unresolved blockers
or decisions needed to preserve user intent.
