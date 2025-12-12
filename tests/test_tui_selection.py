from tasks import Status, TaskTrackerTUI


def build_tui(tmp_path, mono=False):
    tasks_dir = tmp_path / ".tasks"
    return TaskTrackerTUI(tasks_dir=tasks_dir, mono_select=mono)


def test_selection_style_returns_palette_keys(tmp_path):
    tui = build_tui(tmp_path)

    assert tui._selection_style_for_status(Status.DONE) == "selected.ok"
    assert tui._selection_style_for_status(Status.ACTIVE) == "selected.warn"
    assert tui._selection_style_for_status(Status.TODO) == "selected.fail"
    assert tui._selection_style_for_status(Status.UNKNOWN) == "selected.unknown"

    # строковое значение тоже поддерживается
    assert tui._selection_style_for_status("ACTIVE") == "selected.warn"
    assert tui._selection_style_for_status(None) == "selected.unknown"


def test_selection_style_honors_mono_flag(tmp_path):
    tui = build_tui(tmp_path, mono=True)

    for probe in (Status.DONE, Status.TODO, "ACTIVE", None):
        assert tui._selection_style_for_status(probe) == "selected"
