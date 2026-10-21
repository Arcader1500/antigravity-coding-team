---
name: team-plan
description: Start Coding Team planning for a feature, producing an approved spec and a critic-checked implementation plan.
---

Read [planner.toml](../../agents/planner.toml) and use it as the main chat's planning workflow. This selects behavior, not the current model: recommend GPT-6 Sol / high in the composer, or the coding-team-planner CLI profile. State a mismatch if visible; do not claim to switch models.

Clarify material requirements, delegate scoped exploration using registered agent_type="researcher", and write the design spec. Obtain spec approval before task decomposition. Then use writing-plans and registered agent_type="plan-critic". Carry existing approvals forward. Present the critic-checked plan for approval before execution. Hand off to $team-run with the approved plan path. Never implement application code in this workflow.

Use registered role TOML settings; do not paste role prompts or duplicate model overrides. Give workers focused task context, wait for results, and reuse workers for corrections. If a role is unavailable, report it and request configuration reload rather than silently using a generic agent.
