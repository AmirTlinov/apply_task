"""Helpers to load and filter tasks for TaskTrackerTUI."""

from typing import List, Tuple

from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.i18n import translate
from core.desktop.devtools.interface.cli_commands import CliDeps
from core import TaskDetail


def load_tasks_snapshot(manager: TaskManager, domain_filter: str, current_filter) -> List[TaskDetail]:
    items = manager.list_tasks(domain_filter)
    if current_filter:
        items = [t for t in items if t.status.name == current_filter.value[0]]
    items.sort(key=lambda t: (t.status.value, t.progress), reverse=False)
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


__all__ = ["load_tasks_snapshot", "load_tasks_with_state"]
