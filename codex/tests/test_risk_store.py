import hashlib
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
import uuid

from codex.scripts import risk_store


def run(run_id="run-1", repo_root=".", previous_run_id=None):
    return {
        "run_id": run_id,
        "run_kind": "implementation",
        "created_at": "2026-11-16T07:00:00Z",
        "repo_root": repo_root,
        "plan": {"path": "plan.md", "sha256": "a" * 64},
        "spec": {"path": "spec.md", "sha256": "b" * 64},
        "critic": {"status": "unknown", "evidence": None},
        "execution": {"models": {"implementer": "gpt-6-luna/medium"}, "worker_capacity": 2},
        "rubric_version": "1",
        "plugin_version": "1.0.0",
        "previous_run_id": previous_run_id,
    }


def record(kind="event", record_id="event-1", payload=None, task_id="T2"):
    return {
        "schema_version": 1,
        "record_id": record_id,
        "run_id": "run-1",
        "kind": kind,
        "task_id": task_id,
        "created_at": "2026-11-16T07:01:00Z",
        "payload": payload if payload is not None else {
            "event_type": "attempt_start", "task_id": task_id, "attempt": 1,
            "model": "gpt-6-luna/medium", "start_time": "2026-11-16T07:00:59Z",
            "end_time": None, "elapsed_seconds": None, "status": "running",
            "provenance": "controller_system_clock", "known_waits": [], "active_seconds": None,
        },
    }


def prediction():
    return {
        "schema_version": 1, "rubric_version": "1", "consultation_id": "consult-1", "run_id": "run-1",
        "revision": 0, "previous_revision": None, "mode": "estimate", "status": "assessed",
        "provisional": True, "critic_status": "unknown", "storage_status": "not_persisted",
        "basis": {
            "artifacts": [
                {"path": "plan.md", "sha256": "a" * 64},
                {"path": "spec.md", "sha256": "b" * 64},
            ],
            "fingerprint_provenance": "fixture", "evidence_references": [], "platform": "test",
            "execution_models": {"implementer": {"model": "gpt-6-luna", "reasoning_effort": "medium"}},
            "evaluator": {"model": "gpt-6.1-sol", "reasoning_effort": "medium"},
            "available_worker_capacity": 2, "excluded_task_ids": [], "scope": "T2",
        },
        "questions": [],
        "tasks": [{
            "task_id": "T2", "agentic_complexity": "medium", "integration_uncertainty": "low",
            "defect_exposure": "medium", "debugging_cost": "low", "rationale": "fixture",
            "phase_minutes": {
                "implementation": {"optimistic": 2, "likely": 3, "conservative": 4},
                "debugging": {"optimistic": 1, "likely": 2, "conservative": 3},
                "self_review": {"optimistic": 1, "likely": 1, "conservative": 1},
                "task_checks": {"optimistic": 1, "likely": 2, "conservative": 2},
            },
            "agent_minutes": {"optimistic": 5, "likely": 8, "conservative": 10}, "risk_ids": [],
        }],
        "shared_gates": {"independent_review": {"optimistic": 1, "likely": 1, "conservative": 2},
                         "final_verification": {"optimistic": 1, "likely": 1, "conservative": 2},
                         "assumptions": []},
        "totals": {
            "agent_work_minutes": {"optimistic": 7, "likely": 10, "conservative": 14},
            "agent_elapsed_minutes": {"optimistic": 6, "likely": 9, "conservative": 13},
            "human_minutes": None, "external_wait_minutes": None,
            "scheduling_assumptions": ["single task"],
        },
        "risks": [], "unknowns": [], "revision_reason": None,
        "calibration": {"heuristic": True, "historical_run_count": 0, "automatic_updates": False},
    }


def consultation(consultation_id="consult-1", revision=0, round_number=1, questions=None, answers=None):
    return {
        "consultation_id": consultation_id, "run_id": "run-1", "revision": revision,
        "round": round_number, "mode": "estimate" if revision == 0 else "reassess",
        "request": {"run_id": "run-1", "revision": revision}, "response": {"status": "assessed"},
        "questions": questions or [], "answers": answers or [],
    }


class RiskStoreTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent / f".risk-store-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.db = self.root / "risk.sqlite3"

    def tearDown(self):
        for path in self.root.iterdir():
            path.unlink()
        self.root.rmdir()

    def create(self, data=None):
        return risk_store.create_run(self.db, data or run(repo_root=str(self.root)))

    def test_run_validation_unknown_critic_and_idempotent_conflict(self):
        bad = run(repo_root=str(self.root))
        del bad["execution"]
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.create_run(self.db, bad)
        first = self.create()
        self.assertEqual(first["critic"]["status"], "unknown")
        self.assertEqual(first, self.create())
        changed = run(repo_root=str(self.root))
        changed["plan"]["sha256"] = "c" * 64
        with self.assertRaises(risk_store.RiskStoreError):
            self.create(changed)

    def test_previous_run_is_same_repository_and_not_self(self):
        self.create()
        linked = run("run-2", str(self.root / "."), "run-1")
        self.assertEqual("run-1", risk_store.create_run(self.db, linked)["previous_run_id"])
        for data in (run("missing-prev", str(self.root), "no-such-run"),
                     run("cross-prev", str(self.root / "elsewhere"), "run-1"),
                     run("run-1", str(self.root), "run-1")):
            with self.subTest(data=data["run_id"]), self.assertRaises(risk_store.RiskStoreError):
                risk_store.create_run(self.db, data)

    def test_append_retries_conflict_and_missing_run(self):
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record())
        self.create()
        item = record()
        first = risk_store.append_record(self.db, item)
        self.assertEqual(first, risk_store.append_record(self.db, item))
        changed = record(payload={**item["payload"], "status": "failed"})
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, changed)
        self.assertEqual(1, len(risk_store.read_run(self.db, "run-1")["events"]))

    def test_prediction_scenarios_sums_and_revision_links(self):
        self.create()
        p0 = prediction()
        risk_store.append_record(self.db, record("consultation", "consult-1-record", consultation(), task_id=None))
        risk_store.append_record(self.db, record("prediction", "p0", p0))
        self.assertEqual(p0, risk_store.append_record(self.db, record("prediction", "p0", p0))["payload"])
        p1 = prediction()
        p1.update(consultation_id="consult-2", revision=1, previous_revision=0, revision_reason="new evidence")
        risk_store.append_record(self.db, record("consultation", "consult-2-record",
                                                 consultation("consult-2", revision=1), task_id=None))
        risk_store.append_record(self.db, record("prediction", "p1", p1))
        invalid = prediction()
        invalid["tasks"][0]["phase_minutes"]["debugging"]["likely"] = math.inf
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(record("prediction", "bad", invalid))
        bad_order = prediction()
        bad_order["tasks"][0]["agent_minutes"]["optimistic"] = 12
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(record("prediction", "bad-order", bad_order))
        broken = prediction()
        broken.update(revision=2, previous_revision=0)
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("prediction", "broken", broken))
        wrong_sum = prediction()
        wrong_sum["totals"]["agent_work_minutes"]["likely"] += 1
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(record("prediction", "wrong-sum", wrong_sum))
        wrong_task_ref = prediction()
        wrong_task_ref["risks"] = [{"risk_id": "R1", "affected_tasks": ["T404"], "evidence": "source",
                                     "cause_status": "hypothesized", "consequences": "impact",
                                     "next_diagnostic": "inspect"}]
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(record("prediction", "wrong-task", wrong_task_ref))

    def test_event_null_timing_and_bool_duration_validation(self):
        self.create()
        event = record()
        self.assertIsNone(risk_store.append_record(self.db, event)["payload"]["elapsed_seconds"])
        zero = record("event", "zero-duration")
        zero["payload"]["event_type"] = "attempt_result"
        zero["payload"]["end_time"] = zero["payload"]["start_time"]
        zero["payload"]["elapsed_seconds"] = 0
        zero["payload"]["active_seconds"] = 0
        zero["payload"]["status"] = "DONE"
        self.assertEqual(0, risk_store.append_record(self.db, zero)["payload"]["elapsed_seconds"])
        bad = record("event", "bad")
        bad["payload"]["elapsed_seconds"] = True
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(bad)
        bad["payload"]["event_type"] = "attempt_end"
        bad["payload"]["status"] = "DONE"
        bad["payload"]["elapsed_seconds"] = 1
        bad["payload"]["end_time"] = "2026-11-16T06:59:00Z"
        with self.assertRaisesRegex(risk_store.RiskStoreError, "timestamps"):
            risk_store.validate_record(bad)
        bad["payload"]["elapsed_seconds"] = math.nan
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(bad)

    def test_attempt_event_requires_coherent_task_status_and_timing(self):
        good = record("event", "attempt-end", {
            "event_type": "attempt_end", "task_id": "T2", "attempt": 1,
            "model": "gpt-6-luna/high", "start_time": "2026-11-16T07:00:00Z",
            "end_time": "2026-11-16T07:01:00Z", "elapsed_seconds": 60,
            "active_seconds": 50, "status": "DONE_WITH_CONCERNS",
            "provenance": "controller_system_clock", "known_waits": [],
        })
        self.assertEqual("DONE_WITH_CONCERNS", risk_store.validate_record(good)["payload"]["status"])
        invalid = []
        bad = json.loads(json.dumps(good)); bad["payload"]["attempt"] = True; invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"]["elapsed_seconds"] = 999; invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"]["active_seconds"] = 1234; invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"].pop("task_id"); invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"].pop("provenance"); invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"].pop("status"); invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"]["event_type"] = "attempt_start"; invalid.append(bad)
        bad = json.loads(json.dumps(good)); bad["payload"]["task_id"] = "T3"; invalid.append(bad)
        for item in invalid:
            with self.subTest(payload=item["payload"]), self.assertRaises(risk_store.RiskStoreError):
                risk_store.validate_record(item)

    def test_non_task_stages_and_live_statuses_remain_valid(self):
        review = record("event", "review-result", {
            "event_type": "review_result", "status": "REQUEST_CHANGES",
            "provenance": "controller_system_clock", "start_time": "2026-11-16T07:00:00Z",
            "end_time": "2026-11-16T07:00:05Z", "elapsed_seconds": 5,
            "active_seconds": None, "known_waits": [],
        }, task_id=None)
        self.assertEqual("REQUEST_CHANGES", risk_store.validate_record(review)["payload"]["status"])
        reference = record("event", "historical-reference", {
            "event_type": "historical_forecast_reference", "artifact": {"path": "forecast.json"},
        }, task_id=None)
        self.assertEqual("historical_forecast_reference", risk_store.validate_record(reference)["payload"]["event_type"])

    def test_prediction_contract_and_unknown_phase_math(self):
        saved = json.loads((Path(__file__).resolve().parents[2] / "docs/audits/risk-estimator-trial-2026-11-16-output.json").read_text(encoding="utf-8"))
        envelope = {"schema_version": 1, "record_id": "saved-contract", "run_id": saved["run_id"],
                    "kind": "prediction", "task_id": None, "created_at": "2026-11-16T07:00:00Z", "payload": saved}
        self.assertEqual("assessed", risk_store.validate_record(envelope)["payload"]["status"])
        invalid = []
        bad = json.loads(json.dumps(saved)); bad["status"] = "READY"; invalid.append(bad)
        bad = json.loads(json.dumps(saved)); bad.pop("basis"); invalid.append(bad)
        bad = json.loads(json.dumps(saved)); bad["tasks"][0]["phase_minutes"].pop("debugging"); invalid.append(bad)
        bad = json.loads(json.dumps(saved))
        task = bad["tasks"][0]
        task["phase_minutes"]["debugging"] = {key: None for key in ("optimistic", "likely", "conservative")}
        for scenario in ("optimistic", "likely", "conservative"):
            task["agent_minutes"][scenario] = sum(
                phase[scenario] for phase in task["phase_minutes"].values() if phase[scenario] is not None
            )
            bad["totals"]["agent_work_minutes"][scenario] -= (
                saved["tasks"][0]["agent_minutes"][scenario] - task["agent_minutes"][scenario]
            )
        invalid.append(bad)
        for item in invalid:
            current = {**envelope, "payload": item}
            with self.subTest(status=item.get("status")), self.assertRaises(risk_store.RiskStoreError):
                risk_store.validate_record(current)

    def test_consultation_answers_reference_questions_and_prediction_links(self):
        mismatch = consultation(questions=[{"question_id": "Q1", "question": "Can access run?",
                                            "forecast_impact": "affects T2", "requested_evidence": "permission"}],
                                answers=[{"question_id": "DIFFERENT", "answer": "unknown", "evidence": None}])
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.validate_record(record("consultation", "bad-consult", mismatch, task_id=None))

        self.create()
        forecast = prediction()
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("prediction", "orphan", forecast, task_id=None))
        first_consultation = consultation()
        risk_store.append_record(self.db, record("consultation", "consult-round-1", first_consultation, task_id=None))
        risk_store.append_record(self.db, record("prediction", "baseline", forecast, task_id=None))
        second_round = consultation(round_number=2, questions=[{"question_id": "Q1", "question": "Can access run?",
                                                                 "forecast_impact": "affects T2", "requested_evidence": "permission"}],
                                    answers=[{"question_id": "Q1", "answer": "unknown", "evidence": None}])
        risk_store.append_record(self.db, record("consultation", "consult-round-2", second_round, task_id=None))
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("consultation", "duplicate-round",
                                                      second_round, task_id=None))
        second_consultation = consultation("consult-2", revision=1)
        risk_store.append_record(self.db, record("consultation", "consult-2-record",
                                                 second_consultation, task_id=None))
        revised = prediction()
        revised.update(consultation_id="consult-2", revision=1, previous_revision=0,
                       mode="reassess", revision_reason="Evidence remains unknown.")
        risk_store.append_record(self.db, record("prediction", "revision-1", revised, task_id=None))
        third_consultation = consultation("consult-3", revision=2)
        risk_store.append_record(self.db, record("consultation", "consult-3-record",
                                                 third_consultation, task_id=None))
        wrong_basis = prediction()
        wrong_basis["basis"]["artifacts"][0]["sha256"] = "c" * 64
        wrong_basis.update(consultation_id="consult-3", revision=2, previous_revision=1,
                           mode="reassess", revision_reason="Changed evidence.")
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("prediction", "stale-basis", wrong_basis, task_id=None))
        wrong_critic = prediction()
        wrong_critic.update(consultation_id="consult-3", revision=2, previous_revision=1,
                            mode="reassess", revision_reason="Changed evidence.", critic_status="READY")
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("prediction", "wrong-critic", wrong_critic, task_id=None))
        wrong_model = prediction()
        wrong_model["basis"]["execution_models"]["implementer"]["model"] = "different-model"
        wrong_model.update(consultation_id="consult-3", revision=2, previous_revision=1,
                           mode="reassess", revision_reason="Changed evidence.")
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, record("prediction", "wrong-model", wrong_model, task_id=None))

    def test_prediction_basis_requires_exact_execution_model_roles(self):
        run_data = run(repo_root=str(self.root))
        run_data["execution"]["models"]["verifier"] = "gpt-6-luna/low"
        self.create(run_data)
        risk_store.append_record(self.db, record("consultation", "role-consultation",
                                                 consultation(), task_id=None))

        missing = prediction()
        with self.assertRaisesRegex(risk_store.RiskStoreError, "role"):
            risk_store.append_record(self.db, record("prediction", "missing-verifier", missing, task_id=None))

        complete = prediction()
        complete["basis"]["execution_models"]["verifier"] = {
            "model": "gpt-6-luna", "reasoning_effort": "low",
        }
        risk_store.append_record(self.db, record("prediction", "complete-roles", complete, task_id=None))

        extra = json.loads(json.dumps(complete))
        extra["basis"]["execution_models"]["auditor"] = {
            "model": "gpt-6-luna", "reasoning_effort": "low",
        }
        with self.assertRaisesRegex(risk_store.RiskStoreError, "role"):
            risk_store.append_record(self.db, record("prediction", "extra-auditor", extra, task_id=None))

    def test_cli_does_not_echo_untrusted_jsonl_operation(self):
        marker = "credential-fragment-never-print"
        path = self.root / "malicious.jsonl"
        path.write_text(json.dumps({"operation": marker, "payload": {}}) + "\n", encoding="utf-8")
        script = Path(__file__).resolve().parents[1] / "scripts/risk_store.py"
        result = subprocess.run([sys.executable, str(script), "import-jsonl", str(self.db), str(path)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertNotIn(marker, result.stderr)
        self.assertLess(len(result.stderr), 200)

    def test_incident_links_and_delayed_outcome_are_append_only(self):
        self.create()
        incident = record("incident", "incident-1", {
            "incident_id": "I1", "affected_tasks": ["T2"], "observed_symptoms": ["failed check"],
            "root_cause_hypothesis": None, "cause_status": "unknown", "related_incident_ids": [],
            "failed_attempts": ["attempt-1"], "evidence": [], "next_diagnostic": "inspect error",
        })
        risk_store.append_record(self.db, incident)
        related = record("incident", "incident-2", {
            "incident_id": "I2", "affected_tasks": ["T2"], "observed_symptoms": ["second failure"],
            "root_cause_hypothesis": "same interface mismatch", "cause_status": "hypothesized",
            "related_incident_ids": ["I1"], "failed_attempts": ["attempt-2"], "evidence": [],
            "next_diagnostic": "compare errors",
        })
        risk_store.append_record(self.db, related)
        confirmed = record("incident", "incident-3", {
            "incident_id": "I3", "affected_tasks": ["T2"], "observed_symptoms": ["confirmed failure"],
            "root_cause_hypothesis": "verified mismatch", "cause_status": "confirmed",
            "related_incident_ids": ["I2"], "failed_attempts": ["attempt-3"],
            "evidence": ["reproduced against source"], "next_diagnostic": "apply fix",
        })
        risk_store.append_record(self.db, confirmed)
        invalid_confirmed = record("incident", "incident-invalid", {
            "incident_id": "I4", "affected_tasks": ["T2"], "observed_symptoms": ["symptom"],
            "root_cause_hypothesis": "cause", "cause_status": "confirmed", "related_incident_ids": [],
            "failed_attempts": [], "evidence": [], "next_diagnostic": "inspect",
        })
        with self.assertRaises(risk_store.RiskStoreError):
            risk_store.append_record(self.db, invalid_confirmed)
        unknown_link = record("incident", "incident-unknown-link", {
            "incident_id": "I5", "affected_tasks": ["T2"], "observed_symptoms": ["symptom"],
            "root_cause_hypothesis": None, "cause_status": "unknown", "related_incident_ids": ["I404"],
            "failed_attempts": [], "evidence": [], "next_diagnostic": "inspect",
        })
        with self.assertRaisesRegex(risk_store.RiskStoreError, "same run"):
            risk_store.append_record(self.db, unknown_link)
        outcome = record("outcome", "outcome-1", {
            "implementation_status": "complete", "checks": ["passed"],
            "human_live_acceptance": "pending", "evidence": [],
        }, task_id=None)
        risk_store.append_record(self.db, outcome)
        later = record("outcome", "outcome-2", {
            "implementation_status": "complete", "checks": ["passed"],
            "human_live_acceptance": "accepted", "evidence": ["human approval"],
        }, task_id=None)
        risk_store.append_record(self.db, later)
        result = risk_store.read_run(self.db, "run-1")
        self.assertEqual(3, len(result["incidents"]))
        self.assertEqual(2, len(result["outcomes"]))

    def test_artifact_hash_and_import_jsonl_preserves_raw_start_in_order(self):
        artifact = self.root / "plan.md"
        artifact.write_bytes(b"plan")
        self.assertEqual(hashlib.sha256(b"plan").hexdigest(), risk_store.artifact_identity(artifact)["sha256"])
        raw_start = {"event": "run_start", "attempt": 1, "start_time": "2026-11-16T07:00:00Z",
                     "model": "GPT-6 (exact variant unavailable)", "status": "running", "run_id": "run-1"}
        lines = [raw_start, {"operation": "create-run", "payload": run(repo_root=str(self.root))},
                 {"operation": "record", "payload": record()}]
        path = self.root / "timings.jsonl"
        path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        report = risk_store.import_jsonl(self.db, path)
        self.assertEqual(3, report["processed"])
        self.assertEqual([1], report["legacy_run_start_lines"])
        again = risk_store.import_jsonl(self.db, path)
        self.assertEqual(3, again["processed"])
        self.assertEqual(2, len(risk_store.read_run(self.db, "run-1")["events"]))
        path.write_text("{broken\n", encoding="utf-8")
        with self.assertRaisesRegex(risk_store.RiskStoreError, "line 1"):
            risk_store.import_jsonl(self.root / "bad.sqlite3", path)

    def test_saved_prototype_prediction_contract_is_accepted(self):
        project = Path(__file__).resolve().parents[2]
        saved = json.loads((project / "docs/audits/risk-estimator-trial-2026-11-16-output.json").read_text(encoding="utf-8"))
        envelope = {"schema_version": 1, "record_id": "saved-prediction", "run_id": saved["run_id"],
                    "kind": "prediction", "task_id": None, "created_at": "2026-11-16T07:00:00Z",
                    "payload": saved}
        normalized = risk_store.validate_record(envelope)
        self.assertEqual(saved["consultation_id"], normalized["payload"]["consultation_id"])
        self.assertEqual(5, len(normalized["payload"]["tasks"]))


if __name__ == "__main__":
    unittest.main()
