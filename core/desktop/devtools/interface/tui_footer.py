"""Footer renderer for TaskTrackerTUI."""

import time
from typing import List, Tuple

from prompt_toolkit.formatted_text import FormattedText
from wcwidth import wcwidth


def _display_width(text: str) -> int:
    text = (text or "").expandtabs(4)
    width = 0
    for ch in text:
        w = wcwidth(ch)
        if w is None or w < 0:
            w = 0
        width += w
    return width


def _trim_display(text: str, width: int) -> str:
    text = (text or "").expandtabs(4)
    acc: List[str] = []
    used = 0
    for ch in text:
        w = wcwidth(ch)
        if w is None or w < 0:
            w = 0
        if used + w > width:
            break
        acc.append(ch)
        used += w
    return "".join(acc)


def _pad_display(text: str, width: int) -> str:
    trimmed = _trim_display(text, width)
    pad = max(0, width - _display_width(trimmed))
    return trimmed + (" " * pad)


def _slice_display(text: str, start_cols: int, width_cols: int) -> str:
    """Slice text by display-width columns (wcwidth-aware)."""
    if width_cols <= 0:
        return ""
    text = str(text or "")
    start_cols = max(0, start_cols)

    # Advance to start.
    i = 0
    cols = 0
    while i < len(text) and cols < start_cols:
        w = wcwidth(text[i])
        if w is None or w < 0:
            w = 0
        if cols + w > start_cols:
            break
        cols += w
        i += 1

    # Take up to width_cols.
    out: List[str] = []
    used = 0
    while i < len(text) and used < width_cols:
        w = wcwidth(text[i])
        if w is None or w < 0:
            w = 0
        if used + w > width_cols:
            break
        out.append(text[i])
        used += w
        i += 1
    return "".join(out)


def _allocate_pair(inner_width: int, *, left_weight: int, right_weight: int) -> tuple[int, int]:
    sep_w = _display_width(" | ")
    avail = max(0, inner_width - sep_w)
    if avail == 0:
        return 0, 0
    total = max(1, left_weight + right_weight)
    right_w = int((avail * right_weight) / total)
    left_w = avail - right_w

    # Keep both sides usable on narrow terminals.
    min_seg = 12
    if avail >= min_seg * 2:
        if left_w < min_seg:
            left_w = min_seg
            right_w = avail - left_w
        elif right_w < min_seg:
            right_w = min_seg
            left_w = avail - right_w
    return left_w, right_w


def _allocate_triple(
    inner_width: int,
    *,
    left_weight: int,
    middle_weight: int,
    right_weight: int,
) -> tuple[int, int, int]:
    sep_w = _display_width(" | ") * 2
    avail = max(0, inner_width - sep_w)
    if avail == 0:
        return 0, 0, 0
    total = max(1, left_weight + middle_weight + right_weight)
    left = int((avail * left_weight) / total)
    middle = int((avail * middle_weight) / total)
    right = avail - left - middle

    # Keep segments usable on wide enough terminals.
    min_seg = 12
    if avail >= min_seg * 3:
        if left < min_seg:
            left = min_seg
        if middle < min_seg:
            middle = min_seg
        if right < min_seg:
            right = min_seg
        overflow = (left + middle + right) - avail
        if overflow > 0:
            # Trim from the largest segment first.
            sizes = [("left", left), ("middle", middle), ("right", right)]
            sizes.sort(key=lambda x: x[1], reverse=True)
            for name, _size in sizes:
                if overflow <= 0:
                    break
                if name == "left" and left > min_seg:
                    take = min(overflow, left - min_seg)
                    left -= take
                    overflow -= take
                if name == "middle" and middle > min_seg:
                    take = min(overflow, middle - min_seg)
                    middle -= take
                    overflow -= take
                if name == "right" and right > min_seg:
                    take = min(overflow, right - min_seg)
                    right -= take
                    overflow -= take
    return left, middle, right


def _fit_kv(label: str, value: str, width: int) -> str:
    label = str(label or "")
    value = str(value or "—")
    label_w = _display_width(label)
    if width <= 0:
        return ""
    if _display_width(label + value) <= width:
        return _pad_display(label + value, width)
    avail = max(0, width - label_w)
    if avail <= 1:
        return _pad_display(_trim_display(label + value, width), width)
    trimmed = _trim_display(value, max(0, avail - 1)) + "…"
    return _pad_display(label + trimmed, width)


def _strip_id_prefix(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    for prefix in ("PLAN-", "TASK-", "STEP-", "NODE-"):
        if raw.upper().startswith(prefix):
            return raw[len(prefix):]
    return raw


def build_footer_text(tui) -> FormattedText:
    term_width = max(20, int(getattr(tui, "get_terminal_width")() if hasattr(tui, "get_terminal_width") else 80))
    inner_width = max(0, term_width - 4)
    border = "+" + "-" * (inner_width + 2) + "+"

    def boxed(rows: List[str]) -> FormattedText:
        parts: List[Tuple[str, str]] = []
        parts.append(("class:border", border + "\n"))
        for row in rows:
            parts.append(("class:border", "| "))
            parts.append(("class:text", _pad_display(row, inner_width)))
            parts.append(("class:border", " |\n"))
        parts.append(("class:border", border))
        return FormattedText(parts)

    # Empty-state CTA footer (keep height stable and compact).
    detail_mode = bool(getattr(tui, "detail_mode", False))
    if not getattr(tui, "filtered_tasks", []) and not detail_mode:
        row1 = f"{tui._t('CTA_CREATE_TASK')} · {tui._t('CTA_IMPORT_TASK')}"
        row2 = tui._t("CTA_DOMAIN_HINT")
        return boxed([row1, row2])

    detail = tui._current_task_detail_obj()
    desc_full = tui._current_description_snippet()
    if not desc_full and not detail_mode:
        desc_full = tui._t("DESCRIPTION_MISSING")
    domain = "-"
    start_time = "-"
    finish_time = "-"
    if detail:
        domain = str(getattr(detail, "domain", "") or "").strip() or "-"
        if getattr(detail, "created", None):
            start_time = str(detail.created)
        if detail.status == "DONE" and getattr(detail, "updated", None):
            finish_time = str(detail.updated)
    duration_value = tui._task_duration_value(detail)

    # Hover-driven scroll (footer is a separate Window, mouse events arrive there).
    now = time.time()
    hover_last_at = float(getattr(tui, "_footer_desc_hover_last_at", 0.0) or 0.0)
    hover_y = getattr(tui, "_footer_desc_hover_y", None)
    hovered = (now - hover_last_at) <= 1.5 and hover_y == 2
    hover_since = float(getattr(tui, "_footer_desc_hover_since", 0.0) or 0.0)
    if not hovered:
        setattr(tui, "_footer_desc_hover_since", 0.0)
    elif hover_since <= 0:
        hover_since = now
        setattr(tui, "_footer_desc_hover_since", now)

    sep = " | "

    time_value = f"{start_time} → {finish_time}"

    # Row 1: Folder | Time | Duration (requested order).
    # Allocate a bit more room to Duration so even long i18n keys remain readable on ~80-col terminals.
    row1_left_w, row1_mid_w, row1_right_w = _allocate_triple(inner_width, left_weight=3, middle_weight=2, right_weight=2)
    row1_left = _fit_kv(f"{tui._t('DOMAIN')}: ", domain, row1_left_w)
    row1_mid = _fit_kv(f"{tui._t('FOOTER_TIME')}: ", time_value, row1_mid_w)
    row1_right = _fit_kv(f"{tui._t('FOOTER_DURATION')}: ", str(duration_value or "—"), row1_right_w)

    show_desc = True
    if detail_mode and detail:
        title_value = " ".join(str(getattr(detail, "title", "") or "").split()).strip()
        desc_value = " ".join(str(desc_full or "").split()).strip()
        if desc_value and title_value and desc_value.lower() == title_value.lower():
            desc_full = ""
    if detail_mode and not desc_full:
        show_desc = False

    row2 = ""
    if show_desc:
        # Row 2: Description (hover-scroll).
        desc_label = f"{tui._t('DESCRIPTION')}: "
        desc_label_w = _display_width(desc_label)
        desc_value_w = max(0, inner_width - desc_label_w)
        desc_value = str(desc_full or "").strip()
        desc_value = " ".join(desc_value.split())
        desc_total_w = _display_width(desc_value)
        if desc_total_w <= desc_value_w or desc_value_w <= 0:
            desc_rendered = _slice_display(desc_value, 0, desc_value_w)
        else:
            if hovered and hover_since > 0:
                max_offset = max(0, desc_total_w - desc_value_w)
                offset = int((now - hover_since) * 3.0) % (max_offset + 1)
                desc_rendered = _slice_display(desc_value, offset, desc_value_w)
            else:
                desc_rendered = _slice_display(desc_value, 0, max(0, desc_value_w - 1)) + "…"
        row2 = _pad_display(desc_label + desc_rendered, inner_width)

    extra_rows: List[str] = []
    if detail_mode and detail and getattr(detail, "kind", "task") != "plan":
        selected_entry = None
        if hasattr(tui, "_selected_subtask_entry"):
            try:
                if hasattr(tui, "_ensure_detail_flat"):
                    tui._ensure_detail_flat(getattr(tui, "detail_selected_path", None))
                selected_entry = tui._selected_subtask_entry()
            except Exception:
                selected_entry = None
        target = None
        step_label = tui._t("LIST_EDITOR_SCOPE_SUBTASK", fallback="Step")
        if selected_entry and getattr(selected_entry, "kind", "") == "step":
            target = selected_entry.node
            step_id = _strip_id_prefix(getattr(target, "id", ""))
            step_title = str(getattr(target, "title", "") or "").strip()
            step_title = " ".join(step_title.split())
            step_prefix = f"{step_label}: "
            # Avoid duplicating the selected row title (it is already visible in the list).
            step_value = step_id or step_title
            step_row = _fit_kv(step_prefix, step_value or "—", inner_width)
            extra_rows.append(step_row)
        if target is None:
            target = detail
        criteria = "; ".join(list(getattr(target, "success_criteria", []) or [])) or "—"
        tests = "; ".join(list(getattr(target, "tests", []) or [])) or "—"
        blockers_list = list(getattr(target, "blockers", []) or [])
        if target is not detail:
            for item in list(getattr(detail, "blockers", []) or []):
                if item not in blockers_list:
                    blockers_list.append(item)
        blockers = "; ".join(blockers_list) or "—"
        checks_line = f"{tui._t('CRITERIA')}: {criteria} | {tui._t('TESTS')}: {tests} | {tui._t('BLOCKERS')}: {blockers}"
        if _display_width(checks_line) > inner_width:
            checks_line = _trim_display(checks_line, max(0, inner_width - 1)) + "…"
        extra_rows.append(_pad_display(checks_line, inner_width))

    rows = [f"{row1_left}{sep}{row1_mid}{sep}{row1_right}" if inner_width > 0 else ""]
    if row2:
        rows.append(row2 if inner_width > 0 else "")
    rows += extra_rows

    if hasattr(tui, "_set_footer_height"):
        if not any(
            getattr(tui, flag, False)
            for flag in ("confirm_mode", "settings_mode", "checkpoint_mode", "list_editor_mode")
        ):
            desired_height = len(rows) + 2
            if int(getattr(tui, "footer_height", 0) or 0) != desired_height:
                tui._set_footer_height(desired_height)

    return boxed(rows)


__all__ = ["build_footer_text"]
