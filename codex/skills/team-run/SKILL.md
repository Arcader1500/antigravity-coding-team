---
name: team-run
description: Execute an approved Coding Team plan through dependency waves with implementation agents, a review/fix loop followed by final independent verification.
---

Read [orchestrator.toml](../../agents/orchestrator.toml) and follow it as the main chat's workflow. Recommend GPT-6 Sol / low in the composer, or the coding-team-orchestrator CLI profile. This skill cannot change the current model.

Locate the approved spec and plan; preserve existing approvals. Ask for their location if missing, and treat the user's manual handoff of the critic-READY plan as execution approval. Follow subagent-driven-development for task/wave execution followed by review -> implementer fixes -> reviewer recheck until approved -> verifier -> complete. Spawn registered agent_type="implementer", "code-reviewer" and "verifier" for their work. Their TOML files supply instructions and models; do not reproduce prompts or add redundant model overrides. Wait before inspecting output. If a role is missing, report the gap rather than substituting a generic worker.

Before dispatch, complete the required graph preflight linked from subagent-driven-development. Orchestrator repairs missing setup and confirms target-repository MCP access; failures block dispatch.

Only orchestrator stages owned files and commits when authorized. Preserve unrelated changes. Resolve failed checks and Important/Blocker findings before dependent work. Do not add automatic per-wave verifier runs or early risk-based reviews. Only after all required review findings are fixed and approved, dispatch final verifier. Verification failures return through implementer fixes and reviewer approval before verifier reruns. Never push, merge or delete branches without authorization.
