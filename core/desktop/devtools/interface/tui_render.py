"""Rendering helpers for TaskTrackerTUI to keep the class slim."""

from prompt_toolkit.formatted_text import FormattedText


def render_detail_text(tui) -> FormattedText:
    return tui._render_detail_text_impl()


def render_task_list_text(tui) -> FormattedText:
    return tui._render_task_list_text_impl()


def render_subtask_details(tui, path: str):
    return tui._render_subtask_details_impl(path)
