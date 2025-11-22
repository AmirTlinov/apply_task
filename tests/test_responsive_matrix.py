import itertools

import pytest

from tasks import SubTask, TaskDetail, TaskTrackerTUI


@pytest.mark.parametrize(
    "term_width,expected_max",
    [
        (70, 66),   # tw-4
        (100, 94),  # tw-6
        (200, 160), # capped at 160
    ],
)
def test_detail_content_width_breakpoints(term_width, expected_max, tmp_path):
    tui = TaskTrackerTUI(tasks_dir=tmp_path / ".tasks")
    tui.get_terminal_width = lambda: term_width
    width = tui._detail_content_width()

    assert width <= expected_max
    assert width <= term_width - 2
    assert width >= 30


@pytest.mark.parametrize("term_width,term_height", [(58, 10), (82, 14), (120, 18)])
def test_detail_view_resizes_for_various_widths(tmp_path, term_width, term_height):
    tui = TaskTrackerTUI(tasks_dir=tmp_path / ".tasks")
    tui.get_terminal_width = lambda: term_width
    tui.get_terminal_height = lambda: term_height
    tui._set_footer_height(2)

    detail = TaskDetail(
        id="TASK-MATRIX",
        title="Matrix sizing check",
        status="WARN",
        description="\n".join(f"Line {i} content text" for i in range(8)),
        blockers=[f"blocker {i}" for i in range(3)],
        domain="devtools",
    )
    detail.subtasks = []

    tui.detail_mode = True
    tui.current_task_detail = detail
    rendered = "".join(text for _, text in tui.get_detail_text())
    lines = rendered.split("\n")

    assert len(lines) <= tui.get_terminal_height()
    assert all(tui._display_width(line) <= tui.get_terminal_width() for line in lines if line)


@pytest.mark.parametrize("term_width,term_height", [(52, 8), (70, 12), (96, 16)])
def test_single_subtask_resizes_matrix(tmp_path, term_width, term_height):
    tui = TaskTrackerTUI(tasks_dir=tmp_path / ".tasks")
    tui.get_terminal_width = lambda: term_width
    tui.get_terminal_height = lambda: term_height
    tui._set_footer_height(1)

    detail = TaskDetail(id="TASK-SUB", title="Subtask detail", status="WARN")
    detail.subtasks = []
    tui.detail_mode = True
    tui.current_task_detail = detail

    for crit_count, test_count in [(3, 1), (6, 4), (8, 5)]:
        detail.subtasks.append(
            SubTask(
                completed=False,
                title="Subtask",
                success_criteria=[f"Criterion {i}" for i in range(crit_count)],
                tests=[f"Test {i}" for i in range(test_count)],
                blockers=["Blocker 0"],
            )
        )

    tui._rebuild_detail_flat()
    tui.detail_selected_path = "0"
    tui.show_subtask_details("0")

    lines = tui._formatted_lines(tui.single_subtask_view)
    assert len(lines) <= tui.get_terminal_height()
    assert all(tui._display_width("".join(t for _, t in line)) <= tui.get_terminal_width() for line in lines if line)
