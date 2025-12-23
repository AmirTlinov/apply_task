from core import Step, TaskDetail


def test_task_does_not_auto_done_without_root_success_criteria():
    step = Step(False, "Step", success_criteria=["c"], tests=["t"])
    step.completed = True
    step.criteria_confirmed = True
    step.tests_confirmed = True

    task = TaskDetail(id="TASK-001", title="Example", status="ACTIVE", steps=[step])
    task.success_criteria = []

    task.update_status_from_progress()
    assert task.progress == 100
    assert str(task.status).upper() != "DONE"

