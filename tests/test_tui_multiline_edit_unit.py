from unittest.mock import MagicMock

import pytest

from core import TaskDetail
from core.desktop.devtools.interface.tui_app import TaskTrackerTUI


@pytest.fixture
def tui(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    tui = TaskTrackerTUI(tasks_dir=tasks_dir)
    tui.project_mode = False
    tui.detail_mode = True
    # Patch IO to keep tests deterministic.
    tui.manager.save_task = MagicMock()
    tui.load_current_list = MagicMock()
    return tui


def test_multiline_edit_preserves_newlines_and_allows_empty(tui: TaskTrackerTUI):
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo")
    tui.current_task_detail = detail

    tui.start_editing("task_contract", "", None)
    assert tui._editing_multiline is True

    tui.edit_buffer.text = "line1\nline2\n"
    tui.save_edit()
    assert detail.contract == "line1\nline2"
    assert tui.manager.save_task.called

    # Empty value is allowed for multiline fields.
    tui.start_editing("task_contract", detail.contract or "", None)
    tui.edit_buffer.text = ""
    tui.save_edit()
    assert detail.contract == ""


def test_singleline_edit_sanitizes_newlines(tui: TaskTrackerTUI):
    detail = TaskDetail(id="TASK-1", title="Root", status="TODO", domain="demo")
    tui.current_task_detail = detail

    tui.start_editing("task_title", detail.title, None)
    assert tui._editing_multiline is False

    tui.edit_buffer.text = "hello\nworld"
    tui.save_edit()
    assert detail.title == "hello world"
