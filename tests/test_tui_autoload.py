import types
from pathlib import Path

from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface import tui_app


def test_tui_autoloads_current_project(monkeypatch, tmp_path):
    tasks_root = tmp_path / "tasks_root"
    tasks_dir = tasks_root / "ns"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    manager = TaskManager(tasks_dir)
    plan = manager.create_plan("My plan")
    manager.save_task(plan, skip_sync=True)
    task = manager.create_task("Hello world", parent=plan.id)
    manager.save_task(task, skip_sync=True)

    # Route resolver to our temp namespace
    monkeypatch.setattr(tui_app, "get_tasks_dir_for_project", lambda use_global=True: tasks_dir)

    tui = tui_app.TaskTrackerTUI(projects_root=tasks_root)

    assert tui.project_mode is True
    assert any(Path(p.task_file).resolve() == tasks_dir.resolve() for p in tui.tasks)

    # Enter project (simulates pressing Enter)
    tui.show_task_details(tui.tasks[0])
    assert tui.project_mode is False
    assert tui.tasks_dir.resolve() == tasks_dir.resolve()
    assert tui.project_section == "plans"
    assert any(t.id == plan.id for t in tui.tasks)

    # Open tasks for the plan
    tui.open_tasks_for_plan(tui.tasks[0].detail)
    assert tui.project_section == "tasks"
    assert tui.plan_filter_id == plan.id
    assert any(t.id == task.id for t in tui.tasks)
