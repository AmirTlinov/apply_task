from types import SimpleNamespace

from core.desktop.devtools.interface.tui_preview import build_side_preview_text


def test_preview_empty_tasks_shows_empty_message():
    class DummyTUI(SimpleNamespace):
        def __init__(self):
            super().__init__(filtered_tasks=[], selected_index=0)

        def _t(self, key, **kwargs):
            return key

    tui = DummyTUI()
    text = "".join(chunk[1] for chunk in build_side_preview_text(tui))
    assert "SIDE_EMPTY_TASKS" in text


def test_preview_no_detail_shows_no_data():
    class DummyTUI(SimpleNamespace):
        def __init__(self):
            super().__init__(filtered_tasks=[SimpleNamespace(detail=None, task_file=None)], selected_index=0)

        def _t(self, key, **kwargs):
            return key

    tui = DummyTUI()
    text = "".join(chunk[1] for chunk in build_side_preview_text(tui))
    assert "SIDE_NO_DATA" in text


def test_preview_with_detail_renders_title_and_progress():
    class Detail(SimpleNamespace):
        def calculate_progress(self):
            return 50

    detail = Detail(
        id="TASK-1",
        title="Demo title",
        status="OK",
        priority="HIGH",
        description="Line1\nLine2",
        domain="",
        phase="",
        component="",
        blocked=False,
    )

    class DummyTUI(SimpleNamespace):
        def __init__(self):
            super().__init__(filtered_tasks=[SimpleNamespace(detail=detail, task_file=None)], selected_index=0)

        def _t(self, key, **kwargs):
            return key

    tui = DummyTUI()
    text = "".join(chunk[1] for chunk in build_side_preview_text(tui))
    assert "TASK-1" in text and "50%" in text


def test_preview_warn_and_fail_status_chunks():
    class Detail(SimpleNamespace):
        def calculate_progress(self):
            return 0

    warn_detail = Detail(id="T2", title="Warn", status="WARN", priority="M", description="", domain="", phase="", component="", blocked=False)
    fail_detail = Detail(id="T3", title="Fail", status="FAIL", priority="M", description="", domain="", phase="", component="", blocked=False)

    class DummyTUI(SimpleNamespace):
        def __init__(self, detail):
            super().__init__(filtered_tasks=[SimpleNamespace(detail=detail, task_file=None)], selected_index=0)

        def _t(self, key, **kwargs):
            return key

    warn_text = "".join(chunk[1] for chunk in build_side_preview_text(DummyTUI(warn_detail)))
    fail_text = "".join(chunk[1] for chunk in build_side_preview_text(DummyTUI(fail_detail)))
    assert "INPR" in warn_text and "BACK" in fail_text
