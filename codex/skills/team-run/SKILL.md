---
name: team-run
description: Execute an approved Coding Team plan through dependency waves with implementation agents, risk-based review and independent verification.
---

Read [orchestrator.toml](../../agents/orchestrator.toml) and follow it as the main chat's workflow. Recommend GPT-6 Sol / low in the composer, or the coding-team-orchestrator CLI profile. This skill cannot change the current model.

Locate the approved spec and plan; preserve existing approvals. Ask for their location if missing, and obtain plan approval before edits if not already approved. Follow subagent-driven-development for wave scheduling and task, wave and completion checks. Spawn registered agent_type="implementer", "code-reviewer" and "verifier" for their work. Their TOML files supply instructions and models; do not reproduce prompts or add redundant model overrides. Wait before inspecting output. If a role is missing, report the gap rather than substituting a generic worker.

Only orchestrator stages owned files and commits when authorized. Preserve unrelated changes. Resolve failed checks and Important/Blocker findings before dependent work. Completion requires independent full-diff review and independent full relevant verification, not only self-review. Never push, merge or delete branches without authorization.
