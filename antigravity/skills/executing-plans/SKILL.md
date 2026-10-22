---
name: executing-plans
description: Resume an approved written plan in a fresh AGY execution session using the orchestrator workflow.
---

# Executing Plans

Read the approved plan, identify tasks, waves, dependencies, ownership and required
checks, and resolve critical gaps. Preserve existing approvals.

Use the orchestrator role and bundled
[subagent-driven-development](../subagent-driven-development/SKILL.md) skill.
Both entry points use the same contract: required graph setup before dispatch;
fresh implementer per task; disjoint wave parallelism; worker checks and self-review;
controller-owned commits after all wave writers finish; independent review after
the final wave, then independent verification. Fixes require writer completion,
commit, review approval and verification again.

`invoke_subagent` is asynchronous: dispatch eligible wave tasks, end the turn and
resume on completion messages. Never poll or treat the immediate return as DONE.
Do not substitute inline implementation or per-task reviewer pairs. If subagents
are unavailable, report the limitation before choosing another approach.

Finish with bundled
[finishing-a-development-branch](../finishing-a-development-branch/SKILL.md),
preserving user authorization for branch disposition. Never retry unchanged blockers.
