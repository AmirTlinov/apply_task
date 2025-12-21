from datetime import datetime
from pathlib import Path

from core import TaskDetail
from core.desktop.devtools.application import task_manager as tm


def _write_task(repo_dir: Path, task: TaskDetail) -> None:
    path = repo_dir / task.domain / f"{task.id}.task" if task.domain else repo_dir / f"{task.id}.task"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(task.to_file_content(), encoding="utf-8")


def test_auto_clean_moves_old_done_tasks(tmp_path, monkeypatch):
    tasks_dir = tmp_path / ".tasks"
    manager = tm.TaskManager(tasks_dir=tasks_dir, auto_sync=False)

    monkeypatch.setattr(tm, "get_cleanup_done_tasks_ttl_seconds", lambda: 60)
    monkeypatch.setattr(tm, "_AUTO_CLEAN_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(tm, "_AUTO_CLEAN_LAST_RUN", {})

    old = TaskDetail(id="TASK-001", title="Old DONE task for cleanup test", status="DONE")
    old.updated = "2000-01-01 00:00"
    _write_task(tasks_dir, old)

    fresh = TaskDetail(id="TASK-002", title="Fresh DONE task for cleanup test", status="DONE")
    fresh.updated = datetime.now().strftime(tm.TIMESTAMP_FORMAT)
    _write_task(tasks_dir, fresh)

    tasks = manager.list_tasks("", skip_sync=True)
    ids = {t.id for t in tasks}

    assert "TASK-001" not in ids
    assert "TASK-002" in ids
    assert not (tasks_dir / "TASK-001.task").exists()
    assert (tasks_dir / ".trash" / "TASK-001.task").exists()


def test_auto_clean_respects_depends_on(tmp_path, monkeypatch):
    tasks_dir = tmp_path / ".tasks"
    manager = tm.TaskManager(tasks_dir=tasks_dir, auto_sync=False)

    monkeypatch.setattr(tm, "get_cleanup_done_tasks_ttl_seconds", lambda: 60)
    monkeypatch.setattr(tm, "_AUTO_CLEAN_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(tm, "_AUTO_CLEAN_LAST_RUN", {})

    protected = TaskDetail(id="TASK-010", title="DONE task protected by depends_on", status="DONE")
    protected.updated = "2000-01-01 00:00"
    _write_task(tasks_dir, protected)

    blocker = TaskDetail(id="TASK-011", title="Task depending on TASK-010", status="TODO")
    blocker.depends_on = ["TASK-010"]
    blocker.updated = datetime.now().strftime(tm.TIMESTAMP_FORMAT)
    _write_task(tasks_dir, blocker)

    tasks = manager.list_tasks("", skip_sync=True)
    ids = {t.id for t in tasks}

    assert "TASK-010" in ids
    assert "TASK-011" in ids
    assert (tasks_dir / "TASK-010.task").exists()
    assert not (tasks_dir / ".trash" / "TASK-010.task").exists()
