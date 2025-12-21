from tasks import TaskTrackerTUI
from core import Step, TaskDetail


def test_plan_detail_tasks_list_is_cached(tmp_path, monkeypatch):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()

    tui = TaskTrackerTUI(tasks_dir=tasks_dir)
    plan = tui.manager.create_plan("Plan")
    tui.manager.save_task(plan, skip_sync=True)
    task_a = tui.manager.create_task(title="Task A", parent=plan.id)
    tui.manager.save_task(task_a, skip_sync=True)
    task_b = tui.manager.create_task(title="Task B", parent=plan.id)
    tui.manager.save_task(task_b, skip_sync=True)

    tui.detail_mode = True
    tui.current_task_detail = tui.manager.load_task(plan.id, plan.domain, skip_sync=True)
    tui.detail_tab = "overview"
    tui.detail_plan_tasks = []
    tui.detail_selected_task_id = None
    tui._invalidate_plan_detail_tasks_cache()

    calls = {"n": 0}
    original = tui.manager.list_tasks

    def wrapped(domain_path: str = "", skip_sync: bool = False):
        calls["n"] += 1
        return original(domain_path, skip_sync=skip_sync)

    monkeypatch.setattr(tui.manager, "list_tasks", wrapped)

    first = tui._plan_detail_tasks()
    second = tui._plan_detail_tasks()
    assert [t.id for t in first] == [t.id for t in second]
    assert calls["n"] == 1

    # After invalidation we expect a rebuild.
    tui._detail_plan_tasks_dirty = True
    tui._plan_detail_tasks()
    assert calls["n"] == 2


def test_cached_step_tree_counts_respects_fingerprint(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()

    tui = TaskTrackerTUI(tasks_dir=tasks_dir)
    task = TaskDetail(id="TASK-001", title="Task", status="TODO")
    step = Step(False, "Step", success_criteria=["c"], tests=["t"], blockers=["b"])
    task.steps = [step]
    task._source_mtime = 1.0
    task.updated = "v1"

    total, done = tui._cached_step_tree_counts(task)
    assert (total, done) == (1, 0)

    # Mutate the step without updating fingerprint → cached values should remain.
    step.completed = True
    total2, done2 = tui._cached_step_tree_counts(task)
    assert (total2, done2) == (1, 0)

    # Update fingerprint → recompute reflects mutation.
    task._source_mtime = 2.0
    total3, done3 = tui._cached_step_tree_counts(task)
    assert (total3, done3) == (1, 1)
