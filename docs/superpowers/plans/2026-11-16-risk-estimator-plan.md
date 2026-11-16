# Risk estimator implementation plan

Date: 2026-11-16
Design basis: docs/audits/risk-estimator-assessment-2026-11-16.md, accepted as the planning basis by the user's request to write this plan.
Source baseline: 869d36d5db7799065d33ea23312b265fef80349c, branch dev.
Authorization for this turn: write the plan, implement the estimator definitions first and test their instructions on GPT-6.1 Sol / medium. Tasks T2-T6 are future implementation work, not authorized for automatic execution by this test request.

## Goal and acceptance

Add one advisory risk-estimator consulted by planner/orchestrator, initially using a manual rubric. Predict AI-agent implementation, debugging, self-review, checks and shared review/verifier time. Retain original predictions and observations. Rubric review or calibration is entirely manual and outside this implementation plan, with no run-count trigger, deadline, reminder or scheduled reassessment. Implementers retain their existing reporting and no-delegation contracts.

The critic remains responsible for plan correctness. The estimator does not add approval gates or replace review/final verification. No automatic learning, statistical fitting, dashboards, new review roles or always-on service.

The prototype runs on GPT-6.1 Sol / medium as explicitly requested. Forecast target models must be supplied separately from the estimator's own model: use current Codex role settings for the initial trial. Desired Antigravity lightweight target is Hydrogen Medium; its loader currently accepts only tiers, so record exact pinning as unsupported rather than claiming flash guarantees Hydrogen.

## Grounded repository constraints

- codex/agents/planner.toml:7 restricts delegated roles, :10 restricts writes, :35 invokes the critic and :41 defines the manual handoff. Consultation and narrowly allowed state logging must be added there.
- codex/agents/orchestrator.toml:10 defines dispatch/review/verification order; :12 prohibits automatic per-wave gates; :20 requires resolving NEEDS_CONTEXT/BLOCKED causes.
- codex/agents/implementer.toml:11 forbids delegation; :17 already defines usable status/evidence reports. Preserve this contract.
- codex/scripts/validate.ps1:18 counts eight agents and :23 enumerates roles. T1 must extend these so adding an agent does not break source validation.
- codex/scripts/validate.py:8 hardcodes role/model expectations, installed parity and later fixed counts. Existing planner expectations disagree with the source and installer profile; T5 separates those policies without changing the chosen models.
- codex/install.ps1:85 already copies every agent TOML. The profile construction at :94 creates planner/orchestrator profiles independently. No ninth-agent copy step is needed.
- antigravity/install.ps1 validates then installs the whole plugin; antigravity/install.sh does the same. A bundled scripts directory can travel with the plugin.
- Both packages maintain their own files. A helper copied to only one package is incomplete.
- The graph covers executable files, not the full Markdown/TOML workflow. get_minimal_context_tool was used; source reads and rg established the workflow dependencies. New paths below are explicitly new contracts in verified existing directories, not claims about existing symbols.

Python 3.11+ is already required by the deeper Codex validator; the new logger makes that a production prerequisite that must be documented and checked. Use the standard library (sqlite3, json, argparse, datetime, hashlib, pathlib, unittest), with no new package dependency.

## Architecture and contracts

### Agent and consultation

T1 creates self-contained, equivalent instructions in the two native role formats. The prototype's JSON response contract includes identity/revision, provisional/critic status, questions, per-task ratings and phase scenarios, shared gates, work/elapsed totals, evidence-backed risks, unknowns and historical-observation provenance. It contains no review schedule. It edits nothing. Parent agents validate and store responses through the later helper.

Questions carry stable IDs, forecast impact and requested evidence. Parents answer with evidence or an explicit unknown. Default maximum: three questions per reply and two interview rounds, then a provisional assessment with unknowns. Earlier user decisions are evidence, not questions to ask again.

### Storage and measurement

The logger code ships with each installed plugin; its mutable database is project-local at .coding-team/risk.sqlite3, outside plugin caches and separate from graph.db. Resolve that state path against the target repository named in the handoff, never the installed script directory or another checkout. There is no global database or automatic cross-project history. A run is one execution of an approved plan; tasks, retries, later live/human acceptance and consultations belong to that run. Use opaque nonempty IDs and UTC timestamps with explicit provenance. Exclude local database/journals/raw state from Git.

Use two SQLite tables: runs for artifact/execution identity, and append-only records for consultation, prediction, incident, event and outcome kinds. Index run/kind/task identifiers. JSON payloads retain the structured fields for each kind. Enforce run relationships and unique record IDs. Predictions/revisions and outcomes append new records instead of overwriting their predecessors.

New helper signatures in codex/scripts/risk_store.py:
- create_run(db_path: Path, run: dict) -> dict: validate and insert a run identity before linked records. Require run_id, run_kind (implementation or prompt_trial), created_at UTC, repo_root, plan/spec artifact identities, explicit critic status/evidence (unknown permitted), execution models/reasoning/worker capacity, and rubric/plugin versions. Optional previous_run_id links a revised plan execution to an existing run in the same canonical repository root; null means no predecessor. Reject missing, cross-repository or self-referential predecessors. Identical same-ID retries return the existing identity; conflicting reuse fails without changing the original run.
- artifact_identity(path: Path) -> dict: absolute identity and SHA-256 of current file bytes; include dirty/new artifacts when supplied.
- validate_record(record: dict) -> dict: validate the schema/kind/required fields and return normalized data; reject invalid input without mutating the database.
- append_record(db_path: Path, record: dict) -> dict: transact one record and return its stable identity; identical retries are idempotent, conflicting reuse is an error.
- read_run(db_path: Path, run_id: str) -> dict: return run identity, original/revised predictions, linked incidents, events and outcomes.
- main(argv: list[str] | None = None) -> int: JSON input/output CLI with create-run, record and show operations, standard help and nonzero failure exits.

The helper owns SQL/schema initialization. Agents never synthesize SQL. First implementation supports one active parent writer per run, plus transactional protection and idempotency for resumed work. Parent state-write permission is narrow; it does not grant application edits or extra sandbox access.

Observation fields distinguish observed agent start/result, controller dispatch/result elapsed, worker-reported phases, inferred classification, human effort and external/queue wait intervals. Unknown values remain null. Automated checks passing is distinct from human/live acceptance; interrupted, blocked, abandoned and untested outcomes remain represented.

### Actual task timing, including bootstrap

The orchestrator records actual system-clock times from the first remaining task, including implementation of the logger itself. A forecast is never used as a measured duration.

- Before dispatching each task attempt, append its dispatch event; on that individual completion message, append the result event immediately. Do not wait for the entire wave to finish before timestamping an earlier result. This only logs state; existing barriers still govern application-file inspection and commits.
- Use run_id, task_id, attempt, agent_id when available, model/reasoning, UTC started_at/finished_at, elapsed_seconds, status, timing_basis and stable record_id. Start records have null completion/duration. Compute completion duration from observed timestamps. Failed attempts and fixes get separate records; never overwrite the first attempt.
- The default timing_basis is controller_dispatch_to_result: observed wall time including tool/test execution, queueing and result delivery. If workers report first/last system-clock timestamps, retain them separately with worker_reported provenance. Neither measure is represented as precise internal model reasoning time. Record identifiable human pauses/external waits separately; unknown active/debugging phase durations remain null.
- Before the SQLite helper exists, use append-only .coding-team/task-timings.jsonl. Each line wraps an operation (create-run or record) and its payload matching the helper contracts. The first line creates the run identity; following lines contain timing events. The controller adds .coding-team/ to the target repository ignore rules as T2 workspace preparation before logging.
- Once T2's helper is checked and ready, replay complete JSONL lines in order through create_run/append_record. Preserve the bootstrap file and use stable IDs for idempotent retries; report malformed/truncated lines explicitly without silently dropping records. Continue recording through the helper, with JSONL as the reported fallback on a logging failure. No new daemon or installed global state is needed.
- Time final independent review and verification as separate stages. Report per-task attempt sums, estimates versus measured task durations, and whole-run wall time from the first dispatch to the final required result. Parallel task durations overlap; do not sum them into claimed whole-run elapsed time. Missing end events are open/unknown, not zero-duration success.

## Execution Waves

| Wave | Tasks | Dependencies | Parallel ownership |
|---|---|---|---|
| 1 | T1: estimator prototype | None | Role definitions and role-count validation only |
| 2 | T2: validated SQLite logger | T1 | Canonical helper, Antigravity packaged copy and tests |
| 3 | T3: planning consultation; T4: execution/reassessment | T2 | Disjoint planner and orchestrator instruction files |
| 4 | T5: package parity and configuration validation | T3, T4 | Validate existing helper copies; package validation/docs/ignore |
| 5 | T6: integration and timing acceptance | T5 | Integration tests and timing protocol |

The user's test executes T1 only, followed by a read-only forecast of remaining T2-T6. Do not count already completed T1 work as future agent effort. Later implementation follows these waves and the existing review/fix loop, then final verifier.

## T1: Create estimator definitions and run the requested prototype

**Wave:** 1
**Depends on:** None
**Files Touched:**
- Create codex/agents/risk-estimator.toml.
- Create antigravity/agents/risk-estimator.md.
- Modify codex/scripts/validate.ps1.
- Modify codex/scripts/validate.py only to register the new role/model and role-count report; preserve the pre-existing planner/profile mismatch for T5.
- Create docs/audits/risk-estimator-trial-2026-11-16-request.json and docs/audits/risk-estimator-trial-2026-11-16-output.json after plan critique. Capture the request and returned output without claiming SQLite persistence.

**Contracts and acceptance criteria:**
- The shared role instructions encode the four-level responsibility boundary, ordinal rubric, agent-time accounting, parent interview protocol, baseline/revision preservation and incident attribution. They do not schedule or implement rubric review.
- Codex prototype model is gpt-6.1-sol, medium. Antigravity uses its loadable flash tier; desired Hydrogen Medium remains documented as a loader limitation.
- Read-only behavior is explicit, including no database writes and no delegation; agent instructions do not claim an enforced sandbox.
- New role discovery in a fresh session requires installation/reload. This current-session trial may explicitly bootstrap a generic worker with the saved role instructions and the requested Sol/medium settings; disclose that this tests the role prompt, not hot registration of agent_type=risk-estimator.
- The live trial returns a forecast for T2-T6, questions/unknowns where material, and no fabricated critic/history/outcome evidence.
- Capture any consultation continuation and raw output revisions if the first response requests evidence.

**Risks:** Arithmetic mistakes, conflating the evaluator's model with execution models, or treating a prompt test as an installed-role test.

**Task checks:**
- Parse the Codex file with tomllib; verify the requested model/effort and compare its instruction body with the Antigravity Markdown body.
- Run powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1 -ValidateOnly.
- Run powershell -NoProfile -ExecutionPolicy Bypass -File .\antigravity\install.ps1 -ValidateOnly.
- Validate the returned JSON: exact requested task coverage, nonnegative ordered scenarios, phase/task/work sums, wave/capacity-aware elapsed time, correct revision/baseline IDs and not_persisted status.
- Do not add unit tests that only assert prompt wording.

## T2: Implement validated, append-only SQLite records

**Wave:** 2
**Depends on:** T1
**Files Touched:**
- Create codex/scripts/risk_store.py.
- Create antigravity/scripts/risk_store.py as its packaged copy before Antigravity consumers are changed.
- Create codex/tests/test_risk_store.py.
- Modify .gitignore as controller-owned T2 workspace preparation before the first timing event.

**Contracts and acceptance criteria:**
- Implement the six new signatures above and schema version 1. Use parameterized SQL, transactions and explicit errors. Keep the Antigravity helper byte-identical and runnable from its installed package root.
- create_run precedes all linked appends. Test required run fields, valid unknown critic evidence, identical run retries, conflicting same-ID runs and append-before-run rejection. Test a valid same-repository previous_run_id link, plus missing, cross-repository and self-link rejection; compare canonical absolute repository roots. Do not silently upsert changed artifact identities into an existing run.
- Runs bind repo, plan/spec SHA-256, critic verdict/evidence identity, execution models/reasoning and rubric/plugin versions. A missing critic verdict remains explicitly unknown.
- Consultation records retain request/question/answer IDs and evidence. Prediction records retain all scenario fields from the response contract, revision and previous revision.
- Validate scenario ordering, sums, task references, finite numeric values, identity/timestamp types and required kind-specific fields. Reject bool as a duration, NaN/infinity, negative values, conflicting IDs and broken revision links. Preserve explicit nulls.
- Duplicate identical records succeed without another row; conflicting same-ID payloads fail. A failed insert rolls back.
- Incidents retain symptoms, root-cause hypothesis/status, failed attempts and related incident IDs within the same run; unknown causes are allowed. A confirmed cause requires evidence.
- Outcome records permit later human/live acceptance to append to an implementation-complete run, preserving earlier failed/unknown outcomes.
- Helper failures produce a nonzero exit and a bounded actionable error without falsely reporting persistence or leaking raw sensitive evidence.
- Preserve actual T2 dispatch/result times through the bootstrap JSONL path described above. Check ordered create-run/record replay, idempotent re-ingestion and explicit malformed-line reporting; the logger's own development time must not be lost merely because SQLite was unavailable at task start.

**Risks:** Lost baselines, fabricated active-time measurements, stale artifact associations and duplicate records after session resume.

**Task checks:**
- Add focused unittest cases first; run py -3 -m unittest discover -s codex/tests -p test_risk_store.py and observe failing behavior before implementing.
- Cover temporary real SQLite files, identical/conflicting retries, transactions, missing run/revision IDs, malformed records, null-vs-zero timing, cascading incidents and delayed human acceptance.
- Rerun the focused command until passing; exercise py -3 codex/scripts/risk_store.py --help.
- Check helper byte parity and run py -3 antigravity/scripts/risk_store.py --help before consumers are dispatched.
- Avoid writing tests against installed user state or the graph database.

## T3: Add the planner consultation and durable handoff

**Wave:** 3
**Depends on:** T2
**Files Touched:**
- Modify codex/agents/planner.toml.
- Modify codex/skills/team-plan/SKILL.md.
- Modify codex/skills/writing-plans/SKILL.md.
- Modify antigravity/agents/planner.md.
- Modify antigravity/skills/writing-plans/SKILL.md.
- Modify antigravity/rules/AGENTS.md.

**Contracts and acceptance criteria:**
- Add risk-estimator to planner delegation rules; consult after critic READY, or provisionally earlier for a specific material uncertainty.
- Supply the request envelope, artifact identities and available critic output. Preserve critic findings as a record; do not invent a past review.
- Answer targeted questions using supplied decisions/local evidence or unknown; preserve IDs and bound the interview.
- Permit only designated state writes through the helper in addition to existing spec/plan edits. No new application-code permission.
- Persist the baseline prediction before handoff. Include run ID, state path, artifact identities, latest prediction revision and unresolved risks in the existing handoff.
- On persistence failure, surface it and retain the actual unpersisted request/result in docs/superpowers/plans/<plan-stem>.risk-handoff.json beside the current plan. The updated planner instructions narrowly permit this fallback file and its same-directory temporary file, alongside the existing allowed paths. Write a complete JSON document through a temporary file and atomic replacement; an existing fallback for a different run is a conflict, never an overwrite. Include run/consultation IDs, artifact hashes, original request/result, storage_status=not_persisted and the bounded logging error. Store redacted evidence references, not credentials or raw secret-bearing logs. Retry ingestion through the helper's idempotent contracts. Do not claim the durable-history feature succeeded, and do not append fallback data to the critic-approved plan or change its hash.
- Retain existing spec approval/manual execution handoff and critic responsibilities. Additional risk warnings do not require another user approval question.

**Risks:** Conflicting legacy instructions, lost critic context between sessions, and interviewing about decisions already supplied.

**Task checks:**
- Parse role/frontmatter using existing validators; inspect every planning entry point for the same sequence.
- Tabletop a READY plan with an uncertain external permission: retain READY, log provisional estimate, carry the uncertainty through handoff.
- Tabletop missing Python/read-only state location: report logging failure and preserve an unpersisted result, without claiming successful durable logging.
- Use applicable static checks, not artificial code unit tests for prose.

## T4: Add controller-owned execution logging and reassessment

**Wave:** 3
**Depends on:** T2
**Files Touched:**
- Modify codex/agents/orchestrator.toml.
- Modify codex/skills/team-run/SKILL.md.
- Modify codex/skills/subagent-driven-development/SKILL.md.
- Modify codex/skills/executing-plans/SKILL.md.
- Modify antigravity/agents/orchestrator.md.
- Modify antigravity/skills/subagent-driven-development/SKILL.md.
- Modify antigravity/skills/executing-plans/SKILL.md.

**Contracts and acceptance criteria:**
- Resolve a supplied run ID from the persisted handoff. Reject stale plan/spec associations; after the existing planner/critic process establishes a revised plan, create a new run linked to the previous run_id. Environment changes may append a revised prediction with new context to the same run. Preserve earlier identities and predictions.
- Record controller dispatch/result timestamps and provenance, existing worker statuses/checks, review/verifier results, incidents and final outcome. Task retries remain in the same run.
- Follow the actual-task-timing contract above: timestamp each attempt's individual dispatch/result using the system clock, preserve failed/retried/open attempts, distinguish controller elapsed from worker-reported timing, and time final review/verification separately. Finish with estimates versus actuals and total run wall time; never infer missing phase durations from the forecast.
- Consult on repeated failed fixes, emerging shared-cause symptoms or material integration changes. Routine task completion logs an event without another model invocation.
- The controller gathers answers; implementers retain their current reporting/no-delegation contract. Respect active-writer barriers and file ownership.
- Reassessment references baseline/current revision and separately reports observed time and remaining predicted time.
- Failed/blocked/interrupted runs remain usable observations. Human/live testing can remain pending until a later outcome record.
- Keep tasks/waves -> full-change reviewer/fixes -> final verifier. Add no automatic per-wave or risk-based approval gates.
- Use native waits in Codex and Antigravity's asynchronous completion behavior as already documented.

**Risks:** Treating dispatch wall time as active effort, starting readers during worker writes and repeated symptom fixes being counted as unrelated root causes.

**Task checks:**
- Run applicable plugin configuration validation after edits.
- Tabletop one repeated failure and two symptoms sharing an unconfirmed cause; request targeted evidence, retain uncertainty, append revision rather than overwrite.
- Tabletop a fresh-session resume and a changed plan fingerprint.
- Confirm that no implementer instruction or reviewer/verifier role change is needed.

## T5: Package both runtimes and align validation/documentation

**Wave:** 4
**Depends on:** T3, T4
**Files Touched:**
- Create codex/tests/test_risk_packaging.py.
- Modify codex/scripts/validate.ps1.
- Modify codex/scripts/validate.py.
- Modify README.md, codex/README.md and antigravity/README.md.

**Contracts and acceptance criteria:**
- Canonical development helper is codex/scripts/risk_store.py; assert byte parity with the independently installed Antigravity copy. Agent instruction bodies also remain semantically identical across formats.
- Validate nine role definitions and each expected source model; keep planner source expectations separate from the Sol/medium launch-profile expectation. Preserve the user's actual chosen model settings.
- Keep installed-file/cache parity checks explicit and separate from source-only validation. An uninstalled prototype must not be reported as installed parity passing.
- Verify needed runtime scripts are included by each existing installer. Do not install or update global configuration merely to make source validation pass.
- Ignore project-local .coding-team state and SQLite journal/WAL files by directory; keep code/test fixtures tracked.
- Document Python 3.11+, request/result/handoff flow, actual timing/bootstrap provenance and Antigravity's exact-model pin limitation. Explain that rubric review is outside the implemented workflow and occurs only at the user's discretion.
- Do not add another skill/agent-count change unnecessarily; use parent role instructions and existing entry skills.

**Risks:** Independent bundle drift, stale installed agents and masking the existing planner source/profile mismatch.

**Task checks:**
- Write test_risk_packaging.py first and run py -3 -m unittest discover -s codex/tests -p test_risk_packaging.py before/after the copy/parity implementation.
- Validate both package roots using their existing ValidateOnly commands.
- Run source-only parsing/count/parity checks. Run installed-parity validation only after an explicitly authorized installation; report an unrun installed check as a gap.
- Confirm no credential overrides or unrelated installer behavior changed.

## T6: Exercise consultation, resume and observed timing

**Wave:** 5
**Depends on:** T5
**Files Touched:**
- Create codex/tests/test_risk_integration.py.
- Create docs/testing/risk-estimator-timing.md.

**Contracts and acceptance criteria:**
- Drive a temporary run through initial questions/answers, immutable baseline, task events, a shared-cause incident, revised forecast, controller resume and later human/live outcome.
- Include a failed/abandoned run, untested acceptance, null timing, stale artifact identity and duplicate event retry. Never turn unavailable observations into successful outcomes.
- Demonstrate parallel effort versus elapsed accounting with known fixture inputs. Tests check data invariants; model estimates themselves are not deterministic assertions.
- Document actual per-task timing capture and bootstrap replay, comparison with original estimates, and the distinction between per-attempt sums and overlapping whole-run elapsed time. Include missing completion events, retries, human pauses and task completion messages arriving at different times in the same wave. Do not build or schedule any manual review/calibration process.
- Provide a standalone role-prompt test procedure that records evaluator model, target execution models, artifact hashes, raw request/response and elapsed test-call provenance. It does not assert native registration or calibrated timing quality.

**Risks:** A passing fixture pipeline being mistaken for a calibrated estimator or live deployment validation.

**Task checks:**
- Add integration unittest cases first and observe failures; implement required fixtures and rerun py -3 -m unittest discover -s codex/tests -p test_risk_integration.py.
- Verify timing fixtures and the capture protocol against explicit system-clock records. Treat the saved prototype request/output as historical estimates, not runtime observations or the current plan revision.
- Use no cloud credentials, live deployment changes or global installed-state mutation.

## Final review and verification after future implementation

After T2-T6, code-reviewer reviews the full diff against this plan and design basis. Implementer fixes required findings; reviewer rechecks until approved. Only then verifier runs:
- py -3 -m unittest discover -s codex/tests -p test_risk_*.py
- powershell -NoProfile -ExecutionPolicy Bypass -File .\codex\install.ps1 -ValidateOnly
- powershell -NoProfile -ExecutionPolicy Bypass -File .\antigravity\install.ps1 -ValidateOnly
- git diff --check
- applicable source role-model, prompt/helper parity and packaged-resource checks from T5.

Verifier failures return through fixes and reviewer approval before re-verification. Do not claim installed parity, live acceptance, Hydrogen/Argon pinning or calibrated duration accuracy from these checks. Only the orchestrator commits when authorized; no push/merge/install is authorized by this prototype test.

## Trial assumptions supplied to the estimator

Forecast only remaining T2-T6. Use Codex current source-role models for the execution team, including gpt-6-luna/medium implementers and gpt-6.1-sol/medium reviewer, with two implementation worker slots when tasks have disjoint ownership. This is a local Windows PowerShell/Python project; no live cloud provisioning is required. No historical calibration dataset exists. Parent will supply actual artifact hashes and critic findings/status in the captured request.

The test must surface unknowns instead of inventing precision. Estimate the whole requested remaining scope, including shared final review and verification; do not implement it.
