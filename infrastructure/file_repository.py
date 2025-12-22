import time
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from application.ports import TaskRepository
from core import TaskDetail
from core.status import normalize_status_code
from core.desktop.devtools.interface.tasks_dir_resolver import get_tasks_dir_for_project
from infrastructure.task_file_parser import TaskFileParser


def _is_reserved_dir(path: Path) -> bool:
    return ".snapshots" in path.parts or ".trash" in path.parts


class FileTaskRepository(TaskRepository):
    """File-backed repository for both Plans and Tasks.

    Storage:
    - Directory: resolved via tasks_dir_resolver (typically `~/.tasks/<namespace>`)
    - Files: `PLAN-###.task` and `TASK-###.task`
    """

    def __init__(self, tasks_dir: Path | None):
        self.tasks_dir = get_tasks_dir_for_project(use_global=True, create=False) if tasks_dir is None else tasks_dir

    def _resolve_path(self, item_id: str, domain: str = "") -> Path:
        if self.tasks_dir is None:
            raise ValueError("tasks_dir is not set for FileTaskRepository")
        if ".." in item_id or "/" in item_id or "\\" in item_id:
            raise ValueError(f"Invalid id: contains path traversal characters: {item_id}")
        if domain and (".." in domain or domain.startswith("/") or "\\" in domain):
            raise ValueError(f"Invalid domain: contains path traversal characters: {domain}")
        base = self.tasks_dir / domain if domain else self.tasks_dir
        resolved = (base / f"{item_id}.task").resolve()
        if not resolved.is_relative_to(self.tasks_dir.resolve()):
            raise ValueError(f"Path traversal detected: {resolved} is outside {self.tasks_dir}")
        return resolved

    def _assign_domain(self, detail: TaskDetail, path: Path) -> None:
        if detail.domain:
            return
        try:
            rel = path.parent.relative_to(self.tasks_dir)
            detail.domain = "" if str(rel) == "." else rel.as_posix()
        except Exception:
            detail.domain = ""

    def load(self, task_id: str, domain: str = "") -> Optional[TaskDetail]:
        path = self._resolve_path(task_id, domain)
        if path.exists():
            detail = TaskFileParser.parse(path)
            if detail:
                self._assign_domain(detail, path)
            return detail

        candidates = [f for f in self.tasks_dir.rglob(f"{task_id}.task") if not _is_reserved_dir(f)]
        for candidate in candidates:
            try:
                detail = TaskFileParser.parse(candidate)
                if detail:
                    self._assign_domain(detail, candidate)
                    return detail
            except Exception:
                continue
        return None

    def save(self, task: TaskDetail) -> None:
        path = self._resolve_path(task.id, task.domain)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Monotonic revision (etag-like): always bump on write.
        # Best-effort: if file exists but parsing fails, fall back to in-memory revision.
        disk_revision = 0
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1]) or {}
                    disk_revision = int((meta or {}).get("revision", 0) or 0)
            except Exception:
                disk_revision = 0
        current_revision = int(getattr(task, "revision", 0) or 0)
        task.revision = max(0, max(current_revision, disk_revision)) + 1
        path.write_text(task.to_file_content(), encoding="utf-8")

    def list(self, domain_path: str = "", skip_sync: bool = False) -> List[TaskDetail]:
        root = self.tasks_dir / domain_path if domain_path else self.tasks_dir
        items: List[TaskDetail] = []
        for file in root.rglob("*.task"):
            if _is_reserved_dir(file):
                continue
            stem = file.stem
            if not (stem.startswith("TASK-") or stem.startswith("PLAN-")):
                continue
            parsed = TaskFileParser.parse(file)
            if parsed:
                self._assign_domain(parsed, file)
                items.append(parsed)
        return items

    def compute_signature(self) -> int:
        sig = 0
        for f in self.tasks_dir.rglob("*.task"):
            if _is_reserved_dir(f):
                continue
            if not (f.stem.startswith("TASK-") or f.stem.startswith("PLAN-")):
                continue
            try:
                st = f.stat()
                sig ^= int(st.st_mtime_ns) ^ int(st.st_size)
            except OSError:
                continue
        return sig if sig else int(time.time_ns())

    def _next_id_for_prefix(self, prefix: str) -> str:
        ids: list[int] = []
        for f in self.tasks_dir.rglob(f"{prefix}-*.task"):
            # Keep IDs monotonic: include `.trash` and `.snapshots` to avoid reusing IDs.
            try:
                ids.append(int(f.stem.split("-")[1]))
            except (IndexError, ValueError):
                continue
        next_num = (max(ids) + 1) if ids else 1
        return f"{prefix}-{next_num:03d}"

    def next_id(self) -> str:
        return self._next_id_for_prefix("TASK")

    def next_plan_id(self) -> str:
        return self._next_id_for_prefix("PLAN")

    def delete(self, task_id: str, domain: str = "") -> bool:
        path = self._resolve_path(task_id, domain)
        candidates = (
            [path]
            if path.exists()
            else [f for f in self.tasks_dir.rglob(f"{task_id}.task") if not _is_reserved_dir(f)]
        )
        deleted = False
        for candidate in candidates:
            try:
                candidate.unlink()
                deleted = True
            except OSError:
                continue
        return deleted

    def move(self, task_id: str, new_domain: str, current_domain: str = "") -> bool:
        detail = self.load(task_id, current_domain)
        if not detail:
            return False
        old_path = Path(detail.filepath)
        detail.domain = new_domain
        self.save(detail)
        dest_path = self._resolve_path(task_id, new_domain)
        if old_path.exists() and old_path != dest_path:
            try:
                old_path.unlink()
            except OSError:
                pass
        return True

    def move_glob(self, pattern: str, new_domain: str) -> int:
        moved = 0
        for file in self.tasks_dir.rglob("*.task"):
            if _is_reserved_dir(file):
                continue
            try:
                rel = file.relative_to(self.tasks_dir)
            except Exception:
                rel = file
            if rel.match(pattern):
                item_id = file.stem
                if self.move(item_id, new_domain, current_domain=str(rel.parent)) or self.move(item_id, new_domain):
                    moved += 1
        return moved

    def delete_glob(self, pattern: str) -> int:
        removed = 0
        for file in self.tasks_dir.rglob("*.task"):
            if _is_reserved_dir(file):
                continue
            try:
                rel = file.relative_to(self.tasks_dir)
            except Exception:
                rel = file
            if rel.match(pattern):
                try:
                    file.unlink()
                    removed += 1
                except OSError:
                    continue
        return removed

    def clean_filtered(self, tag: str = "", status: str = "", phase: str = "") -> Tuple[List[str], int]:
        matched: list[str] = []
        removed = 0
        norm_tag = tag.strip().lower() if tag else ""
        norm_status = normalize_status_code(status) if status else ""
        norm_phase = phase.strip().lower() if phase else ""

        for file in self.tasks_dir.rglob("*.task"):
            if _is_reserved_dir(file):
                continue
            if not (file.stem.startswith("TASK-") or file.stem.startswith("PLAN-")):
                continue
            parsed = TaskFileParser.parse(file)
            if not parsed:
                continue
            tags = [t.strip().lower() for t in (parsed.tags or [])]
            if norm_tag and norm_tag not in tags:
                continue
            if norm_status:
                parsed_status = normalize_status_code(parsed.status) if parsed.status else ""
                if parsed_status != norm_status:
                    continue
            if norm_phase and (parsed.phase or "").strip().lower() != norm_phase:
                continue
            matched.append(parsed.id)
            try:
                file.unlink()
                removed += 1
            except OSError:
                continue
        return matched, removed


__all__ = ["FileTaskRepository"]
