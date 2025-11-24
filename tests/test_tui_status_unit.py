from types import SimpleNamespace

from core.desktop.devtools.interface.tui_status import build_status_text


def test_build_status_text_basic():
    fragments = {}

    class DummyTUI(SimpleNamespace):
        def __init__(self):
            super().__init__(
                filtered_tasks=[SimpleNamespace(status="OK"), SimpleNamespace(status="WARN"), SimpleNamespace(status="FAIL")],
                domain_filter="",
                phase_filter=None,
                component_filter=None,
                current_filter=SimpleNamespace(value=["ALL"]),
                _filter_flash_until=0,
                spinner_message="",
                status_message="",
                status_message_expires=0,
                detail_mode=False,
                single_subtask_view=False,
            )

        def _t(self, key, **kwargs):
            return key

        def _sync_indicator_fragments(self, flash=False):
            return [("class", "sync")]

        def _spinner_frame(self):
            return None

        def get_terminal_width(self):
            return 80

        def exit_detail_view(self):
            fragments["back"] = fragments.get("back", 0) + 1

        def open_settings_dialog(self):
            fragments["settings"] = fragments.get("settings", 0) + 1

    tui = DummyTUI()
    result = build_status_text(tui)
    text = "".join(fragment[1] for fragment in result)
    assert "STATUS_TASKS_COUNT" in text
    assert "ALL" in text
    # ensure settings button exists
    assert any("SETTINGS" in frag[1] for frag in result)


def test_build_status_text_filter_flash(monkeypatch):
    class DummyTUI(SimpleNamespace):
        def __init__(self):
            super().__init__(
                filtered_tasks=[],
                domain_filter="",
                phase_filter=None,
                component_filter=None,
                current_filter=SimpleNamespace(value=["WARN"]),
                _filter_flash_until=0,
                spinner_message="",
                status_message="",
                status_message_expires=0,
                detail_mode=False,
                single_subtask_view=False,
            )

        def _t(self, key, **kwargs):
            return key

        def _sync_indicator_fragments(self, flash=False):
            return [("class", "sync")]

        def _spinner_frame(self):
            return None

        def get_terminal_width(self):
            return 80

        def exit_detail_view(self):
            pass

        def open_settings_dialog(self):
            pass

    tui = DummyTUI()
    result = build_status_text(tui)
    text = "".join(fragment[1] for fragment in result)
    assert "IN PROGRESS" in text
