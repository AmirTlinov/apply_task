from pathlib import Path
import os
import subprocess
import shutil
import threading
from urllib.parse import urlparse


_LEGACY_MIGRATION_LOCK = threading.Lock()


def _git_remote_url_from_config(project_dir: Path) -> str | None:
    """Best-effort read of remote origin URL from .git/config (no git subprocess)."""
    git_config = project_dir / ".git" / "config"
    if not git_config.exists():
        return None

    try:
        content = git_config.read_text(encoding="utf-8")
    except Exception:
        return None

    current_remote: str | None = None
    remotes: dict[str, str] = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current_remote = None
            if line.lower().startswith('[remote "') and line.endswith('"]'):
                current_remote = line[len('[remote "') : -len('"]')]
            continue
        if current_remote and line.startswith("url = "):
            remotes.setdefault(current_remote, line.split("url = ", 1)[1].strip())

    return remotes.get("origin") or (next(iter(remotes.values()), None) if remotes else None)


def _namespace_from_remote_url(url: str) -> str | None:
    """Derive canonical namespace from a git remote URL.

    Supports:
    - https://host/owner/repo(.git)
    - ssh://git@host/owner/repo(.git)
    - git@host:owner/repo(.git) (scp-like)
    """
    raw = (url or "").strip()
    if not raw:
        return None

    path = ""
    try:
        if "://" in raw:
            parsed = urlparse(raw)
            path = parsed.path or ""
        elif "@" in raw and ":" in raw:
            # scp-like form: git@github.com:owner/repo.git
            path = raw.split(":", 1)[1]
        else:
            # Fallback: treat as path-like
            path = raw
    except Exception:
        path = raw

    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) < 2:
        return None

    owner, repo = parts[-2], parts[-1]
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]
    if not owner or not repo:
        return None
    return f"{owner}_{repo}"


def _max_task_number(tasks_dir: Path) -> int:
    max_num = 0
    for f in tasks_dir.rglob("TASK-*.task"):
        # Keep IDs monotonic: include `.trash` and `.snapshots` to avoid reusing IDs
        # after auto-clean or history snapshots.
        try:
            max_num = max(max_num, int(f.stem.split("-")[1]))
        except Exception:
            continue
    return max_num


def _max_plan_number(tasks_dir: Path) -> int:
    max_num = 0
    for f in tasks_dir.rglob("PLAN-*.task"):
        # Keep IDs monotonic: include `.trash` and `.snapshots` to avoid reusing IDs
        # after auto-clean or history snapshots.
        try:
            max_num = max(max_num, int(f.stem.split("-")[1]))
        except Exception:
            continue
    return max_num


def _update_depends_on_in_task_file(task_file: Path, mapping: dict[str, str]) -> None:
    if not mapping:
        return
    try:
        from infrastructure.task_file_parser import TaskFileParser
    except Exception:
        return
    task = TaskFileParser.parse(task_file)
    if not task:
        return
    original = list(getattr(task, "depends_on", []) or [])
    if not original:
        return
    updated = [mapping.get(x, x) for x in original]
    if updated == original:
        return
    task.depends_on = updated
    try:
        task_file.write_text(task.to_file_content(), encoding="utf-8")
    except Exception:
        return


def _update_parent_in_task_file(task_file: Path, mapping: dict[str, str]) -> None:
    if not mapping:
        return
    try:
        from infrastructure.task_file_parser import TaskFileParser
    except Exception:
        return
    task = TaskFileParser.parse(task_file)
    if not task:
        return
    parent = getattr(task, "parent", None)
    if not parent or not isinstance(parent, str):
        return
    updated = mapping.get(parent)
    if not updated or updated == parent:
        return
    task.parent = updated
    try:
        task_file.write_text(task.to_file_content(), encoding="utf-8")
    except Exception:
        return


def _merge_history_json(dst_history: Path, src_history: Path, mapping: dict[str, str]) -> None:
    import json
    from datetime import datetime

    try:
        dst = json.loads(dst_history.read_text(encoding="utf-8")) if dst_history.exists() else {}
    except Exception:
        dst = {}
    try:
        src = json.loads(src_history.read_text(encoding="utf-8")) if src_history.exists() else {}
    except Exception:
        src = {}

    dst_ops = list(dst.get("operations", []) or [])
    src_ops = list(src.get("operations", []) or [])

    def _apply_mapping(op):
        task_id = op.get("task_id")
        if isinstance(task_id, str) and task_id in mapping:
            op = dict(op)
            op["task_id"] = mapping[task_id]
        return op

    if mapping:
        src_ops = [_apply_mapping(op) for op in src_ops]

    seen = {str(op.get("id", "")) for op in dst_ops if op.get("id")}
    merged = list(dst_ops)
    for op in src_ops:
        op_id = str(op.get("id", ""))
        if op_id and op_id in seen:
            continue
        merged.append(op)
        if op_id:
            seen.add(op_id)

    merged.sort(key=lambda o: float(o.get("timestamp", 0) or 0))
    dst_out = {
        "operations": merged,
        "current_index": len(merged) - 1,
        "updated_at": datetime.now().isoformat(),
    }
    dst_history.write_text(json.dumps(dst_out, ensure_ascii=False, indent=2), encoding="utf-8")


def _migrate_legacy_github_namespace_dir(tasks_root: Path, legacy_dir: Path, target_dir: Path) -> None:
    """Merge legacy directory into target directory with conflict-safe item renames.

    Ensures filenames match item IDs (`PLAN-###.task` / `TASK-###.task`), renaming colliding items
    and updating references (task.parent / depends_on / history).
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    existing_task_ids: set[str] = set()
    for f in target_dir.rglob("TASK-*.task"):
        if ".snapshots" in f.parts or ".trash" in f.parts:
            continue
        existing_task_ids.add(f.stem)

    existing_plan_ids: set[str] = set()
    for f in target_dir.rglob("PLAN-*.task"):
        if ".snapshots" in f.parts or ".trash" in f.parts:
            continue
        existing_plan_ids.add(f.stem)

    next_task_num = _max_task_number(target_dir)
    next_plan_num = _max_plan_number(target_dir)
    task_id_mapping: dict[str, str] = {}
    plan_id_mapping: dict[str, str] = {}

    def next_task_id() -> str:
        nonlocal next_task_num
        while True:
            next_task_num += 1
            candidate = f"TASK-{next_task_num:03d}"
            if candidate not in existing_task_ids and candidate not in task_id_mapping.values():
                return candidate

    def next_plan_id() -> str:
        nonlocal next_plan_num
        while True:
            next_plan_num += 1
            candidate = f"PLAN-{next_plan_num:03d}"
            if candidate not in existing_plan_ids and candidate not in plan_id_mapping.values():
                return candidate

    # Move plans first (preserve relative domain paths).
    for src_file in sorted(legacy_dir.rglob("PLAN-*.task")):
        if ".snapshots" in src_file.parts or ".trash" in src_file.parts:
            continue
        rel = src_file.relative_to(legacy_dir)
        plan_id = src_file.stem
        dst_parent = (target_dir / rel.parent)
        dst_parent.mkdir(parents=True, exist_ok=True)
        if plan_id not in existing_plan_ids:
            dst_file = dst_parent / src_file.name
            try:
                src_file.rename(dst_file)
                existing_plan_ids.add(plan_id)
            except Exception:
                shutil.copy2(src_file, dst_file)
                src_file.unlink(missing_ok=True)
                existing_plan_ids.add(plan_id)
            continue

        # Collision: rename plan ID and update file content.
        try:
            from infrastructure.task_file_parser import TaskFileParser
        except Exception:
            continue
        plan = TaskFileParser.parse(src_file)
        if not plan:
            continue
        new_id = next_plan_id()
        plan_id_mapping[plan_id] = new_id
        plan.id = new_id
        dst_file = dst_parent / f"{new_id}.task"
        dst_file.write_text(plan.to_file_content(), encoding="utf-8")
        try:
            src_file.unlink()
        except Exception:
            pass
        existing_plan_ids.add(new_id)

    # Move tasks (preserve relative domain paths).
    migrated_task_files: list[Path] = []
    for src_file in sorted(legacy_dir.rglob("TASK-*.task")):
        if ".snapshots" in src_file.parts or ".trash" in src_file.parts:
            continue
        rel = src_file.relative_to(legacy_dir)
        task_id = src_file.stem
        dst_parent = (target_dir / rel.parent)
        dst_parent.mkdir(parents=True, exist_ok=True)
        if task_id not in existing_task_ids:
            dst_file = dst_parent / src_file.name
            try:
                src_file.rename(dst_file)
                existing_task_ids.add(task_id)
            except Exception:
                shutil.copy2(src_file, dst_file)
                src_file.unlink(missing_ok=True)
                existing_task_ids.add(task_id)
            migrated_task_files.append(dst_file)
            continue

        # Collision: rename task ID and update file content.
        try:
            from infrastructure.task_file_parser import TaskFileParser
        except Exception:
            continue
        task = TaskFileParser.parse(src_file)
        if not task:
            continue
        new_id = next_task_id()
        task_id_mapping[task_id] = new_id
        task.id = new_id
        parent = getattr(task, "parent", None)
        if isinstance(parent, str) and parent in plan_id_mapping:
            task.parent = plan_id_mapping[parent]
        dst_file = dst_parent / f"{new_id}.task"
        dst_file.write_text(task.to_file_content(), encoding="utf-8")
        try:
            src_file.unlink()
        except Exception:
            pass
        existing_task_ids.add(new_id)
        migrated_task_files.append(dst_file)

    id_mapping: dict[str, str] = {}
    id_mapping.update(plan_id_mapping)
    id_mapping.update(task_id_mapping)

    # Move remaining files/dirs (history/snapshots/etc).
    for item in sorted(legacy_dir.iterdir()):
        rel = item.relative_to(legacy_dir)
        dst_item = target_dir / rel

        # Skip items handled above.
        if item.is_file() and item.suffix == ".task" and (item.name.startswith("TASK-") or item.name.startswith("PLAN-")):
            continue

        if item.is_dir():
            dst_item.mkdir(parents=True, exist_ok=True)
            for src_child in sorted(item.rglob("*")):
                rel_child = src_child.relative_to(item)
                dst_child = dst_item / rel_child
                if src_child.is_dir():
                    dst_child.mkdir(parents=True, exist_ok=True)
                    continue
                dst_child.parent.mkdir(parents=True, exist_ok=True)
                if dst_child.exists():
                    # Keep both with deterministic suffix.
                    candidate = dst_child
                    suffix_i = 1
                    while candidate.exists():
                        candidate = dst_child.with_name(f"{dst_child.name}.legacy{suffix_i}")
                        suffix_i += 1
                    dst_child = candidate
                try:
                    src_child.rename(dst_child)
                except Exception:
                    shutil.copy2(src_child, dst_child)
                    try:
                        src_child.unlink()
                    except Exception:
                        pass
            shutil.rmtree(item, ignore_errors=True)
        else:
            dst_item.parent.mkdir(parents=True, exist_ok=True)
            if dst_item.exists():
                # Special-case merge of .history.json
                if item.name == ".history.json":
                    _merge_history_json(dst_item, item, id_mapping)
                    try:
                        item.unlink()
                    except Exception:
                        pass
                    continue
                candidate = dst_item
                suffix_i = 1
                while candidate.exists():
                    candidate = dst_item.with_name(f"{dst_item.name}.legacy{suffix_i}")
                    suffix_i += 1
                dst_item = candidate
            try:
                item.rename(dst_item)
            except Exception:
                shutil.copy2(item, dst_item)
                try:
                    item.unlink()
                except Exception:
                    pass

    # Update references inside migrated tasks only (avoid rewriting canonical files).
    if migrated_task_files:
        for f in migrated_task_files:
            if plan_id_mapping:
                _update_parent_in_task_file(f, plan_id_mapping)
            if task_id_mapping:
                _update_depends_on_in_task_file(f, task_id_mapping)

    shutil.rmtree(legacy_dir, ignore_errors=True)


def resolve_project_root() -> Path:
    """Resolve project root using env or git; fallback to cwd."""
    env_root = os.environ.get("APPLY_TASK_PROJECT_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser()
        if candidate.exists():
            return candidate.resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        root = Path(result.stdout.strip())
        if root.exists():
            return root.resolve()
    except Exception:
        pass

    return Path.cwd().resolve()


def get_project_namespace(project_dir: Path) -> str:
    """Derive namespace from git remote or folder name."""
    url = _git_remote_url_from_config(project_dir)
    ns = _namespace_from_remote_url(url) if url else None
    if ns:
        return ns
    return project_dir.name


def migrate_legacy_github_namespaces(tasks_root: Path) -> None:
    """One-time migration: normalize legacy GitHub namespace prefixes.

    Historically some namespaces were created as:
    - "__github.com_<owner>_<repo>"
    - "github.com_<owner>_<repo>"
    This migrates both to the canonical "<owner>_<repo>" to avoid duplicates and keep project
    names clean in the TUI.
    """
    root = Path(tasks_root).expanduser().resolve()
    if not root.exists():
        return
    with _LEGACY_MIGRATION_LOCK:
        _migrate_legacy_github_namespaces_locked(root)


def _migrate_legacy_github_namespaces_locked(root: Path) -> None:
    """Run migration under a shared lock to keep the store consistent."""

    def _canonicalize(name: str) -> str | None:
        raw = (name or "").strip()
        if not raw:
            return None
        # Optional legacy marker.
        if raw.startswith("__"):
            raw = raw[2:]
        if not raw.startswith("github.com_"):
            return None
        candidate = raw[len("github.com_") :].strip("_").strip()
        # We expect "<owner>_<repo>" (both parts non-empty).
        if not candidate or "_" not in candidate:
            return None
        return candidate

    for legacy in sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]):
        target_name = _canonicalize(legacy.name)
        if not target_name or target_name == legacy.name:
            continue
        target = (root / target_name).resolve()
        if legacy.resolve() == target:
            continue
        if not target.exists():
            try:
                legacy.rename(target)
            except Exception:
                _migrate_legacy_github_namespace_dir(root, legacy, target)
            continue
        _migrate_legacy_github_namespace_dir(root, legacy, target)

    # Merge legacy repo-only folders into canonical "<owner>_<repo>" when unambiguous.
    # Example: both "Owner_repo" and "repo" exist → merge "repo" into canonical.
    try:
        dirs = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    except Exception:
        dirs = []

    repo_only_dirs: dict[str, Path] = {p.name: p for p in dirs}
    by_repo: dict[str, list[Path]] = {}
    for p in dirs:
        name = p.name
        if name.startswith("_") or "_" not in name:
            continue
        owner, repo = name.split("_", 1)
        if not owner or not repo:
            continue
        by_repo.setdefault(repo, []).append(p)

    for repo, candidates in sorted(by_repo.items(), key=lambda kv: kv[0].lower()):
        repo_dir = repo_only_dirs.get(repo)
        if not repo_dir or not repo_dir.exists():
            continue
        # Skip ambiguous cases: multiple owners share the same repo name.
        if len(candidates) != 1:
            continue
        canonical = candidates[0]
        if canonical.resolve() == repo_dir.resolve():
            continue
        _migrate_legacy_github_namespace_dir(root, repo_dir, canonical)


def get_tasks_dir_for_project(
    use_global: bool = True,
    tasks_dir: Path | None = None,
    project_root: Path | None = None,
    *,
    create: bool = False,
) -> Path:
    """Unified resolver for tasks storage directory.

    Priority:
    1. APPLY_TASK_TASKS_DIR env variable (for tests/automation).
    2. Explicit tasks_dir if provided.
    3. Global (~/.tasks/<namespace>) when use_global=True.
    4. Local .tasks under project root (only when use_global=False).
    """
    # Allow env override for tests
    env_tasks_dir = os.environ.get("APPLY_TASK_TASKS_DIR")
    if env_tasks_dir:
        env_path = Path(env_tasks_dir).expanduser().resolve()
        if create:
            env_path.mkdir(parents=True, exist_ok=True)
        return env_path

    if tasks_dir:
        return Path(tasks_dir).expanduser().resolve()

    project_root = (Path(project_root).expanduser().resolve() if project_root else resolve_project_root())
    if use_global:
        # Normalize legacy namespaces (cheap after first run).
        migrate_legacy_github_namespaces(Path.home() / ".tasks")
        namespace = get_project_namespace(project_root)
        global_dir = (Path.home() / ".tasks" / namespace).resolve()
        if create:
            global_dir.mkdir(parents=True, exist_ok=True)
        return global_dir

    local_dir = (project_root / ".tasks").resolve()
    if create:
        local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir


__all__ = [
    "get_tasks_dir_for_project",
    "resolve_project_root",
    "get_project_namespace",
    "migrate_legacy_github_namespaces",
]
