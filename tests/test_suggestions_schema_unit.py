from core import TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import generate_suggestions


def test_create_plan_suggestion_includes_title(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    suggestions = generate_suggestions(manager)
    assert suggestions
    sug = suggestions[0]
    assert sug.action == "create"
    assert (sug.params or {}).get("kind") == "plan"
    assert (sug.params or {}).get("title")


def test_create_task_suggestion_includes_title(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    manager.save_task(plan, skip_sync=True)

    suggestions = generate_suggestions(manager, "PLAN-001")
    assert suggestions
    sug = suggestions[0]
    assert sug.action == "create"
    assert (sug.params or {}).get("kind") == "task"
    assert (sug.params or {}).get("parent") == "PLAN-001"
    assert (sug.params or {}).get("title")

