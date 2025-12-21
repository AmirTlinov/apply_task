"""Schema round-trip tests for plan/task/embedded checkpoints."""

from pathlib import Path

from core import TaskDetail
from core.step import PlanNode, Step, TaskNode
from infrastructure.task_file_parser import TaskFileParser


def test_taskdetail_checkpoint_fields_roundtrip(tmp_path: Path) -> None:
    plan = TaskDetail(id="PLAN-001", title="P", status="TODO", kind="plan", domain="dom/a", created="", updated="")
    plan.success_criteria = ["Done criteria"]
    plan.tests = ["Smoke test"]
    plan.blockers = ["Depends on API"]
    plan.criteria_confirmed = True
    plan.tests_confirmed = False
    plan.tests_auto_confirmed = False
    plan.criteria_notes = ["criteria ok"]
    plan.tests_notes = ["pending env"]

    path = tmp_path / "PLAN-001.task"
    path.write_text(plan.to_file_content(), encoding="utf-8")

    loaded = TaskFileParser.parse(path)
    assert loaded is not None
    assert loaded.id == "PLAN-001"
    assert loaded.kind == "plan"
    assert loaded.success_criteria == ["Done criteria"]
    assert loaded.tests == ["Smoke test"]
    assert loaded.blockers == ["Depends on API"]
    assert loaded.criteria_confirmed is True
    assert loaded.tests_confirmed is False
    assert loaded.criteria_notes == ["criteria ok"]
    assert loaded.tests_notes == ["pending env"]


def test_embedded_plan_task_checkpoint_fields_roundtrip(tmp_path: Path) -> None:
    leaf = Step(False, "Leaf step", success_criteria=["c1"], tests=["t1"], blockers=["b1"])
    leaf.criteria_confirmed = True
    leaf.tests_confirmed = True

    nested_task = TaskNode(
        title="Nested task",
        success_criteria=["tc"],
        tests=["tt"],
        criteria_confirmed=True,
        tests_confirmed=True,
        blockers=["tb"],
        steps=[leaf],
    )
    nested_plan = PlanNode(
        title="Nested plan",
        doc="Doc",
        success_criteria=["pc"],
        tests=["pt"],
        blockers=["pb"],
        criteria_confirmed=True,
        tests_confirmed=True,
        tasks=[nested_task],
    )

    root_step = Step(False, "Root step", success_criteria=["rc"], tests=["rt"], blockers=["rb"], plan=nested_plan)
    root_step.criteria_confirmed = True
    root_step.tests_confirmed = True

    task = TaskDetail(id="TASK-001", title="T", status="ACTIVE", kind="task", domain="dom/a", created="", updated="", steps=[root_step])
    path = tmp_path / "TASK-001.task"
    path.write_text(task.to_file_content(), encoding="utf-8")

    loaded = TaskFileParser.parse(path)
    assert loaded is not None
    assert loaded.steps
    st0 = loaded.steps[0]
    assert st0.plan is not None
    assert st0.plan.title == "Nested plan"
    assert st0.plan.success_criteria == ["pc"]
    assert st0.plan.tests == ["pt"]
    assert st0.plan.blockers == ["pb"]
    assert st0.plan.criteria_confirmed is True
    assert st0.plan.tests_confirmed is True
    assert st0.plan.tasks
    t0 = st0.plan.tasks[0]
    assert t0.title == "Nested task"
    assert t0.success_criteria == ["tc"]
    assert t0.tests == ["tt"]
    assert t0.blockers == ["tb"]
    assert t0.criteria_confirmed is True
    assert t0.tests_confirmed is True


def test_embedded_plan_checkpoint_fields_roundtrip_without_tasks(tmp_path: Path) -> None:
    nested_plan = PlanNode(
        title="Nested plan",
        doc="Doc",
        success_criteria=["pc"],
        tests=[],
        blockers=["pb"],
        criteria_confirmed=True,
        tests_confirmed=False,
        tasks=[],
    )
    root_step = Step(False, "Root step", success_criteria=["rc"], tests=["rt"], blockers=["rb"], plan=nested_plan)
    root_step.criteria_confirmed = True
    root_step.tests_confirmed = True

    task = TaskDetail(id="TASK-002", title="T", status="ACTIVE", kind="task", domain="dom/a", created="", updated="", steps=[root_step])
    path = tmp_path / "TASK-002.task"
    path.write_text(task.to_file_content(), encoding="utf-8")

    loaded = TaskFileParser.parse(path)
    assert loaded is not None
    assert loaded.steps
    st0 = loaded.steps[0]
    assert st0.plan is not None
    assert st0.plan.title == "Nested plan"
    assert st0.plan.success_criteria == ["pc"]
    assert st0.plan.tests == []
    assert st0.plan.blockers == ["pb"]
    assert st0.plan.criteria_confirmed is True
    assert st0.plan.tests_confirmed is False
    assert st0.plan.tasks == []
