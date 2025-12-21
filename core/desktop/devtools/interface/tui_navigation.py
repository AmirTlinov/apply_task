"""Navigation helpers for TaskTrackerTUI to keep tasks_app slim."""



def move_vertical_selection(tui, delta: int) -> None:
    """
    Move selected row/panel pointer by `delta`, clamping to available items.

    Works both in list mode (task rows) and detail mode (subtasks/dependencies).
    """
    if getattr(tui, "detail_mode", False):
        detail = getattr(tui, "current_task_detail", None)
        if detail and getattr(detail, "kind", "task") == "plan" and getattr(tui, "detail_tab", "overview") == "overview":
            cached = getattr(tui, "detail_plan_tasks", []) or []
            if cached and not getattr(tui, "_detail_plan_tasks_dirty", False):
                plan_tasks = cached
            else:
                plan_tasks = tui._plan_detail_tasks() if hasattr(tui, "_plan_detail_tasks") else cached
            items = len(plan_tasks)
            if items <= 0:
                tui.detail_selected_index = 0
                tui.detail_selected_task_id = None
                return
            new_index = max(0, min(tui.detail_selected_index + delta, items - 1))
            tui.detail_selected_index = new_index
            tui.detail_selected_task_id = getattr(plan_tasks[new_index], "id", None)
            tui.force_render()
            return
        # Keep flat cache in sync for step-tree navigation.
        if detail and not tui.detail_flat_subtasks and getattr(detail, "steps", None):
            tui._rebuild_detail_flat(tui.detail_selected_path)
        items = tui.get_detail_items_count()
        if items <= 0:
            tui.detail_selected_index = 0
            return
        new_index = max(0, min(tui.detail_selected_index + delta, items - 1))
        tui.detail_selected_index = new_index
        tui._selected_subtask_entry()
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
