"""Shared edit semantics for step-level Notes/Meta updates.

This module centralizes validation and normalization for partial root-step edits used by
MCP and UI adapters (TUI/GUI). It intentionally does NOT touch Contract/Plan/Steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Tuple

from core import StepEvent, validate_dependencies, build_dependency_graph
from core import TaskDetail
from core.desktop.devtools.application.context import normalize_task_id
from core.desktop.devtools.application.plan_semantics import normalize_tag


_DEP_ID_PATTERN = re.compile(r"^TASK-\d+$")
_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}


@dataclass(frozen=True)
class EditFailure:
    code: str
    message: str
    field_name: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EditOutcome:
    step: TaskDetail
    updated_fields: List[str]
    target_domain: Optional[str] = None


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _parse_tags(raw: Any) -> Tuple[Optional[List[str]], Optional[EditFailure]]:
    if raw is None:
        return None, None
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
    elif isinstance(raw, list):
        parts = [str(p).strip() for p in raw]
    else:
        return None, EditFailure(code="INVALID_TAGS", message="Field 'tags' must be a string or a list of strings", field_name="tags")
    normalized = [normalize_tag(p) for p in parts if normalize_tag(p)]
    return _dedupe_preserve_order(normalized), None


def _parse_priority(raw: Any) -> Tuple[Optional[str], Optional[EditFailure]]:
    if raw is None:
        return None, None
    value = str(raw).strip().upper()
    # UI / legacy aliases.
    if value == "NORMAL":
        value = "MEDIUM"
    if value == "CRITICAL":
        value = "HIGH"
    if value not in _PRIORITIES:
        return None, EditFailure(
            code="INVALID_PRIORITY",
            message="Field 'priority' must be one of: LOW, MEDIUM, HIGH",
            field_name="priority",
            payload={"expected": "LOW|MEDIUM|HIGH", "got": str(raw)},
        )
    return value, None


def _parse_dep_list(raw: Any) -> Tuple[Optional[List[str]], Optional[EditFailure]]:
    if raw is None:
        return None, None
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
    elif isinstance(raw, list):
        parts = [str(p).strip() for p in raw]
    else:
        return None, EditFailure(code="INVALID_DEPENDENCIES", message="depends_on must be a string or a list of strings", field_name="depends_on")
    out: List[str] = []
    for item in parts:
        if not item:
            continue
        try:
            dep_id = normalize_task_id(item)
        except Exception:
            dep_id = item.strip().upper()
        out.append(dep_id)
    out = _dedupe_preserve_order(out)
    for dep_id in out:
        if not _DEP_ID_PATTERN.match(dep_id):
            return None, EditFailure(code="INVALID_DEPENDENCY_ID", message=f"Invalid dependency id: {dep_id}", field_name="depends_on")
    return out, None


def validate_depends_on_for_step(manager, step_id: str, new_deps: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[EditFailure]]:
    """Validate a depends_on replacement/addition against existing steps and cycles.

    Returns:
        (payload, error) where payload is a recovery hint (errors/cycle) for UI/AI.
    """
    if not new_deps:
        return None, None
    all_tasks = manager.list_all_tasks()
    existing_ids = {t.id for t in all_tasks}
    dep_graph = build_dependency_graph([(t.id, t.depends_on) for t in all_tasks if t.id != step_id])
    errors, cycle = validate_dependencies(step_id, new_deps, existing_ids, dep_graph)
    if errors:
        payload = {"errors": [str(e) for e in errors]}
        return payload, EditFailure(code="INVALID_DEPENDENCIES", message="Invalid dependencies", field_name="depends_on", payload=payload)
    if cycle:
        payload = {"cycle": cycle}
        return payload, EditFailure(code="CIRCULAR_DEPENDENCY", message="Circular dependency detected", field_name="depends_on", payload=payload)
    return None, None


def apply_step_edit(step: TaskDetail, manager, patch: Dict[str, Any]) -> Tuple[Optional[EditOutcome], Optional[EditFailure]]:
    """Apply a partial Notes/Meta edit to a TaskDetail (no persistence).

    Accepted keys (partial update):
      - description, context, tags, priority, phase, component
      - depends_on (replace), add_dep, remove_dep
      - new_domain (move)
    """
    sentinel = object()
    updated_fields: List[str] = []

    raw_description = patch.get("description", sentinel)
    raw_context = patch.get("context", sentinel)
    raw_tags = patch.get("tags", sentinel)
    raw_priority = patch.get("priority", sentinel)
    raw_phase = patch.get("phase", sentinel)
    raw_component = patch.get("component", sentinel)
    raw_depends_on = patch.get("depends_on", sentinel)
    raw_add_dep = patch.get("add_dep", sentinel)
    raw_remove_dep = patch.get("remove_dep", sentinel)
    raw_new_domain = patch.get("new_domain", sentinel)

    # Pre-parse/validate fields that can fail without mutating the step.
    parsed_tags: Optional[List[str]] = None
    parsed_priority: Optional[str] = None
    parsed_depends_on: Optional[List[str]] = None
    parsed_add_dep: Optional[str] = None
    parsed_remove_dep: Optional[str] = None
    target_domain: Optional[str] = None

    if raw_tags is not sentinel and raw_tags is not None:
        parsed_tags, err = _parse_tags(raw_tags)
        if err:
            return None, err

    if raw_priority is not sentinel and raw_priority is not None:
        parsed_priority, err = _parse_priority(raw_priority)
        if err:
            return None, err

    if raw_depends_on is not sentinel and raw_depends_on is not None:
        parsed_depends_on, err = _parse_dep_list(raw_depends_on)
        if err:
            return None, err

    if raw_add_dep is not sentinel and raw_add_dep is not None:
        try:
            parsed_add_dep = normalize_task_id(str(raw_add_dep).strip())
        except Exception:
            parsed_add_dep = str(raw_add_dep).strip().upper()
        if parsed_add_dep and not _DEP_ID_PATTERN.match(parsed_add_dep):
            return None, EditFailure(
                code="INVALID_DEPENDENCY_ID",
                message=f"Invalid dependency id: {parsed_add_dep}",
                field_name="depends_on",
            )

    if raw_remove_dep is not sentinel and raw_remove_dep is not None:
        try:
            parsed_remove_dep = normalize_task_id(str(raw_remove_dep).strip())
        except Exception:
            parsed_remove_dep = str(raw_remove_dep).strip().upper()
        if parsed_remove_dep and not _DEP_ID_PATTERN.match(parsed_remove_dep):
            return None, EditFailure(
                code="INVALID_DEPENDENCY_ID",
                message=f"Invalid dependency id: {parsed_remove_dep}",
                field_name="depends_on",
            )

    if raw_new_domain is not sentinel and raw_new_domain is not None:
        try:
            target_domain = manager.sanitize_domain(str(raw_new_domain))
        except Exception as exc:
            return None, EditFailure(code="INVALID_DOMAIN", message=str(exc), field_name="new_domain")

    # Dependencies: validate final result before mutating.
    dep_events: List[StepEvent] = []
    final_deps = list(getattr(step, "depends_on", []) or [])

    if parsed_depends_on is not None:
        _, err = validate_depends_on_for_step(manager, step.id, parsed_depends_on)
        if err:
            return None, err
        old = set(final_deps)
        new = set(parsed_depends_on)
        for dep_id in old - new:
            dep_events.append(StepEvent.dependency_resolved(dep_id))
        for dep_id in new - old:
            dep_events.append(StepEvent.dependency_added(dep_id))
        final_deps = list(parsed_depends_on)
        updated_fields.append("depends_on")

    if parsed_add_dep:
        if parsed_add_dep not in final_deps:
            test_deps = final_deps + [parsed_add_dep]
            _, err = validate_depends_on_for_step(manager, step.id, test_deps)
            if err:
                return None, err
            final_deps.append(parsed_add_dep)
            dep_events.append(StepEvent.dependency_added(parsed_add_dep))
            updated_fields.append("depends_on")

    if parsed_remove_dep:
        if parsed_remove_dep in final_deps:
            final_deps = [d for d in final_deps if d != parsed_remove_dep]
            dep_events.append(StepEvent.dependency_resolved(parsed_remove_dep))
            updated_fields.append("depends_on")

    # Apply safe updates.
    if raw_description is not sentinel and raw_description is not None:
        step.description = str(raw_description)
        updated_fields.append("description")

    if raw_context is not sentinel and raw_context is not None:
        step.context = str(raw_context)
        updated_fields.append("context")

    if raw_phase is not sentinel and raw_phase is not None:
        step.phase = str(raw_phase).strip()
        updated_fields.append("phase")

    if raw_component is not sentinel and raw_component is not None:
        step.component = str(raw_component).strip()
        updated_fields.append("component")

    if parsed_tags is not None:
        step.tags = list(parsed_tags)
        updated_fields.append("tags")

    if parsed_priority is not None:
        step.priority = parsed_priority
        updated_fields.append("priority")

    if final_deps != list(getattr(step, "depends_on", []) or []):
        step.depends_on = list(final_deps)

    if dep_events:
        step.events.extend(dep_events)

    if target_domain is not None:
        updated_fields.append("domain")

    updated_fields = _dedupe_preserve_order(updated_fields)
    if not updated_fields:
        return None, EditFailure(code="NO_FIELDS", message="No editable fields provided")

    return EditOutcome(step=step, updated_fields=updated_fields, target_domain=target_domain), None


def persist_step_edit(manager, step: TaskDetail, *, target_domain: Optional[str] = None) -> Tuple[bool, Optional[EditFailure]]:
    """Persist an edited task and optionally move it to a new domain (best-effort)."""
    original_domain = getattr(step, "domain", "") or ""
    manager.save_task(step)
    if target_domain is not None and target_domain != original_domain:
        moved = bool(manager.move_task(step.id, target_domain))
        if not moved:
            return False, EditFailure(code="MOVE_FAILED", message="Failed to move step to new domain", field_name="new_domain")
        step.domain = target_domain
    return True, None


__all__ = [
    "EditFailure",
    "EditOutcome",
    "apply_step_edit",
    "persist_step_edit",
    "validate_depends_on_for_step",
]
