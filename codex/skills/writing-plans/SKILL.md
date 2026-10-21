---
name: writing-plans
description: Turn an approved spec into a repository-grounded plan with dependency waves and proportionate checks.
---

Require an approved design spec; preserve prior explicit approval. Save under docs/superpowers/plans/YYYY-MM-DD-<topic>-plan.md unless the project/user specifies otherwise. Never implement source while planning.

Inspect language, framework, manifests, build configuration and CI before choosing commands. Use actual project scripts, test runner and paths. Verify existing symbols/signatures against source with file:line citations; distinguish new contracts. Resolve or flag unknown tooling/dependencies instead of inventing them.

Describe goals, approved spec path, architecture and acceptance criteria. Include an "## Execution Waves" table derived from real dependencies, not fixed framework layers. Same-wave tasks own disjoint files. Create contracts before consumers; choose the number of waves from dependencies. Do not prescribe Python, FastAPI, a test runner, OS or directory layout.

Each task specifies:
- **Wave:** number.
- **Depends on:** task IDs or None.
- **Files Touched:** exact created/modified/test paths.
- **Contracts and acceptance criteria:** interfaces, behavior, errors and important edge cases.
- **Risks:** relevant implementation concerns and acceptance checks; do not automatically add extra review gates.
- **Task checks:** concrete repository commands and expected behavior. Non-trivial logic uses failing behavior, implementation, then passing behavior. Static/config/documentation changes use applicable validators.

Specify focused implementer checks for tasks and full relevant verifier checks after the review/fix loop. Follow subagent-driven-development: all tasks/waves -> code-reviewer -> orchestrator dispatches implementer fixes -> reviewer rechecks until approved -> verifier -> complete. Do not add mandatory verifier runs per wave or early risk-based review gates unless the user explicitly requests them. State when shared contracts require broader typecheck/build. Do not put full suites or two reviewers into every routine task. No worker commit steps; orchestrator alone commits authorized verified changes.

Use contracts and test cases instead of full implementation dumps. Keep snippets short and only for tricky behavior. No placeholder commands or entire modules/templates. Use real temporary filesystem fixtures. Follow repository patterns and stay within scope.

Self-review against every spec requirement, dependency, owned file, symbol and command. The planner then delegates critique using registered agent_type="plan-critic", supplying approved spec and plan context; TOML provides role/model settings. Wait for findings, fix blockers, and recheck only changed/unresolved items until READY. After critic READY, stop and present the plan for manual handoff to $team-run. Do not auto-start execution. The user's explicit handoff counts as execution approval. Do not repeat execution-choice questions already answered.
