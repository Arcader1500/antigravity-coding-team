# Spec compliance review payload

Use registered agent_type="code-reviewer" for high-impact early review or full-change completion review. Routine tasks use implementer self-review and wave integration checks; this file does not mandate another reviewer per task.

Supply approved spec/requirements, review scope (base/head or working diff including new files), implemented task IDs, risk, claims and current verification evidence. Ask the reviewer to verify behavior in source against acceptance criteria, flag missing/extra scope and report Blocker/Important/Nit findings with file:line and verdict. Combine spec compliance and code quality in the same independent review unless a user explicitly requests separate reviews. The registered TOML provides instructions/model; do not paste an alternate role prompt.
