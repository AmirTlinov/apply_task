from tasks import Status, SubTask, TaskDetail, TaskTrackerTUI


def test_detail_view_clamped_to_terminal(tmp_path):
    tui = TaskTrackerTUI(tasks_dir=tmp_path / ".tasks")
    tui.get_terminal_width = lambda: 62
    tui.get_terminal_height = lambda: 14
    tui._set_footer_height(2)

    detail = TaskDetail(
        id="TASK-DET",
        title="Very long detail title that would otherwise stretch the frame",
        status="WARN",
        description="\n".join(f"Line {i} with more text to consume space" for i in range(12)),
        blockers=[f"blocker {i}" for i in range(5)],
        domain="devtools",
    )
    detail.subtasks = [SubTask(False, f"Subtask {i}") for i in range(6)]

    tui.detail_mode = True
    tui.current_task_detail = detail
    text = tui.get_detail_text()
    rendered = "".join(fragment for _, fragment in text)
    lines = rendered.split("\n")

    assert len(lines) <= tui.get_terminal_height()
    assert all(tui._display_width(line) <= tui.get_terminal_width() for line in lines if line)


def test_single_subtask_view_respects_height(tmp_path):
    tui = TaskTrackerTUI(tasks_dir=tmp_path / ".tasks")
    tui.get_terminal_width = lambda: 58
    tui.get_terminal_height = lambda: 10
    tui._set_footer_height(1)

    st = SubTask(
        False,
        "Subtask title",
        success_criteria=[f"Criterion {i} long text chunk to wrap" for i in range(8)],
        tests=[f"Test {i}" for i in range(3)],
        blockers=[f"Blocker {i}" for i in range(2)],
    )
    detail = TaskDetail(id="TASK-ST", title="Detail", status="WARN")
    detail.subtasks = [st]

    tui.detail_mode = True
    tui.current_task_detail = detail
    tui._rebuild_detail_flat()
    tui.detail_selected_path = "0"
    tui.show_subtask_details("0")

    lines = tui._formatted_lines(tui.single_subtask_view)
    assert len(lines) <= tui.get_terminal_height()
    assert all(tui._display_width("".join(t for _, t in line)) <= tui.get_terminal_width() for line in lines if line)
