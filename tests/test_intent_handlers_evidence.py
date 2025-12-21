from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_progress, handle_verify


def test_handle_verify_persists_checks_and_attachments(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[step])
    manager.save_task(task, skip_sync=True)

    data = {
        "intent": "verify",
        "task": "TASK-001",
        "path": "s:0",
        "checkpoints": {"criteria": {"confirmed": True}, "tests": {"confirmed": True}},
        "checks": [
            {
                "kind": "command",
                "spec": "pytest -q",
                "outcome": "pass",
                "observed_at": "2025-12-21T00:00:00Z",
                "digest": "abc123",
                "preview": "ok",
            }
        ],
        "attachments": [{"kind": "log", "path": "logs/test.log"}],
        "verification_outcome": "pass",
    }
    response = handle_verify(manager, data)
    assert response.success is True

    updated = manager.load_task("TASK-001", skip_sync=True)
    updated_step = updated.steps[0]
    assert updated_step.verification_checks
    assert updated_step.verification_checks[0].spec == "pytest -q"
    assert updated_step.attachments
    assert updated_step.attachments[0].kind == "log"
    assert updated_step.verification_outcome == "pass"


def test_handle_progress_force_requires_override(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[step])
    manager.save_task(task, skip_sync=True)

    response = handle_progress(
        manager,
        {"intent": "progress", "task": "TASK-001", "path": "s:0", "completed": True, "force": True},
    )
    assert response.success is False
    assert response.error_code == "MISSING_OVERRIDE_REASON"


def test_handle_progress_records_override(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[step])
    manager.save_task(task, skip_sync=True)

    response = handle_progress(
        manager,
        {
            "intent": "progress",
            "task": "TASK-001",
            "path": "s:0",
            "completed": True,
            "force": True,
            "override_reason": "manual override for demo",
        },
    )
    assert response.success is True

    updated = manager.load_task("TASK-001", skip_sync=True)
    assert updated.events
    assert any(e.event_type == "override" for e in updated.events)
