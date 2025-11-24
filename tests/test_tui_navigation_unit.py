from types import SimpleNamespace

from core.desktop.devtools.interface import tui_navigation


def test_move_vertical_selection_list_mode():
    calls = {}

    class TUI:
        filtered_tasks = [1, 2, 3]
        selected_index = 1
        detail_mode = False
        settings_mode = False

        def _ensure_selection_visible(self):
            calls["visible"] = True

        def force_render(self):
            calls["render"] = True

    tui_navigation.move_vertical_selection(TUI(), 1)
    assert calls["visible"] and calls["render"]


def test_move_vertical_selection_settings_mode():
    class TUI:
        settings_mode = True
        settings_selected_index = 0
        def __init__(self):
            self._calls = {}

        def _settings_options(self):
            return ["a", "b", "c"]

        def _ensure_settings_selection_visible(self, total):
            self._calls["visible"] = total

        def force_render(self):
            self._calls["render"] = True

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert tui.settings_selected_index == 1
    assert tui._calls["visible"] == 3 and tui._calls["render"]


def test_move_vertical_selection_detail_mode_rebuild(monkeypatch):
    calls = {}

    class TUI:
        detail_mode = True
        detail_flat_subtasks = []
        current_task_detail = SimpleNamespace(subtasks=[1])
        detail_selected_path = ""
        detail_selected_index = 0

        def _rebuild_detail_flat(self, path):
            self.detail_flat_subtasks = [(0, None)]
            calls["rebuilt"] = True

        def get_detail_items_count(self):
            return 1

        def _selected_subtask_entry(self):
            calls["selected"] = True

        def _ensure_detail_selection_visible(self, items):
            calls["visible"] = items

        def force_render(self):
            calls["render"] = True

    tui_navigation.move_vertical_selection(TUI(), 0)
    assert calls["rebuilt"] and calls["selected"] and calls["render"]


def test_move_vertical_selection_single_subtask_view(monkeypatch):
    moves = {}

    class TUI:
        single_subtask_view = True
        _subtask_detail_total_lines = 5
        _subtask_header_lines_count = 1
        subtask_detail_cursor = 1
        subtask_detail_scroll = 0
        _subtask_view_height = 3
        _subtask_detail_buffer = ["a"]

        def _formatted_lines(self, buf): return ["h", "1", "2", "3", "4"]
        def _focusable_line_indices(self, lines): return [1, 2, 3, 4]
        def _snap_cursor(self, cursor, focusables): return cursor
        def _calculate_subtask_viewport(self, total, pinned, desired_offset):
            return desired_offset, 2, 0, 0, 0
        def get_terminal_width(self): return 80
        def _render_single_subtask_view(self, w): moves["render_width"] = w
        def force_render(self): moves["render"] = True

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert moves["render_width"] == 78 and moves["render"]


def test_move_vertical_selection_single_subtask_empty_total():
    class TUI:
        single_subtask_view = True
        _subtask_detail_total_lines = 0

        def _formatted_lines(self, buf):  # pragma: no cover - must not be called
            raise AssertionError("should not format")

        def force_render(self):  # pragma: no cover - must not be called
            raise AssertionError("render not expected")

    tui_navigation.move_vertical_selection(TUI(), 1)


def test_move_vertical_selection_single_subtask_backward_and_offsets():
    moves = {}

    class TUI:
        single_subtask_view = True
        _subtask_detail_total_lines = 6
        _subtask_header_lines_count = 0
        subtask_detail_cursor = 2
        subtask_detail_scroll = 0
        _subtask_detail_buffer = ["x"]

        def _formatted_lines(self, buf):
            return ["0", "1", "2", "3", "4", "5"]

        def _focusable_line_indices(self, lines):
            return [2, 4]

        def _snap_cursor(self, cursor, focusables):
            return cursor

        def _calculate_subtask_viewport(self, total, pinned, desired_offset):
            moves.setdefault("offsets", []).append(desired_offset)
            return desired_offset, 2, 0, 0, 0

        def get_terminal_width(self):
            return 60

        def _render_single_subtask_view(self, width):
            moves["render_width"] = width

        def force_render(self):
            moves["render"] = True

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, -1)
    assert moves["render_width"] == 58
    assert moves["offsets"][-1] == 1  # cursor_rel >= visible branch
    assert moves["render"]


def test_move_vertical_selection_single_subtask_offset_clamped():
    calls = {}

    class TUI:
        single_subtask_view = True
        _subtask_detail_total_lines = 4
        _subtask_header_lines_count = 2
        subtask_detail_cursor = 2
        subtask_detail_scroll = 3
        _subtask_detail_buffer = ["z"]

        def _formatted_lines(self, buf):
            return ["h", "1", "2", "3"]

        def _focusable_line_indices(self, lines):
            return [2, 3]

        def _snap_cursor(self, cursor, focusables):
            return cursor

        def _calculate_subtask_viewport(self, total, pinned, desired_offset):
            calls.setdefault("desired", []).append(desired_offset)
            return desired_offset, 1, 0, 0, 0

        def get_terminal_width(self):
            return 72

        def _render_single_subtask_view(self, width):
            calls["width"] = width

        def force_render(self):
            calls["render"] = True

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert calls["desired"][0] == 3  # initial offset
    assert calls["desired"][1] == 1  # clamped by cursor_rel < offset
    assert calls["width"] == 70 and calls["render"]


def test_move_vertical_selection_single_subtask_no_next_candidates():
    class TUI:
        single_subtask_view = True
        _subtask_detail_total_lines = 3
        _subtask_header_lines_count = 0
        subtask_detail_cursor = 2
        subtask_detail_scroll = 0
        _subtask_detail_buffer = ["x"]

        def _formatted_lines(self, buf):
            return ["0", "1", "2"]

        def _focusable_line_indices(self, lines):
            return [2]

        def _snap_cursor(self, cursor, focusables):
            return cursor

        def _calculate_subtask_viewport(self, total, pinned, desired_offset):
            return desired_offset, 1, 0, 0, 0

        def get_terminal_width(self):
            return 50

        def _render_single_subtask_view(self, width):
            self.width = width

        def force_render(self):
            self.rendered = True

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert tui.subtask_detail_cursor == 2
    assert getattr(tui, "rendered", False)


def test_move_vertical_selection_detail_mode_no_items():
    class TUI:
        detail_mode = True
        detail_selected_index = 5

        def _rebuild_detail_flat(self, path):
            raise AssertionError("should not rebuild")

        def get_detail_items_count(self):
            return 0

        def force_render(self):  # pragma: no cover - should not happen
            raise AssertionError("render not expected")

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert tui.detail_selected_index == 0


def test_move_vertical_selection_settings_empty_options():
    class TUI:
        settings_mode = True
        settings_selected_index = 3

        def _settings_options(self):
            return []

        def force_render(self):  # pragma: no cover - should not happen
            raise AssertionError("render not expected")

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert tui.settings_selected_index == 0


def test_move_vertical_selection_list_empty():
    class TUI:
        filtered_tasks = []
        selected_index = 7
        detail_mode = False
        settings_mode = False

        def force_render(self):  # pragma: no cover - should not happen
            raise AssertionError("render not expected")

    tui = TUI()
    tui_navigation.move_vertical_selection(tui, 1)
    assert tui.selected_index == 0
