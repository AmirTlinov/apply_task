from pathlib import Path

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager


class DummySync:
    enabled = False
    config = type("Cfg", (), {"workers": 1})


def _manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir, sync_service=DummySync(), auto_sync=False, use_global=False)


def test_set_step_completed_sets_started_and_completed_at(tmp_path):
    manager = _manager(tmp_path)
    st = Step(False, "Step title long enough 12345", ["c"], ["t"], ["b"], criteria_confirmed=True, tests_confirmed=True)
    task = TaskDetail(id="TASK-001", title="T", status="TODO", parent="PLAN-001", steps=[st])
    manager.repo.save(task)

    ok, msg = manager.set_step_completed("TASK-001", 0, True, "")
    assert ok is True
    assert msg is None
    reloaded = manager.load_task("TASK-001", "")
    assert reloaded.steps[0].completed is True
    assert reloaded.steps[0].started_at is not None
    assert reloaded.steps[0].completed_at is not None

