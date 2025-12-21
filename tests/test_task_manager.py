from pathlib import Path

from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager


class DummySync:
    def __init__(self, enabled=False, workers=1):
        self.enabled = enabled
        self.config = type("Cfg", (), {"workers": workers})

    def sync_step(self, task):  # pragma: no cover - stub
        return False

    def pull_step_fields(self, task):  # pragma: no cover - stub
        return False

    def clone(self):
        return self


def _manager(tmp_path: Path) -> TaskManager:
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir, sync_service=DummySync(enabled=False), auto_sync=False, use_global=False)


def test_update_task_status_sets_done_when_ready(tmp_path):
    manager = _manager(tmp_path)
    task = TaskDetail(id="TASK-010", title="Demo", status="ACTIVE", parent="PLAN-001")
    task.success_criteria = ["ok"]
    task.steps = [
        Step(True, "Step title long enough 12345", ["c"], ["t"], ["b"], criteria_confirmed=True, tests_confirmed=True),
        Step(True, "Second step title long enough 12345", ["c"], ["t"], ["b"], criteria_confirmed=True, tests_confirmed=True),
    ]
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-010", "DONE", "")
    assert ok is True
    assert err is None
    assert manager.load_task("TASK-010", "").status == "DONE"


def test_add_step_requires_criteria(tmp_path):
    manager = _manager(tmp_path)
    task = TaskDetail(id="TASK-013", title="Base", status="TODO", parent="PLAN-001")
    manager.repo.save(task)

    ok, err = manager.add_step("TASK-013", "No criteria", criteria=[], tests=["t"], blockers=["b"])
    assert ok is False
    assert err == "missing_fields"


def test_add_step_nested_by_path(tmp_path):
    manager = _manager(tmp_path)
    parent = Step(False, "Parent step title long enough 12345", ["c"], ["t"], ["b"])
    task = TaskDetail(id="TASK-014", title="Base", status="TODO", parent="PLAN-001", steps=[parent])
    manager.repo.save(task)

    ok, err, _, task_path = manager.add_task_node("TASK-014", step_path="s:0", title="Nested task", domain="")
    assert ok is True
    assert err is None
    assert task_path == "s:0.t:0"

    ok, err = manager.add_step(
        "TASK-014",
        "Child step title long enough 12345",
        criteria=["c1"],
        tests=["t1"],
        blockers=["b1"],
        parent_path=task_path,
    )
    assert ok is True
    reloaded = manager.load_task("TASK-014", "")
    assert reloaded and reloaded.steps[0].plan and reloaded.steps[0].plan.tasks
    assert reloaded.steps[0].plan.tasks[0].steps
    assert reloaded.steps[0].plan.tasks[0].steps[0].title.startswith("Child")


def test_update_step_checkpoint_records_note_and_started_at(tmp_path):
    manager = _manager(tmp_path)
    st = Step(False, "Step title long enough 12345", ["c"], ["t"], ["b"])
    task = TaskDetail(id="TASK-020", title="T", status="TODO", parent="PLAN-001", steps=[st])
    manager.repo.save(task)

    ok, msg = manager.update_step_checkpoint("TASK-020", 0, "criteria", True, "evidence", "")
    assert ok is True
    assert msg is None
    reloaded = manager.load_task("TASK-020", "")
    assert reloaded and reloaded.steps[0].criteria_confirmed is True
    assert reloaded.steps[0].criteria_notes == ["evidence"]
    assert reloaded.steps[0].started_at


def test_set_step_completed_requires_checkpoints(tmp_path):
    manager = _manager(tmp_path)
    st = Step(False, "Step title long enough 12345", ["c"], ["t"], ["b"], criteria_confirmed=False, tests_confirmed=False)
    task = TaskDetail(id="TASK-030", title="T", status="TODO", parent="PLAN-001", steps=[st])
    manager.repo.save(task)

    ok, msg = manager.set_step_completed("TASK-030", 0, True, "")
    assert ok is False
    assert msg  # human-readable reason
