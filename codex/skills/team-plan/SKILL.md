---
name: team-plan
description: Start Coding Team planning for a feature, producing an approved spec and a critic-checked implementation plan.
---

Read [planner.toml](../../agents/planner.toml) and use it as the main chat's planning workflow. This selects behavior, not the current model: recommend GPT-6.1 Sol / medium in the composer, or the coding-team-planner CLI profile. State a mismatch if visible; do not claim to switch models.

Clarify material requirements, delegate scoped exploration using registered agent_type="researcher", and write the design spec. Obtain spec approval before task decomposition. Then use writing-plans and registered agent_type="plan-critic". Carry existing approvals forward. After critic READY, consult registered agent_type="risk-estimator", persist the consultation and baseline prediction through the packaged helper, and include run ID, state path, artifact identities, latest revision and unresolved risks in the existing handoff to $team-run. Consult provisionally earlier only for a specific material uncertainty. Preserve critic findings and verdict; risk advice adds no approval gate. If helper persistence fails, surface the bounded error and use the planner's adjacent `.risk-handoff.json` fallback contract with `storage_status: not_persisted`; never change the critic-approved plan. Then stop for the user's manual handoff. That handoff itself authorizes execution; do not add a separate plan-approval question. Never implement application code in this workflow.

Use registered role TOML settings; do not paste role prompts or duplicate model overrides. Give workers focused task context, wait for results, and reuse workers for corrections. If a role is unavailable, report it and request configuration reload rather than silently using a generic agent.
