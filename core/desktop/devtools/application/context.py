import re
from pathlib import Path
from typing import List, Optional, Tuple

from core.desktop.devtools.interface.i18n import translate
from core.desktop.devtools.interface.tasks_dir_resolver import resolve_project_root


def _sanitize_domain(domain: Optional[str]) -> str:
    if not domain:
        return ""
    candidate = Path(domain.strip("/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(translate("ERR_INVALID_FOLDER"))
    return candidate.as_posix()


def _last_file_candidates() -> List[Path]:
    """Return candidate locations for `.last` pointer.

    Prefer the project root for stability across subdirectories.
    Fallback to CWD for non-git contexts (or when root cannot be resolved).
    """
    candidates: List[Path] = []
    try:
        candidates.append((resolve_project_root() / ".last").resolve())
    except Exception:
        pass
    candidates.append(Path(".last").resolve())

    seen: set[str] = set()
    unique: List[Path] = []
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def save_last_task(task_id: str, domain: str = "") -> None:
    for candidate in _last_file_candidates():
        try:
            candidate.write_text(f"{task_id}@{domain}", encoding="utf-8")
            return
        except Exception:
            continue


def get_last_task() -> Tuple[Optional[str], Optional[str]]:
    last_path: Optional[Path] = None
    for candidate in _last_file_candidates():
        if candidate.exists():
            last_path = candidate
            break
    if not last_path:
        return None, None

    raw = last_path.read_text(encoding="utf-8").strip()
    if "@" in raw:
        tid, domain = raw.split("@", 1)
        return tid or None, domain or None
    return raw or None, None


def clear_last_task() -> bool:
    """Clear stored focus pointer (`.last`).

    Returns True if any candidate file was removed.
    """
    removed = False
    for candidate in _last_file_candidates():
        try:
            if candidate.exists():
                candidate.unlink()
                removed = True
        except Exception:
            continue
    return removed


def normalize_task_id(raw: str) -> str:
    """Normalize task ID with path traversal protection."""
    value = raw.strip().upper()
    # SEC: Prevent path traversal attacks
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid task_id: contains forbidden characters: {raw}")
    m = re.match(r"^(TASK|PLAN)-(\d+)$", value)
    if m:
        prefix, num_raw = m.group(1), m.group(2)
        num = int(num_raw)
        return f"{prefix}-{num:03d}"
    if value.isdigit():
        return f"TASK-{int(value):03d}"
    return value


def derive_domain_explicit(domain: Optional[str], phase: Optional[str], component: Optional[str]) -> str:
    """Build domain path from explicit domain or phase/component fallback."""
    if domain:
        return _sanitize_domain(domain)
    parts = []
    if phase:
        parts.append(phase.strip("/"))
    if component:
        parts.append(component.strip("/"))
    if not parts:
        return ""
    return _sanitize_domain("/".join(parts))


def derive_folder_explicit(domain: Optional[str], phase: Optional[str], component: Optional[str]) -> str:
    """Alias for derive_domain_explicit (kept for call-site clarity)."""
    return derive_domain_explicit(domain, phase, component)


def resolve_task_reference(
    raw_task_id: Optional[str],
    domain: Optional[str],
    phase: Optional[str],
    component: Optional[str],
) -> Tuple[str, str]:
    """
    Return (task_id, domain) with shortcuts:
    '.' / 'last' / '@last' / empty → last task from .last.
    """
    sentinel = (raw_task_id or "").strip()
    use_last = not sentinel or sentinel in (".", "last", "@last")
    if use_last:
        last_id, last_domain = get_last_task()
        if not last_id:
            raise ValueError(translate("ERR_NO_LAST_TASK"))
        resolved_domain = derive_domain_explicit(domain, phase, component) or (last_domain or "")
        return normalize_task_id(last_id), resolved_domain or ""
    resolved_domain = derive_domain_explicit(domain, phase, component)
    return normalize_task_id(sentinel), resolved_domain


def parse_smart_title(title: str) -> Tuple[str, List[str], List[str]]:
    tags = re.findall(r"#(\w+)", title)
    deps = re.findall(r"@(TASK-\d+)", title.upper())
    clean = re.sub(r"#\w+", "", title)
    clean = re.sub(r"@TASK-\d+", "", clean, flags=re.IGNORECASE).strip()
    return clean, [t.lower() for t in tags], deps


__all__ = [
    "save_last_task",
    "get_last_task",
    "clear_last_task",
    "normalize_task_id",
    "derive_domain_explicit",
    "derive_folder_explicit",
    "resolve_task_reference",
    "parse_smart_title",
]
