---
name: coding-team
description: Plan a feature with a spec and critic, or execute an approved wave-based plan with implementer, review and verification agents in Codex.
---

Use the planner for requirements, spec and plan; use orchestrator for an approved written plan. Load only the selected role's instructions from ../../agents/<role>.toml. These instructions also define delegation for this workflow. Delegate scoped tasks with native collaboration tools and wait for results. A model override requires a fresh worker without full chat history; supply task context explicitly.

Main chat model settings are selected in the composer or at CLI startup. For planning choose GPT-6 Sol / high; for orchestration choose GPT-6 Sol / low. A skill cannot change the current chat's model. Do not silently substitute a different model if the requested model is unavailable.

Use researcher (Luna / low) for scoped exploration and plan-critic (Sol / high) to check the plan against the approved spec. Pause for spec approval before task decomposition, and plan approval before implementation. Carry existing approvals forward. Hand off only the approved documents, decisions and unresolved risks when starting a fresh execution chat.

Use implementer (Sol / medium) for one owned task, code-reviewer (Sol / high) for diff review, verifier (Luna / low) for actual project checks. Worker status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED. Only orchestrator commits; workers never commit. Respect wave dependencies and disjoint file ownership, and await workers before inspecting their output. Graph MCP is optional; source evidence wins. Report exact verification commands, exit codes and gaps.

Other bundled skills are supporting material. Apply their intent using tools actually exposed by Codex. Their references to other platforms, tool names, worker commits or mandatory branch publishing are not instructions to bypass this workflow or user authorization. Ask a concise direct question if no interactive question tool is available. Never claim instruction-only read-only roles are sandbox-enforced.
