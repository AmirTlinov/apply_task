#!/usr/bin/env python3
"""TUI data models and constants."""

from dataclasses import dataclass
from typing import Optional

from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEvent

from core import Status, TaskDetail


@dataclass
class Task:
    """TUI task model."""
    name: str
    status: Status
    description: str
    category: str
    completed: bool = False
    task_file: Optional[str] = None
    progress: int = 0
    children_count: int = 0
    children_completed: int = 0
    id: Optional[str] = None
    parent: Optional[str] = None
    detail: Optional[TaskDetail] = None
    domain: str = ""
    phase: str = ""
    component: str = ""
    blocked: bool = False


CHECKLIST_SECTIONS = [
    (
        "plan",
        ["plan", "break", "шаг"],
        "Plan: break work into atomic steps with measurable outcomes",
        ["step", "milestone", "outcome", "scope", "estimate"],
    ),
    (
        "validation",
        ["test", "lint", "вали", "qa"],
        "Validation plan: tests/linters per step and commit checkpoints",
        ["test", "pytest", "unit", "integration", "lint", "coverage", "commit", "checkpoint"],
    ),
    (
        "risks",
        ["risk", "dependency", "риск", "завис", "блок"],
        "Risk scan: failures, dependencies, bottlenecks",
        ["risk", "dependency", "blocker", "bottleneck", "assumption"],
    ),
    (
        "readiness",
        ["readiness", "ready", "done", "criteria", "dod", "готов", "metric"],
        "Readiness criteria: DoD, coverage/perf metrics, expected behavior",
        ["DoD", "definition", "coverage", "perf", "metric", "acceptance", "criteria"],
    ),
    (
        "execute",
        ["execute", "implement", "исполн", "build"],
        "Execute steps with per-step validation and record results",
        ["implement", "code", "wire", "build", "validate"],
    ),
    (
        "final",
        ["final", "full", "release", "финаль", "итог"],
        "Final verification: full tests/linters, metrics check, release/commit prep",
        ["regression", "full", "release", "report", "metrics", "handoff"],
    ),
]


class InteractiveFormattedTextControl(FormattedTextControl):
    """FormattedTextControl with external mouse handler support."""

    def __init__(self, *args, mouse_handler=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._external_mouse_handler = mouse_handler

    def mouse_handler(self, mouse_event: MouseEvent):
        if self._external_mouse_handler:
            result = self._external_mouse_handler(mouse_event)
            if result is not NotImplemented:
                return result
        return super().mouse_handler(mouse_event)
