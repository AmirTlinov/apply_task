from core import Attachment, PlanNode, Step, TaskDetail, TaskNode, VerificationCheck
from core.desktop.devtools.application.task_manager import TaskManager


def test_evidence_and_attachments_roundtrip(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    manager = TaskManager(tasks_dir=tasks_dir)

    check = VerificationCheck(
        kind="command",
        spec="pytest -q",
        outcome="pass",
        observed_at="2025-12-21T00:00:00Z",
        digest="abc123",
        preview="all green",
    )
    attachment = Attachment(kind="log", path="logs/test.log", digest="def456", observed_at="2025-12-21T00:00:00Z")

    nested_task = TaskNode(title="Nested task")
    nested_task.attachments = [Attachment(kind="report", path="reports/nested.json")]
    root_step = Step(False, "Root step", success_criteria=["c"], tests=["t"])
    root_step.attachments = [attachment]
    root_step.verification_checks = [check]
    root_step.verification_outcome = "pass"
    root_step.plan = PlanNode(tasks=[nested_task], attachments=[Attachment(kind="doc", path="docs/plan.md")])

    task = TaskDetail(id="TASK-001", title="Example", status="TODO", steps=[root_step])
    task.attachments = [Attachment(kind="artifact", path="artifacts/root.bin")]
    manager.save_task(task, skip_sync=True)

    reloaded = manager.load_task("TASK-001", skip_sync=True)
    assert reloaded.attachments and reloaded.attachments[0].kind == "artifact"
    reloaded_step = reloaded.steps[0]
    assert reloaded_step.attachments and reloaded_step.attachments[0].kind == "log"
    assert reloaded_step.verification_checks and reloaded_step.verification_checks[0].spec == "pytest -q"
    assert reloaded_step.verification_outcome == "pass"
    assert reloaded_step.plan.attachments and reloaded_step.plan.attachments[0].kind == "doc"
    assert reloaded_step.plan.tasks[0].attachments and reloaded_step.plan.tasks[0].attachments[0].kind == "report"
