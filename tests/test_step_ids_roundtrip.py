from core import PlanNode, Step, TaskDetail, TaskNode
from core.desktop.devtools.application.task_manager import TaskManager


def test_step_and_tasknode_ids_roundtrip(tmp_path):
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
    assert reloaded.steps[0].id
    nested_task_id = reloaded.steps[0].plan.tasks[0].id
    nested_step_id = reloaded.steps[0].plan.tasks[0].steps[0].id
    assert nested_task_id
    assert nested_step_id

    manager.save_task(reloaded, skip_sync=True)
    reloaded_again = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded_again.steps[0].id == reloaded.steps[0].id
    assert reloaded_again.steps[0].plan.tasks[0].id == nested_task_id
    assert reloaded_again.steps[0].plan.tasks[0].steps[0].id == nested_step_id
