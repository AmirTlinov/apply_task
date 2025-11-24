"""Small helpers to keep TaskTrackerTUI methods slim."""

from typing import Optional


def toggle_collapse_selected(tui) -> None:
    if tui.detail_mode or not tui.filtered_tasks:
        return
    task = tui.filtered_tasks[tui.selected]
    if task.id not in tui.collapsed_tasks:
        tui.collapsed_tasks.add(task.id)
    else:
        tui.collapsed_tasks.remove(task.id)
    tui.render(force=True)


def toggle_subtask_collapse(tui, expand: bool) -> None:
    entry = tui._selected_subtask_entry()
    if not entry:
        return
    path, st, _, collapsed, has_children = entry
    if not has_children:
        if not expand and "." in path:
            parent_path = ".".join(path.split(".")[:-1])
            tui._select_subtask_by_path(parent_path)
            tui._ensure_detail_selection_visible(len(tui.detail_flat_subtasks))
            tui.force_render()
        return
    if expand:
        if collapsed:
            tui.detail_collapsed.discard(path)
            tui._rebuild_detail_flat(path)
        else:
            child_path = f"{path}.0" if st.children else path
            tui._select_subtask_by_path(child_path)
            tui._rebuild_detail_flat(child_path)
    else:
        if not collapsed:
            tui.detail_collapsed.add(path)
            tui._rebuild_detail_flat(path)
        elif "." in path:
            parent_path = ".".join(path.split(".")[:-1])
            tui._select_subtask_by_path(parent_path)
            tui._ensure_detail_selection_visible(len(tui.detail_flat_subtasks))
            tui.force_render()


def maybe_reload(tui, now: Optional[float] = None) -> None:
    from time import time

    ts = now if now is not None else time()
    if ts - tui._last_check < 0.7:
        return
    tui._last_check = ts
    sig = tui.compute_signature()
    if sig == tui._last_signature:
        return
    selected_task_file = tui.tasks[tui.selected_index].task_file if tui.tasks else None
    prev_detail = tui.current_task_detail.id if (tui.detail_mode and tui.current_task_detail) else None
    prev_detail_path = tui.detail_selected_path
    prev_single = getattr(tui, "single_subtask_view", None)

    tui.load_tasks(preserve_selection=True, selected_task_file=selected_task_file, skip_sync=True)
    tui._last_signature = sig
    tui.set_status_message(tui._t("STATUS_MESSAGE_CLI_UPDATED"), ttl=3)

    if prev_detail:
        for t in tui.tasks:
            if t.id != prev_detail:
                continue
            tui.show_task_details(t)
            if prev_detail_path:
                tui._select_subtask_by_path(prev_detail_path)
            items = tui.get_detail_items_count()
            tui._ensure_detail_selection_visible(items)
            if prev_single and prev_detail_path:
                st = tui._get_subtask_by_path(prev_detail_path)
                if st:
                    tui.show_subtask_details(prev_detail_path)
            break


__all__ = ["toggle_collapse_selected", "toggle_subtask_collapse", "maybe_reload"]


__all__ = ["toggle_collapse_selected", "maybe_reload"]
