#!/usr/bin/env python3
"""Public facade for apply_task Python integrations.

This module intentionally contains no CLI surface. Use:
- TUI: `apply_task tui`
- MCP: `apply_task mcp`
- GUI: see `make gui-dev` / `make gui-build`
"""

from core import Status, Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.tui_app import TaskTrackerTUI
from core.desktop.devtools.interface.tui_models import Task
from core.desktop.devtools.interface.tui_themes import DEFAULT_THEME, THEMES
from util.responsive import ResponsiveLayoutManager
from core.desktop.devtools.application.context import (
    derive_domain_explicit,
    derive_folder_explicit,
    get_last_task,
    normalize_task_id,
    resolve_task_reference,
    save_last_task,
)
from projects_sync import get_projects_sync

__all__ = [
    "Status",
    "Step",
    "TaskDetail",
    "TaskManager",
    "TaskTrackerTUI",
    "Task",
    "DEFAULT_THEME",
    "THEMES",
    "ResponsiveLayoutManager",
    "derive_domain_explicit",
    "derive_folder_explicit",
    "get_projects_sync",
    "get_last_task",
    "normalize_task_id",
    "resolve_task_reference",
    "save_last_task",
]
