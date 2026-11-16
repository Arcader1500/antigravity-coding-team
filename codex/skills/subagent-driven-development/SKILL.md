---
name: subagent-driven-development
description: Execute a manually handed-off plan by waves, then loop independent review and fixes until approved before final verification.
---

## Approved sequence

Planner -> spec checkpoint -> create plan -> plan-critic -> planner fixes -> repeat critic until READY -> manual handoff to orchestrator -> implementers execute tasks/waves -> code-reviewer -> orchestrator dispatches implementer fixes -> reviewer rechecks until approved -> verifier -> complete.

The planner stops after READY and presents the plan for manual handoff. Do not start execution automatically. An explicit user handoff authorizes execution of that plan; do not ask for the same approval again.

## Required graph preflight

Before worker dispatch, the orchestrator must read and complete
[code-review-graph setup](references/code-review-graph.md). Set up any missing
executable, repository index, ignore entry and post-commit hook under session
permissions. Confirm MCP access to the intended repository. Failed setup or missing
MCP access blocks execution; source inspection alone does not replace readiness.

## Tasks and waves

Read the handed-off spec and plan. Extract full task text, IDs, dependencies, owned files, acceptance criteria and checks. Follow waves strictly; parallelize only disjoint files with satisfied dependencies within actual concurrency. Await all writers in the current wave before inspecting or committing wave output; never advance while writers remain active. Preserve unrelated user changes.

Dispatch registered agent_type="implementer" for one scoped task, "code-reviewer" for independent review, and "verifier" for final command execution. Role TOML supplies model/effort/instructions; do not paste role prompts or duplicate model overrides. Provide focused context, reuse workers for fixes and report missing roles instead of generic substitution. Workers never delegate or commit.

Each implementer reads the bundled ponytail skill in full mode within assigned scope, runs focused project checks and self-reviews. The role controls ownership, checks, status format and the no-commit rule. For non-trivial logic, demonstrate failing behavior before implementation, then passing behavior. Static/config/documentation changes use applicable validators. Run broader typecheck/build only when needed to establish the task's correctness. Report commands, exit codes, scope and concerns. DONE is task completion, not final feature approval.

Orchestrator inspects task results and resolves failures/concerns before dependent tasks. A completed wave is a scheduling boundary, not an automatic verifier or reviewer dispatch. Do not impose per-wave verification, early risk-based reviews, or two reviews per task. Honor extra checks/reviews only when explicitly requested or specified by the handed-off plan. Only orchestrator stages owned files and commits when authorized, after applicable task checks; a task commit is not final approval.

## Review and fix loop

After all tasks/waves finish, dispatch code-reviewer on the full change against the spec. Reviewer covers correctness, security, design fit, clarity, performance and coverage. If findings require changes, orchestrator delegates fixes to implementer; implementer runs focused checks; code-reviewer rechecks fixes and affected scope. Repeat until reviewer approves and every required finding is resolved. Non-blocking advisory nits may remain only when reviewer explicitly approves them. Do not dispatch final verifier while required review findings remain open.

## Final verification and completion

Only after reviewer approval, dispatch verifier for full relevant project tests, lint, typecheck and build that exist, or applicable static/config validators. Missing required tooling or unrun required checks are gaps, not passes. Implementer checks and review approval cannot replace this independent final verifier stage.

If verification fails, orchestrator dispatches implementer fixes, obtains code-reviewer approval of the changes, then returns to verifier for affected checks and final relevant coverage. Repeat until review is approved and required verification passes; do not declare completion while either fails. Reuse verifier evidence only when code, dependencies, configuration, environment, commands and scope remain unchanged. Evidence before the required post-review verifier stage cannot skip that stage.

Report final review verdict, verifier commands/exit codes/coverage, commits and limitations. Resolve NEEDS_CONTEXT or concrete BLOCKED causes rather than retrying unchanged. Never push, merge or delete branches without authorization.

## Risk-estimator state and observed timing

Resolve the run ID, local state path, artifact identities and latest prediction
revision from the planner's persisted handoff or its explicit unpersisted fallback.
The database belongs under `.coding-team/risk.sqlite3` in the handed-off target
repository, never in a plugin cache or graph database. Before resume, use the
bundled helper's `artifact_identity` contract to verify the current plan/spec
SHA-256 values. Reject stale associations. A changed plan/spec goes through the
existing planner/critic process and manual handoff, then starts a new run linked
with `previous_run_id`. A changed environment with stable artifacts can append a
prediction revision to the current run. Preserve the baseline prediction.

The controller is the sole state writer. Use `risk_store.py`'s schema-v1
`create-run`, `record`, `show`, and `import-jsonl` operations and stable record IDs.
Immediately before each task-attempt dispatch, append an `attempt_start` event
with the task, attempt, configured model/reasoning when known, UTC `start_time`,
null `end_time` and `elapsed_seconds`, running status, controller-clock
provenance, empty `known_waits`, and null/unknown `active_seconds`. Upon each
individual completion message, immediately append a separate `attempt_end` event
with a distinct ID, the same start, observed UTC end, computed controller
dispatch-to-result elapsed seconds, status/checks and only measured waits. Store
worker-reported timing separately with its provenance; absent timings remain
null. Record an earlier completion without waiting for the rest of its wave, but
do not inspect worker edits until every writer in that wave has completed. Retries
and fixes use new attempt numbers and records; never overwrite failed attempts.

When SQLite is not ready, bootstrap an append-only `.coding-team/task-timings.jsonl`
in the target repo using a `create-run` envelope followed by ordered `record`
envelopes matching the helper. Replay via `import-jsonl` when it is available,
keep the bootstrap file, and continue through the helper. On persistence failure,
retain the operation in JSONL and surface the error; do not claim it was stored.
Retry with the same IDs. Preserve/import an existing legacy `run_start` line using
the helper's compatibility handling.

Log review and verifier dispatch/results as separate stages, including each
review/fix iteration and verification rerun. Append final implementation/check
outcome separately from human/live acceptance; leave acceptance pending or
unavailable until evidence supports a later outcome. Compare predictions with
measured attempt sums, and report whole-run wall time from first task dispatch to
the final required result separately because parallel tasks overlap. Do not infer
unobserved phases from the forecast.

Consult the estimator only for material new evidence such as a repeated failed
fix, symptoms that may share a contract cause, an unexpected external dependency,
live behavior diverging from checks, or material integration changes. Routine
completion only logs an event. The controller gathers answers; worker reporting
and no-delegation contracts remain unchanged. Store incidents with symptoms,
attempts, affected tasks, links/evidence and cause status `unknown`,
`hypothesized`, or `confirmed`; group symptoms under a shared cause only when
evidence warrants it. Reassessment cites baseline/current revisions, observed
time/provenance and remaining predicted time, then appends a revision without
replacing prior estimates. This adds no approval gate or fixed trigger.
