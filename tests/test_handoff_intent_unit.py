"""Unit tests for handoff intent handler."""

from pathlib import Path

import pytest

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_handoff


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_handle_handoff_plan_compact_snapshot(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    plan.contract = "Goal: ship\nDone: tests green"
    plan.contract_data = {"goal": "ship", "risks": ["Vendor dependency"]}
    plan.plan_steps = ["Design", "Implement", "Verify"]
    plan.plan_current = 1
    manager.save_task(plan)

    resp = handle_handoff(manager, {"intent": "handoff", "plan": "PLAN-001", "limit": 1})
    assert resp.success is True
    result = resp.result
    assert result["focus"]["id"] == "PLAN-001"
    assert result["now"]["kind"] == "plan_step"
    assert result["done"]["count"] == 1
    assert result["remaining"]["count"] == 2
    assert "Vendor dependency" in result["risks"]


def test_handle_handoff_task_snapshot_includes_done_remaining_and_risks(manager: TaskManager):
    step_done = Step.new("Step 1", criteria=["c1"], tests=[])
    assert step_done is not None
    step_done.completed = True
    step_todo = Step.new("Step 2", criteria=["c2"], tests=[])
    assert step_todo is not None
    task = TaskDetail(
        id="TASK-001",
        title="Task",
        status="ACTIVE",
        steps=[step_done, step_todo],
        risks=["Timeline slip"],
    )
    manager.save_task(task)

    resp = handle_handoff(manager, {"intent": "handoff", "task": "TASK-001", "limit": 2})
    assert resp.success is True
    result = resp.result
    assert set(["now", "why", "verify", "next", "blockers", "open_checkpoints", "done", "remaining", "risks"]).issubset(
        result.keys()
    )
    assert result["done"]["count"] == 1
    assert result["remaining"]["count"] == 1
    assert "Timeline slip" in result["risks"]


def test_handle_handoff_budget_enforced(manager: TaskManager):
    huge_title = "X" * 5000
    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title=huge_title, status="ACTIVE", steps=[step])
    manager.save_task(task)

    resp = handle_handoff(manager, {"intent": "handoff", "task": "TASK-001", "max_chars": 1000})
    assert resp.success is True
    result = resp.result
    assert set(["now", "why", "verify", "next", "blockers", "open_checkpoints"]).issubset(result.keys())
    assert result["budget"]["truncated"] is True
    assert result["budget"]["used_chars"] <= 1000


def test_handle_handoff_invalid_id_has_recovery_and_suggestions(manager: TaskManager):
    resp = handle_handoff(manager, {"intent": "handoff", "task": "BAD/ID"})
    assert resp.success is False
    assert resp.error_code == "INVALID_ID"
    assert resp.error_recovery
    assert resp.suggestions
