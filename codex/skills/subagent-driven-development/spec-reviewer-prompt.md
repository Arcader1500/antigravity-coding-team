# Spec compliance review payload

After all implementation tasks/waves finish, spawn registered agent_type="code-reviewer". Supply approved spec, handed-off plan, full diff scope including new files, implemented task IDs and focused check evidence. Ask for source-grounded acceptance-criteria review and Blocker/Important/Nit findings with file:line, fixes and verdict. Combine spec compliance and code quality in one review, not two per task.

Orchestrator dispatches implementer fixes for required findings; reviewer rechecks fixes and affected scope until approved. Final verifier runs only after approval. If verifier then requires code fixes, review those fixes before returning to verifier. Role TOML supplies instructions/model; payload contains task context only.
