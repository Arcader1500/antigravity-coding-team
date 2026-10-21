---
name: verification-before-completion
description: Require scoped evidence for task claims and post-review independent verifier evidence for overall completion.
---

Follow subagent-driven-development's sequence: implement tasks/waves -> review/fix loop until approved -> verifier -> complete. No automatic per-wave verifier runs or early risk-based review gates.

Task completion requires actual focused checks and implementer self-review. Passing a focused test supports only its scope; it cannot justify "all tests pass" or final feature completion. Orchestrator can use task evidence to advance dependencies and commit authorized owned changes, without claiming final approval.

Overall completion requires code-reviewer approval followed by independent verifier execution of full relevant project tests/lint/typecheck/build that exist, or applicable static/config/documentation validators. A review verdict is not command evidence, and task checks do not substitute for final verification. Missing required tooling is a gap, never a pass.

Evidence identifies command, working directory, source revision or diff fingerprint including uncommitted/new files, environment, scope, exit code and relevant output. Read the output; a started command, empty log or promise is insufficient. Report failures honestly.

If verifier fails, orchestrator delegates implementer fixes, reviewer approves the changes, then verifier reruns affected checks and establishes final coverage. Matching verifier evidence may be reused only for unchanged inputs/environment/commands/scope after the required post-review verifier stage has occurred. Do not use earlier task or wave evidence to bypass that stage. Re-run affected checks after source/configuration/dependency/environment changes.

Never claim full completion before reviewer approval and passing required independent verification. State exactly what passed and its limitations.
