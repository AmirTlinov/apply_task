"""Unit tests for edit intent handler (task-level Notes/Meta updates)."""

from pathlib import Path

import pytest

from core import TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_edit


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_handle_edit_updates_notes_and_meta(manager: TaskManager):
    task = TaskDetail(
        id="TASK-001",
        title="Test",
        status="TODO",
        domain="d1",
        description="old",
        context="old ctx",
        tags=["a"],
        depends_on=["TASK-002"],
    )
    manager.save_task(task)

    resp = handle_edit(
        manager,
        {
            "intent": "edit",
            "task": "TASK-001",
            "description": "",
            "context": "new ctx",
            "tags": [],
            "priority": "HIGH",
            "depends_on": [],
            "new_domain": "d2",
        },
    )

    assert resp.success is True
    assert resp.intent == "edit"
    assert "task" in resp.result
    assert set(resp.result.get("updated_fields", [])) >= {"description", "context", "tags", "priority", "depends_on", "domain"}

    moved = manager.load_task("TASK-001", "d2")
    assert moved is not None
    assert moved.domain == "d2"
    assert moved.description == ""
    assert moved.context == "new ctx"
    assert moved.tags == []
    assert moved.depends_on == []
    assert moved.priority == "HIGH"

    # Old file should be removed (move, not copy)
    assert not (manager.tasks_dir / "d1" / "TASK-001.task").exists()


def test_handle_edit_rejects_missing_deps(manager: TaskManager):
    task = TaskDetail(id="TASK-001", title="Test", status="TODO")
    manager.save_task(task)

    resp = handle_edit(
        manager,
        {
            "intent": "edit",
            "task": "TASK-001",
            "depends_on": ["TASK-999"],
        },
    )

    assert resp.success is False
    assert resp.intent == "edit"
    assert resp.error_code in {"INVALID_DEPENDENCIES", "CIRCULAR_DEPENDENCY"}
    assert isinstance(resp.result, dict)


def test_handle_edit_requires_fields(manager: TaskManager):
    task = TaskDetail(id="TASK-001", title="Test", status="TODO")
    manager.save_task(task)

    resp = handle_edit(manager, {"intent": "edit", "task": "TASK-001"})
    assert resp.success is False
    assert resp.error_code == "NO_FIELDS"
