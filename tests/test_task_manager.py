from pathlib import Path

from core.desktop.devtools.application import task_manager
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


def test_update_task_status_not_found(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    ok, err = manager.update_task_status("NOPE", "OK")
    assert ok is False
    assert err and err["code"] == "not_found"


def test_update_task_status_warn_recalculates_progress(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-011",
        title="Progress",
        status="FAIL",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    task.subtasks.append(SubTask(completed=True, title="done", success_criteria=["c"], tests=["t"], blockers=["b"]))
    task.subtasks.append(SubTask(completed=False, title="todo", success_criteria=["c"], tests=["t"], blockers=["b"]))
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-011", "WARN")
    assert ok and err is None
    updated = manager.load_task("TASK-011")
    assert updated.status == "WARN"
    assert updated.progress == 50


def test_update_task_status_validation_failure(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-012",
        title="Invalid",
        status="FAIL",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    task.subtasks.append(SubTask(completed=True, title="child", success_criteria=[], tests=[], blockers=["b"]))
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-012", "OK")
    assert ok is False
    assert err and err["code"] == "validation"


def test_add_subtask_missing_fields_and_path(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    base = TaskDetail(
        id="TASK-013",
        title="Base",
        status="FAIL",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    manager.repo.save(base)

    ok, err = manager.add_subtask("TASK-013", "No fields")
    assert ok is False and err == "missing_fields"

    ok, err = manager.add_subtask(
        "TASK-013",
        "Wrong path",
        criteria=["c"],
        tests=["t"],
        blockers=["b"],
        parent_path="9",
    )
    assert ok is False and err == "path"


def test_add_subtask_success_nested(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    base = TaskDetail(
        id="TASK-014",
        title="Base",
        status="FAIL",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    parent = SubTask(False, "parent", ["c"], ["t"], ["b"])
    base.subtasks.append(parent)
    manager.repo.save(base)

    ok, err = manager.add_subtask(
        "TASK-014",
        "Child",
        criteria=["c1"],
        tests=["t1"],
        blockers=["b1"],
        parent_path="0",
    )
    assert ok and err is None
    reloaded = manager.load_task("TASK-014")
    assert len(reloaded.subtasks[0].children) == 1


def test_add_subtask_success_root(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    base = TaskDetail(
        id="TASK-015",
        title="Base",
        status="FAIL",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    manager.repo.save(base)

    ok, err = manager.add_subtask(
        "TASK-015",
        "Root child",
        criteria=["c"],
        tests=["t"],
        blockers=["b"],
    )
    assert ok and err is None
    reloaded = manager.load_task("TASK-015")
    assert len(reloaded.subtasks) == 1


def test_update_task_status_subtask_missing_criteria(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-016",
        title="Criteria check",
        status="WARN",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    task.success_criteria = ["goal"]
    task.subtasks.append(SubTask(completed=True, title="child", success_criteria=[], tests=["t"], blockers=["b"]))
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-016", "OK")
    assert ok is False
    assert err and err["code"] == "validation"


def test_update_task_status_subtask_missing_tests(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-017",
        title="Tests check",
        status="WARN",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    task.success_criteria = ["goal"]
    task.subtasks.append(SubTask(completed=True, title="child", success_criteria=["c"], tests=[], blockers=["b"]))
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-017", "OK")
    assert ok is False
    assert err and err["code"] == "validation"


def test_find_subtask_by_path_invalid_returns_none():
    root = SubTask(False, "root", ["c"], ["t"], ["b"])
    child = SubTask(False, "child", ["c"], ["t"], ["b"])
    root.children.append(child)

    assert task_manager._find_subtask_by_path([root], "invalid") == (None, None, None)
    assert task_manager._find_subtask_by_path([root], "5") == (None, None, None)
    assert task_manager._find_subtask_by_path([root], "0.9") == (None, None, None)
    assert task_manager._find_subtask_by_path([root], "") == (None, None, None)


def test_update_progress_for_status_sets_progress():
    task = TaskDetail(id="TASK-018", title="p", status="FAIL", created="2025-01-01", updated="2025-01-01")
    task.subtasks.append(SubTask(completed=True, title="child", success_criteria=["c"], tests=["t"], blockers=["b"]))
    task_manager._update_progress_for_status(task, "WARN")
    assert task.progress == 100


def test_update_task_status_requires_full_progress(tmp_path):
    manager = TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync(enabled=False))
    task = TaskDetail(
        id="TASK-019",
        title="Partial",
        status="WARN",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    task.success_criteria = ["goal"]
    task.subtasks.append(SubTask(completed=False, title="child", success_criteria=["c"], tests=["t"], blockers=["b"]))
    manager.repo.save(task)

    ok, err = manager.update_task_status("TASK-019", "OK")
    assert ok is False
    assert err and err["code"] == "validation"
