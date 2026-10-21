# Plan critic task payload

Spawn registered agent_type="plan-critic"; its TOML supplies instructions and model. Supply the approved spec and proposed plan paths, relevant verified source context, and changed/unresolved findings for a recheck.

Ask for spec coverage, grounded symbols and paths, actionable contracts, valid dependencies, disjoint same-wave file ownership and project-defined checks. Require task-focused checks and the execution sequence: all tasks/waves -> code-review/fix loop until approved -> final verifier -> complete. Do not add mandatory per-wave verifier runs or early risk-based review gates. Do not impose a language/framework or a fixed number of waves/reviewers. Wait for READY or NOT READY and resolve blockers until READY, then stop for the user's manual handoff, which authorizes execution without a separate plan-approval checkpoint.
