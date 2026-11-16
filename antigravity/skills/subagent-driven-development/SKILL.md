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

## Risk-estimator state and observed timing

Resolve the run ID, state path, artifact identities and latest prediction revision
from the planner's persisted handoff or its explicit same-directory unpersisted
fallback. Store state in `.coding-team/risk.sqlite3` under the handed-off target
repository, never in a plugin cache or graph database. On resume, recompute the
plan/spec SHA-256 identities with the packaged helper's `artifact_identity`
contract. Reject stale associations. A changed plan/spec returns through the
existing planner/critic process and manual handoff, then starts a new run with
`previous_run_id` pointing to the prior run in the same repo. A material
environment change with unchanged artifacts can append a revision to the same
run; preserve the baseline.

The orchestrator is the sole state writer. Follow the packaged `risk_store.py`
schema-v1 CLI (`create-run`, `record`, `show`, `import-jsonl`) and stable record
IDs. Before each asynchronous implementer invocation, append an `attempt_start`
event with task ID, attempt, configured model/reasoning when known, UTC system
clock start, null end/duration, running status, controller-clock provenance,
empty known waits and null/unknown active time. On each individual completion
message, append a separate `attempt_end` event immediately with a different ID,
the same start, observed end, computed dispatch-to-result elapsed seconds, actual
status/checks and only measured waits. Do not wait for later wave completions to
timestamp an earlier result. These controller timings include tool/check time,
queueing and result delivery; they are not active model time. Preserve any
worker-reported times/effort separately with provenance; otherwise keep them
null. Retries/fixes get new attempt numbers and records; retain failed attempts.
Continue to respect the existing writer barrier: do not inspect worker edits or
start final gates while a writer remains active.

Before SQLite is ready, create append-only `.coding-team/task-timings.jsonl` in
the target repository with an ordered `create-run` operation followed by
`record` operations matching the helper. Replay with `import-jsonl` when
available, retain the bootstrap file, then continue through the helper. On a
write failure, retain the operation in JSONL and surface the error without
claiming persistence; retry with the same IDs. Preserve legacy `run_start` input
through the helper's compatibility handling.

Record review and verifier starts/results separately, including each review/fix
iteration and verifier rerun. Append an outcome with implementation/check status
separate from `human_live_acceptance`; leave later acceptance pending/unavailable
until evidence arrives. Compare estimates with per-task sums across attempts and
report whole-run wall time from first dispatch to final required result
separately, because wave tasks can overlap. Never infer missing phase timing.

Consult the estimator for materially new evidence only: a repeated failed fix,
symptoms suggesting a shared contract mismatch, an unexpected external
dependency, live behavior diverging from checks, or a material integration
change. Routine completion is an event only. The orchestrator gathers answers;
implementers keep their current reporting and no-delegation rules. Incident
records use the helper's required symptom, affected-task, failed-attempt, related
incident, evidence and next-diagnostic fields. Keep cause status unknown or
hypothesized without evidence; confirmed causes require evidence. Reassessment
references baseline/current revisions and separately states observed time and
remaining predicted time, appending rather than replacing the prediction. This
workflow creates no extra approval gate or fixed reassessment threshold.
