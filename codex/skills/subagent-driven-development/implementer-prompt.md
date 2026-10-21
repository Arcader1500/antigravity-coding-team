# Implementer task payload

Spawn registered agent_type="implementer". Its TOML defines role, instructions and model; this is task data, not a replacement system prompt.

Supply task ID and full text; approved spec acceptance criteria; wave and dependencies; exact owned files; working directory; relevant source contracts; risk and required checks. State that other agents may be editing disjoint files and their changes must be preserved.

Request scoped implementation, focused checks and self-review. Use project-defined commands; run broader typecheck/build only when needed for changed contracts or unavailable narrower checks. No fixed framework, tool runner or full-suite command. No delegation or commits. Ask for status, owned files, exact commands/results/scope and concerns. A task's DONE is not full-feature completion. Follow subagent-driven-development for wave/completion checks and early high-impact review.
