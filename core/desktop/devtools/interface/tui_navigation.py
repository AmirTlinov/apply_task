"""Navigation helpers for TaskTrackerTUI to keep tasks_app slim."""

from typing import List


def move_vertical_selection(tui, delta: int) -> None:
    """
    Move selected row/panel pointer by `delta`, clamping to available items.

    Works both in list mode (task rows) and detail mode (subtasks/dependencies).
    """
    if getattr(tui, "single_subtask_view", None):
        total = tui._subtask_detail_total_lines or 0
        if total <= 0:
            return
        lines = tui._formatted_lines(tui._subtask_detail_buffer)
        pinned = min(len(lines), getattr(tui, "_subtask_header_lines_count", 0))
        focusables = tui._focusable_line_indices(lines)
        if focusables:
            current = tui._snap_cursor(tui.subtask_detail_cursor, focusables)
            steps = abs(delta)
            direction = 1 if delta > 0 else -1
            for _ in range(steps):
                if direction > 0:
                    next_candidates = [i for i in focusables if i > current]
                    if not next_candidates:
                        break
                    current = next_candidates[0]
                else:
                    prev_candidates = [i for i in reversed(focusables) if i < current]
                    if not prev_candidates:
                        break
                    current = prev_candidates[0]
            tui.subtask_detail_cursor = current
        offset = tui.subtask_detail_scroll
        for _ in range(2):  # максимум два пересчёта, чтобы учесть изменение индикаторов
            offset, visible_content, _, _, _ = tui._calculate_subtask_viewport(
                total=len(lines), pinned=pinned, desired_offset=offset
            )
            cursor_rel = max(0, tui.subtask_detail_cursor - pinned)
            if cursor_rel < offset:
                offset = cursor_rel
                continue
            if cursor_rel >= offset + visible_content:
                offset = cursor_rel - visible_content + 1
                continue
            break
        tui.subtask_detail_scroll = offset
        term_width = tui.get_terminal_width()
        content_width = max(40, term_width - 2)
        tui._render_single_subtask_view(content_width)
        tui.force_render()
        return

    if getattr(tui, "detail_mode", False):
        if getattr(tui, "current_task_detail", None) and not tui.detail_flat_subtasks and tui.current_task_detail.subtasks:
            tui._rebuild_detail_flat(tui.detail_selected_path)
        items = tui.get_detail_items_count()
        if items <= 0:
            tui.detail_selected_index = 0
            return
        new_index = max(0, min(tui.detail_selected_index + delta, items - 1))
        tui.detail_selected_index = new_index
        tui._selected_subtask_entry()
        tui._ensure_detail_selection_visible(items)
    elif getattr(tui, "settings_mode", False):
        options = tui._settings_options()
        total = len(options)
        if total <= 0:
            tui.settings_selected_index = 0
            return
        tui.settings_selected_index = max(0, min(tui.settings_selected_index + delta, total - 1))
        tui._ensure_settings_selection_visible(total)
    else:
        total = len(tui.filtered_tasks)
        if total <= 0:
            tui.selected_index = 0
            return
        tui.selected_index = max(0, min(tui.selected_index + delta, total - 1))
        tui._ensure_selection_visible()
    tui.force_render()


__all__ = ["move_vertical_selection"]
