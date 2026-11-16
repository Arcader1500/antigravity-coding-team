"""Validated, append-only storage for risk-estimator runs and observations."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any


SCHEMA_VERSION = 1
KINDS = {"consultation", "prediction", "incident", "event", "outcome"}
SCENARIOS = ("optimistic", "likely", "conservative")
PHASES = ("implementation", "debugging", "self_review", "task_checks")
ELAPSED_TOLERANCE_SECONDS = 0.01


class RiskStoreError(ValueError):
    """Invalid input or a persistence conflict with an actionable message."""


def _json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RiskStoreError("record contains values that cannot be stored as finite JSON") from exc


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise RiskStoreError(f"{field} must be a UTC timestamp string")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise RiskStoreError(f"{field} must be an ISO 8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RiskStoreError(f"{field} must include a UTC offset")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RiskStoreError(f"{field} must be a non-empty string")
    return value


def _number(value: Any, field: str, nullable: bool = False) -> int | float | None:
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise RiskStoreError(f"{field} must be a finite non-negative number" + (" or null" if nullable else ""))
    return value


def _scenario(values: Any, field: str) -> dict[str, int | float | None]:
    if not isinstance(values, dict) or set(values) != set(SCENARIOS):
        raise RiskStoreError(f"{field} must contain optimistic, likely and conservative")
    result = {key: _number(values[key], f"{field}.{key}", nullable=True) for key in SCENARIOS}
    present = [result[key] for key in SCENARIOS]
    known = [value for value in present if value is not None]
    if any(left > right for left, right in zip(known, known[1:])):
        raise RiskStoreError(f"{field} known scenarios must be ordered optimistic <= likely <= conservative")
    return result


def _attempt_number(value: Any, field: str = "event.attempt") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RiskStoreError(f"{field} must be a positive integer")
    return value


def _validate_elapsed(payload: dict) -> None:
    start_value = payload.get("start_time")
    end_value = payload.get("end_time")
    elapsed = payload.get("elapsed_seconds")
    if end_value is not None:
        if start_value is None or elapsed is None:
            raise RiskStoreError("completed timed events require start_time and elapsed_seconds")
        start = datetime.fromisoformat(start_value.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_value.replace("Z", "+00:00"))
        measured = (end - start).total_seconds()
        if end < start or abs(measured - elapsed) > ELAPSED_TOLERANCE_SECONDS:
            raise RiskStoreError("event elapsed_seconds must match its observed timestamps")
    elif elapsed is not None:
        raise RiskStoreError("open timed events must leave elapsed_seconds null")
    active = payload.get("active_seconds")
    if active is not None and elapsed is not None and active > elapsed + ELAPSED_TOLERANCE_SECONDS:
        raise RiskStoreError("active_seconds cannot exceed elapsed_seconds")


def _validate_consultation(payload: dict, run_id: str) -> None:
    for field in ("consultation_id", "run_id", "mode"):
        _text(payload.get(field), f"consultation.{field}")
    if payload["run_id"] != run_id:
        raise RiskStoreError("consultation.run_id must match record.run_id")
    if payload["mode"] not in ("estimate", "reassess"):
        raise RiskStoreError("consultation.mode must be estimate or reassess")
    revision = payload.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise RiskStoreError("consultation.revision must be a non-negative integer")
    round_number = payload.get("round", 1)
    if isinstance(round_number, bool) or not isinstance(round_number, int) or round_number < 1:
        raise RiskStoreError("consultation.round must be a positive integer")
    for field in ("request", "response"):
        if not isinstance(payload.get(field), dict):
            raise RiskStoreError(f"consultation.{field} must be an object")
    questions = payload.get("questions")
    answers = payload.get("answers")
    if not isinstance(questions, list) or not isinstance(answers, list):
        raise RiskStoreError("consultation.questions and answers must be arrays")
    question_ids = set()
    for question in questions:
        if not isinstance(question, dict):
            raise RiskStoreError("consultation question entries must be objects")
        question_id = _text(question.get("question_id"), "consultation.question.question_id")
        if question_id in question_ids:
            raise RiskStoreError("consultation question IDs must be unique")
        question_ids.add(question_id)
        for field in ("question", "forecast_impact", "requested_evidence"):
            _text(question.get(field), f"consultation.question.{field}")
    for answer in answers:
        if not isinstance(answer, dict):
            raise RiskStoreError("consultation answer entries must be objects")
        question_id = _text(answer.get("question_id"), "consultation.answer.question_id")
        if question_id not in question_ids:
            raise RiskStoreError("consultation answer references an unknown question_id")
        _text(answer.get("answer"), "consultation.answer.answer")
        if "evidence" not in answer:
            raise RiskStoreError("consultation.answer.evidence is required; use null when unavailable")
    for field, expected in (("consultation_id", payload["consultation_id"]), ("run_id", run_id), ("revision", revision)):
        if field in payload["request"] and payload["request"][field] != expected:
            raise RiskStoreError(f"consultation.request.{field} does not match its record")
        if field in payload["response"] and payload["response"][field] != expected:
            raise RiskStoreError(f"consultation.response.{field} does not match its record")


@contextmanager
def _connect(db_path: Path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        "CREATE TABLE IF NOT EXISTS runs ("
        "run_id TEXT PRIMARY KEY, repo_root TEXT NOT NULL, payload TEXT NOT NULL);"
        "CREATE TABLE IF NOT EXISTS records ("
        "record_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),"
        "kind TEXT NOT NULL, task_id TEXT, created_at TEXT NOT NULL, payload TEXT NOT NULL);"
        "CREATE INDEX IF NOT EXISTS records_run_kind_task ON records(run_id, kind, task_id);"
    )
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        connection.execute("PRAGMA user_version = 1")
        version = 1
    if version != SCHEMA_VERSION:
        connection.close()
        raise RiskStoreError(f"unsupported database schema version {version}")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _run_normalized(run: dict) -> dict:
    if not isinstance(run, dict):
        raise RiskStoreError("run must be an object")
    data = dict(run)
    _text(data.get("run_id"), "run_id")
    if data.get("run_kind") not in ("implementation", "prompt_trial"):
        raise RiskStoreError("run_kind must be implementation or prompt_trial")
    data["created_at"] = _timestamp(data.get("created_at"), "created_at")
    root_value = _text(data.get("repo_root"), "repo_root")
    root = Path(root_value).expanduser().resolve()
    data["repo_root"] = str(root)
    for name in ("plan", "spec"):
        artifact = data.get(name)
        if not isinstance(artifact, dict):
            raise RiskStoreError(f"{name} artifact identity is required")
        artifact = dict(artifact)
        path = Path(_text(artifact.get("path"), f"{name}.path")).expanduser()
        artifact["path"] = str((root / path).resolve() if not path.is_absolute() else path.resolve())
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise RiskStoreError(f"{name}.sha256 must be a 64-character SHA-256 hex digest")
        artifact["sha256"] = digest.lower()
        data[name] = artifact
    critic = data.get("critic")
    if not isinstance(critic, dict) or critic.get("status") not in ("READY", "NOT READY", "unknown"):
        raise RiskStoreError("critic.status must be READY, NOT READY or unknown")
    if "evidence" not in critic:
        raise RiskStoreError("critic.evidence is required; use null when unavailable")
    if critic["evidence"] is not None and not isinstance(critic["evidence"], (str, dict, list)):
        raise RiskStoreError("critic.evidence must be text, structured evidence or null")
    execution = data.get("execution")
    if not isinstance(execution, dict) or not isinstance(execution.get("models"), dict) or not execution["models"]:
        raise RiskStoreError("execution.models must be a non-empty object")
    for role, model in execution["models"].items():
        _text(role, "execution model role")
        if isinstance(model, str):
            _text(model, f"execution.models.{role}")
        elif isinstance(model, dict):
            _text(model.get("model"), f"execution.models.{role}.model")
            _text(model.get("reasoning_effort"), f"execution.models.{role}.reasoning_effort")
        else:
            raise RiskStoreError(f"execution.models.{role} must identify a model and reasoning effort")
    capacity = execution.get("worker_capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        raise RiskStoreError("execution.worker_capacity must be a positive integer")
    for field in ("rubric_version", "plugin_version"):
        _text(data.get(field), field)
    previous = data.get("previous_run_id")
    if previous is not None:
        _text(previous, "previous_run_id")
        if previous == data["run_id"]:
            raise RiskStoreError("run cannot be its own predecessor")
    return data


def create_run(db_path: Path, run: dict) -> dict:
    data = _run_normalized(run)
    with _connect(db_path) as conn:
        previous = data.get("previous_run_id")
        if previous:
            prior = conn.execute("SELECT repo_root FROM runs WHERE run_id = ?", (previous,)).fetchone()
            if prior is None:
                raise RiskStoreError("previous_run_id does not exist")
            if prior["repo_root"] != data["repo_root"]:
                raise RiskStoreError("previous_run_id belongs to a different repository")
        encoded = _json(data)
        existing = conn.execute("SELECT payload FROM runs WHERE run_id = ?", (data["run_id"],)).fetchone()
        if existing:
            if existing["payload"] != encoded:
                raise RiskStoreError("run_id already exists with different identity")
            return json.loads(existing["payload"])
        conn.execute("INSERT INTO runs(run_id, repo_root, payload) VALUES (?, ?, ?)",
                     (data["run_id"], data["repo_root"], encoded))
    return data


def artifact_identity(path: Path) -> dict:
    artifact = Path(path).expanduser().resolve()
    try:
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    except OSError as exc:
        raise RiskStoreError(f"cannot read artifact: {artifact}") from exc
    return {"path": str(artifact), "sha256": digest}


def _validate_prediction(payload: dict) -> None:
    for field in ("consultation_id", "run_id", "rubric_version", "mode", "status"):
        _text(payload.get(field), f"prediction.{field}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RiskStoreError(f"prediction.schema_version must be {SCHEMA_VERSION}")
    if payload.get("mode") not in ("estimate", "reassess"):
        raise RiskStoreError("prediction.mode must be estimate or reassess")
    if payload.get("status") not in ("assessed", "needs_evidence"):
        raise RiskStoreError("prediction.status must be assessed or needs_evidence")
    if isinstance(payload.get("revision"), bool) or not isinstance(payload.get("revision"), int) or payload["revision"] < 0:
        raise RiskStoreError("prediction.revision must be a non-negative integer")
    expected_previous = None if payload["revision"] == 0 else payload["revision"] - 1
    if payload.get("previous_revision") != expected_previous:
        raise RiskStoreError("prediction.previous_revision must link to the immediately prior revision")
    if payload.get("revision") == 0:
        if payload.get("revision_reason") is not None:
            raise RiskStoreError("baseline prediction revision_reason must be null")
    else:
        _text(payload.get("revision_reason"), "prediction.revision_reason")
    if not isinstance(payload.get("provisional"), bool):
        raise RiskStoreError("prediction.provisional must be boolean")
    if payload.get("critic_status") not in ("READY", "NOT READY", "unknown"):
        raise RiskStoreError("prediction.critic_status must be READY, NOT READY or unknown")
    if "unknowns" not in payload or not isinstance(payload["unknowns"], list):
        raise RiskStoreError("prediction.unknowns must be an array")
    if payload.get("storage_status") != "not_persisted":
        raise RiskStoreError("prediction.storage_status must be not_persisted")
    basis = payload.get("basis")
    if not isinstance(basis, dict):
        raise RiskStoreError("prediction.basis is required")
    artifacts = basis.get("artifacts")
    if not isinstance(artifacts, list):
        raise RiskStoreError("prediction.basis.artifacts must be an array")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise RiskStoreError("prediction basis artifacts must be objects")
        _text(artifact.get("path"), "prediction.basis.artifact.path")
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise RiskStoreError("prediction basis artifact sha256 must be a 64-character digest")
    _text(basis.get("fingerprint_provenance"), "prediction.basis.fingerprint_provenance")
    if not isinstance(basis.get("evidence_references"), list):
        raise RiskStoreError("prediction.basis.evidence_references must be an array")
    _text(basis.get("platform"), "prediction.basis.platform")
    models = basis.get("execution_models")
    if not isinstance(models, dict) or not models:
        raise RiskStoreError("prediction.basis.execution_models must be a non-empty object")
    for role, model in models.items():
        if not isinstance(model, dict):
            raise RiskStoreError("prediction execution model entries must be objects")
        _text(model.get("model"), "prediction.basis.execution_model.model")
        _text(model.get("reasoning_effort"), "prediction.basis.execution_model.reasoning_effort")
    evaluator = basis.get("evaluator")
    if not isinstance(evaluator, dict):
        raise RiskStoreError("prediction.basis.evaluator is required")
    _text(evaluator.get("model"), "prediction.basis.evaluator.model")
    _text(evaluator.get("reasoning_effort"), "prediction.basis.evaluator.reasoning_effort")
    capacity = basis.get("available_worker_capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        raise RiskStoreError("prediction.basis.available_worker_capacity must be a positive integer")
    if not isinstance(basis.get("excluded_task_ids"), list):
        raise RiskStoreError("prediction.basis.excluded_task_ids must be an array")
    _text(basis.get("scope"), "prediction.basis.scope")
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise RiskStoreError("prediction.questions must be an array")
    question_ids = set()
    for question in questions:
        if not isinstance(question, dict):
            raise RiskStoreError("prediction question entries must be objects")
        question_id = _text(question.get("question_id"), "prediction.question.question_id")
        if question_id in question_ids:
            raise RiskStoreError("prediction question IDs must be unique")
        question_ids.add(question_id)
        for field in ("question", "forecast_impact", "requested_evidence"):
            _text(question.get(field), f"prediction.question.{field}")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise RiskStoreError("prediction.tasks must be a non-empty array")
    task_ids = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise RiskStoreError(f"prediction.tasks[{index}] must be an object")
        tid = _text(task.get("task_id"), f"prediction.tasks[{index}].task_id")
        if tid in task_ids:
            raise RiskStoreError(f"duplicate prediction task_id {tid}")
        task_ids.add(tid)
        for field in ("agentic_complexity", "integration_uncertainty", "defect_exposure", "debugging_cost"):
            if task.get(field) not in ("low", "medium", "high"):
                raise RiskStoreError(f"prediction task {tid} requires {field}=low|medium|high")
        _text(task.get("rationale"), f"prediction task {tid}.rationale")
        phases = task.get("phase_minutes")
        if not isinstance(phases, dict) or set(phases) != set(PHASES):
            raise RiskStoreError(f"prediction task {tid}.phase_minutes must define all four required phases")
        phase_scenarios = [_scenario(phases[name], f"task {tid}.phase_minutes.{name}") for name in PHASES]
        agent = _scenario(task.get("agent_minutes"), f"task {tid}.agent_minutes")
        for scenario in SCENARIOS:
            values = [phase[scenario] for phase in phase_scenarios]
            phase_sum = None if any(value is None for value in values) else sum(values)
            if (phase_sum is None) != (agent[scenario] is None) or (
                phase_sum is not None and not math.isclose(agent[scenario], phase_sum)
            ):
                raise RiskStoreError(f"task {tid}.agent_minutes.{scenario} must equal its phase sum")
        if not isinstance(task.get("risk_ids"), list):
            raise RiskStoreError(f"task {tid}.risk_ids must be an array")
    gates = payload.get("shared_gates")
    if not isinstance(gates, dict) or set(gates) != {"independent_review", "final_verification", "assumptions"}:
        raise RiskStoreError("prediction.shared_gates must define independent_review, final_verification and assumptions")
    if not isinstance(gates["assumptions"], list):
        raise RiskStoreError("prediction.shared_gates.assumptions must be an array")
    gate_values = [_scenario(gates[name], f"shared_gates.{name}") for name in ("independent_review", "final_verification")]
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise RiskStoreError("prediction.totals is required")
    work = _scenario(totals.get("agent_work_minutes"), "totals.agent_work_minutes")
    elapsed = _scenario(totals.get("agent_elapsed_minutes"), "totals.agent_elapsed_minutes")
    for scenario in SCENARIOS:
        contributions = [_scenario(task["agent_minutes"], "agent_minutes")[scenario] for task in tasks]
        contributions.extend(gate[scenario] for gate in gate_values)
        expected = None if any(value is None for value in contributions) else sum(contributions)
        if (expected is None) != (work[scenario] is None) or (
            expected is not None and not math.isclose(work[scenario], expected)
        ):
            raise RiskStoreError(f"totals.agent_work_minutes.{scenario} must equal task and gate sums")
        if expected is None and elapsed[scenario] is not None:
            raise RiskStoreError(f"totals.agent_elapsed_minutes.{scenario} must be null when work is unknown")
        if elapsed[scenario] is not None and elapsed[scenario] > work[scenario]:
            raise RiskStoreError(f"totals.agent_elapsed_minutes.{scenario} cannot exceed agent work")
    for field in ("human_minutes", "external_wait_minutes"):
        if field not in totals:
            raise RiskStoreError(f"totals.{field} is required; use null when unknown")
        _number(totals[field], f"totals.{field}", nullable=True)
    if not isinstance(totals.get("scheduling_assumptions"), list):
        raise RiskStoreError("prediction.totals.scheduling_assumptions must be an array")
    risks = payload.get("risks")
    if not isinstance(risks, list):
        raise RiskStoreError("prediction.risks must be an array")
    risk_ids = set()
    for risk in risks:
        if not isinstance(risk, dict):
            raise RiskStoreError("prediction risk entries must be objects")
        rid = _text(risk.get("risk_id"), "risk.risk_id")
        risk_ids.add(rid)
        affected = risk.get("affected_tasks", [])
        if not isinstance(affected, list) or any(tid not in task_ids for tid in affected):
            raise RiskStoreError(f"risk {rid} references an unknown task")
        for field in ("category", "evidence", "cause_status", "consequences", "next_diagnostic"):
            _text(risk.get(field), f"risk {rid}.{field}")
        if risk["cause_status"] not in ("unknown", "hypothesized", "confirmed"):
            raise RiskStoreError(f"risk {rid}.cause_status is invalid")
        if risk["cause_status"] == "confirmed" and not risk.get("evidence"):
            raise RiskStoreError(f"confirmed risk {rid} requires evidence")
        if risk.get("root_cause_hypothesis") is not None:
            _text(risk["root_cause_hypothesis"], f"risk {rid}.root_cause_hypothesis")
        for field in ("observed_symptoms", "related_incident_ids"):
            if field in risk and not isinstance(risk[field], list):
                raise RiskStoreError(f"risk {rid}.{field} must be an array")
    for task in tasks:
        if any(rid not in risk_ids for rid in task["risk_ids"]):
            raise RiskStoreError(f"task {task['task_id']} references an unknown risk")

    calibration = payload.get("calibration")
    if not isinstance(calibration, dict) or calibration.get("heuristic") is not True or calibration.get("automatic_updates") is not False:
        raise RiskStoreError("prediction.calibration must declare heuristic estimates and no automatic updates")
    sample_count = calibration.get("historical_run_count")
    if sample_count is not None and (isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 0):
        raise RiskStoreError("prediction.calibration.historical_run_count must be a non-negative integer or null")


def validate_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise RiskStoreError("record must be an object")
    data = dict(record)
    if isinstance(data.get("schema_version"), bool) or data.get("schema_version") != SCHEMA_VERSION:
        raise RiskStoreError(f"schema_version must be {SCHEMA_VERSION}")
    for field in ("record_id", "run_id", "kind"):
        _text(data.get(field), field)
    if data["kind"] not in KINDS:
        raise RiskStoreError("kind must be consultation, prediction, incident, event or outcome")
    if data.get("task_id") is not None:
        _text(data["task_id"], "task_id")
    data["created_at"] = _timestamp(data.get("created_at"), "created_at")
    payload = data.get("payload")
    if not isinstance(payload, dict):
        raise RiskStoreError("payload must be an object")
    payload = dict(payload)
    kind = data["kind"]
    if kind == "event":
        event_type = _text(payload.get("event_type"), "event.event_type")
        if payload.get("task_id") is not None:
            _text(payload["task_id"], "event.task_id")
            if data.get("task_id") is not None and payload["task_id"] != data["task_id"]:
                raise RiskStoreError("event.task_id must match record.task_id")
        if "attempt" in payload:
            payload["attempt"] = _attempt_number(payload["attempt"])
        for field in ("start_time", "end_time"):
            if field in payload and payload[field] is not None:
                payload[field] = _timestamp(payload[field], f"event.{field}")
        for field in ("elapsed_seconds", "active_seconds"):
            if field in payload:
                _number(payload[field], f"event.{field}", nullable=True)
        if payload.get("known_waits") is not None and not isinstance(payload.get("known_waits"), list):
            raise RiskStoreError("event.known_waits must be an array or null")
        if event_type in ("attempt_start", "attempt_end"):
            if payload.get("task_id") is None or data.get("task_id") != payload["task_id"]:
                raise RiskStoreError("task attempt events require matching top-level and payload task_id")
            _attempt_number(payload.get("attempt"))
            _text(payload.get("model"), "event.model")
            _text(payload.get("status"), "event.status")
            _text(payload.get("provenance"), "event.provenance")
            if not isinstance(payload.get("known_waits"), list):
                raise RiskStoreError("task attempt events require known_waits array")
            if "active_seconds" not in payload:
                raise RiskStoreError("task attempt events require active_seconds; use null when unknown")
            if event_type == "attempt_start":
                if payload.get("start_time") is None or payload.get("end_time") is not None or payload.get("elapsed_seconds") is not None:
                    raise RiskStoreError("attempt_start requires start_time and null end_time/elapsed_seconds")
                if payload["status"] != "running" or payload["active_seconds"] is not None:
                    raise RiskStoreError("attempt_start requires running status and unknown active_seconds")
            else:
                if payload.get("start_time") is None or payload.get("end_time") is None or payload.get("elapsed_seconds") is None:
                    raise RiskStoreError("attempt_end requires start_time, end_time and elapsed_seconds")
                if payload["status"] == "running":
                    raise RiskStoreError("attempt_end requires a completion status")
                _validate_elapsed(payload)
        elif any(payload.get(field) is not None for field in ("start_time", "end_time", "elapsed_seconds")):
            if payload.get("end_time") is None and payload.get("elapsed_seconds") is not None:
                raise RiskStoreError("open timed events must leave elapsed_seconds null")
            if payload.get("end_time") is not None or payload.get("elapsed_seconds") is not None:
                _validate_elapsed(payload)
            _text(payload.get("status"), "event.status")
            _text(payload.get("provenance"), "event.provenance")
    elif kind == "prediction":
        _validate_prediction(payload)
        if payload["run_id"] != data["run_id"]:
            raise RiskStoreError("prediction.run_id must match record.run_id")
    elif kind == "consultation":
        _validate_consultation(payload, data["run_id"])
        payload.setdefault("round", 1)
    elif kind == "incident":
        for field in ("incident_id", "cause_status"):
            _text(payload.get(field), f"incident.{field}")
        if payload["cause_status"] not in ("unknown", "hypothesized", "confirmed"):
            raise RiskStoreError("incident.cause_status is invalid")
        for field in ("observed_symptoms", "affected_tasks", "failed_attempts", "related_incident_ids", "evidence"):
            if not isinstance(payload.get(field), list):
                raise RiskStoreError(f"incident.{field} must be an array")
        if payload["cause_status"] == "confirmed" and not payload.get("evidence"):
            raise RiskStoreError("confirmed incident cause requires evidence")
        _text(payload.get("next_diagnostic"), "incident.next_diagnostic")
        if not payload["observed_symptoms"]:
            raise RiskStoreError("incident.observed_symptoms cannot be empty")
        if payload.get("root_cause_hypothesis") is not None:
            _text(payload["root_cause_hypothesis"], "incident.root_cause_hypothesis")
    elif kind == "outcome":
        _text(payload.get("implementation_status"), "outcome.implementation_status")
        if not isinstance(payload.get("checks"), list):
            raise RiskStoreError("outcome.checks must be an array")
        acceptance = payload.get("human_live_acceptance")
        if acceptance not in ("pending", "unavailable", "not_applicable", "accepted", "rejected", "unknown"):
            raise RiskStoreError("outcome.human_live_acceptance has an invalid value")
        if "evidence" in payload and not isinstance(payload["evidence"], list):
            raise RiskStoreError("outcome.evidence must be an array")
        if acceptance in ("accepted", "rejected") and not payload.get("evidence"):
            raise RiskStoreError("human/live acceptance decisions require evidence")
    data["payload"] = payload
    return data


def _canonical_artifact_path(path: str, repo_root: str) -> str:
    artifact = Path(path).expanduser()
    return str((Path(repo_root) / artifact).resolve() if not artifact.is_absolute() else artifact.resolve())


def _model_identity(value: Any) -> tuple[str, str | None]:
    if isinstance(value, dict):
        return value.get("model"), value.get("reasoning_effort")
    if isinstance(value, str) and "/" in value:
        return tuple(value.rsplit("/", 1))
    if isinstance(value, str):
        return value, None
    return "", None


def _validate_prediction_run_basis(prediction: dict, run: dict) -> None:
    basis = prediction["basis"]
    expected_artifacts = {name: run[name] for name in ("plan", "spec")}
    found = {}
    for artifact in basis["artifacts"]:
        path = _canonical_artifact_path(artifact["path"], run["repo_root"])
        for name, expected in expected_artifacts.items():
            if path == expected["path"]:
                found[name] = artifact
    if set(found) != set(expected_artifacts) or any(
        found[name]["sha256"].lower() != expected["sha256"].lower()
        for name, expected in expected_artifacts.items()
    ):
        raise RiskStoreError("prediction plan/spec basis differs from the immutable run")
    if prediction["critic_status"] != run["critic"]["status"]:
        raise RiskStoreError("prediction critic status differs from the immutable run")
    critic_evidence = run["critic"]["evidence"]
    if critic_evidence is not None:
        references = {_json(item) for item in basis["evidence_references"]}
        required = critic_evidence if isinstance(critic_evidence, list) else [critic_evidence]
        if any(_json(item) not in references for item in required):
            raise RiskStoreError("prediction critic evidence references differ from the immutable run")
    if basis["available_worker_capacity"] != run["execution"]["worker_capacity"]:
        raise RiskStoreError("prediction worker capacity differs from the immutable run")
    execution_models = run["execution"]["models"]
    if set(basis["execution_models"]) != set(execution_models):
        raise RiskStoreError("prediction execution model roles differ from the immutable run")
    if any(
        _model_identity(spec) != _model_identity(execution_models[role])
        for role, spec in basis["execution_models"].items()
    ):
        raise RiskStoreError("prediction execution model basis differs from the immutable run")


def append_record(db_path: Path, record: dict) -> dict:
    data = validate_record(record)
    encoded = _json(data["payload"])
    with _connect(db_path) as conn:
        run_row = conn.execute("SELECT payload FROM runs WHERE run_id = ?", (data["run_id"],)).fetchone()
        if run_row is None:
            raise RiskStoreError("run_id must be created before linked records")
        existing = conn.execute("SELECT run_id, kind, task_id, created_at, payload FROM records WHERE record_id = ?",
                                (data["record_id"],)).fetchone()
        if existing:
            identity = (existing["run_id"], existing["kind"], existing["task_id"], existing["created_at"], existing["payload"])
            expected = (data["run_id"], data["kind"], data.get("task_id"), data["created_at"], encoded)
            if identity != expected:
                raise RiskStoreError("record_id already exists with different content")
            return data
        if data["kind"] == "prediction":
            _validate_prediction_run_basis(data["payload"], json.loads(run_row["payload"]))
            linked = conn.execute("SELECT payload FROM records WHERE run_id = ? AND kind = 'consultation'",
                                  (data["run_id"],)).fetchall()
            if not any(
                (payload := json.loads(row["payload"])).get("consultation_id") == data["payload"]["consultation_id"]
                and payload.get("revision") == data["payload"]["revision"]
                for row in linked
            ):
                raise RiskStoreError("prediction must reference a same-run consultation for its revision")
            rev = data["payload"]["revision"]
            prior = conn.execute("SELECT payload FROM records WHERE run_id = ? AND kind = 'prediction'",
                                 (data["run_id"],)).fetchall()
            revisions = {json.loads(row["payload"])["revision"] for row in prior}
            expected = 0 if not revisions else max(revisions) + 1
            if rev != expected:
                raise RiskStoreError(f"prediction revision must be {expected}")
        if data["kind"] == "consultation":
            current = data["payload"]
            prior = [json.loads(row["payload"]) for row in conn.execute(
                "SELECT payload FROM records WHERE run_id = ? AND kind = 'consultation'",
                (data["run_id"],),
            ) if json.loads(row["payload"]).get("consultation_id") == current["consultation_id"]]
            round_number = current["round"]
            if prior:
                if round_number != max(item.get("round", 1) for item in prior) + 1:
                    raise RiskStoreError("consultation rounds must append in sequence under a stable consultation_id")
                if any(item["mode"] != current["mode"] or item["revision"] != current["revision"] for item in prior):
                    raise RiskStoreError("consultation rounds must retain their mode and prediction revision")
                prior_questions = {question["question_id"]: question for item in prior for question in item["questions"]}
                for question in current["questions"]:
                    if question["question_id"] in prior_questions and question != prior_questions[question["question_id"]]:
                        raise RiskStoreError("reused consultation question IDs must retain their wording and evidence request")
            elif round_number != 1:
                raise RiskStoreError("a new consultation must start at round 1")
        if data["kind"] == "incident":
            related = data["payload"]["related_incident_ids"]
            if data["payload"]["incident_id"] in related or data["record_id"] in related:
                raise RiskStoreError("incident cannot be related to itself")
            known = set()
            for row in conn.execute("SELECT record_id, payload FROM records WHERE run_id = ? AND kind = 'incident'",
                                    (data["run_id"],)):
                known.add(row["record_id"])
                known.add(json.loads(row["payload"])["incident_id"])
            if any(item not in known for item in related):
                raise RiskStoreError("related incident IDs must refer to incidents in the same run")
        conn.execute("INSERT INTO records(record_id, run_id, kind, task_id, created_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                     (data["record_id"], data["run_id"], data["kind"], data.get("task_id"), data["created_at"], encoded))
    return data


def read_run(db_path: Path, run_id: str) -> dict:
    _text(run_id, "run_id")
    with _connect(db_path) as conn:
        row = conn.execute("SELECT payload FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise RiskStoreError("run_id was not found")
        result = json.loads(row["payload"])
        records = conn.execute("SELECT record_id, kind, task_id, created_at, payload FROM records WHERE run_id = ? ORDER BY rowid",
                               (run_id,)).fetchall()
    result.update({"predictions": [], "consultations": [], "incidents": [], "events": [], "outcomes": []})
    categories = {"prediction": "predictions", "consultation": "consultations", "incident": "incidents",
                  "event": "events", "outcome": "outcomes"}
    for row in records:
        result[categories[row["kind"]]].append({"record_id": row["record_id"], "task_id": row["task_id"],
                                                  "created_at": row["created_at"], "payload": json.loads(row["payload"])})
    return result


def _import_record(db_path: Path, operation: str, payload: dict) -> dict:
    if operation == "create-run":
        return create_run(db_path, payload)
    if operation == "record":
        return append_record(db_path, payload)
    raise RiskStoreError("unsupported JSONL operation")


def import_jsonl(db_path: Path, jsonl_path: Path) -> dict:
    report = {"processed": 0, "created_runs": 0, "records": 0, "legacy_run_start_lines": [], "errors": []}
    pending_starts = []
    known_runs = set()
    try:
        lines = Path(jsonl_path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RiskStoreError("cannot read JSONL bootstrap file") from exc
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RiskStoreError(f"malformed JSONL line {line_no}: invalid JSON") from exc
        try:
            if isinstance(entry, dict) and entry.get("event") == "run_start":
                run_id = _text(entry.get("run_id"), "run_start.run_id")
                start_time = _timestamp(entry.get("start_time"), "run_start.start_time")
                attempt = entry.get("attempt")
                if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
                    raise RiskStoreError("run_start.attempt must be a positive integer")
                event_payload = {
                    "event_type": "run_start", "attempt": attempt, "start_time": start_time,
                    "end_time": None, "elapsed_seconds": None, "status": entry.get("status"),
                    "model": entry.get("model"), "provenance": "legacy_jsonl_run_start",
                    "legacy_payload": entry,
                }
                event = {"schema_version": 1, "record_id": f"legacy-run-start-{run_id}-{attempt}",
                         "run_id": run_id, "kind": "event", "task_id": None,
                         "created_at": start_time, "payload": event_payload}
                report["legacy_run_start_lines"].append(line_no)
                if run_id in known_runs:
                    append_record(db_path, event)
                    report["records"] += 1
                else:
                    pending_starts.append((line_no, run_id, event))
            else:
                if not isinstance(entry, dict) or not isinstance(entry.get("payload"), dict):
                    raise RiskStoreError("line must contain an operation and object payload")
                operation = entry.get("operation")
                _import_record(db_path, operation, entry["payload"])
                report["created_runs"] += operation == "create-run"
                report["records"] += operation == "record"
                if operation == "create-run":
                    run_id = entry["payload"].get("run_id")
                    known_runs.add(run_id)
                    waiting = [item for item in pending_starts if item[1] == run_id]
                    for _, _, legacy_event in waiting:
                        append_record(db_path, legacy_event)
                        report["records"] += 1
                    pending_starts = [item for item in pending_starts if item[1] != run_id]
            report["processed"] += 1
        except RiskStoreError as exc:
            raise RiskStoreError(f"JSONL line {line_no}: {exc}") from exc
    if pending_starts:
        line_no, run_id, _ = pending_starts[0]
        raise RiskStoreError(f"JSONL line {line_no}: run_start references run {run_id!r} with no create-run operation")
    return report


def _read_input() -> dict:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RiskStoreError("stdin must contain one JSON object") from exc
    if not isinstance(value, dict):
        raise RiskStoreError("stdin must contain one JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("create-run", "record"):
        cmd = sub.add_parser(name, help=f"read one JSON object from stdin and {name}")
        cmd.add_argument("db", type=Path)
    show = sub.add_parser("show", help="show one run as JSON")
    show.add_argument("db", type=Path)
    show.add_argument("run_id")
    importer = sub.add_parser("import-jsonl", help="replay ordered bootstrap operations from JSONL")
    importer.add_argument("db", type=Path)
    importer.add_argument("jsonl", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create-run":
            result = create_run(args.db, _read_input())
        elif args.command == "record":
            result = append_record(args.db, _read_input())
        elif args.command == "show":
            result = read_run(args.db, args.run_id)
        else:
            result = import_jsonl(args.db, args.jsonl)
        print(_json(result))
        return 0
    except (RiskStoreError, OSError, sqlite3.Error, TypeError) as exc:
        line = re.search(r"JSONL line (\d+)", str(exc)) if isinstance(exc, RiskStoreError) else None
        if line:
            message = f"invalid JSONL entry at line {line.group(1)}; check operation, run ordering and schema"
        elif isinstance(exc, RiskStoreError):
            message = "input validation or persistence conflict; check schema, IDs, timestamps and run relationships"
        elif isinstance(exc, (OSError, sqlite3.Error)):
            message = "database or file operation failed; check the storage path and permissions"
        else:
            message = "invalid input type; provide a JSON object"
        print(f"risk_store: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
