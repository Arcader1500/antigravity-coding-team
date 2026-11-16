from copy import deepcopy
from datetime import datetime
import unittest
from pathlib import Path
import uuid

from codex.scripts import risk_store


class RiskIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent / f".risk-integration-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.db = self.root / "risk.sqlite3"

    def tearDown(self):
        for path in self.root.iterdir():
            path.unlink()
        self.root.rmdir()

    def record(self, kind, record_id, payload, task_id="T3", run_id="risk-run", created_at="2026-11-16T07:02:00Z"):
        return {
            "schema_version": 1, "record_id": record_id, "run_id": run_id, "kind": kind,
            "task_id": task_id, "created_at": created_at, "payload": payload,
        }

    def create_run(self, run_id="risk-run", previous_run_id=None):
        plan_path = self.root / "plan.md"
        spec_path = self.root / "spec.md"
        if not plan_path.exists():
            plan_path.write_text("approved plan v1\n", encoding="utf-8")
        if not spec_path.exists():
            spec_path.write_text("approved spec v1\n", encoding="utf-8")
        return risk_store.create_run(self.db, {
            "run_id": run_id, "run_kind": "implementation", "created_at": "2026-11-16T07:00:00Z",
            "repo_root": str(self.root), "plan": risk_store.artifact_identity(plan_path),
            "spec": risk_store.artifact_identity(spec_path),
            "critic": {"status": "READY", "evidence": [{"id": "F1", "status": "resolved"}]},
            "execution": {"models": {"implementer": {"model": "gpt-6-luna", "reasoning_effort": "medium"},
                                       "code-reviewer": {"model": "gpt-6.1-sol", "reasoning_effort": "medium"}},
                          "worker_capacity": 2},
            "rubric_version": "1", "plugin_version": "1.0.0", "previous_run_id": previous_run_id,
        })

    def prediction(self, run_id, consultation_id, revision, previous_revision, reason=None):
        run = risk_store.read_run(self.db, run_id)
        tasks = []
        for task_id, values in (("T3", (5, 8, 12)), ("T4", (5, 7, 10))):
            if task_id == "T3":
                phases = {
                    "implementation": {"optimistic": 3, "likely": 5, "conservative": 8},
                    "debugging": {"optimistic": 1, "likely": 1, "conservative": 2},
                    "self_review": {"optimistic": 1, "likely": 1, "conservative": 1},
                    "task_checks": {"optimistic": 0, "likely": 1, "conservative": 1},
                }
            else:
                phases = {
                    "implementation": {"optimistic": 3, "likely": 4, "conservative": 7},
                    "debugging": {"optimistic": 1, "likely": 1, "conservative": 1},
                    "self_review": {"optimistic": 1, "likely": 1, "conservative": 1},
                    "task_checks": {"optimistic": 0, "likely": 1, "conservative": 1},
                }
            tasks.append({
                "task_id": task_id, "agentic_complexity": "medium", "integration_uncertainty": "medium",
                "defect_exposure": "low", "debugging_cost": "medium", "rationale": "fixture inputs",
                "phase_minutes": phases,
                "agent_minutes": dict(zip(("optimistic", "likely", "conservative"), values)),
                "risk_ids": ["R_SHARED"],
            })
        return {
            "schema_version": 1, "rubric_version": "1", "consultation_id": consultation_id,
            "run_id": run_id, "revision": revision,
            "previous_revision": previous_revision, "revision_reason": reason,
            "mode": "estimate" if revision == 0 else "reassess", "status": "assessed", "provisional": False,
            "critic_status": run["critic"]["status"], "storage_status": "not_persisted",
            "basis": {
                "artifacts": [run["plan"], run["spec"]], "fingerprint_provenance": "fixture hashes",
                "evidence_references": run["critic"]["evidence"], "platform": "test fixture",
                "execution_models": run["execution"]["models"],
                "evaluator": {"model": "gpt-6.1-sol", "reasoning_effort": "medium"},
                "available_worker_capacity": run["execution"]["worker_capacity"],
                "excluded_task_ids": [], "scope": "T3 and T4",
            },
            "questions": [], "unknowns": [], "tasks": tasks,
            "shared_gates": {
                "independent_review": {"optimistic": 1, "likely": 1, "conservative": 2},
                "final_verification": {"optimistic": 1, "likely": 1, "conservative": 1},
                "assumptions": ["T3 and T4 run concurrently."],
            },
            "totals": {"agent_work_minutes": {"optimistic": 12, "likely": 17, "conservative": 25},
                       "agent_elapsed_minutes": {"optimistic": 8, "likely": 10, "conservative": 15},
                       "human_minutes": None, "external_wait_minutes": None,
                       "scheduling_assumptions": ["Known fixture wave schedule."]},
            "risks": [{"risk_id": "R_SHARED", "category": "shared-contract",
                       "affected_tasks": ["T3", "T4"],
                       "evidence": "Two worker reports describe the same interface mismatch.",
                       "root_cause_hypothesis": "A shared interface mismatch.",
                       "cause_status": "hypothesized", "consequences": "Shared rework may affect both tasks.",
                       "next_diagnostic": "Compare the failing contract against source."}],
            "calibration": {"heuristic": True, "historical_run_count": 0, "automatic_updates": False},
        }

    def event(self, record_id, run_id, task_id, event_type, start_time, end_time=None,
              elapsed_seconds=None, status="running", attempt=1):
        return self.record("event", record_id, {
            "event_type": event_type, "task_id": task_id, "attempt": attempt,
            "model": "gpt-6-luna/medium", "start_time": start_time, "end_time": end_time,
            "elapsed_seconds": elapsed_seconds, "active_seconds": None, "status": status,
            "provenance": "controller_system_clock", "known_waits": [],
        }, task_id=task_id, run_id=run_id, created_at=end_time or start_time)

    def build_consultation_history(self):
        run = self.create_run()
        run_id = run["run_id"]
        consultation = {"consultation_id": "consult-1", "run_id": run_id, "revision": 0, "round": 1,
                        "mode": "estimate",
                        "request": {"plan": run["plan"], "spec": run["spec"], "critic": run["critic"]},
                        "response": {"status": "assessed", "consultation_id": "consult-1", "run_id": run_id, "revision": 0},
                        "questions": [{"question_id": "Q-ACCESS-1", "question": "Is the external permission available?",
                                       "forecast_impact": "It may affect T3 elapsed time.",
                                       "requested_evidence": "Permission response or explicit unknown."}],
                        "answers": [{"question_id": "Q-ACCESS-1", "answer": "unknown", "evidence": None}]}
        risk_store.append_record(self.db, self.record("consultation", "consult-record-1", consultation,
                                                       task_id=None, run_id=run_id))
        baseline = self.prediction(run_id, "consult-1", 0, None)
        risk_store.append_record(self.db, self.record("prediction", "prediction-0", baseline,
                                                       task_id=None, run_id=run_id))
        incident = {"incident_id": "I-SHARED-1", "affected_tasks": ["T3", "T4"],
                    "observed_symptoms": ["T3 contract check failed", "T4 contract check failed"],
                    "root_cause_hypothesis": "shared interface mismatch", "cause_status": "hypothesized",
                    "related_incident_ids": [], "failed_attempts": ["T3-attempt-1", "T4-attempt-1"],
                    "evidence": ["both reports point to the same contract"],
                    "next_diagnostic": "compare source signatures"}
        risk_store.append_record(self.db, self.record("incident", "incident-shared-1", incident,
                                                       task_id=None, run_id=run_id))
        follow_up = {"consultation_id": "consult-2", "run_id": run_id, "revision": 1, "round": 1,
                     "mode": "reassess", "request": {"run_id": run_id, "revision": 1},
                     "response": {"status": "assessed", "consultation_id": "consult-2", "run_id": run_id, "revision": 1},
                     "questions": [{"question_id": "Q-CAUSE-1", "question": "Do both failures share a cause?",
                                    "forecast_impact": "A shared cause may change debugging time.",
                                    "requested_evidence": "Evidence comparing the failures."}],
                     "answers": [{"question_id": "Q-CAUSE-1", "answer": "unknown", "evidence": None}]}
        risk_store.append_record(self.db, self.record("consultation", "consult-record-2", follow_up,
                                                       task_id=None, run_id=run_id))
        revised = self.prediction(run_id, "consult-2", 1, 0, "Shared symptoms were observed; root cause remains hypothesized.")
        risk_store.append_record(self.db, self.record("prediction", "prediction-1", revised,
                                                       task_id=None, run_id=run_id))
        return run_id

    def build_failed_abandoned_history(self):
        run_id = self.create_run("abandoned-run")["run_id"]
        open_attempt = self.event("open-attempt-1", run_id, "T3", "attempt_start",
                                  "2026-11-16T07:00:00Z")
        risk_store.append_record(self.db, open_attempt)
        risk_store.append_record(self.db, deepcopy(open_attempt))
        failed = self.event("failed-attempt-1", run_id, "T3", "attempt_end",
                            "2026-11-16T07:00:00Z", "2026-11-16T07:01:00Z", 60, "failed")
        risk_store.append_record(self.db, failed)
        outcome = {"implementation_status": "abandoned", "checks": ["targeted check failed"],
                   "human_live_acceptance": "pending", "evidence": []}
        risk_store.append_record(self.db, self.record("outcome", "abandoned-outcome", outcome,
                                                       task_id=None, run_id=run_id))
        return run_id

    def build_stale_resume_pair(self):
        old = self.create_run("plan-v1-run")
        changed_plan = self.root / "plan.md"
        changed_plan.write_text("approved plan v2\n", encoding="utf-8")
        new_data = {
            "run_id": "plan-v2-run", "run_kind": "implementation", "created_at": "2026-11-16T08:00:00Z",
            "repo_root": str(self.root), "plan": risk_store.artifact_identity(changed_plan),
            "spec": old["spec"], "critic": old["critic"], "execution": old["execution"],
            "rubric_version": "1", "plugin_version": "1.0.0", "previous_run_id": old["run_id"],
        }
        with self.assertRaisesRegex(risk_store.RiskStoreError, "different identity"):
            risk_store.create_run(self.db, {**old, "plan": new_data["plan"]})
        return old, risk_store.create_run(self.db, new_data)

    def build_parallel_history(self):
        run_id = self.create_run("parallel-run")["run_id"]
        consultation = {"consultation_id": "consult-parallel", "run_id": run_id, "revision": 0,
                        "round": 1, "mode": "estimate", "request": {"run_id": run_id, "revision": 0},
                        "response": {"status": "assessed", "consultation_id": "consult-parallel",
                                     "run_id": run_id, "revision": 0}, "questions": [], "answers": []}
        risk_store.append_record(self.db, self.record("consultation", "parallel-consultation", consultation,
                                                       task_id=None, run_id=run_id))
        forecast = self.prediction(run_id, "consult-parallel", 0, None)
        risk_store.append_record(self.db, self.record("prediction", "parallel-prediction", forecast,
                                                       task_id=None, run_id=run_id))
        events = [
            self.event("T3-start", run_id, "T3", "attempt_start", "2026-11-16T07:00:00Z"),
            self.event("T4-start", run_id, "T4", "attempt_start", "2026-11-16T07:00:30Z"),
            self.event("T3-end", run_id, "T3", "attempt_end", "2026-11-16T07:00:00Z",
                       "2026-11-16T07:05:00Z", 300, "DONE"),
            self.event("T4-end", run_id, "T4", "attempt_end", "2026-11-16T07:00:30Z",
                       "2026-11-16T07:06:30Z", 360, "DONE"),
        ]
        for item in events:
            risk_store.append_record(self.db, item)
        return forecast, run_id

    def test_consultation_revision_incident_resume_and_later_acceptance(self):
        run_id = self.build_consultation_history()
        first_read = risk_store.read_run(self.db, run_id)
        self.assertEqual("READY", first_read["critic"]["status"])
        self.assertEqual("Q-ACCESS-1", first_read["consultations"][0]["payload"]["questions"][0]["question_id"])
        self.assertEqual([0, 1], [item["payload"]["revision"] for item in first_read["predictions"]])
        self.assertEqual("hypothesized", first_read["incidents"][0]["payload"]["cause_status"])
        baseline = deepcopy(first_read["predictions"][0]["payload"])

        resumed = risk_store.read_run(self.db, run_id)
        self.assertEqual(first_read["plan"], resumed["plan"])
        outcome = self.record("outcome", "outcome-live-1", {
            "implementation_status": "complete", "checks": ["automated checks passed"],
            "human_live_acceptance": "accepted", "evidence": ["human acceptance recorded after resume"],
        }, task_id=None, run_id=run_id)
        risk_store.append_record(self.db, outcome)
        final_read = risk_store.read_run(self.db, run_id)
        self.assertEqual("accepted", final_read["outcomes"][0]["payload"]["human_live_acceptance"])
        self.assertEqual(2, len(final_read["predictions"]))
        self.assertEqual(baseline, final_read["predictions"][0]["payload"])
        self.assertEqual(["unknown", "unknown"], [item["payload"]["answers"][0]["answer"]
                                                    for item in final_read["consultations"]])

    def test_failed_abandoned_open_attempt_nulls_and_duplicate_retry(self):
        run_id = self.build_failed_abandoned_history()
        result = risk_store.read_run(self.db, run_id)
        self.assertEqual(2, len(result["events"]))
        open_event = result["events"][0]["payload"]
        self.assertIsNone(open_event["end_time"])
        self.assertIsNone(open_event["elapsed_seconds"])
        self.assertEqual("abandoned", result["outcomes"][0]["payload"]["implementation_status"])
        self.assertEqual("pending", result["outcomes"][0]["payload"]["human_live_acceptance"])
        self.assertEqual("failed", result["events"][1]["payload"]["status"])

    def test_stale_artifact_starts_linked_run_and_preserves_old_identity(self):
        old_run, resumed_run = self.build_stale_resume_pair()
        self.assertNotEqual(old_run["plan"]["sha256"], resumed_run["plan"]["sha256"])
        self.assertEqual(old_run["run_id"], resumed_run["previous_run_id"])
        self.assertEqual(old_run["plan"], risk_store.read_run(self.db, old_run["run_id"])["plan"])
        self.assertEqual(resumed_run["plan"], risk_store.read_run(self.db, resumed_run["run_id"])["plan"])

    def test_parallel_task_effort_and_elapsed_remain_distinct(self):
        forecast, run_id = self.build_parallel_history()
        self.assertEqual(17, forecast["totals"]["agent_work_minutes"]["likely"])
        self.assertEqual(10, forecast["totals"]["agent_elapsed_minutes"]["likely"])
        attempts = risk_store.read_run(self.db, run_id)["events"]
        starts = [item["payload"]["start_time"] for item in attempts if item["payload"]["event_type"] == "attempt_start"]
        ends = [item["payload"]["end_time"] for item in attempts if item["payload"]["event_type"] == "attempt_end"]
        self.assertEqual(2, len(starts))
        self.assertEqual(2, len(ends))
        self.assertLess(starts[1], ends[0])
        self.assertGreater(sum(item["payload"]["elapsed_seconds"] for item in attempts if item["payload"]["event_type"] == "attempt_end"), 10 * 60)
        self.assertEqual(6.5 * 60, (datetime.fromisoformat(ends[-1].replace("Z", "+00:00")) -
                                    datetime.fromisoformat(starts[0].replace("Z", "+00:00"))).total_seconds())


if __name__ == "__main__":
    unittest.main()
