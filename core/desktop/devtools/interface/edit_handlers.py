"""Small helpers to keep TaskTrackerTUI.save_edit slim."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from typing import Optional

from core import Step, TaskDetail
from core.desktop.devtools.application.context import derive_domain_explicit
from config import set_user_token
from projects_sync import update_project_workers, reload_projects_sync


def handle_token(tui, new_value: str) -> bool:
    if tui.edit_context != "token":
        return False
    set_user_token(new_value)
    tui.set_status_message(
        tui._t("STATUS_MESSAGE_PAT_SAVED") if new_value else tui._t("STATUS_MESSAGE_PAT_CLEARED")
    )
    tui.cancel_edit()
    if tui.settings_mode:
        tui.force_render()
    return True


def handle_project_number(tui, new_value: str) -> bool:
    if tui.edit_context != "project_number":
        return False
    try:
        number_value = int(new_value)
        if number_value <= 0:
            raise ValueError
    except ValueError:
        tui.set_status_message(tui._t("STATUS_MESSAGE_PROJECT_NUMBER_REQUIRED"))
    else:
        tui._set_project_number(number_value)
        tui.set_status_message(tui._t("STATUS_MESSAGE_PROJECT_NUMBER_UPDATED"))
    tui.cancel_edit()
    if tui.settings_mode:
        tui.force_render()
    return True


def handle_project_workers(tui, new_value: str) -> bool:
    if tui.edit_context != "project_workers":
        return False
    try:
        workers_value = int(new_value)
        if workers_value < 0:
            raise ValueError
    except ValueError:
        tui.set_status_message(tui._t("STATUS_MESSAGE_POOL_INTEGER"))
    else:
        update_project_workers(None if workers_value == 0 else workers_value)
        reload_projects_sync()
        tui.set_status_message(tui._t("STATUS_MESSAGE_POOL_UPDATED"))
    tui.cancel_edit()
    if tui.settings_mode:
        tui.force_render()
    return True


def handle_bootstrap_remote(tui, new_value: str) -> bool:
    if tui.edit_context != "bootstrap_remote":
        return False
    tui._bootstrap_git(new_value)
    tui.cancel_edit()
    return True


def _resolve_subtask(tui, path: str) -> Optional[Step]:
    return tui._get_step_by_path(path) if path else None


def _selected_path(tui) -> str:
    if getattr(tui, "detail_selected_path", ""):
        return tui.detail_selected_path
    if getattr(tui, "detail_flat_subtasks", None) and tui.detail_selected_index < len(tui.detail_flat_subtasks):
        return tui.detail_flat_subtasks[tui.detail_selected_index].key
    return ""


def _path_by_index(tui, edit_index: int) -> str:
    if getattr(tui, "detail_selected_path", ""):
        return tui.detail_selected_path
    if getattr(tui, "detail_flat_subtasks", None) and edit_index < len(tui.detail_flat_subtasks):
        return tui.detail_flat_subtasks[edit_index].key
    return ""


def _latest_contract_entry(entries: Any) -> tuple[Optional[Dict[str, Any]], int]:
    best: Optional[Dict[str, Any]] = None
    best_v = 0
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        try:
            v = int(entry.get("version"))
        except (TypeError, ValueError):
            continue
        if v >= best_v:
            best_v = v
            best = entry
    return best, best_v


def _next_contract_version(entries: Any) -> int:
    _, latest_v = _latest_contract_entry(entries)
    return int(latest_v) + 1


def _append_contract_version(task: TaskDetail) -> None:
    """Append a version entry for current contract if it changed."""
    entries = list(getattr(task, "contract_versions", []) or [])
    latest, _ = _latest_contract_entry(entries)
    if latest is not None:
        latest_text = str(latest.get("text", "") or "")
        latest_done = latest.get("done_criteria") or []
        if not isinstance(latest_done, list):
            latest_done = []
        if latest_text == str(getattr(task, "contract", "") or "") and list(latest_done) == list(getattr(task, "success_criteria", []) or []):
            return
    version = _next_contract_version(entries)
    entries.append(
        {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": str(getattr(task, "contract", "") or ""),
            "done_criteria": list(getattr(task, "success_criteria", []) or []),
        }
    )
    task.contract_versions = entries


def handle_task_edit(tui, context: str, new_value: str, edit_index: Optional[int]) -> bool:
    current_detail: Optional[TaskDetail] = tui.current_task_detail
    if not current_detail:
        return False

    root_task_id, root_domain, path_prefix = tui._get_root_task_context()
    if not root_task_id:
        return False

    # When inside nested navigation, always persist against the root task file.
    root_detail: Optional[TaskDetail]
    if not getattr(tui, "navigation_stack", None):
        root_detail = current_detail
    else:
        root_detail = tui.task_details_cache.get(root_task_id)
        if not root_detail:
            root_detail = tui.manager.load_task(root_task_id, root_domain, skip_sync=True)
    if not root_detail:
        return False

    def _full_path(relative: str) -> str:
        rel = str(relative or "").strip()
        if not rel:
            return str(path_prefix or "").strip()
        if path_prefix:
            return f"{path_prefix}.{rel}"
        return rel

    if context == "task_title":
        root_detail.title = new_value
    elif context == "task_description":
        root_detail.description = new_value
    elif context == "task_context":
        root_detail.context = new_value
    elif context == "task_contract":
        old = str(getattr(root_detail, "contract", "") or "")
        root_detail.contract = new_value
        if old != new_value:
            _append_contract_version(root_detail)
    elif context == "task_plan_doc":
        old = str(getattr(root_detail, "plan_doc", "") or "")
        root_detail.plan_doc = new_value
        if old != new_value:
            try:
                from core.desktop.devtools.application.plan_semantics import mark_plan_updated

                mark_plan_updated(root_detail)
            except Exception:
                pass
    elif context == "subtask_title" and edit_index is not None:
        from core.desktop.devtools.application.task_manager import _find_step_by_path

        path = _full_path(_path_by_index(tui, edit_index))
        st, _, _ = _find_step_by_path(root_detail.steps, path)
        if not st:  # pragma: no cover - safety
            return False
        st.title = new_value
    elif context in {"criterion", "test", "blocker"} and edit_index is not None:
        from core.desktop.devtools.application.task_manager import _find_step_by_path

        path = _full_path(_selected_path(tui))
        st, _, _ = _find_step_by_path(root_detail.steps, path)
        if not st:  # pragma: no cover - safety
            return False
        if context == "criterion" and edit_index < len(st.success_criteria):
            st.success_criteria[edit_index] = new_value
        elif context == "test" and edit_index < len(st.tests):
            st.tests[edit_index] = new_value
        elif context == "blocker" and edit_index < len(st.blockers):
            st.blockers[edit_index] = new_value
        else:
            return False
    else:
        return False

    # Persist through the root task to avoid saving synthetic IDs.
    try:
        tui._list_editor_persist_root(root_task_id, root_domain, root_detail)
    except Exception:
        # Fallback: best-effort save (root only).
        tui.manager.save_task(root_detail)
    tui.cancel_edit()
    return True


def handle_create_plan(tui, new_value: str) -> bool:
    if tui.edit_context != "create_plan_title":
        return False
    title = str(new_value or "").strip()
    if not title:
        tui.cancel_edit()
        return True
    plan = tui.manager.create_plan(title, status="TODO", priority="MEDIUM", domain="", phase="", component="")
    tui.manager.save_task(plan)
    selected_task_file = f".tasks/{plan.domain + '/' if plan.domain else ''}{plan.id}.task"
    if hasattr(tui, "load_current_list"):
        tui.load_current_list(preserve_selection=True, selected_task_file=selected_task_file, skip_sync=True)
    tui.set_status_message(tui._t("STATUS_MESSAGE_CREATED_PLAN", task_id=plan.id))
    tui.cancel_edit()
    return True


def handle_create_task(tui, new_value: str) -> bool:
    if tui.edit_context != "create_task_title":
        return False
    title = str(new_value or "").strip()
    if not title:
        tui.cancel_edit()
        return True
    parent_id = str(getattr(tui, "_pending_create_parent_id", "") or "").strip() or None
    if not parent_id:
        tui.set_status_message(tui._t("ERR_PARENT_REQUIRED"))
        tui.cancel_edit()
        return True
    domain = derive_domain_explicit(getattr(tui, "domain_filter", ""), getattr(tui, "phase_filter", None), getattr(tui, "component_filter", None))
    try:
        task = tui.manager.create_task(
            title,
            status="TODO",
            priority="MEDIUM",
            parent=parent_id,
            domain=domain,
            phase=getattr(tui, "phase_filter", "") or "",
            component=getattr(tui, "component_filter", "") or "",
        )
    except ValueError as exc:
        tui.set_status_message(str(exc) or tui._t("ERR_PARENT_REQUIRED"))
        tui.cancel_edit()
        return True
    tui.manager.save_task(task)
    tui._pending_create_parent_id = None
    selected_task_file = f".tasks/{task.domain + '/' if task.domain else ''}{task.id}.task"
    if hasattr(tui, "load_current_list"):
        tui.load_current_list(preserve_selection=True, selected_task_file=selected_task_file, skip_sync=True)
    tui.set_status_message(tui._t("STATUS_MESSAGE_CREATED_TASK", task_id=task.id))
    tui.cancel_edit()
    return True
