# Risk estimator assessment for Coding Team

Assessed: 2026-11-16. Source revision: `869d36d5db7799065d33ea23312b265fef80349c` on `dev`.
Scope: the independently maintained Antigravity and Codex plugins in this repository. This is an assessment, not an approved implementation spec or a claim that the feature exists.

## Recommendation

The proposed estimator fits the existing division of responsibilities. Keep `plan-critic` responsibilities unchanged. Add one lightweight `risk-estimator` role, a common structured consultation contract, and a small deterministic SQLite logging utility. The substantive work is reliable measurement and handoff between sessions; adding the agent definition is the easy part.

Confirmed scope: begin with a rubric, task complexity ratings, agent time estimates and observation logging. Any rubric review or revision is entirely manual, outside this implementation, and happens whenever the user chooses. There is no run-count trigger, deadline or scheduled review. Do not add automatic training, statistical fitting or self-modifying estimator behavior to the initial version.

Only the planner and orchestrator need to invoke the estimator initially. Implementers already report failed checks, concerns, missing context and blockers. The orchestrator can turn that evidence into a reassessment request and pass useful guidance back to the implementer. This preserves task ownership and gives the estimator context across workers. Direct implementer consultations offer little initial value and would conflict with Codex's existing no-delegation rule.

Use the estimator as advisory input. A high risk estimate does not invalidate a critic-READY plan, authorize new scope, or replace reviewer approval and final verification. If targeted investigation discovers an actual plan defect, return it to the planner's existing critic loop.

## Current support and gaps

| Responsibility | Existing support | Required addition |
|---|---|---|
| Estimate | Plans already specify tasks, dependencies, owned files, risks and checks. Critic findings distinguish verified contracts from unknowns. | A consistent agentic complexity rubric, evidence-based risk statements and phase-specific agent execution time ranges. |
| Interview | Planner and orchestrator can invoke specialist roles. Antigravity already documents request/result consultation with `devops-expert`. | Stable question IDs, answers with evidence, explicit unknowns and continuation across invocations. |
| Reassess | Worker reports, reviewer findings and verifier failures reach the controller. Existing loops already support fixes and rechecks. | Triggers for reassessment, linked incidents, root-cause hypotheses and immutable estimate revisions. |
| Record observations | An earlier audit records useful historical failure mechanisms. | A structured outcome store and reliable observation collection that the user can inspect at their discretion. Manual review is outside the implementation; there is no comparable calibrated dataset in the inspected bundle. |

Relevant source evidence:

- `codex/agents/plan-critic.toml:10` and `:34`: source/contract validation, findings and READY/NOT READY verdicts.
- `codex/skills/writing-plans/SKILL.md:10` and `:12`: task and dependency contracts, including risks and verification commands.
- `codex/agents/planner.toml:7`, `:10` and `:35`: delegation rules, restricted write scope and critic loop.
- `codex/agents/implementer.toml:11` and `:17`: no delegation, owned task scope and existing result reports.
- `codex/agents/orchestrator.toml:10` through `:18`: wave execution, concerns, review/fix loop and final verifier.
- `antigravity/agents/planner.md:23`: an existing specialist consultation pattern.
- `antigravity/agents/implementer.md:37`: existing worker statuses and evidence reports.
- `codex/README.md:127`: durable execution state is already identified as remaining work.
- `docs/audits/agy-coding-team-deep-audit-2026-10-22.md:56`: historical examples are a bounded sample, not a measured failure rate. Use them to seed risk categories, not invented incident probabilities or durations.

## Workflow integration

The initial planning path should be:

`Planner -> Plan-Critic READY -> Risk-Estimator consultation -> existing manual handoff`

The execution path should remain:

`Orchestrator -> implementer waves -> reviewer/fix loop -> final verifier`

The orchestrator adds logging and consults the estimator when new evidence materially changes delivery risk. Useful triggers include a repeated failure after attempted fixes, multiple symptoms that may share one contract mismatch, an unexpected external dependency, or live behavior diverging from local checks. Routine task completion needs an event record, not another estimator invocation.

Consult before planning is finalized when a specific uncertainty warrants it; mark that assessment provisional and identify the absence of a critic verdict. After READY, supply the final spec, plan and findings. Do not ask the estimator to verify every symbol or audit every test again.

Preserve the existing review cadence. Codex explicitly rejects automatic per-wave verifier runs and early risk-based review gates. An estimator can recommend a diagnostic or expose an assumption without creating another approval gate. Changes to implementation scope still require the existing planning/ownership process.

The planner's manual handoff needs a run ID, task IDs, approved artifact fingerprints, estimator revision and a resolvable state location. Preserve the critic output as an artifact or record; it is currently primarily a returned report. A fresh execution chat cannot rely on the previous chat's agent memory. Bind each estimate to the exact plan/spec and critic evidence it used. A changed plan makes the old assessment stale; a changed environment may require reassessment even when the plan is unchanged.

## Consultation contract

Use one portable request/result envelope rather than persistent peer conversations:

| Direction | Minimum information |
|---|---|
| Request | Schema version, consultation/run/task IDs, mode (`estimate` or `reassess`), artifact fingerprints, critic findings, relevant runtime/model context, previous assessment and observed evidence. |
| Questions | Stable question ID, uncertainty being resolved, why the answer affects the forecast, and the smallest useful supporting evidence. |
| Answers | Question ID, answer or explicit unknown, evidence reference and observation time. Reuse existing user decisions. |
| Assessment | Per-task agentic complexity/risk dimensions, rationale, optimistic/likely/conservative agent execution time ranges with units and assumptions, correlated risks, unknowns, confidence, suggested diagnostics and revision reason. Human effort and external waits, if estimated, are separate. |

Return a provisional assessment when evidence remains unavailable. Bound the consultation effort and record unanswered questions rather than creating an unlimited interview. Distinguish `needs_evidence` from `assessed`; do not reuse the critic's READY/NOT READY vocabulary.

The estimator reads relevant local evidence and historical summaries but edits no application source and spawns no agents. Parent agents validate and persist its output through the logger. Any specialist investigation goes through the parent, which can consult the existing DevOps expert if needed.

## Prediction and measurement

The primary estimate is how many minutes the configured AI agents will take to complete the tasks. It is not a human developer estimate translated into agent time. Include agent source investigation, implementation, debugging/retries, agent review/rework and agent-run tests. Identify the model slug, reasoning level, tools, environment and available concurrency used for the forecast.

Start with ordinal low/medium/high scores for agentic complexity, integration uncertainty, defect exposure and debugging cost. Base complexity on discovery difficulty, ambiguity, tool interactions, integration and reproducibility rather than primarily on lines changed. Give each score concrete anchors and an evidence-based explanation. Record environmental access, dependency familiarity and acceptance-test realism where they affect a score. Avoid turning an arbitrary score sum into a probability.

Report optimistic, likely and conservative agent time estimates for each task, broken down into implementation, debugging, agent review/rework and automated/live tests performed by an agent. Express these as minutes with assumptions. Human review/manual testing, scheduling/queue delays and external provisioning waits have separate fields and must not be folded into agent work. Define whether review rework is counted under review or debugging so it is not counted twice.

Distinguish total agent work (the sum across agents) from elapsed time for the agent workflow. Use actual waves, dependencies and worker capacity to estimate elapsed execution; concurrently running agent tasks overlap. If a delivery-time forecast including human or external waits is useful, show it as a separate output. Risks from a shared external service are correlated and should not be treated as independent task incidents.

Initially label ranges and confidence as heuristic. Use optimistic/likely/conservative labels without claiming calibrated P10/P50/P90 percentiles. A fast model's self-reported confidence does not establish calibrated accuracy. Preserve predictions and observations for any later user-initiated inspection or rubric change, with no scheduled review or sample-count threshold. Preserve old rubric versions and original estimates for comparison.

The current workflow has no structured per-phase timing instrumentation. Measure task execution from an observed agent start to its result, including tool execution, agent-run checks and retries. Record any observed queue delays, human pauses and external waits separately. Controller timestamps alone measure dispatch-to-result elapsed time, including any unobserved waits; label that measurement accordingly rather than calling it active agent work. Log measurement provenance: controller-measured elapsed, worker-reported effort or inferred classification. Leave unavailable measurements null. Precise model reasoning time is not required for this feature; if finer phase measurement is needed, add explicit events rather than reconstructing precise durations from final prose.

Record implementation/check completion independently from human/live acceptance. Keep live testing pending, unavailable or not applicable until evidence arrives; do not count an untested deployment as a successful live outcome. Support a later outcome update without changing the original prediction. Preserve abandoned, interrupted and blocked runs so calibration is not based only on successful completions.

## Persistence

Use a small Python standard-library SQLite utility with validated JSON input and structured output. The agent reasons about risk; the utility validates IDs, schema versions, timestamp formats, numeric ranges and database operations. Do not ask the agent to generate arbitrary SQL for each consultation. This introduces a Python runtime requirement for the production logging path; the plugin currently uses Python for deeper validation but does not establish it as a required runtime for every workflow.

The initial logical records should cover:

| Record | Purpose |
|---|---|
| Runs and tasks | Stable identity, repository/plan/spec versions, platform, plugin/rubric/model versions and reasoning level, wave/dependency context and execution status. Count a run once per execution of an approved plan; tasks and retries belong to that run. |
| Consultations | Requests, linked questions/answers, evidence and unresolved uncertainty. |
| Predictions and revisions | Immutable baseline and subsequent forecasts, each tied to its evidence and superseded revision. |
| Incidents | Observed symptoms, failed attempts, hypothesized/confirmed root cause, evidence, affected tasks and related incident IDs. |
| Events and outcomes | Phase timestamps with provenance, checks, observed agent time and separately recorded waits/human effort where available, final revision and later human/live acceptance. |

A parent incident/root-cause reference can represent several symptoms from one underlying mismatch. Allow the cause to remain unknown or hypothesized until established. Preserve the symptom count and the distinct confirmed cause count; neither substitutes for the other.

The logger code ships with each installed plugin, while the database is local to the target project at `.coding-team/risk.sqlite3`. Keep database/journal/raw state excluded from Git and outside installed plugin caches so reinstalling the plugin does not overwrite history. Resolve local state against the target repository root. There is no global database or automatic cross-project history. Never reuse the graph's internal database for estimation history.

Actual timing starts before the logger is implemented: the parent uses the system clock and appends create-run/record envelopes to `.coding-team/task-timings.jsonl` from the first task. Once SQLite support is ready, it ingests those records idempotently and continues through the helper. Record each task attempt's dispatch/result time, status, model and elapsed seconds; keep identifiable pauses/waits separate and label controller elapsed versus worker-reported timing. Whole-run elapsed comes from the run's first/last timestamps, not a sum of concurrent tasks.

Have the active parent own state writes. This avoids workers competing to mutate the same records or editing outside task ownership. Add a narrow state-logging allowance to the planner's existing spec/plan-only write instructions. Use transactions and idempotent event IDs so a resumed session cannot duplicate observations. Surface logging failures, retain the unpersisted result for retry, and do not claim durable history was written when it was not. Missing history should yield an explicitly uncalibrated forecast.

The initial version gathers records; recording history does not automatically change future estimates. Manual inspection or rubric revision is entirely outside the implemented workflow and occurs only at the user's discretion. Track sample counts and model/environment changes as evidence, never as a review trigger. Automated historical retrieval or statistical calibration is outside the initial scope.

## Change surface

1. Add `antigravity/agents/risk-estimator.md` and `codex/agents/risk-estimator.toml`. The requested Antigravity estimator model is `gemini-4-hydrogen-medium`, matching the user's lightweight subagent choice. Exact slug pins are currently blocked by Antigravity's tier-only custom-agent loader (see follow-up below); do not claim `model: flash` guarantees Hydrogen Medium. The existing lightweight roles retain `flash`, and `plan-critic` now selects `pro`. Codex already uses `gpt-6-luna` for lightweight work. These are starting allocations, not benchmarked guarantees for estimation quality.
2. Add the shared contract/rubric and SQLite utility, packaged so both independently installed plugins can find their own installed copies. Choose one canonical development source or test parity; the repository currently has no shared production packaging layer.
3. Update planner and orchestrator instructions plus planning/execution entry skills and handoff templates. Include the permitted state writes and the advisory consultation flow. Existing implementer result fields are enough to begin; no new worker delegation capability is needed.
4. Update Codex structural validation: `codex/scripts/validate.ps1:18` hardcodes eight agents, and `:23` enumerates role names. `codex/scripts/validate.py:8` likewise fixes role/model mappings and later checks skill counts and installed parity. New skills, if introduced, affect the fixed counts too. Codex's installer already copies every agent TOML at `codex/install.ps1:85`; it does not need a separate copy step for the ninth agent.
5. Update both READMEs and runtime-state ignore rules. Keep `plan-critic`, code-reviewer and verifier responsibilities intact. Check the installed roles after reload; a source definition alone does not make a role available in an already-running session.

No new review role, trained prediction model, automatic calibration, dashboard, service or always-on MCP server is needed for the first version.

## Delivery order and validation

Implement the contract and logger first, then rubric-based complexity/agent-time estimation and persisted handoff, then incident-driven reassessment and later outcome updates. Record measured timing throughout. Manual rubric review and automated learning are outside this implementation; no timeline or run-count checkpoint applies.

Meaningful checks for an eventual implementation:

- A critic-READY plan with uncertain external access yields an advisory risk assessment without changing the critic verdict or final review sequence.
- Question/answer continuations retain identity; unavailable evidence remains unknown; the baseline survives every revision.
- A fresh orchestrator session resumes the correct run and rejects stale artifact associations.
- Duplicate events, interrupted writes and logging errors do not corrupt history or fabricate successful persistence.
- Multiple symptoms can share one supported root cause; a revised hypothesis does not erase the original observations.
- Measured elapsed time, reported effort and unknown timing stay distinguishable; parallel execution is not summed into a false delivery estimate.
- Agent execution time remains separate from human estimates and external waits, and predictions identify the model/reasoning configuration.
- The initial estimator produces rubric-based complexity and optimistic/likely/conservative agent time estimates without automatic changes to its rubric or model. A manual rubric update preserves earlier versions and predictions.
- Human/live testing can be added after implementation completion, including failure and untested outcomes.
- Both plugin packages contain the needed runtime resources and expose the new role after installation/reload.

## Checks performed for this assessment

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1 -ValidateOnly`: exit 0, structure validated.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\antigravity\install.ps1 -ValidateOnly`: exit 0, strict validation passed; an advisory missing-logo notice was emitted.
- `python .\codex\scripts\validate.py`: could not start because the `python` command resolves to an unavailable Windows application alias. Retried with the installed Python launcher.
- `py -3 .\codex\scripts\validate.py`: exit 1 at the planner model assertion. The validator expects `gpt-6.1-sol/medium`; `codex/agents/planner.toml:3` configures `gpt-6-luna/high`. Later assertions were not reached. Resolve intended model/profile policy before relying on this check for the extension.
- Graph tools used: `get_minimal_context_tool`, `build_or_update_graph_tool`, `get_impact_radius_tool`, `query_graph_tool`, `get_docs_section_tool`. The graph was initially stale and was refreshed. The planner TOML query confirmed it is not indexed; graph impact results do not capture the workflow dependencies encoded in Markdown/TOML. Source inspection and text searches established those dependencies.

## Follow-up: requested Antigravity models and loader limitation

The user requested replacing Flash subagents with Hydrogen Medium and the plan critic with Argon. The installed `agy models` command returned `gemini-4-hydrogen-medium` and `gemini-4-argon-high`; the [official CLI reference](https://antigravity.google/docs/cli/headless/#select-a-model-effort-or-agent) also lists both slugs.

Writing those slugs into the five agent definitions failed strict validation: `agy` 1.5.8 reported `Invalid model tier` for each and skipped all five agents. The [plugin schema](https://antigravity.google/docs/build-plugins/#subagents) documents tier names (`inherit`, `flash_lite`, `flash`, `pro`), not arbitrary model slugs, for this field. CLI session model selection and custom-subagent frontmatter have different contracts.

To retain a loadable plugin, `implementer`, `researcher`, `code-reviewer` and `verifier` retain `model: flash`; `plan-critic` now uses `model: pro`. These tiers do not establish exact Hydrogen Medium or Argon High pins. The requested mapping and limitation are documented in the Antigravity README. Exact subagent pinning requires loader support or a separately designed dispatch path supporting explicit model selection; no unverified override fields or dispatch rewrite were added. Planner, orchestrator and DevOps model settings retain their existing configuration. The critic's responsibilities remain unchanged.

Follow-up validation: strict validation with literal model slugs exited 1 with five invalid-tier errors. After restoring supported tiers, `powershell -NoProfile -ExecutionPolicy Bypass -File .\antigravity\install.ps1 -ValidateOnly` exited 0 and discovered all eight agents. `git diff --check` also passed. Live subagent model selection has not been tested.

The estimator now has a role-definition prototype and a saved prompt trial. The logger and parent workflow integration remain unimplemented; installed plugin configuration and permissions were not changed. Agent-time accuracy and calibration quality remain untested. The central delivery risk is incomplete or misleading outcome measurement, followed by policy/packaging drift between the two platform bundles.
