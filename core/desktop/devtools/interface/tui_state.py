"""Small helpers to keep TaskTrackerTUI methods slim."""

from typing import Optional

from core.desktop.devtools.interface.tui_detail_tree import canonical_path, first_child_key, plan_key


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
    key = entry.key
    collapsed = bool(getattr(entry, "collapsed", False))
    has_children = bool(getattr(entry, "has_children", False))

    if not has_children:
        if not expand and getattr(entry, "parent_key", None):
            tui._select_subtask_by_path(entry.parent_key)
            tui.force_render()
        return

    if expand:
        if collapsed:
            tui.detail_collapsed.discard(key)
            tui._rebuild_detail_flat(key)
            return
        child = first_child_key(entry)
        if child:
            tui._select_subtask_by_path(child)
            tui._rebuild_detail_flat(child)
        return

    # collapse
    if not collapsed:
        tui.detail_collapsed.add(key)
        tui._rebuild_detail_flat(key)
        return
    parent = getattr(entry, "parent_key", None)
    if parent:
        tui._select_subtask_by_path(parent)
        tui.force_render()


def _iter_subtree_nodes(entry):
    """Iterate nodes in the subtree rooted at entry (includes root), deterministic DFS."""
    stack = [(entry.kind, entry.key, entry.node)]
    while stack:
        kind, key, node = stack.pop()
        yield kind, key, node
        if kind == "step":
            plan = getattr(node, "plan", None)
            if plan is not None:
                stack.append(("plan", plan_key(key), plan))
            continue
        if kind == "plan":
            plan = node
            tasks = list(getattr(plan, "tasks", []) or [])
            base = canonical_path(key, "plan")
            for t_idx in reversed(range(len(tasks))):
                stack.append(("task", f"{base}.t:{t_idx}", tasks[t_idx]))
            continue
        # task
        task = node
        steps = list(getattr(task, "steps", []) or [])
        for s_idx in reversed(range(len(steps))):
            stack.append(("step", f"{key}.s:{s_idx}", steps[s_idx]))


def _has_children(kind: str, node) -> bool:
    if kind == "step":
        return getattr(node, "plan", None) is not None
    if kind == "plan":
        return bool(list(getattr(node, "tasks", []) or []))
    if kind == "task":
        return bool(list(getattr(node, "steps", []) or []))
    return False


def collapse_subtask_descendants(tui) -> None:
    """Collapse all descendants of the selected node (keeps the node itself expanded)."""
    entry = tui._selected_subtask_entry()
    if not entry:
        return
    root_key = entry.key
    first = True
    changed = False
    for kind, key, node in _iter_subtree_nodes(entry):
        if first:
            first = False
            continue
        if _has_children(kind, node) and key not in tui.detail_collapsed:
            tui.detail_collapsed.add(key)
            changed = True

    if not changed:
        return
    if getattr(tui, "current_task_detail", None) and getattr(tui, "collapsed_by_task", None) is not None:
        tui.collapsed_by_task[tui.current_task_detail.id] = set(tui.detail_collapsed)
    tui._rebuild_detail_flat(root_key)
    tui.force_render()


def expand_subtask_descendants(tui) -> None:
    """Expand the selected node and all its descendants."""
    entry = tui._selected_subtask_entry()
    if not entry:
        return
    root_key = entry.key
    changed = False
    for kind, key, node in _iter_subtree_nodes(entry):
        if _has_children(kind, node) and key in tui.detail_collapsed:
            tui.detail_collapsed.discard(key)
            changed = True

    if not changed:
        return
    if getattr(tui, "current_task_detail", None) and getattr(tui, "collapsed_by_task", None) is not None:
        tui.collapsed_by_task[tui.current_task_detail.id] = set(tui.detail_collapsed)
    tui._rebuild_detail_flat(root_key)
    tui.force_render()


def maybe_reload(tui, now: Optional[float] = None) -> None:
    from time import time

    ts = now if now is not None else time()
    if ts - tui._last_check < 0.3:
        return
    tui._last_check = ts

    sig = tui.compute_signature()
    if sig == tui._last_signature:
        return
    selected_task_file = tui.tasks[tui.selected_index].task_file if tui.tasks else None
    prev_detail = tui.current_task_detail.id if (tui.detail_mode and tui.current_task_detail) else None
    prev_detail_path = tui.detail_selected_path

    # Newer TUI supports multiple within-project list sections (plans/tasks) and should
    # reload the active section. Fallback to legacy load_tasks for unit stubs.
    if hasattr(tui, "load_current_list"):
        tui.load_current_list(preserve_selection=True, selected_task_file=selected_task_file, skip_sync=True)
    else:  # pragma: no cover - compatibility with minimal test doubles
        tui.load_tasks(preserve_selection=True, selected_task_file=selected_task_file, skip_sync=True)
    tui._last_signature = sig
    tui.set_status_message(tui._t("STATUS_MESSAGE_EXTERNAL_UPDATED"), ttl=3)

    if prev_detail:
        for t in tui.tasks:
            if t.id != prev_detail:
                continue
            tui.show_task_details(t)
            if prev_detail_path:
                tui._select_subtask_by_path(prev_detail_path)
            items = tui.get_detail_items_count()
            break


__all__ = [
    "toggle_collapse_selected",
    "toggle_subtask_collapse",
    "collapse_subtask_descendants",
    "expand_subtask_descendants",
    "maybe_reload",
]
