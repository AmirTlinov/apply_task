from core.desktop.devtools.interface.tui_models import Task
from tasks import Status, TaskDetail, TaskTrackerTUI


def test_marks_dots_are_individually_styled(tmp_path):
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()

    tui = TaskTrackerTUI(tasks_dir=tasks_dir)
    tui.get_terminal_width = lambda: 120

    detail = TaskDetail(id="TASK-001", title="Example", status="TODO")
    detail.criteria_confirmed = True
    detail.tests_confirmed = False

    tui.tasks = [
        Task(
            name="TASK-001 Example",
            status=Status.TODO,
            description="",
            category="",
            detail=detail,
            progress=0,
        )
    ]
    # Avoid selection styles affecting assertions.
    tui.selected_index = 99

    rendered = tui.get_task_list_text()
    dot_fragments = [(style, text) for style, text in rendered if ("•" in text or "·" in text)]
    assert any("icon.check" in style and "•" in text for style, text in dot_fragments)
    assert any("text.dim" in style and "•" in text for style, text in dot_fragments)
