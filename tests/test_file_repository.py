from pathlib import Path

from core import Step, TaskDetail
from infrastructure.file_repository import FileTaskRepository
from infrastructure.task_file_parser import TaskFileParser


def _sample_task() -> TaskDetail:
    sub = Step.new(
        "Nested step for repo roundtrip with enough details",
        criteria=["criterion A"],
        tests=["pytest -q"],
        blockers=["wait for review"],
        created_at="2025-12-14T00:00:00Z",
    )
    assert sub is not None
    task = TaskDetail(
        id="TASK-001",
        title="Repository roundtrip sample task with rich content",
        status="TODO",
        kind="task",
        parent="PLAN-001",
        domain="demo",
        description="Demo description",
        contract="Current user request (contract)",
        context="Extra context",
    )
    task.steps = [sub]
    task.contract_versions = [
        {"version": 1, "timestamp": "2025-12-14T00:00:00Z", "text": "Initial request"},
    ]
    task.success_criteria = ["task-level criterion"]
    task.dependencies = ["external dependency"]
    task.next_steps = ["ship feature"]
    task.problems = ["problem one"]
    task.risks = ["risk one"]
    task.history = ["created via test"]
    return task


def _sample_plan() -> TaskDetail:
    plan = TaskDetail(
        id="PLAN-001",
        title="Repository roundtrip sample plan",
        status="TODO",
        kind="plan",
        domain="demo",
        contract="Plan contract",
        plan_doc="Goal: keep the plan narrative here.\n\nMilestones:\n- Foundation\n- Integration",
        plan_steps=["Step 1", "Step 2", "Step 3"],
        plan_current=1,
    )
    plan.contract_versions = [
        {"version": 1, "timestamp": "2025-12-14T00:00:00Z", "text": "Initial request"},
    ]
    return plan


def test_file_repository_roundtrip(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    task = _sample_task()
    plan = _sample_plan()

    repo.save(task)
    repo.save(plan)
    loaded = repo.load(task.id, domain=task.domain)
    loaded_plan = repo.load(plan.id, domain=plan.domain)

    assert loaded is not None
    assert loaded.title == task.title
    assert loaded.domain == task.domain
    assert loaded.steps[0].success_criteria == task.steps[0].success_criteria
    assert loaded.contract == task.contract
    assert loaded.contract_versions == task.contract_versions
    assert loaded.problems == task.problems
    assert loaded.history == task.history
    assert loaded_plan is not None
    assert loaded_plan.kind == "plan"
    assert loaded_plan.plan_steps == plan.plan_steps
    assert loaded_plan.plan_current == plan.plan_current
    assert loaded_plan.plan_doc == plan.plan_doc


def test_compute_signature_changes_on_write(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    initial = repo.compute_signature()

    task = _sample_task()
    repo.save(task)
    after_save = repo.compute_signature()

    task.description = "Updated description"
    repo.save(task)
    after_update = repo.compute_signature()

    assert initial != after_save
    assert after_save != after_update


def test_taskfileparser_roundtrip(tmp_path: Path):
    task = _sample_task()
    task.id = "TASK-123"
    task.domain = "alpha/beta"
    task.steps[0].criteria_notes.append("note")
    content = task.to_file_content()

    path = tmp_path / ".tasks" / task.domain / f"{task.id}.task"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    parsed = TaskFileParser.parse(path)
    assert parsed is not None
    assert parsed.title == task.title
    assert parsed.domain == task.domain
    assert parsed.steps[0].criteria_notes == task.steps[0].criteria_notes
    assert parsed.contract == task.contract
    assert parsed.contract_versions == task.contract_versions
    assert parsed.risks == task.risks
    assert parsed.next_steps == task.next_steps
    assert parsed.dependencies == task.dependencies


def test_next_id_increments(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    assert repo.next_id() == "TASK-001"
    first = _sample_task()
    first.id = repo.next_id()
    repo.save(first)
    assert repo.next_id() == "TASK-002"
    assert repo.next_plan_id() == "PLAN-001"


def test_next_id_does_not_reuse_trashed_ids(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    trash_dir = tmp_path / ".tasks" / ".trash"
    trash_dir.mkdir(parents=True, exist_ok=True)
    (trash_dir / "TASK-010.task").write_text("---\nid: TASK-010\n---\n", encoding="utf-8")

    assert repo.next_id() == "TASK-011"


def test_delete_removes_file(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    task = _sample_task()
    task.id = "TASK-050"
    repo.save(task)
    assert repo.load(task.id, task.domain) is not None
    assert repo.delete(task.id, task.domain)
    assert repo.load(task.id, task.domain) is None


def test_move_updates_domain_and_path(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    task = _sample_task()
    task.id = "TASK-060"
    task.domain = "phase1/api"
    repo.save(task)

    assert repo.move(task.id, "phase2/api", current_domain=task.domain)
    moved = repo.load(task.id, "phase2/api")
    assert moved is not None
    assert moved.domain == "phase2/api"
    # старый путь удалён
    old_path = (tmp_path / ".tasks" / "phase1" / "api" / f"{task.id}.task")
    assert not old_path.exists()


def test_delete_glob(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    for i in range(3):
        t = _sample_task()
        t.id = f"TASK-10{i}"
        t.domain = "demo"
        repo.save(t)
    removed = repo.delete_glob("demo/TASK-10*.task")
    assert removed == 3


def test_clean_filtered(tmp_path: Path):
    repo = FileTaskRepository(tmp_path / ".tasks")
    t1 = _sample_task()
    t1.id = "TASK-201"
    t1.tags = ["alpha", "beta"]
    t1.status = "DONE"
    repo.save(t1)

    t2 = _sample_task()
    t2.id = "TASK-202"
    t2.tags = ["beta"]
    t2.status = "TODO"
    repo.save(t2)

    matched, removed = repo.clean_filtered(tag="alpha", status="DONE")
    assert matched == ["TASK-201"]
    assert removed == 1
    assert repo.load("TASK-201") is None
    assert repo.load("TASK-202") is not None
