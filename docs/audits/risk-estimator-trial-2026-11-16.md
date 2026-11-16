# Risk estimator prompt trial

Date: 2026-11-16. Evaluator: GPT-6.1 Sol, medium reasoning.

Historical trial: the user subsequently removed all scheduled/run-count-based rubric review and clarified actual timing capture. The raw request/output and their original artifact hashes remain unchanged; they describe the earlier plan/agent version. The forecasts below are historical, uncalibrated estimates and are not refreshed predictions for the revised scope.

The user requested an implementation plan, creation of the estimator before invocation, and a live demonstration of its output. The [plan](../superpowers/plans/2026-11-16-risk-estimator-plan.md) passed the existing plan critic after four contract/dependency findings were resolved. Only the agent prototype and its validation registration were implemented; T2-T6 remain future work.

## Invocation

- Definitions: [Codex](../../codex/agents/risk-estimator.toml) and [Antigravity](../../antigravity/agents/risk-estimator.md). Their instruction bodies match.
- The new role is not hot-registered in this running session. An explicitly configured generic worker read the saved Codex role definition and followed its instructions, with model gpt-6.1-sol and reasoning_effort medium. This validates the prompt behavior, not native installed-role discovery.
- [Request](risk-estimator-trial-2026-11-16-request.json) captures artifact hashes, critic findings, target execution models, two implementation worker slots, completed T1 and remaining T2-T6.
- [Raw returned JSON](risk-estimator-trial-2026-11-16-output.json) is preserved without correcting its predictions or causal labels.
- Parent UTC clock observations immediately before invocation and after receiving the result were 06:34:05 and 06:36:38, respectively: 153 seconds. This is a coarse parent-observed interval, including dispatch/result handling, not measured model reasoning time. This prompt trial is not one of the 30-50 completed implementation runs.

## Output

All durations below are the agent's uncalibrated forecasts, in agent minutes. The estimator returned no questions and marked the forecast provisional because there are no calibration observations.

| Remaining work | Complexity | Optimistic | Likely | Conservative |
|---|---|---:|---:|---:|
| T2: SQLite records and validation | High | 45 | 90 | 160 |
| T3: Planner consultation and handoff | Medium | 20 | 40 | 70 |
| T4: Execution logging and reassessment | High | 25 | 45 | 80 |
| T5: Packaging and validation | Medium | 25 | 45 | 80 |
| T6: Integration and manual-review protocol | Medium | 25 | 45 | 85 |
| Independent final review | Shared gate | 15 | 25 | 45 |
| Final verification | Shared gate | 10 | 20 | 35 |
| Summed agent work | | 165 | 310 | 555 |
| Elapsed agent workflow | | 145 | 270 | 485 |

Execution assumptions are the current Codex roles: Luna/medium implementation workers, Sol/medium reviewer, Luna/low verifier and Sol/low controller. Only T3 and T4 overlap. Human effort and external waits remain null. The evaluator's Sol/medium setting is separate from these target execution models.

The main risks were record integrity, mismatched handoff contracts, conflicting workflow instructions, validation/packaging drift and misleading timing provenance. Each returned risk includes affected tasks and a proposed diagnostic. The role added no approval gate or implementation changes.

## Checks and limitations

Both package ValidateOnly commands passed and discovered nine agents. TOML parsing, prototype model/effort and cross-platform instruction parity passed. The response passed checks for JSON structure, identity/revision, exact task coverage, ordinal labels, finite ordered scenario values, phase/task/total arithmetic, two-worker elapsed scheduling, risk references, manual-review metadata and unchanged artifact hashes. Python syntax parsing of the modified validator and git diff --check passed.

One causal-confidence label needs human attention: R4 marks the existing validator policy mismatch as confirmed. The supplied evidence confirms a model-expectation mismatch; the stronger explanation that the validator conflates source-role and launch-profile policy is an inference about its cause. Preserve the raw output and treat that explanation as a hypothesis until verified. No automatic prompt/rubric change was made from this trial.

The trial did not exercise interview continuation, incident reassessment, durable SQLite logging, native role registration, installed-file parity, live deployment testing or timing calibration. The known pre-existing deep-validator planner-model mismatch remains for T5. The Antigravity exact Hydrogen/Argon model-pin limitation also remains.
