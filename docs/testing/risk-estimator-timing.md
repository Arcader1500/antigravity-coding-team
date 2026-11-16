# Risk estimator timing and prompt-test protocol

This document describes how to collect and compare task-level timing evidence for the risk estimator. The SQLite records preserve observations; they do not calibrate forecasts or alter the rubric. Predictions are heuristic unless independently established otherwise.

## Capture one attempt at a time

Use the active run's `run_id` and the planned task ID. Before dispatching each attempt, append an `event` record with a stable `record_id`, `event_type: "attempt_start"`, attempt number, worker/model when known, UTC `start_time`, `end_time: null`, `elapsed_seconds: null`, status `running`, provenance `controller_system_clock`, and `active_seconds: null`. Record that event before dispatch.

When that worker's result arrives, append a separate `attempt_end` event immediately, even if other work in its wave is still running. Keep the same run/task/attempt and record ID convention; capture the result time, computed dispatch-to-result seconds, reported status, model and any known wait intervals. The dispatch-to-result duration includes tool/test time, queueing and result delivery. It is an elapsed wall measurement, not active model reasoning time. Keep `active_seconds` null unless an observed worker report provides a defensible value and provenance. Never reconstruct it from final prose.

Retries and fixes are new attempt pairs with incremented attempt numbers and distinct stable record IDs. Preserve failed results. For a known human pause or external wait, record the observed interval separately in `known_waits`; do not subtract it from dispatch-to-result elapsed. If a result/completion event is missing, leave the start open with null end and duration. Missing is not zero and is not success. Human/live acceptance is recorded separately; keep it `pending`, `unavailable`, or `unknown` until evidence supports another value.

Do not wait for every worker in a wave before recording an earlier result. Two result events may have different timestamps in one wave. Existing writer barriers and review order still govern file access; timing writes do not authorize inspection or commits.

## Bootstrap and SQLite replay

Until the helper is available, append JSONL lines to the project-local `.coding-team/task-timings.jsonl`. Preserve every complete line and record its system-clock timestamp at dispatch/result time. The bootstrap stream starts with its run-creation operation and then ordered record operations. Retain legacy/raw start entries as supplied; do not replace an open attempt with a fabricated completion.

Once `risk_store.py` is available, replay the retained bootstrap with `import-jsonl <db-path> <jsonl-path>`. The helper uses stable record IDs for idempotent retries and reports malformed lines rather than silently dropping them. Keep the bootstrap file after replay and continue through `record <db-path>` for new events. On helper failure, retain the JSONL fallback and report the error; do not say SQLite persistence succeeded. Resolve the database under the target repository's `.coding-team` directory, never under an installed plugin cache or the graph database.

The T2 check replayed four bootstrap lines into a temporary database: it reported the raw legacy `run_start` on line 1 and stored three events in order. This was a temporary-database test, not a replay into live project state; the current JSONL has since gained more controller events.

## Compare forecast and observations carefully

For a completed run, show each task attempt separately, including retries; compare task attempt elapsed sums with the original task forecast, and compare whole-run elapsed from the first remaining-task dispatch to the final required result. Do not sum concurrent tasks and call that whole-run elapsed. Time final independent review and final verification as separate stages. Report known waits and human effort separately; retain unknown values as null. A task sum can exceed its wave's elapsed interval because tasks overlap.

The T6 fixture uses known values to guard this distinction: T3 and T4 task work is 8 and 7 likely agent minutes, with a 2-minute shared review gate, so likely agent work is 17 minutes. The fixture's likely agent elapsed is 10 minutes. Its observed attempt intervals are 300 and 360 seconds, overlapping from 07:00:30Z to 07:05:00Z; their 660-second sum is not the wave's 390-second elapsed span.

The current captured implementation run illustrates the same rule. T3 and T4 were dispatched about 0.18 seconds apart; T3 returned at 07:23:59.799435Z and T4 at 07:26:45.894351Z. Their measured durations sum to 1,526.485 seconds, while the interval from the first dispatch to the last result is 846.380 seconds. The T3 result was recorded when it arrived, before the T4 result. The T6 controller record currently has a start at 07:38:00.370545Z and no end or elapsed value. Therefore the run has no final whole-run duration yet; do not report the T6 attempt as zero or claim final completion time.

### Historical estimate comparison for this implementation

These estimates are the saved trial's likely per-task agent minutes, not measurements. Actual values are controller dispatch-to-result elapsed from `.coding-team/controller-state.json`; they are not active effort.

| Task | Saved trial likely (agent min) | Observed controller elapsed | Status at capture |
|---|---:|---:|---|
| T2 | 90 | 13m 30.237s | DONE |
| T3 | 40 | 11m 20.285s | DONE |
| T4 | 45 | 14m 06.200s | DONE |
| T5 | 45 | 11m 03.634s | DONE |
| T6 | 45 | null | Open; end event not yet recorded |

Do not interpret these as a forecast accuracy result. The saved trial was bound to plan hash `c53fb47e28bebe12b9272ef426239b20009740acb32bc287d82b2a659bc6dc2f`, spec hash `d082d10f4e07e4378023380499608ef0a4a625dcb0d2abc931f2ce77654f1148`, and role hash `8a123b93e8c4a6628318b05d087a33c7182eafc77d1f4ce573a692e42a10036c`. The current controller run binds plan hash `cb697ff297f5ae19082b554f6503012631e14b558ab3baa29a807396608f68f8`, spec hash `eb2ad6280479729110644f34ac8edb74a43d35bccf05f478cbc309f5d5b93745`, and role hash `aab26455e5a55f7eaecbd91581b4888f7d3b58baf0b7488fa2823e6f53a7d1d1`. The current run also records the implementer as `gpt-6-luna/high`; the trial request forecast `gpt-6-luna/medium`. Artifact and model context differ, and measured wall time includes tool execution and result delivery. The trial's `310` likely agent-work minutes and `270` likely elapsed minutes cover T2-T6 plus shared gates; the present run is open and independent review/final verification remain future results. No active-time or calibration conclusion follows from this comparison.

## Standalone role-prompt test

To test the prompt itself without claiming native role registration or timing calibration:

1. Record the evaluator model and reasoning effort separately from all target execution-role model/reasoning settings and worker capacity. State whether the evaluator is a generic worker bootstrap or the registered role in a fresh session.
2. Record the exact spec, plan and role artifact paths and SHA-256 hashes used for the call. Include the critic status/findings and distinguish an old trial from the current plan revision.
3. Save the complete request envelope and raw response with stable consultation/run IDs, question IDs, supplied answers/unknowns, and any continuation. Redact credentials and secret-bearing logs while retaining evidence references. Record `storage_status` honestly.
4. Capture UTC system-clock time immediately before and after the evaluator call and report its wall duration with provenance such as `evaluator_call_wall_clock`. This is prompt-call elapsed time; do not label it implementation effort or model reasoning time.
5. Validate only the response contract and its arithmetic/ranges. The procedure does not prove fresh-session discovery, native registration, forecast calibration, installed parity, or live acceptance.

The saved 2026-11-16 trial is historical: it records evaluator `gpt-6.1-sol/medium`, `storage_status: not_persisted`, and the then-supplied artifact identities. Its response is not a current-plan estimate or an implementation timing record. Rubric review or changes remain manual at the user's discretion; this protocol creates no schedule, run-count trigger, reminder, or automatic rubric update.
