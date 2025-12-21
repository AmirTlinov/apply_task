#!/usr/bin/env python3
"""Unit tests for TUI command palette and plan hygiene helpers."""

from pathlib import Path

import pytest

from core.desktop.devtools.interface.tui_app import TaskTrackerTUI


@pytest.fixture
def tui(tmp_path: Path) -> TaskTrackerTUI:
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    projects_root = tmp_path / "projects_root"
    projects_root.mkdir()
    # Local mode: start inside a project (no project picker) so palette is usable.
    tui = TaskTrackerTUI(tasks_dir=tasks_dir, projects_root=projects_root, use_global=False)
    # Keep tests quiet/fast.
    tui.force_render = lambda: None
    return tui


def _create_task(tui: TaskTrackerTUI, title: str) -> str:
    plan = tui.manager.create_plan("Plan for palette")
    tui.manager.save_task(plan, skip_sync=True)
    task = tui.manager.create_task(title=title, status="TODO", parent=plan.id)
    tui.manager.save_task(task, skip_sync=True)
    return task.id


def test_command_palette_tags_add_remove_set(tui: TaskTrackerTUI):
    task_id = _create_task(tui, "Palette tags")
    # Enter tasks view for the plan that owns the task.
    tui.load_plans(skip_sync=True)
    tui.selected_index = 0
    tui.open_tasks_for_plan(tui.tasks[0].detail)
    tui.selected_index = 0

    tui._run_command_palette("tag +ux +mcp")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert sorted(task.tags) == ["mcp", "ux"]

    tui._run_command_palette("tag -mcp")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.tags == ["ux"]

    tui._run_command_palette("tag =a,b")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.tags == ["a", "b"]


def test_command_palette_priority_cycle_and_set(tui: TaskTrackerTUI):
    task_id = _create_task(tui, "Palette prio")
    tui.load_plans(skip_sync=True)
    tui.selected_index = 0
    tui.open_tasks_for_plan(tui.tasks[0].detail)
    tui.selected_index = 0

    tui._run_command_palette("prio")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.priority == "HIGH"

    tui._run_command_palette("prio LOW")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.priority == "LOW"


def test_command_palette_dep_add_remove_set(tui: TaskTrackerTUI):
    task_id = _create_task(tui, "Palette deps A")
    dep_id = _create_task(tui, "Palette deps B")
    tui.load_plans(skip_sync=True)
    tui.selected_index = 0
    tui.open_tasks_for_plan(tui.tasks[0].detail)
    tui.selected_index = 0

    tui._run_command_palette(f"dep +{dep_id}")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.depends_on == [dep_id]

    tui._run_command_palette(f"dep -{dep_id}")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.depends_on == []

    tui._run_command_palette(f"dep ={dep_id}")
    task = tui.manager.load_task(task_id, "", skip_sync=True)
    assert task is not None
    assert task.depends_on == [dep_id]


def test_command_palette_plan_sanitize_moves_contract_and_checklist(tui: TaskTrackerTUI):
    plan = tui.manager.create_plan("Palette plan sanitize")
    # Use ### headings so content stays inside plan_doc and sanitizer can detect boundaries.
    plan.plan_doc = (
        "### Contract\n"
        "Contract v1\n\n"
        "### Steps\n"
        "- [ ] First item\n"
        "- [x] Second item\n"
        "- [ ] Third item\n"
    )
    tui.manager.save_task(plan, skip_sync=True)

    tui.load_plans(skip_sync=True)
    tui.selected_index = 0
    tui._run_command_palette("plan sanitize")

    updated = tui.manager.load_task(plan.id, "", skip_sync=True)
    assert updated is not None
    assert "Contract v1" in (updated.contract or "")
    assert "Contract" not in (updated.plan_doc or "")
    assert "Steps" not in (updated.plan_doc or "")
    assert (tui.manager.tasks_dir / ".snapshots").exists()
    assert list(updated.plan_steps) == ["First item", "Second item", "Third item"]


def test_help_footer_height_is_sticky(tui: TaskTrackerTUI):
    tui.help_visible = True
    tui._set_footer_height(0)
    assert tui.footer_height == 12
    assert getattr(tui, "_footer_height_after_help", None) == 0
