#!/usr/bin/env python3
"""Unit tests for list editor integration in TaskTrackerTUI."""

from unittest.mock import MagicMock

import pytest

from core import Step, TaskDetail
from core.desktop.devtools.interface.tui_app import TaskTrackerTUI


@pytest.fixture
def tui(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    tui = TaskTrackerTUI(tasks_dir=tasks_dir)
    # Patch manager IO for deterministic unit tests.
    tui.manager.save_task = MagicMock()
    tui.manager.load_task = MagicMock()
    tui.manager.list_tasks = MagicMock()
    return tui


def _attach_detail(tui: TaskTrackerTUI, detail: TaskDetail) -> None:
    tui.project_mode = False
    tui.detail_mode = True
    tui.current_task_detail = detail
    tui.task_details_cache[detail.id] = detail
    tui._rebuild_detail_flat()
    tui.manager.load_task.return_value = detail
    tui.manager.list_tasks.return_value = [detail]


def test_list_editor_menu_options_include_task_and_subtask_lists(tui):
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo")
    detail.next_steps = ["one"]
    detail.plan_steps = ["s1", "s2"]
    detail.plan_current = 0
    detail.dependencies = ["dep"]
    detail.success_criteria = ["ok"]
    detail.problems = ["p"]
    detail.risks = ["r"]
    detail.history = ["h"]
    detail.steps = [Step(completed=False, title="Sub", success_criteria=["c1"], tests=["t1"], blockers=["b1"])]
    _attach_detail(tui, detail)

    opts = tui._list_editor_menu_options()
    assert any(o.get("scope") == "task" and o.get("key") == "plan_steps" for o in opts)
    assert any(o.get("scope") == "task" and o.get("key") == "next_steps" for o in opts)
    assert any(o.get("scope") == "task" and o.get("key") == "history" for o in opts)
    assert any(o.get("scope") == "subtask" and o.get("key") == "success_criteria" for o in opts)
    assert any(o.get("scope") == "subtask" and o.get("key") == "tests" for o in opts)
    assert any(o.get("scope") == "subtask" and o.get("key") == "blockers" for o in opts)


def test_plan_steps_space_toggles_plan_current_boundary(tui):
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo")
    detail.plan_steps = ["one", "two", "three"]
    detail.plan_current = 0
    _attach_detail(tui, detail)

    tui.open_list_editor()
    opts = tui._list_editor_menu_options()
    idx = next(i for i, o in enumerate(opts) if o.get("scope") == "task" and o.get("key") == "plan_steps")
    tui.list_editor_selected_index = idx
    tui.activate_list_editor()
    assert tui.list_editor_stage == "list"

    tui.list_editor_selected_index = 0
    tui._list_editor_toggle_plan_steps_current()
    assert detail.plan_current == 1

    tui._list_editor_toggle_plan_steps_current()
    assert detail.plan_current == 0

    tui.list_editor_selected_index = 1
    tui._list_editor_toggle_plan_steps_current()
    assert detail.plan_current == 2


def test_task_list_editor_add_edit_delete_persists(tui):
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo")
    detail.next_steps = ["one"]
    _attach_detail(tui, detail)

    # Open list editor and select "Task: Next steps".
    tui.open_list_editor()
    assert tui.list_editor_mode is True
    assert tui.list_editor_stage == "menu"

    opts = tui._list_editor_menu_options()
    tui.list_editor_selected_index = next(i for i, o in enumerate(opts) if o.get("scope") == "task" and o.get("key") == "next_steps")
    tui.activate_list_editor()
    assert tui.list_editor_stage == "list"
    assert tui.list_editor_target and tui.list_editor_target.get("key") == "next_steps"

    # Add item after selection.
    tui.list_editor_selected_index = 0
    tui.add_list_editor_item()
    assert tui.editing_mode is True
    assert tui.edit_context == "list_editor_item_add"
    tui.edit_buffer.text = "two"
    tui.save_edit()

    assert detail.next_steps == ["one", "two"]
    assert tui.manager.save_task.called

    # Edit the second item.
    tui.list_editor_selected_index = 1
    tui.edit_list_editor_item()
    assert tui.edit_context == "list_editor_item_edit"
    tui.edit_buffer.text = "two!"
    tui.save_edit()
    assert detail.next_steps == ["one", "two!"]

    # Delete the edited item via confirmation.
    tui.list_editor_selected_index = 1
    tui.confirm_delete_list_editor_item()
    assert tui.confirm_mode is True
    tui._confirm_accept()
    assert tui.confirm_mode is False
    assert detail.next_steps == ["one"]


def test_subtask_list_editor_add_persists(tui):
    st = Step(completed=False, title="Sub", success_criteria=["c1"], tests=["t1"], blockers=["b1"])
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo", steps=[st])
    _attach_detail(tui, detail)

    tui.open_list_editor()
    opts = tui._list_editor_menu_options()
    idx = next(i for i, o in enumerate(opts) if o.get("scope") == "subtask" and o.get("key") == "success_criteria")
    tui.list_editor_selected_index = idx
    tui.activate_list_editor()
    assert tui.list_editor_stage == "list"
    assert tui.list_editor_target and tui.list_editor_target.get("scope") == "subtask"

    tui.list_editor_selected_index = 0
    tui.add_list_editor_item()
    tui.edit_buffer.text = "c2"
    tui.save_edit()
    assert st.success_criteria == ["c1", "c2"]
