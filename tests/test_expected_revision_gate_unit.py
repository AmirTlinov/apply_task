"""Unit tests for expected_revision optimistic concurrency gate."""

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import process_intent


def _make_task(task_id: str) -> TaskDetail:
    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    return TaskDetail(id=task_id, title="Example", status="TODO", steps=[step])


def test_expected_revision_allows_current_and_rejects_stale(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    manager.save_task(_make_task("TASK-001"), skip_sync=True)
    initial = manager.load_task("TASK-001", skip_sync=True)
    assert initial is not None
    assert int(getattr(initial, "revision", 0) or 0) == 1

    r1 = process_intent(
        manager,
        {"intent": "note", "task": "TASK-001", "path": "s:0", "note": "n1", "expected_revision": initial.revision},
    )
    assert r1.success is True

    after_r1 = manager.load_task("TASK-001", skip_sync=True)
    assert after_r1 is not None
    stale_revision = int(getattr(after_r1, "revision", 0) or 0)
    assert stale_revision >= 2

    # External change (no expected_revision).
    r2 = process_intent(manager, {"intent": "note", "task": "TASK-001", "path": "s:0", "note": "n2"})
    assert r2.success is True
    after_r2 = manager.load_task("TASK-001", skip_sync=True)
    assert after_r2 is not None
    current_revision = int(getattr(after_r2, "revision", 0) or 0)
    assert current_revision > stale_revision

    rejected = process_intent(
        manager,
        {"intent": "note", "task": "TASK-001", "path": "s:0", "note": "n3", "expected_revision": stale_revision},
    )
    assert rejected.success is False
    assert rejected.error_code == "REVISION_MISMATCH"
    assert rejected.result.get("current_revision") == current_revision
    assert rejected.error_recovery
    assert any(s.action == "resume" for s in (rejected.suggestions or []))


def test_expected_revision_is_ignored_for_non_mutating_intents(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    resp = process_intent(manager, {"intent": "context", "expected_revision": 1})
    assert resp.success is True

