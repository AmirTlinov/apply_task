"""Unit tests for strict verify semantics and PLAN-### verification."""

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_verify


def test_verify_requires_explicit_confirmed_true(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[step])
    manager.save_task(task, skip_sync=True)

    resp = handle_verify(
        manager,
        {
            "intent": "verify",
            "task": "TASK-001",
            "path": "s:0",
            "checkpoints": {"criteria": {}},
        },
    )
    assert resp.success is False
    assert resp.error_code == "VERIFY_NOOP"

    reloaded = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded.steps[0].criteria_confirmed is False
    assert reloaded.steps[0].tests_confirmed is False
    assert reloaded.steps[0].started_at is None
    assert reloaded.events == []


def test_verify_plan_root_accepts_kind_plan(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan", success_criteria=["goal"])
    manager.save_task(plan, skip_sync=True)

    resp = handle_verify(
        manager,
        {
            "intent": "verify",
            "task": "PLAN-001",
            "kind": "plan",
            "checkpoints": {"criteria": {"confirmed": True, "note": "ok"}},
        },
    )
    assert resp.success is True
    assert resp.result["task_id"] == "PLAN-001"
    assert resp.result["kind"] == "plan"
    assert resp.result["path"] is None
    assert resp.result["plan"]["id"] == "PLAN-001"
    assert resp.result["checkpoints_before"]["criteria"]["confirmed"] is False
    assert resp.result["checkpoints_after"]["criteria"]["confirmed"] is True


def test_verify_plan_root_accepts_kind_auto(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan", success_criteria=["goal"])
    manager.save_task(plan, skip_sync=True)

    resp = handle_verify(
        manager,
        {
            "intent": "verify",
            "task": "PLAN-001",
            "kind": "auto",
            "checkpoints": {"criteria": {"confirmed": True}},
        },
    )
    assert resp.success is True
    # Auto resolves to plan for PLAN-###.
    assert resp.result["kind"] == "plan"
    assert manager.load_task("PLAN-001", skip_sync=True).criteria_confirmed is True

