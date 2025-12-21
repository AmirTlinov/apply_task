from types import SimpleNamespace

from core.desktop.devtools.interface import tui_loader


def test_load_tasks_snapshot_filters_and_sorts(monkeypatch):
    class DummyTask:
        def __init__(self, id, status, progress, title):
            self.id = id
            self.status = status
            self.progress = progress
            self.title = title

    tasks = [
        DummyTask("1", "DONE", 100, "B"),
        DummyTask("2", "TODO", 10, "A"),
        DummyTask("3", "ACTIVE", 50, "C"),
    ]

    class DummyManager:
        def list_tasks(self, domain):
            return tasks

    filtered = tui_loader.load_tasks_snapshot(DummyManager(), "dom", SimpleNamespace(value=["TODO"]))
    assert len(filtered) == 1 and filtered[0].id == "2"
    # sort order by status.value then progress
    filtered_all = tui_loader.load_tasks_snapshot(DummyManager(), "dom", None)
    assert [t.id for t in filtered_all] == ["3", "2", "1"]


def test_load_tasks_with_state_handles_errors(monkeypatch):
    class DummyManager:
        def list_tasks(self, domain):
            raise ValueError("boom")

    class DummyTUI:
        manager = DummyManager()
        domain_filter = ""
        current_filter = None

    items, message = tui_loader.load_tasks_with_state(DummyTUI())
    assert items == []
    assert "ERR_TASK_LIST_FAILED" in message


def test_load_tasks_with_state_includes_filter_message():
    class DummyTask:
        def __init__(self, name):
            self.status = name
            self.progress = 0

    class DummyManager:
        def list_tasks(self, domain):
            return [DummyTask("DONE"), DummyTask("TODO")]

    class DummyTUI:
        manager = DummyManager()
        domain_filter = ""
        current_filter = SimpleNamespace(value=["DONE"])

    items, message = tui_loader.load_tasks_with_state(DummyTUI())
    assert [t.status for t in items] == ["DONE"]
    assert message == tui_loader.translate("FILTER_APPLIED", value="DONE")


def test_apply_context_filters_and_models():
    class DummyTask:
        def __init__(self, phase, component, status, blocked=False):
            self.phase = phase
            self.component = component
            self.status = status
            self.blocked = blocked
            self.subtasks = []

        def calculate_progress(self):
            return 100 if self.status == "DONE" else 0

    tasks = [DummyTask("p", "c", "DONE"), DummyTask("x", "y", "TODO", blocked=True)]
    filtered = tui_loader.apply_context_filters(tasks, "p", "c")
    assert len(filtered) == 1

    built = tui_loader.build_task_models(filtered, lambda det, st, prog, subs, total: (det.status, st, prog, subs, total))
    assert built[0][1].name == "DONE"


def test_select_index_after_load():
    class T:
        def __init__(self, task_file):
            self.task_file = task_file

    tasks = [T("a"), T("b")]
    assert tui_loader.select_index_after_load(tasks, True, "b") == 1
    assert tui_loader.select_index_after_load(tasks, False, "b") == 0


def test_load_tasks_with_state_no_filter_message():
    class DummyManager:
        def list_tasks(self, domain):
            return []

    class DummyTUI:
        manager = DummyManager()
        domain_filter = ""
        current_filter = None

    items, message = tui_loader.load_tasks_with_state(DummyTUI())
    assert items == [] and message == ""
