---
name: team-review
description: Independently review a local diff, branch or approved task using the Coding Team code-reviewer agent.
---

Determine the requested diff and base/head or working-tree scope. Ask for a missing target only if project context cannot establish it. Delegate using registered agent_type="code-reviewer", providing scope, requirements, risks and available verification evidence. Its TOML selects GPT-6 Sol / high; no main-chat model change is required. Do not paste the role prompt or duplicate model settings. Report a missing role instead of substituting an unnamed agent.

Wait for review, then return prioritized Blocker/Important/Nit findings with file:line, concrete fixes and verdict. Do not edit or commit for a review-only request. Check evidence is current for the reviewed source and environment. Report missing/stale evidence. Spawn agent_type="verifier" if fresh verification is requested or a material evidence gap needs resolving, not automatically for every review.
