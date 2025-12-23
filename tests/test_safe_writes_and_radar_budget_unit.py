"""Unit tests for safe writes (expected_target) and radar budget enforcement."""

from pathlib import Path

import pytest

from core import Step, TaskDetail
from core.desktop.devtools.application.context import save_last_task
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_radar, process_intent


@pytest.fixture
def manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TaskManager:
    # Ensure focus pointer (.last) is written inside the tmp_path, not the repo root.
    monkeypatch.setattr("core.desktop.devtools.application.context.resolve_project_root", lambda: tmp_path)
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_strict_targeting_requires_expected_target_id_when_using_focus(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title="Task", status="TODO", parent="PLAN-001", steps=[step])
    manager.save_task(task, skip_sync=True)

    save_last_task("TASK-001")
    resp = process_intent(manager, {"intent": "note", "path": "s:0", "note": "x", "strict_targeting": True})
    assert resp.success is False
    assert resp.error_code == "STRICT_TARGETING_REQUIRES_EXPECTED_TARGET_ID"
    assert resp.context.get("target_resolution", {}).get("source") == "focus"


def test_expected_target_mismatch_fails_fast(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title="Task", status="TODO", parent="PLAN-001", steps=[step])
    manager.save_task(task, skip_sync=True)

    save_last_task("TASK-001")
    resp = process_intent(
        manager,
        {"intent": "note", "path": "s:0", "note": "x", "strict_targeting": True, "expected_target_id": "TASK-999"},
    )
    assert resp.success is False
    assert resp.error_code == "EXPECTED_TARGET_MISMATCH"
    assert resp.context.get("target_resolution", {}).get("source") == "focus"


def test_strict_writes_alias_requires_expected_target(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title="Task", status="TODO", parent="PLAN-001", steps=[step])
    manager.save_task(task, skip_sync=True)

    save_last_task("TASK-001")
    resp = process_intent(manager, {"intent": "note", "path": "s:0", "note": "x", "strict_writes": True})
    assert resp.success is False
    assert resp.error_code == "STRICT_TARGETING_REQUIRES_EXPECTED_TARGET_ID"


def test_auto_strict_writes_requires_expected_target_when_multiple_active(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step1 = Step.new("Step 1", criteria=["c"], tests=["t"])
    assert step1 is not None
    task1 = TaskDetail(id="TASK-001", title="Task 1", status="ACTIVE", parent="PLAN-001", steps=[step1])
    manager.save_task(task1, skip_sync=True)

    step2 = Step.new("Step 2", criteria=["c"], tests=["t"])
    assert step2 is not None
    task2 = TaskDetail(id="TASK-002", title="Task 2", status="ACTIVE", parent="PLAN-001", steps=[step2])
    manager.save_task(task2, skip_sync=True)

    save_last_task("TASK-001")
    resp = process_intent(manager, {"intent": "note", "path": "s:0", "note": "x"})
    assert resp.success is False
    assert resp.error_code == "STRICT_TARGETING_REQUIRES_EXPECTED_TARGET_ID"
    assert resp.context.get("strict_writes_auto") is True
    assert resp.context.get("strict_writes_active_count") == 2


def test_auto_strict_writes_allows_explicit_target(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step1 = Step.new("Step 1", criteria=["c"], tests=["t"])
    assert step1 is not None
    task1 = TaskDetail(id="TASK-001", title="Task 1", status="ACTIVE", parent="PLAN-001", steps=[step1])
    manager.save_task(task1, skip_sync=True)

    step2 = Step.new("Step 2", criteria=["c"], tests=["t"])
    assert step2 is not None
    task2 = TaskDetail(id="TASK-002", title="Task 2", status="ACTIVE", parent="PLAN-001", steps=[step2])
    manager.save_task(task2, skip_sync=True)

    resp = process_intent(manager, {"intent": "note", "task": "TASK-001", "path": "s:0", "note": "x"})
    assert resp.success is True


def test_expected_target_alias_mismatch_fails_fast(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title="Task", status="TODO", parent="PLAN-001", steps=[step])
    manager.save_task(task, skip_sync=True)

    save_last_task("TASK-001")
    resp = process_intent(
        manager,
        {"intent": "note", "path": "s:0", "note": "x", "strict_writes": True, "expected_target": "TASK-999"},
    )
    assert resp.success is False
    assert resp.error_code == "EXPECTED_TARGET_MISMATCH"


def test_radar_budget_enforced(manager: TaskManager):
    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    # Oversized titles should be clamped by radar budget enforcement.
    huge_title = "X" * 5000
    step = Step.new("Step", criteria=["c"], tests=["t"])
    assert step is not None
    task = TaskDetail(id="TASK-001", title=huge_title, status="ACTIVE", parent="PLAN-001", steps=[step])
    manager.save_task(task, skip_sync=True)

    resp = handle_radar(manager, {"intent": "radar", "task": "TASK-001", "max_chars": 1000})
    assert resp.success is True
    result = resp.result
    assert set(["now", "why", "verify", "next", "blockers", "open_checkpoints"]).issubset(result.keys())
    assert result["budget"]["truncated"] is True
    assert result["budget"]["used_chars"] <= 1000
