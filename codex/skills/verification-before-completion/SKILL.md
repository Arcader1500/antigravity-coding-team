---
name: verification-before-completion
description: Require stage-appropriate command evidence before claiming task, wave or feature success, committing or handing off verified work.
---

Evidence before claims. Determine what is being claimed: a scoped task, integration wave, independent code review, or full feature completion. Use subagent-driven-development's task/wave/completion cadence. A passing focused test establishes only its scoped behavior; it cannot justify "all tests pass" or full feature completion.

For a task, require actual focused checks and implementer self-review. For a wave, require verifier interaction checks after writers finish, with early independent review for high-impact changes before dependent work. For feature completion, require independent full-diff review and verifier evidence for full relevant project tests, lint, typecheck and build that exist. Static/config/documentation projects use applicable validators. Missing tooling or unrun required checks are gaps, never passes.

Evidence must identify command, working directory, checked source revision or diff fingerprint including uncommitted/new files, environment, scope, exit code and relevant output. Read and assess the output; a started command, empty log, implementer promise or green unrelated check is insufficient. Report failures honestly. Code review approval is distinct from execution evidence.

Matching evidence may be handed off by verifier and reused when inputs, environment, required commands and scope are unchanged. The current agent need not rerun a command solely to repeat a supported claim, commit a scoped verified task, move to the next wave, delegate or finish a branch. A full final-wave run on the final code may also satisfy completion; targeted checks cannot substitute. Invalidate affected evidence after code, dependencies, configuration or environment changes, rerun the affected checks and ensure final full coverage before claiming overall success.

Only orchestrator commits when authorized and after the applicable stage checks/review. A task commit does not certify final feature completion. Never claim checks ran if they were only inferred. State precisely what passed, who ran it, its scope, and any limitations.
