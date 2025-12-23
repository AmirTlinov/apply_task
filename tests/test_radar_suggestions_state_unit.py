from core import Step, TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_radar


def test_radar_now_ready_and_suggests_close_task_when_all_steps_completed_but_task_not_done(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    step = Step.new("Step title long enough 12345", criteria=["c"], tests=["t"])
    assert step is not None
    step.completed = True
    step.criteria_confirmed = True
    step.tests_confirmed = True

    # Root DoD missing keeps the task non-DONE even at 100% progress (runway closed).
    task = TaskDetail(id="TASK-001", title="Task", status="ACTIVE", steps=[step])
    task.success_criteria = []
    manager.save_task(task, skip_sync=True)

    resp = handle_radar(manager, {"intent": "radar", "task": "TASK-001"})
    assert resp.success is True
    assert (resp.result.get("now") or {}).get("kind") == "task"
    assert (resp.result.get("now") or {}).get("status") == "ready"

    suggestions = list(resp.result.get("next") or [])
    assert any(s.get("action") == "close_task" and (s.get("params") or {}).get("task") == "TASK-001" for s in suggestions)


def test_radar_runway_plan_current_recipe_is_schema_safe(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    plan = TaskDetail(id="PLAN-001", title="Plan", status="TODO", kind="plan")
    plan.plan_steps = ["one", "two"]
    plan.plan_current = 99
    manager.save_task(plan, skip_sync=True)

    resp = handle_radar(manager, {"intent": "radar", "plan": "PLAN-001"})
    assert resp.success is True
    runway = resp.result.get("runway") or {}
    assert runway.get("open") is False
    recipe = runway.get("recipe") or {}
    assert recipe.get("intent") == "patch"
    ops = recipe.get("ops") or []
    assert ops and isinstance(ops[0].get("value"), str)

