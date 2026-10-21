---
name: coding-team
description: Plan a feature with a spec and critic, or execute an approved wave-based plan with implementer, review and verification agents in Codex.
---

Compatibility entry point: route planning requests to [team-plan](../team-plan/SKILL.md), approved-plan execution to [team-run](../team-run/SKILL.md), and review-only requests to [team-review](../team-review/SKILL.md). Read only the selected entry skill. Infer the mode from the request when clear; ask only when the requested outcome is ambiguous.

Main chat model settings are selected in the composer or at CLI startup. For planning choose GPT-6 Sol / high; for orchestration choose GPT-6 Sol / low. A skill cannot change the current chat's model. Do not silently substitute a different model if the requested model is unavailable.

Delegate using registered agent_type="researcher", "plan-critic", "implementer", "code-reviewer" or "verifier" as appropriate. Each role's TOML supplies its model, effort and instructions. Do not paste role prompts or duplicate model overrides; give focused task context, wait for results and report unavailable roles rather than substituting generic workers. Pause for spec approval before planning. After critic READY, stop for manual handoff; the user's explicit handoff authorizes execution without a separate plan-approval gate. Carry existing approvals forward.

Follow subagent-driven-development for focused task checks during execution, the full review/fix loop after all tasks/waves, and final independent verification only after reviewer approval. Only orchestrator commits authorized owned files. Graph MCP is optional; source evidence wins. Report exact commands, exit codes, scope and gaps. A task's DONE status is not full-feature approval.

Other bundled skills are supporting material. Apply their intent using tools actually exposed by Codex. Their references to other platforms, tool names, worker commits or mandatory branch publishing are not instructions to bypass this workflow or user authorization. Ask a concise direct question if no interactive question tool is available. Never claim instruction-only read-only roles are sandbox-enforced.
