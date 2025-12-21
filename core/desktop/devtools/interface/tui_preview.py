"""Side preview renderer extracted from TaskTrackerTUI."""

from pathlib import Path
from typing import List

from prompt_toolkit.formatted_text import FormattedText

from core import Status
from infrastructure.task_file_parser import TaskFileParser


def _empty_box(message: str) -> FormattedText:
    return FormattedText(
        [
            ("class:border", "+------------------------------+\n"),
            ("class:text.dim", "| " + message.ljust(26) + " |\n"),
            ("class:border", "+------------------------------+"),
        ]
    )


def _status_chunk(detail) -> List:
    if detail.status == "DONE":
        return [("class:icon.check", "DONE ")]
    if detail.status == "ACTIVE":
        return [("class:icon.warn", "ACTV ")]
    return [("class:icon.fail", "TODO ")]


def _project_status_chunk(status) -> List:
    code = ""
    if isinstance(status, Status):
        code = status.value[0]
    elif isinstance(status, bool):
        code = "DONE" if status else "TODO"
    elif isinstance(status, str):
        code = status.strip().upper()

    if code == "DONE":
        return [("class:icon.check", "DONE ")]
    if code == "ACTIVE":
        return [("class:icon.warn", "ACTV ")]
    return [("class:icon.fail", "TODO ")]


def _build_project_preview_text(tui, task) -> FormattedText:
    done = int(getattr(task, "children_completed", 0) or 0)
    total = int(getattr(task, "children_count", 0) or 0)
    prog = int(getattr(task, "progress", 0) or 0)
    prog = max(0, min(100, prog))

    result: List = []
    result.append(("class:border", "+------------------------------------------+\n"))
    result.append(("class:border", "| "))
    result.append(("class:header", f"{tui._t('TABLE_HEADER_PROJECT')} "))
    result.append(("class:text.dim", "| "))
    result.extend(_project_status_chunk(getattr(task, "status", None)))
    summary = f"{done}/{total} {tui._t('COMPLETED_SUFFIX')}" if total else tui._t("SIDE_EMPTY_TASKS")
    result.append(("class:text.dim", summary[:20].ljust(20)))
    result.append(("class:border", " |\n"))
    result.append(("class:border", "+------------------------------------------+\n"))

    title = str(getattr(task, "name", "") or "")
    title_lines = [title[i : i + 38] for i in range(0, len(title), 38)] or [""]
    for tline in title_lines[:3]:
        result.append(("class:border", "| "))
        result.append(("class:text", tline.ljust(40)))
        result.append(("class:border", " |\n"))

    bar_width = 30
    filled = int(prog * bar_width / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    result.append(("class:border", "| "))
    result.append(("class:text.dim", f"{prog:3d}% ["))
    result.append(("class:text.dim", bar[:30]))
    result.append(("class:text.dim", "]"))
    result.append(("class:border", "    |\n"))

    path_raw = str(getattr(task, "task_file", "") or "").strip()
    if path_raw:
        tail = Path(path_raw).name
        result.append(("class:border", "+------------------------------------------+\n"))
        result.append(("class:border", "| "))
        result.append(("class:text.dim", tail[:40].ljust(40)))
        result.append(("class:border", " |\n"))

    result.append(("class:border", "+------------------------------------------+"))
    return FormattedText(result)


def build_side_preview_text(tui) -> FormattedText:
    if not tui.filtered_tasks:
        return _empty_box(tui._t("SIDE_EMPTY_TASKS"))

    idx = min(tui.selected_index, len(tui.filtered_tasks) - 1)
    task = tui.filtered_tasks[idx]
    if getattr(task, "category", "") == "project":
        return _build_project_preview_text(tui, task)
    detail = task.detail
    if not detail and task.task_file:
        try:
            path = Path(task.task_file)
            if path.exists() and path.is_dir():
                return _build_project_preview_text(tui, task)
            detail = TaskFileParser.parse(path)
        except Exception:
            detail = None
    if not detail:
        return _empty_box(tui._t("SIDE_NO_DATA"))

    result = []
    result.append(("class:border", "+------------------------------------------+\n"))
    result.append(("class:border", "| "))
    result.append(("class:header", f"{detail.id} "))
    result.append(("class:text.dim", "| "))
    result.extend(_status_chunk(detail))
    result.append(("class:text.dim", f"| {detail.priority}"))
    result.append(("class:border", "                   |\n"))
    result.append(("class:border", "+------------------------------------------+\n"))

    title_lines = [detail.title[i : i + 38] for i in range(0, len(detail.title), 38)]
    for tline in title_lines:
        result.append(("class:border", "| "))
        result.append(("class:text", tline.ljust(40)))
        result.append(("class:border", " |\n"))

    ctx = detail.domain or detail.phase or detail.component
    if ctx:
        result.append(("class:border", "| "))
        result.append(("class:text.dim", tui._t("STATUS_CONTEXT", ctx=ctx[:32]).ljust(40)))
        result.append(("class:border", " |\n"))

    prog = detail.calculate_progress()
    bar_width = 30
    filled = int(prog * bar_width / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    result.append(("class:border", "| "))
    result.append(("class:text.dim", f"{prog:3d}% ["))
    result.append(("class:text.dim", bar[:30]))
    result.append(("class:text.dim", "]"))
    result.append(("class:border", "    |\n"))

    preview_text = getattr(detail, "description", "")
    contract_text = getattr(detail, "contract", "") or ""
    if getattr(tui, "project_section", "tasks") == "plans":
        preview_text = contract_text or preview_text
    elif not preview_text:
        preview_text = contract_text
    if preview_text:
        result.append(("class:border", "+------------------------------------------+\n"))
        desc_lines = preview_text.split("\n")
        for dline in desc_lines[:5]:
            chunks = [dline[i : i + 38] for i in range(0, len(dline), 38)]
            for chunk in chunks[:3]:
                result.append(("class:border", "| "))
                result.append(("class:text", chunk.ljust(40)))
                result.append(("class:border", " |\n"))

    result.append(("class:border", "+------------------------------------------+"))
    return FormattedText(result)


__all__ = ["build_side_preview_text"]
