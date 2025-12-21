"""List editor dialog for TaskTrackerTUI (task/subtask lists)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prompt_toolkit.formatted_text import FormattedText


def render_list_editor_dialog(tui) -> FormattedText:
    content_width = tui._detail_content_width()
    inner = max(0, content_width - 2)

    stage = getattr(tui, "list_editor_stage", "menu") or "menu"
    selected = int(getattr(tui, "list_editor_selected_index", 0) or 0)
    view_offset = int(getattr(tui, "list_editor_view_offset", 0) or 0)

    target = getattr(tui, "list_editor_target", None) or {}
    is_plan_steps = str(target.get("scope", "") or "") == "task" and str(target.get("key", "") or "") == "plan_steps"

    if stage == "menu":
        title = tui._t("LIST_EDITOR_TITLE_MENU")
        options = list(getattr(tui, "_list_editor_menu_options")() or [])
        rows = [_menu_row(opt, inner) for opt in options]
    else:
        title, items = getattr(tui, "_list_editor_current_title_and_items")()
        title = title or tui._t("LIST_EDITOR_TITLE_LIST")
        plan_current = 0
        if is_plan_steps:
            try:
                _, _, root_detail, _ = getattr(tui, "_list_editor_root_detail")()
            except Exception:
                root_detail = None
            if root_detail is not None:
                steps = list(getattr(root_detail, "plan_steps", []) or [])
                plan_current = int(getattr(root_detail, "plan_current", 0) or 0)
                plan_current = max(0, min(plan_current, len(steps)))
        if is_plan_steps:
            rows = [_plan_step_row(item, idx + 1, idx, plan_current, len(items), inner) for idx, item in enumerate(items)]
        else:
            rows = [_list_row(item, idx + 1, inner) for idx, item in enumerate(items)]
        if not rows:
            rows = [[("class:text.dim", tui._pad_display(tui._t("LIST_EDITOR_EMPTY"), inner))]]
            selected = 0

    header_lines = _dialog_header_lines(tui, title, content_width)
    hint_key = "LIST_EDITOR_HINT_MENU" if stage == "menu" else ("LIST_EDITOR_HINT_STEPS" if is_plan_steps else "LIST_EDITOR_HINT_LIST")
    hint = tui._t(hint_key)
    footer_lines = [
        [("class:border", "| "), ("class:text.dim", tui._pad_display(hint, inner)), ("class:border", " |")],
        [("class:border", "+" + "=" * content_width + "+")],
    ]

    max_lines = max(5, tui.get_terminal_height() - tui.footer_height - 1)
    base_avail = max(1, max_lines - len(header_lines) - len(footer_lines))

    total = len(rows)
    if total <= 0:
        selected = 0
        view_offset = 0
    else:
        selected = max(0, min(selected, total - 1))
        visible = min(total, base_avail)
        max_offset = max(0, total - visible)
        view_offset = max(0, min(view_offset, max_offset))
        if selected < view_offset:
            view_offset = selected
        elif selected >= view_offset + visible:
            view_offset = max(0, min(selected - visible + 1, max_offset))

    # Persist clamped indices for stability.
    tui.list_editor_selected_index = selected
    tui.list_editor_view_offset = view_offset

    visible = base_avail
    hidden_above = view_offset
    hidden_below = max(0, total - (view_offset + visible))
    marker_count = int(hidden_above > 0) + int(hidden_below > 0)
    if marker_count and visible > 1:
        visible = max(1, base_avail - marker_count)
        hidden_below = max(0, total - (view_offset + visible))

    composed: List[List[Tuple[str, str]]] = []
    composed.extend(header_lines)

    if hidden_above:
        composed.append([("class:border", "| "), ("class:text.dim", f"↑ +{hidden_above}".ljust(inner)), ("class:border", " |")])

    start = view_offset
    end = min(total, start + visible)
    for idx in range(start, end):
        is_selected = idx == selected and stage != "menu"
        # In menu stage, selection is also meaningful.
        if stage == "menu":
            is_selected = idx == selected
        row_style = "class:header" if is_selected else "class:text"
        prefix = "> " if is_selected else "  "
        text_fragments = rows[idx]
        rendered = "".join(frag for _, frag in text_fragments)
        line_text = tui._trim_display(prefix + rendered, inner)
        composed.append([("class:border", "| "), (row_style, tui._pad_display(line_text, inner)), ("class:border", " |")])

    if hidden_below:
        composed.append([("class:border", "| "), ("class:text.dim", f"↓ +{hidden_below}".ljust(inner)), ("class:border", " |")])

    composed.extend(footer_lines)

    output: List[Tuple[str, str]] = []
    for idx, line in enumerate(composed[:max_lines]):
        output.extend(line)
        if idx < min(len(composed), max_lines) - 1:
            output.append(("", "\n"))
    return FormattedText(output)


def _dialog_header_lines(tui, title: str, content_width: int) -> List[List[Tuple[str, str]]]:
    inner = max(0, content_width - 2)
    lines: List[List[Tuple[str, str]]] = []
    lines.append([("class:border", "+" + "=" * content_width + "+")])
    lines.append([("class:border", "| "), ("class:header", tui._pad_display(f"{title}", inner)), ("class:border", " |")])
    lines.append([("class:border", "+" + "-" * content_width + "+")])
    return lines


def _menu_row(option: Dict[str, Any], inner: int) -> List[Tuple[str, str]]:
    label = str(option.get("label", "") or "")
    return [("class:text", label[:inner])]


def _list_row(item: str, number: int, inner: int) -> List[Tuple[str, str]]:
    text = str(item or "")
    prefix = f"{number}. "
    return [("class:text", (prefix + text)[:inner])]


def _plan_step_row(item: str, number: int, idx0: int, plan_current: int, total: int, inner: int) -> List[Tuple[str, str]]:
    text = str(item or "")
    marker = "✓" if idx0 < plan_current else ("▶" if idx0 == plan_current and plan_current < total else "·")
    prefix = f"{number}. {marker} "
    return [("class:text", (prefix + text)[:inner])]


__all__ = ["render_list_editor_dialog"]
