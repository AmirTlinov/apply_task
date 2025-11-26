from pathlib import Path
import os
import subprocess


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
    git_config = project_dir / ".git" / "config"
    if git_config.exists():
        try:
            content = git_config.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if "url = " in line:
                    url = line.split("url = ")[1].strip()
                    if ":" in url:
                        parts = url.split(":")[-1]
                    else:
                        parts = "/".join(url.split("/")[-2:])
                    return parts.replace(".git", "").replace("/", "_")
        except Exception:
            pass
    return project_dir.name


def get_tasks_dir_for_project(use_global: bool = True, tasks_dir: Path | None = None) -> Path:
    """Unified resolver for tasks directory.

    Priority:
    1. Explicit tasks_dir if provided.
    2. Global (~/.tasks/<namespace>) when use_global=True.
    3. Local .tasks under project root (fallback for test/temp dirs without git).
    """
    if tasks_dir:
        return Path(tasks_dir).expanduser().resolve()

    project_root = resolve_project_root()
    if use_global:
        namespace = get_project_namespace(project_root)
        global_dir = (Path.home() / ".tasks" / namespace).resolve()
        # Fallback: if no git/namespace dir exists and local .tasks is present, use local
        local_dir = (project_root / ".tasks").resolve()
        if not global_dir.exists() and local_dir.exists():
            return local_dir
        if not global_dir.exists() and not local_dir.exists():
            # test/temp dir with no git: use local
            return local_dir
        return global_dir

    return (project_root / ".tasks").resolve()


__all__ = ["get_tasks_dir_for_project", "resolve_project_root", "get_project_namespace"]
