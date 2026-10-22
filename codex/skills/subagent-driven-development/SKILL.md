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
