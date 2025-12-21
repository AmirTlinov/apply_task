from core import PlanNode, Step, TaskDetail, TaskNode
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_define, handle_task_define


def test_handle_define_resolves_step_id(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)
    root_step = Step(False, "Root step", success_criteria=["c"], tests=["t"])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[root_step])
    manager.save_task(task, skip_sync=True)

    reloaded = manager.load_task("TASK-001", skip_sync=True)
    step_id = reloaded.steps[0].id

    data = {
        "intent": "define",
        "task": "TASK-001",
        "step_id": step_id,
        "title": "Root step updated",
        "success_criteria": ["c1"],
    }
    response = handle_define(manager, data)
    assert response.success is True

    updated = manager.load_task("TASK-001", skip_sync=True)
    assert updated.steps[0].title == "Root step updated"
    assert updated.steps[0].success_criteria == ["c1"]


def test_handle_task_define_resolves_task_node_id(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)
    child_step = Step(False, "Child step", success_criteria=["c"], tests=["t"])
    nested_task = TaskNode(title="Nested task", steps=[child_step])
    root_step = Step(False, "Root step", success_criteria=["c"], tests=["t"])
    root_step.plan = PlanNode(tasks=[nested_task])
    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[root_step])
    manager.save_task(task, skip_sync=True)

    reloaded = manager.load_task("TASK-001", skip_sync=True)
    task_node_id = reloaded.steps[0].plan.tasks[0].id

    data = {
        "intent": "task_define",
        "task": "TASK-001",
        "task_node_id": task_node_id,
        "title": "Nested task updated",
    }
    response = handle_task_define(manager, data)
    assert response.success is True

    updated = manager.load_task("TASK-001", skip_sync=True)
    assert updated.steps[0].plan.tasks[0].title == "Nested task updated"
