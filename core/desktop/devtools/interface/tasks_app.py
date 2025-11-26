#!/usr/bin/env python3
"""
tasks.py — flagship task manager (single-file CLI/TUI).

All tasks live under .tasks/ (one .task file per task).

This is now a thin facade that delegates to specialized modules.
"""

import argparse
import sys
from pathlib import Path

from core.desktop.devtools.interface.cli_parser import build_parser as build_cli_parser
from core.desktop.devtools.interface.constants import AI_HELP
from core.desktop.devtools.interface.cli_automation import AUTOMATION_TMP

# Import all command functions
from .cli_commands_core import (
    cmd_list,
    cmd_show,
    cmd_create,
    cmd_smart_create,
    cmd_create_guided,
    cmd_status_set,
    cmd_analyze,
    cmd_next,
    cmd_add_subtask,
    cmd_add_dependency,
    cmd_subtask,
    cmd_bulk,
    cmd_checkpoint,
    cmd_move,
    cmd_clean,
    cmd_edit,
    cmd_lint,
)
from .cli_projects import (
    cmd_projects_auth,
    cmd_projects_webhook,
    cmd_projects_webhook_serve,
    cmd_projects_sync_cli,
    cmd_projects_status,
    cmd_projects_autosync,
    cmd_projects_workers,
)
from .cli_automation import (
    cmd_automation_task_template,
    cmd_automation_task_create,
    cmd_automation_projects_health,
    cmd_automation_health,
    cmd_automation_checkpoint,
)
from .cli_templates import cmd_template_subtasks
from .cli_ai import cmd_ai
from .mcp_server import run_stdio_server as _mcp_run
from .tui_app import cmd_tui, TaskTrackerTUI
from .tui_themes import THEMES, DEFAULT_THEME
from .tui_models import Task, CLI_DEPS, CHECKLIST_SECTIONS, InteractiveFormattedTextControl
from core.desktop.devtools.interface.cli_macros_extended import cmd_update, cmd_ok, cmd_note, cmd_suggest, cmd_quick

# Additional exports for backward compatibility and tests
from core import Status, SubTask, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.application.context import (
    derive_domain_explicit,
    derive_folder_explicit,
    save_last_task,
    get_last_task,
    resolve_task_reference,
    normalize_task_id,
)
from util.responsive import ResponsiveLayoutManager
from .cli_automation import _automation_template_payload
from infrastructure.task_file_parser import TaskFileParser
from projects_sync import get_projects_sync
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import get_user_token
from .projects_integration import validate_pat_token_http

# Re-export for backward compatibility
__all__ = [
    # Commands
    "cmd_list",
    "cmd_show",
    "cmd_create",
    "cmd_smart_create",
    "cmd_create_guided",
    "cmd_status_set",
    "cmd_analyze",
    "cmd_next",
    "cmd_add_subtask",
    "cmd_add_dependency",
    "cmd_subtask",
    "cmd_bulk",
    "cmd_checkpoint",
    "cmd_move",
    "cmd_clean",
    "cmd_edit",
    "cmd_lint",
    "cmd_projects_auth",
    "cmd_projects_webhook",
    "cmd_projects_webhook_serve",
    "cmd_projects_sync_cli",
    "cmd_projects_status",
    "cmd_projects_autosync",
    "cmd_projects_workers",
    "cmd_automation_task_template",
    "cmd_automation_task_create",
    "cmd_automation_projects_health",
    "cmd_automation_health",
    "cmd_automation_checkpoint",
    "cmd_template_subtasks",
    "cmd_ai",
    "cmd_mcp",
    "cmd_tui",
    "cmd_update",
    "cmd_ok",
    "cmd_note",
    "cmd_suggest",
    "cmd_quick",
    # Models and constants
    "Task",
    "TaskTrackerTUI",
    "CLI_DEPS",
    "CHECKLIST_SECTIONS",
    "InteractiveFormattedTextControl",
    "THEMES",
    "DEFAULT_THEME",
    "AUTOMATION_TMP",
    # Additional exports for backward compatibility
    "Status",
    "SubTask",
    "TaskDetail",
    "TaskManager",
    "derive_domain_explicit",
    "derive_folder_explicit",
    "save_last_task",
    "get_last_task",
    "resolve_task_reference",
    "normalize_task_id",
    "ResponsiveLayoutManager",
    "_automation_template_payload",
    "TaskFileParser",
    "get_projects_sync",
    "ThreadPoolExecutor",
    "as_completed",
    "get_user_token",
    "validate_pat_token_http",
]


def cmd_mcp(args) -> int:
    """Запустить MCP stdio сервер."""
    from pathlib import Path
    tasks_dir = Path(args.tasks_dir) if getattr(args, "tasks_dir", None) else None
    use_global = not getattr(args, "local", False)
    _mcp_run(tasks_dir=tasks_dir, use_global=use_global)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    return build_cli_parser(commands=sys.modules[__name__], themes=THEMES, default_theme=DEFAULT_THEME, automation_tmp=AUTOMATION_TMP)


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    if args.command == "help":
        parser.print_help()
        print("\nКонтекст: --domain или phase/component формируют путь; .last хранит TASK@domain.")
        print("\nПравила для ИИ-агентов:\n")
        print(AI_HELP.strip())
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
