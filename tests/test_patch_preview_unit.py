"""Unit tests for patch previews and lifecycle invariants (trust-by-contract)."""

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import process_intent


def _done_task(task_id: str) -> TaskDetail:
    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    step.completed = True
    step.criteria_confirmed = True
    step.tests_confirmed = True
    task = TaskDetail(
        id=task_id,
        title="Example",
        status="DONE",
        steps=[step],
        success_criteria=["ok"],
    )
    return task


def test_patch_dry_run_reopens_done_task_when_step_changes(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    manager.save_task(_done_task("TASK-001"), skip_sync=True)

    resp = process_intent(
        manager,
        {
            "intent": "patch",
            "task": "TASK-001",
            "kind": "step",
            "path": "s:0",
            "dry_run": True,
            "ops": [{"op": "append", "field": "blockers", "value": "b1"}],
        },
    )
    assert resp.success is True
    diff = (resp.result.get("diff") or {}).get("state") or {}
    assert diff.get("lifecycle_status") == {"from": "DONE", "to": "ACTIVE"}
    assert ((resp.result.get("after") or {}).get("state") or {}).get("lifecycle_status") == "ACTIVE"


def test_patch_persists_reopen_of_done_task_on_apply(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    manager.save_task(_done_task("TASK-001"), skip_sync=True)

    resp = process_intent(
        manager,
        {
            "intent": "patch",
            "task": "TASK-001",
            "kind": "step",
            "path": "s:0",
            "ops": [{"op": "append", "field": "blockers", "value": "b1"}],
        },
    )
    assert resp.success is True
    reloaded = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded is not None
    assert str(reloaded.status).upper() == "ACTIVE"


def test_patch_reopens_done_task_when_root_success_criteria_removed(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    manager.save_task(_done_task("TASK-001"), skip_sync=True)

    resp = process_intent(
        manager,
        {
            "intent": "patch",
            "task": "TASK-001",
            "kind": "task_detail",
            "dry_run": True,
            "ops": [{"op": "set", "field": "success_criteria", "value": []}],
        },
    )
    assert resp.success is True
    diff = (resp.result.get("diff") or {}).get("state") or {}
    assert diff.get("lifecycle_status") == {"from": "DONE", "to": "ACTIVE"}

