"""Action handlers extracted from TaskTrackerTUI to reduce coupling."""

import os
import shutil
from pathlib import Path

from projects_sync import update_projects_enabled, reload_projects_sync
from core.desktop.devtools.application.task_manager import TaskManager


def activate_settings_option(tui) -> None:
    options = tui._settings_options()
    if not options:
        return
    idx = tui.settings_selected_index
    option = options[idx]
    if option.get("disabled"):
        tui.set_status_message(option.get("disabled_msg") or tui._t("OPTION_DISABLED"))
        return
    action = option.get("action")
    if not action:
        return
    if action == "edit_pat":
        tui.set_status_message(tui._t("STATUS_MESSAGE_PASTE_PAT"))
        tui.start_editing("token", "", None)
        tui.edit_buffer.cursor_position = 0
        return
    if action == "toggle_sync":
        snapshot = tui._project_config_snapshot()
        desired = not snapshot["config_enabled"]
        update_projects_enabled(desired)
        state = tui._t("STATUS_MESSAGE_SYNC_ON") if desired else tui._t("STATUS_MESSAGE_SYNC_OFF")
        tui.set_status_message(state)
        tui.force_render()
        return
    if action == "edit_number":
        snapshot = tui._project_config_snapshot()
        tui.start_editing("project_number", str(snapshot["number"]), None)
        tui.edit_buffer.cursor_position = len(tui.edit_buffer.text)
        return
    if action == "edit_workers":
        snapshot = tui._project_config_snapshot()
        current = snapshot.get("workers")
        tui.start_editing("project_workers", str(current) if current else "0", None)
        tui.edit_buffer.cursor_position = len(tui.edit_buffer.text)
        return
    if action == "bootstrap_git":
        tui.start_editing("bootstrap_remote", "https://github.com/owner/repo.git", None)
        tui.edit_buffer.cursor_position = 0
        return
    if action == "refresh_metadata":
        reload_projects_sync()
        tui.set_status_message(tui._t("STATUS_MESSAGE_REFRESHED"))
        tui.force_render()
        return
    if action == "validate_pat":
        tui._start_pat_validation()
        return
    if action == "cycle_lang":
        tui._cycle_language()
        return
    tui.set_status_message(tui._t("STATUS_MESSAGE_OPTION_DISABLED"))


def delete_current_item(tui) -> None:
    # Project-level deletion: remove project folder with all tasks
    if getattr(tui, "project_mode", False) and not getattr(tui, "detail_mode", False):
        if not tui.tasks:
            return
        project = tui.filtered_tasks[tui.selected_index]
        prev_index = tui.selected_index
        path_raw = getattr(project, "task_file", None)
        if not path_raw:
            return
        path = Path(path_raw).expanduser()
        root = getattr(tui, "projects_root", None)
        if not root:
            return
        root_resolved = Path(root).expanduser().resolve()

        # Guardrail: only allow deleting direct children of projects_root.
        try:
            if path.parent.resolve() != root_resolved:
                tui.set_status_message("Нельзя удалить: неверный путь проекта", ttl=3)
                return
        except Exception:
            tui.set_status_message("Нельзя удалить: неверный путь проекта", ttl=3)
            return

        def _detach_active_manager() -> None:
            """Keep TUI manager pointing to a valid directory after deleting the active project."""
            scratch = root_resolved / ".scratch"
            try:
                scratch.mkdir(parents=True, exist_ok=True)
            except Exception:
                return
            try:
                tui.tasks_dir = scratch
                tui.manager = TaskManager(scratch)
                tui.current_project_path = None
            except Exception:
                return

        # If deleting the currently active project folder, detach first.
        try:
            current_dir = getattr(tui, "tasks_dir", None)
            if current_dir and path.exists() and path.samefile(Path(current_dir)):
                _detach_active_manager()
        except Exception:
            pass

        def _force_rmtree(target: Path) -> None:
            def _onerror(func, p, exc_info):
                try:
                    os.chmod(p, 0o700)
                    func(p)
                except Exception:
                    raise

            shutil.rmtree(target, onerror=_onerror)

        try:
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                _force_rmtree(path)
            tui.set_status_message(f"Проект удален: {project.name}", ttl=3)
        except OSError as exc:
            tui.set_status_message(f"Не удалось удалить проект: {exc}", ttl=3)
            return
        if path.exists():
            tui.set_status_message("Не удалось удалить проект: путь остался", ttl=3)
            return
        # reload list and keep selection in bounds
        tui.load_projects()
        tui.selected_index = min(prev_index, max(0, len(tui.tasks) - 1))
        if tui.tasks:
            tui.last_project_index = tui.selected_index
            tui.last_project_id = getattr(tui.tasks[tui.selected_index], "id", None)
            tui.last_project_name = tui.tasks[tui.selected_index].name
        else:
            tui.last_project_index = 0
            tui.last_project_id = None
            tui.last_project_name = None
        tui._ensure_selection_visible()
        tui.force_render()
        return

    if getattr(tui, "detail_mode", False) and getattr(tui, "current_task_detail", None):
        entry = tui._selected_subtask_entry()
        if not entry:
            return
        if getattr(entry, "kind", "") == "plan":
            tui.set_status_message("Нельзя удалить: план не удаляется отдельно", ttl=3)
            return
        path = entry.key
        node = entry.node
        if not node:
            return
        if not getattr(tui, "manager", None):
            return
        if hasattr(tui, "_get_root_task_context"):
            root_task_id, root_domain, path_prefix = tui._get_root_task_context()
        else:  # pragma: no cover - unit-test doubles
            root_task_id = getattr(tui.current_task_detail, "id", "")
            root_domain = getattr(tui.current_task_detail, "domain", "") or ""
            path_prefix = ""
        full_path = f"{path_prefix}.{path}" if path_prefix else path
        leaf = full_path.split(".")[-1] if full_path else ""
        if leaf.startswith("t:"):
            ok, _code, _deleted = tui.manager.delete_task_node(root_task_id, path=full_path, domain=root_domain)
        else:
            ok, _code, _deleted = tui.manager.delete_step_node(root_task_id, path=full_path, domain=root_domain)
        if not ok:
            tui.set_status_message(tui._t("ERR_DELETE_FAILED", task_id=root_task_id), ttl=4)
            return
        updated_root = tui.manager.load_task(root_task_id, root_domain, skip_sync=True)
        if updated_root:
            tui.task_details_cache[root_task_id] = updated_root
            if path_prefix:
                derived = tui._derive_nested_detail(updated_root, root_task_id, path_prefix)
                if derived:
                    derived.domain = root_domain
                    tui.current_task_detail = derived
                else:
                    tui.current_task_detail = updated_root
            else:
                tui.current_task_detail = updated_root
        tui._rebuild_detail_flat()
        if tui.detail_selected_index >= len(tui.detail_flat_subtasks):
            tui.detail_selected_index = max(0, len(tui.detail_flat_subtasks) - 1)
        tui.detail_selected_path = tui.detail_flat_subtasks[tui.detail_selected_index].key if tui.detail_flat_subtasks else ""
        if hasattr(tui, "load_current_list"):
            tui.load_current_list(preserve_selection=True, skip_sync=True)
        else:  # pragma: no cover - legacy fallback
            tui.load_tasks(preserve_selection=True, skip_sync=True)
        return

    if getattr(tui, "filtered_tasks", None):
        task = tui.filtered_tasks[tui.selected_index]
        deleted = tui.manager.delete_task(task.id, task.domain)
        if deleted:
            if tui.selected_index >= len(tui.filtered_tasks) - 1:
                tui.selected_index = max(0, len(tui.filtered_tasks) - 2)
            if hasattr(tui, "load_current_list"):
                tui.load_current_list(preserve_selection=False, skip_sync=True)
            else:  # pragma: no cover - legacy fallback
                tui.load_tasks(preserve_selection=False, skip_sync=True)
            tui.set_status_message(tui._t("STATUS_MESSAGE_DELETED", task_id=task.id))
        else:
            tui.set_status_message(tui._t("ERR_DELETE_FAILED", task_id=task.id))


__all__ = ["activate_settings_option", "delete_current_item"]
