"""Unit tests for radar intent handler."""

from pathlib import Path

import pytest

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_radar


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_handle_radar_plan_compact_snapshot(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    plan.contract = "Goal: ship\nDone: tests green"
    plan.plan_steps = ["Design", "Implement", "Verify"]
    plan.plan_current = 1
    manager.save_task(plan)

    resp = handle_radar(manager, {"intent": "radar", "plan": "PLAN-001", "limit": 1})
    assert resp.success is True
    result = resp.result
    assert result["focus"]["id"] == "PLAN-001"
    assert result["now"]["kind"] == "plan_step"
    assert result["why"]["plan_id"] == "PLAN-001"
    assert isinstance(result["next"], list)


def test_handle_radar_task_includes_now_verify_and_deps(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    plan.contract = "Goal: ship"
    manager.save_task(plan)

    dep = TaskDetail(id="TASK-002", title="Dep", status="TODO", parent="PLAN-001")
    manager.save_task(dep)

    step1 = Step.new("Step 1", criteria=["c1"], tests=["t1"])
    assert step1 is not None
    step2 = Step.new("Step 2", criteria=["c2"], tests=[])
    assert step2 is not None
    task = TaskDetail(
        id="TASK-001",
        title="Task",
        status="ACTIVE",
        parent="PLAN-001",
        steps=[step1, step2],
        depends_on=["TASK-002"],
    )
    manager.save_task(task)

    resp = handle_radar(manager, {"intent": "radar", "task": "TASK-001", "limit": 2})
    assert resp.success is True
    result = resp.result
    assert result["focus"]["id"] == "TASK-001"
    assert result["now"]["kind"] == "step"
    assert "verify" in result
    assert "open_checkpoints" in result
    assert result["blockers"]["depends_on"] == ["TASK-002"]
    assert result["blockers"]["unresolved_depends_on"] == ["TASK-002"]

