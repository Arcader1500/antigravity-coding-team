# Code quality review payload

Use registered agent_type="code-reviewer" after all tasks/waves, and again after fixes. Supply full initial diff scope, approved requirements, affected contracts and task-check evidence; for rechecks supply findings, fixes and affected scope. Review correctness, security, design fit, clarity, performance and coverage with file:line, fixes and verdict.

Combine code quality with spec compliance. Loop reviewer -> orchestrator -> implementer -> reviewer until approved. Do not impose automatic per-task or per-wave review. Final verifier is dispatched after approval; verification fixes return through implementer and reviewer before verification resumes. Do not duplicate model overrides or role prompts.
