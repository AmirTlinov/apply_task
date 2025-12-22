"""Unit tests for TaskDetail revision persistence and monotonic bumping."""

from pathlib import Path

from core import TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from infrastructure.task_file_parser import TaskFileParser


def test_revision_increments_on_each_save(tmp_path: Path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    task = TaskDetail(id="TASK-001", title="Example", status="TODO")
    assert task.revision == 0

    manager.save_task(task, skip_sync=True)
    assert task.revision == 1

    reloaded = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded is not None
    assert reloaded.revision == 1

    manager.save_task(reloaded, skip_sync=True)
    assert reloaded.revision == 2

    reloaded2 = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded2 is not None
    assert reloaded2.revision == 2


def test_legacy_file_without_revision_loads_as_zero(tmp_path: Path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    legacy = tasks_dir / "TASK-001.task"
    legacy.write_text(
        "\n".join(
            [
                "---",
                "schema_version: 7",
                "id: TASK-001",
                "kind: task",
                "title: Legacy",
                "status: TODO",
                "created: ''",
                "updated: ''",
                "---",
                "",
                "# Legacy",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = TaskFileParser.parse(legacy)
    assert parsed is not None
    assert parsed.revision == 0

