---
name: subagent-driven-development
description: Execute an approved plan with registered Codex agents, dependency waves and risk-based verification.
---

Read the approved spec and plan. Extract full task text, IDs, dependencies, owned files, acceptance criteria and checks. Follow waves strictly: parallelize only disjoint owned files with satisfied dependencies, within actual concurrency. Wait for workers before inspecting output. Preserve unrelated work and prior approvals.

Dispatch registered agent types: implementer for one task, code-reviewer for independent analysis, verifier for command execution. Use agent_type and let role TOML supply instructions/model/effort; do not reconstruct role prompts or duplicate model overrides. Provide focused context rather than full chat history. Reuse workers for corrections. Report unavailable roles; never silently substitute generic roles. Workers never commit or delegate further.

## Task checks

Implementer runs focused checks for owned behavior and self-reviews against the task. For new non-trivial logic, demonstrate a meaningful failing test before implementation, then passing behavior. For static/config/documentation changes, use suitable syntax, rendering, link or configuration checks rather than artificial unit tests.

Run targeted typecheck/build for compiled contract changes or tasks that cannot be checked in isolation. If no narrower command exists, a full command may be needed; explain why. Report commands, exit codes, relevant output and scope. DONE means scoped task checks passed, not that the whole feature is verified.

## Wave checks

After all wave workers finish, inspect edits and resolve concerns. Dispatch verifier for checks covering interactions among the tasks and dependencies. Include relevant typecheck/build when shared types, package boundaries or generated interfaces changed. Discover commands from the actual repository, not a prescribed language/framework.

Require independent reviewer approval before dependent work for authentication/authorization, security boundaries, migrations or persistent data formats, public/shared interfaces, concurrency-sensitive logic, or other high-impact changes. Also review early when acceptance criteria are uncertain or scope changed. Routine isolated tasks do not require two separate reviewers each. User-requested stricter cadence takes precedence.

Never run integration checks while implementers are writing. Do not advance after failed wave checks or unresolved Important/Blocker findings. Only orchestrator stages explicit owned paths and commits when authorized, after applicable checks and review. Such commits may precede final feature verification; they are not a completion claim.

## Completion checks

After the last wave, dispatch code-reviewer against the approved spec and full change for correctness, security, design fit, clarity, performance and coverage. Dispatch verifier for the full relevant project tests, lint, typecheck and build commands that exist. Static/documentation-only repositories use applicable validators. Missing tooling is a gap, not a pass. These independent checks cannot be replaced by implementer self-review.

Avoid duplicate identical checks on unchanged inputs/environment. A final-wave verifier run can serve as completion verification only if it already covered the full final revision and all completion commands. Earlier targeted checks cannot replace full coverage. Record command, scope, source revision or diff fingerprint, environment and result in reports. After fixes or dependency/configuration changes, rerun affected checks; full checks must cover the final revision before claiming overall success. Reviewer consumes verifier evidence rather than rerunning every command.

Resolve correctness/scope concerns before dependent work. Answer NEEDS_CONTEXT and continue the worker. Resolve a BLOCKED cause or report it; do not retry unchanged. Give concise progress and a final report with independent review, checks, commits and limitations. Never push, merge or delete branches without authorization.
