"""Reusable helpers for parsing/validating nested Steps payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, List, Tuple

from core import PlanNode, Step, TaskNode, Attachment, VerificationCheck
from core.desktop.devtools.interface.i18n import translate


class StepParseError(Exception):
    """Steps payload parsing error."""


def _load_input_source(raw: str, label: str) -> str:
    """Load text payload from string, file, or STDIN.

    Supported sources:
    - '-'            : STDIN
    - '@path/to.json': file
    - otherwise      : inline string
    """
    source = (raw or "").strip()
    if not source:
        return source
    if source == "-":
        data = sys.stdin.read()
        if not data.strip():
            raise StepParseError(f"STDIN is empty: provide {label}")
        return data
    if source.startswith("@"):
        path_str = source[1:].strip()
        if not path_str:
            raise StepParseError(f"Specify path to {label} after '@'")
        file_path = Path(path_str).expanduser()
        if not file_path.exists():
            raise StepParseError(f"File not found: {file_path}")
        return file_path.read_text(encoding="utf-8")
    return source


def load_steps_source(raw: str) -> str:
    return _load_input_source(raw, translate("LABEL_STEPS_JSON", fallback="steps JSON"))


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y", "ok", "done", "ready", "готов", "готово", "+")
    return bool(value)


def _parse_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()] if str(value).strip() else []


def parse_steps_json(raw: str) -> List[Step]:
    """Parse a JSON array of steps (recursive) into Step objects."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StepParseError(translate("ERR_JSON_INVALID", error=exc)) from exc

    if not isinstance(data, list):
        raise StepParseError(translate("ERR_JSON_ARRAY_REQUIRED"))

    def parse_node(item: Any, *, idx: str) -> Step:
        if not isinstance(item, dict):
            raise StepParseError(translate("ERR_JSON_ELEMENT_OBJECT", idx=idx))

        title = str(item.get("title", "") or "").strip()
        if not title:
            raise StepParseError(translate("ERR_JSON_ELEMENT_TITLE", idx=idx))

        criteria = _parse_string_list(item.get("success_criteria", []))
        tests = _parse_string_list(item.get("tests", []))
        blockers = _parse_string_list(item.get("blockers", []))

        step = Step.new(
            title,
            criteria=criteria,
            tests=tests,
            blockers=blockers,
            created_at=str(item.get("created_at") or "").strip() or None,
        )
        if not step:
            raise StepParseError(translate("ERR_JSON_ELEMENT_CRITERIA", idx=idx))
        node_id = str(item.get("id", "") or "").strip()
        if node_id:
            step.id = node_id

        step.completed = _to_bool(item.get("completed", False))
        step.criteria_confirmed = _to_bool(item.get("criteria_confirmed", step.criteria_confirmed))
        step.tests_confirmed = _to_bool(item.get("tests_confirmed", step.tests_confirmed))
        step.criteria_notes = _parse_string_list(item.get("criteria_notes", []))
        step.tests_notes = _parse_string_list(item.get("tests_notes", []))
        step.progress_notes = _parse_string_list(item.get("progress_notes", []))
        step.started_at = str(item.get("started_at") or "").strip() or None
        step.blocked = _to_bool(item.get("blocked", False))
        step.block_reason = str(item.get("block_reason") or "").strip()
        step.verification_outcome = str(item.get("verification_outcome", "") or "").strip()
        checks_raw = item.get("verification_checks", []) or []
        if isinstance(checks_raw, list):
            try:
                step.verification_checks = [VerificationCheck.from_dict(c) for c in checks_raw if isinstance(c, dict)]
            except Exception:
                step.verification_checks = []
        attachments_raw = item.get("attachments", []) or []
        if isinstance(attachments_raw, list):
            try:
                step.attachments = [Attachment.from_dict(a) for a in attachments_raw if isinstance(a, dict)]
            except Exception:
                step.attachments = []

        plan_raw = item.get("plan", None)
        if isinstance(plan_raw, dict):
            step.plan = _parse_plan_node(plan_raw, idx=idx)
        elif "steps" in item:
            raise StepParseError("step.steps is not supported; use step.plan.tasks[].steps")

        return step

    def _parse_plan_node(item: Any, *, idx: str) -> PlanNode:
        if not isinstance(item, dict):
            raise StepParseError(translate("ERR_JSON_ELEMENT_OBJECT", idx=idx))
        tasks_raw = item.get("tasks", [])
        if tasks_raw is None:
            tasks_raw = []
        if not isinstance(tasks_raw, list):
            raise StepParseError(translate("ERR_JSON_ELEMENT_OBJECT", idx=idx))
        tasks = [_parse_task_node(task, idx=f"{idx}.t{i}") for i, task in enumerate(tasks_raw, 1)]
        attachments_raw = item.get("attachments", []) or []
        attachments = []
        if isinstance(attachments_raw, list):
            try:
                attachments = [Attachment.from_dict(a) for a in attachments_raw if isinstance(a, dict)]
            except Exception:
                attachments = []
        plan = PlanNode(
            title=str(item.get("title", "") or ""),
            doc=str(item.get("doc", "") or ""),
            attachments=attachments,
            success_criteria=_parse_string_list(item.get("success_criteria", [])),
            tests=_parse_string_list(item.get("tests", [])),
            blockers=_parse_string_list(item.get("blockers", [])),
            criteria_confirmed=_to_bool(item.get("criteria_confirmed", False)),
            tests_confirmed=_to_bool(item.get("tests_confirmed", False)),
            criteria_auto_confirmed=_to_bool(item.get("criteria_auto_confirmed", False)),
            tests_auto_confirmed=_to_bool(item.get("tests_auto_confirmed", False)),
            criteria_notes=_parse_string_list(item.get("criteria_notes", [])),
            tests_notes=_parse_string_list(item.get("tests_notes", [])),
            steps=_parse_string_list(item.get("steps", [])),
            current=int(item.get("current", 0) or 0),
            tasks=tasks,
        )
        if not plan.tests and not plan.tests_confirmed:
            plan.tests_auto_confirmed = True
        return plan

    def _parse_task_node(item: Any, *, idx: str) -> TaskNode:
        if not isinstance(item, dict):
            raise StepParseError(translate("ERR_JSON_ELEMENT_OBJECT", idx=idx))
        title = str(item.get("title", "") or "").strip()
        if not title:
            raise StepParseError(translate("ERR_JSON_ELEMENT_TITLE", idx=idx))
        attachments_raw = item.get("attachments", []) or []
        attachments = []
        if isinstance(attachments_raw, list):
            try:
                attachments = [Attachment.from_dict(a) for a in attachments_raw if isinstance(a, dict)]
            except Exception:
                attachments = []
        task = TaskNode(
            title=title,
            status=str(item.get("status", "TODO") or "TODO"),
            priority=str(item.get("priority", "MEDIUM") or "MEDIUM"),
            description=str(item.get("description", "") or ""),
            context=str(item.get("context", "") or ""),
            attachments=attachments,
            success_criteria=_parse_string_list(item.get("success_criteria", [])),
            tests=_parse_string_list(item.get("tests", [])),
            criteria_confirmed=_to_bool(item.get("criteria_confirmed", False)),
            tests_confirmed=_to_bool(item.get("tests_confirmed", False)),
            criteria_auto_confirmed=_to_bool(item.get("criteria_auto_confirmed", False)),
            tests_auto_confirmed=_to_bool(item.get("tests_auto_confirmed", False)),
            criteria_notes=_parse_string_list(item.get("criteria_notes", [])),
            tests_notes=_parse_string_list(item.get("tests_notes", [])),
            dependencies=_parse_string_list(item.get("dependencies", [])),
            next_steps=_parse_string_list(item.get("next_steps", [])),
            problems=_parse_string_list(item.get("problems", [])),
            risks=_parse_string_list(item.get("risks", [])),
            blocked=_to_bool(item.get("blocked", False)),
            blockers=_parse_string_list(item.get("blockers", [])),
            status_manual=_to_bool(item.get("status_manual", False)),
            steps=[],
        )
        task_id = str(item.get("id", "") or "").strip()
        if task_id:
            task.id = task_id
        if not task.tests and not task.tests_confirmed:
            task.tests_auto_confirmed = True
        steps_raw = item.get("steps", [])
        if steps_raw:
            if not isinstance(steps_raw, list):
                raise StepParseError(translate("ERR_JSON_ELEMENT_STEPS", idx=idx, fallback="steps must be an array"))
            task.steps = [parse_node(ch, idx=f"{idx}.s{i}") for i, ch in enumerate(steps_raw, 1)]
        return task

    return [parse_node(item, idx=str(i)) for i, item in enumerate(data, 1)]


def parse_steps_flexible(raw: str) -> List[Step]:
    raw = raw.strip()
    if not raw:
        return []
    return parse_steps_json(raw)


def _flatten_steps(nodes: List[Step]) -> List[Step]:
    out: List[Step] = []
    for st in nodes:
        out.append(st)
        plan = getattr(st, "plan", None)
        if plan and getattr(plan, "tasks", None):
            for task in plan.tasks:
                out.extend(_flatten_steps(list(getattr(task, "steps", []) or [])))
    return out


def validate_flagship_steps(steps: List[Step]) -> Tuple[bool, List[str]]:
    """Flagship validation for steps."""
    flat = _flatten_steps(steps)
    if not flat:
        return False, [translate("ERR_TASK_NEEDS_STEPS", fallback="Task needs steps")]
    if len(flat) < 3:
        return False, [translate("ERR_STEPS_MIN", count=len(flat), fallback=f"Need at least 3 steps (got {len(flat)})")]

    all_issues: List[str] = []
    for idx, st in enumerate(flat, 1):
        valid, issues = st.is_valid_flagship()
        if not valid:
            all_issues.extend(
                [translate("ERR_STEP_PREFIX", idx=idx, issue=issue, fallback=f"{idx}: {issue}") for issue in issues]
            )

    return len(all_issues) == 0, all_issues


__all__ = [
    "StepParseError",
    "_load_input_source",
    "load_steps_source",
    "parse_steps_json",
    "parse_steps_flexible",
    "validate_flagship_steps",
]
