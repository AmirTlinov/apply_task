"""Unit tests for mirror intent handler."""

from pathlib import Path

import pytest

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_mirror


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_handle_mirror_task_steps(manager: TaskManager):
    step1 = Step.new("Step one", criteria=["c1"], tests=["t1"])
    step2 = Step.new("Step two", criteria=["c2"], tests=[])
    assert step1 is not None
    assert step2 is not None
    step2.criteria_confirmed = True

    task = TaskDetail(
        id="TASK-001",
        title="Mirror task",
        status="TODO",
        steps=[step1, step2],
    )
    manager.save_task(task)

    resp = handle_mirror(manager, {"intent": "mirror", "task": "TASK-001"})
    assert resp.success is True
    items = resp.result.get("items", [])
    assert [item.get("path") for item in items] == ["s:0", "s:1"]
    assert sum(1 for item in items if item.get("queue_status") == "in_progress") == 1


def test_handle_mirror_plan_tasks(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan)
    task1 = TaskDetail(id="TASK-010", title="T1", status="TODO", parent="PLAN-001")
    task2 = TaskDetail(id="TASK-011", title="T2", status="DONE", parent="PLAN-001")
    manager.save_task(task1)
    manager.save_task(task2)

    resp = handle_mirror(manager, {"intent": "mirror", "plan": "PLAN-001"})
    assert resp.success is True
    items = resp.result.get("items", [])
    assert [item.get("task_id") for item in items] == ["TASK-010", "TASK-011"]
    assert resp.result.get("summary", {}).get("in_progress", 0) == 1
