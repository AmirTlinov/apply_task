"""Mouse event handling helpers for TaskTrackerTUI."""

from prompt_toolkit.mouse_events import MouseEventType, MouseButton, MouseModifier


def _handle_middle_paste(tui, mouse_event):
    if (
        mouse_event.event_type == MouseEventType.MOUSE_UP
        and mouse_event.button == MouseButton.MIDDLE
        and getattr(tui, "editing_mode", False)
        and getattr(tui, "edit_context", "") == "token"
    ):
        tui._paste_from_clipboard()
        return True
    return False


def _handle_settings_mode(tui, mouse_event):
    if not getattr(tui, "settings_mode", False) or getattr(tui, "editing_mode", False):
        return None
    if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
        tui.move_settings_selection(1)
        return True
    if mouse_event.event_type == MouseEventType.SCROLL_UP:
        tui.move_settings_selection(-1)
        return True
    if mouse_event.event_type == MouseEventType.MOUSE_UP and mouse_event.button == MouseButton.LEFT:
        tui.activate_settings_option()
        return True
    return True


def _handle_scroll(tui, mouse_event):
    shift = MouseModifier.SHIFT in mouse_event.modifiers
    vertical_step = 1
    horizontal_step = 5
    if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
        if shift:
            tui.horizontal_offset = min(200, getattr(tui, "horizontal_offset", 0) + horizontal_step)
        else:
            tui.move_vertical_selection(vertical_step)
        return True
    if mouse_event.event_type == MouseEventType.SCROLL_UP:
        if shift:
            tui.horizontal_offset = max(0, getattr(tui, "horizontal_offset", 0) - horizontal_step)
        else:
            tui.move_vertical_selection(-vertical_step)
        return True
    return False


def _handle_detail_click(tui, mouse_event):
    if not getattr(tui, "detail_mode", False):
        return None
    if not getattr(tui, "current_task_detail", None):
        return True

    # Detail tab bar click (hitboxes are computed by the renderer).
    if mouse_event.event_type == MouseEventType.MOUSE_UP and mouse_event.button == MouseButton.LEFT:
        hitboxes = getattr(tui, "_detail_tab_hitboxes", None)
        if isinstance(hitboxes, dict):
            try:
                y = int(getattr(mouse_event.position, "y", -1))
                x = int(getattr(mouse_event.position, "x", -1))
            except Exception:
                y = -1
                x = -1
            if y == int(hitboxes.get("y", -2)):
                for start, end, tab_id in list(hitboxes.get("ranges", []) or []):
                    try:
                        if int(start) <= x < int(end):
                            current = getattr(tui, "detail_tab", "overview") or "overview"
                            if tab_id != current:
                                tui.detail_tab = tab_id
                                if tab_id != "overview":
                                    getattr(tui, "detail_tab_scroll_offsets", {}).setdefault(tab_id, 0)
                            tui.force_render()
                            return True
                    except Exception:
                        continue
                # Click on the tab bar line, but not on a tab.
                return True

    idx = tui._subtask_index_from_y(mouse_event.position.y)
    if idx is None:
        return True

    detail = getattr(tui, "current_task_detail", None)
    if detail and getattr(detail, "kind", "task") == "plan" and getattr(tui, "detail_tab", "overview") == "overview":
        plan_tasks = tui._plan_detail_tasks() if hasattr(tui, "_plan_detail_tasks") else []
        if not plan_tasks:
            return True
        idx = max(0, min(idx, len(plan_tasks) - 1))
        if getattr(tui, "detail_selected_index", None) == idx:
            if hasattr(tui, "_open_selected_plan_task_detail"):
                tui._open_selected_plan_task_detail()
        else:
            tui.detail_selected_index = idx
            tui.detail_selected_task_id = getattr(plan_tasks[idx], "id", None)
            tui.force_render()
        return True

    if not getattr(tui, "detail_flat_subtasks", None):
        return True
    idx = max(0, min(idx, len(tui.detail_flat_subtasks) - 1))
    path = tui.detail_flat_subtasks[idx].key
    if getattr(tui, "detail_selected_index", None) == idx:
        tui.show_subtask_details(path)
    else:
        tui.detail_selected_index = idx
        tui._selected_subtask_entry()
    return True


def _handle_list_click(tui, mouse_event):
    if getattr(tui, "detail_mode", False):
        return None
    idx = tui._task_index_from_y(mouse_event.position.y)
    if idx is None:
        return True
    if getattr(tui, "selected_index", None) == idx:
        tui.show_task_details(tui.filtered_tasks[idx])
    else:
        tui.selected_index = idx
        tui._ensure_selection_visible()
    return True


def handle_body_mouse(tui, mouse_event):
    """Route mouse events for TaskTrackerTUI body."""
    if _handle_middle_paste(tui, mouse_event):
        return None
    if getattr(tui, "editing_mode", False):
        return NotImplemented
    settings = _handle_settings_mode(tui, mouse_event)
    if settings is True:
        return None
    if settings is not None:
        return NotImplemented
    if _handle_scroll(tui, mouse_event):
        return None
    if mouse_event.event_type == MouseEventType.MOUSE_UP and mouse_event.button == MouseButton.LEFT:
        if _handle_detail_click(tui, mouse_event):
            return None
        if _handle_list_click(tui, mouse_event):
            return None
    return NotImplemented


__all__ = ["handle_body_mouse"]
