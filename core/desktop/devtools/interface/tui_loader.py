"""Helpers to load and filter steps for the TUI."""

from typing import Callable, List, Tuple

from core.desktop.devtools.application.task_manager import TaskManager, _flatten_steps
from core.desktop.devtools.interface.i18n import translate
from core import Status, TaskDetail
from core.status import normalize_status_code, status_label


_STATUS_SORT_ORDER = {"ACTIVE": 0, "TODO": 1, "DONE": 2}


def _status_token(task: object) -> str:
    raw = getattr(task, "status", "")
    if isinstance(raw, Status):
        return raw.value[0]
    if isinstance(raw, str):
        return raw.strip().upper()
    if hasattr(raw, "name"):
        return str(getattr(raw, "name")).strip().upper()
    return str(raw).strip().upper()


def _status_code_safe(raw: str) -> str:
    try:
        return normalize_status_code(raw)
    except ValueError:
        return raw


def load_tasks_snapshot(manager: TaskManager, domain_filter: str, current_filter) -> List[TaskDetail]:
    items = manager.list_tasks(domain_filter)
    if current_filter:
        wanted_raw = current_filter.value[0] if hasattr(current_filter, "value") else str(current_filter)
        wanted = _status_code_safe(str(wanted_raw).strip().upper())
        items = [
            t
            for t in items
            if _status_code_safe(status_label(_status_token(t))) == wanted
        ]

    def _key(task: TaskDetail) -> tuple[int, int]:
        code = _status_code_safe(status_label(_status_token(task)))
        order = _STATUS_SORT_ORDER.get(code, 99)
        progress = int(getattr(task, "progress", 0) or 0)
        return order, progress

    items.sort(key=_key, reverse=False)
    return items


def load_tasks_with_state(tui) -> Tuple[List, str]:
    """Loads tasks for TUI, returns (items, message)."""
    manager = getattr(tui, "manager", TaskManager())
    domain = getattr(tui, "domain_filter", "") or ""
    try:
        items = load_tasks_snapshot(manager, domain, getattr(tui, "current_filter", None))
    except Exception as exc:
        return [], translate("ERR_TASK_LIST_FAILED", error=str(exc))
    if getattr(tui, "current_filter", None):
        label = tui.current_filter.value[0]
        message = translate("FILTER_APPLIED", value=label)
    else:
        message = ""
    return items, message


def apply_context_filters(details: List[TaskDetail], phase_filter: str, component_filter: str) -> List[TaskDetail]:
    filtered = details
    if phase_filter:
        filtered = [d for d in filtered if d.phase == phase_filter]
    if component_filter:
        filtered = [d for d in filtered if d.component == component_filter]
    return filtered


def build_task_models(details: List[TaskDetail], factory: Callable) -> List:
    tasks = []
    for det in details:
        calc_progress = det.calculate_progress() if hasattr(det, "calculate_progress") else int(getattr(det, "progress", 0) or 0)
        blocked = bool(getattr(det, "blocked", False))
        derived_status = Status.DONE if calc_progress == 100 and not blocked else Status.from_string(_status_token(det))
        steps = getattr(det, "steps", []) or []
        flat = list(_flatten_steps(list(steps)))
        steps_total = len(flat)
        steps_completed = sum(1 for _, st in flat if getattr(st, "completed", False))
        tasks.append(factory(det, derived_status, calc_progress, steps_completed, steps_total))
    return tasks


def select_index_after_load(tasks: List, preserve_selection: bool, selected_task_file: str) -> int:
    if preserve_selection and selected_task_file:
        for idx, t in enumerate(tasks):
            if getattr(t, "task_file", None) == selected_task_file:
                return idx
    return 0


__all__ = [
    "load_tasks_snapshot",
    "load_tasks_with_state",
    "apply_context_filters",
    "build_task_models",
    "select_index_after_load",
]
