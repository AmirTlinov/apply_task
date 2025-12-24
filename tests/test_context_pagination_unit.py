import pytest

from core import Step
from core.step import PlanNode, TaskNode
from core.task_detail import TaskDetail
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_context


@pytest.fixture
def manager(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    return TaskManager(tasks_dir=tasks_dir)


def test_handle_context_pagination_and_filters(manager):
    plan = manager.create_plan("Plan")
    manager.save_task(plan)
    t1 = TaskDetail(id="TASK-001", title="One", status="TODO", parent=plan.id, kind="task")
    t2 = TaskDetail(id="TASK-002", title="Two", status="DONE", parent=plan.id, kind="task", success_criteria=["ok"])
    manager.save_task(t1)
    manager.save_task(t2)

    resp = handle_context(manager, {"include_all": True, "tasks_limit": 1, "tasks_cursor": 0})
    assert resp.success is True
    assert len(resp.result["tasks"]) == 1
    assert resp.result["tasks_pagination"]["total"] == 2
    assert resp.result["tasks_pagination"]["next_cursor"] == "1"

    resp_done = handle_context(manager, {"include_all": True, "tasks_status": "DONE"})
    assert resp_done.success is True
    assert len(resp_done.result["tasks"]) == 1
    assert resp_done.result["tasks"][0]["status"] == "DONE"


def test_handle_context_subtree_plan(manager):
    task = TaskDetail(
        id="TASK-001",
        title="Root",
        status="TODO",
        steps=[Step(completed=False, title="Step 0", success_criteria=["c1"], tests=["t1"])],
    )
    task.steps[0].plan = PlanNode(title="Nested Plan", tasks=[TaskNode(title="Nested Task")])
    manager.save_task(task)

    resp = handle_context(
        manager,
        {"task": "TASK-001", "subtree": {"path": "s:0", "kind": "plan", "compact": True}},
    )
    assert resp.success is True
    subtree = resp.result["subtree"]
    assert subtree["kind"] == "plan"
    assert subtree["path"] == "s:0"
    assert subtree["node"]["tasks"][0]["title"] == "Nested Task"
