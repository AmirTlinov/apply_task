from pathlib import Path

from core.desktop.devtools.application.task_manager import TaskManager
from core import TaskDetail, SubTask


class DummySync:
    def __init__(self, enabled=True, workers=1):
        self.enabled = enabled
        self.config = type("Cfg", (), {"workers": workers})
        self.calls = []
        self.last_push = None

    def sync_task(self, task):
        self.calls.append(task.id)
        # emulate project fields population
        task.project_item_id = task.project_item_id or "item"
        task.project_issue_number = task.project_issue_number or 1
        return True

    def clone(self):
        return self


def _write_task(path: Path, task_id: str):
    content = f"""---
id: {task_id}
title: Demo {task_id}
status: FAIL
domain:
created: 2025-01-01 00:00
updated: 2025-01-01 00:00
---
# Demo
"""
    path.write_text(content, encoding="utf-8")


def test_auto_sync_all_writes_back(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    task_file = tasks_dir / "TASK-001.task"
    _write_task(task_file, "TASK-001")

    dummy = DummySync(enabled=True, workers=1)
    manager = TaskManager(tasks_dir=tasks_dir, sync_service=dummy)

    # auto_sync runs in __init__, ensure call recorded and file updated
    assert dummy.calls == ["TASK-001"]
    saved = task_file.read_text()
    assert "project_item_id" in saved
    assert "project_issue_number" in saved
    assert manager.auto_sync_message


def test_update_task_status_validates_and_sets_ok(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-010",
        title="Demo",
        status="WARN",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    # add subtask with checkpoints to satisfy validation
    sub = SubTask(
        completed=True,
        title="Sub with checkpoints",
        success_criteria=["c"],
        tests=["t"],
        blockers=["b"],
        criteria_confirmed=True,
        tests_confirmed=True,
        blockers_resolved=True,
    )
    task.subtasks.append(sub)
    task.success_criteria = ["sc"]
    task.tests = ["tt"]
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-010", "OK")
    assert ok is True
    assert err is None
    reloaded = manager.load_task("TASK-010")
    assert reloaded.status == "OK"
