"""Confirmation dialog renderer for TaskTrackerTUI."""

from typing import List, Tuple

from prompt_toolkit.formatted_text import FormattedText


def render_confirm_dialog(tui) -> FormattedText:
    title = (getattr(tui, "confirm_title", "") or "").strip() or tui._t("CONFIRM_TITLE")
    lines = list(getattr(tui, "confirm_lines", []) or [])
    if not lines:
        lines = [tui._t("CONFIRM_BODY_FALLBACK")]

    term_width = max(40, int(getattr(tui, "get_terminal_width", lambda: 80)()))
    box_width = max(44, min(96, term_width - 6))
    inner = box_width - 2

    def _clip(text: str) -> str:
        if len(text) <= inner:
            return text
        if inner <= 1:
            return text[:inner]
        return text[: inner - 1] + "…"

    out: List[Tuple[str, str]] = []
    out.append(("class:border", "+" + "=" * box_width + "+\n"))
    out.append(("class:border", "| "))
    out.append(("class:header", _clip(title).ljust(inner)))
    out.append(("class:border", " |\n"))
    out.append(("class:border", "+" + "-" * box_width + "+\n"))

    for raw in lines:
        for line in str(raw).splitlines() or [""]:
            out.append(("class:border", "| "))
            out.append(("class:text", _clip(line).ljust(inner)))
            out.append(("class:border", " |\n"))

    out.append(("class:border", "+" + "-" * box_width + "+\n"))
    hint = tui._t("CONFIRM_HINT")
    out.append(("class:border", "| "))
    out.append(("class:text.dim", _clip(hint).ljust(inner)))
    out.append(("class:border", " |\n"))
    out.append(("class:border", "+" + "=" * box_width + "+"))
    return FormattedText(out)


__all__ = ["render_confirm_dialog"]

