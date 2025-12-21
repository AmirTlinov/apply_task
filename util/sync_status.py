from typing import Dict, List, Tuple


def sync_status_fragments(snapshot: Dict[str, str], enabled: bool, flash: bool, filter_flash: bool) -> List[Tuple[str, str]]:
    """Unified status label for Git Projects."""
    has_issue = bool(snapshot.get("status_reason"))
    label = "Git"

    if has_issue:
        style = "class:status.fail"
    elif flash and not filter_flash:
        style = "class:icon.warn"
    elif enabled:
        style = "class:icon.check"
    else:
        style = "class:text.dim"

    return [(style, label)]


__all__ = ["sync_status_fragments"]
