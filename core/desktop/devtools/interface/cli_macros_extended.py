"""CLI macro handlers extracted from tasks_app for lower complexity."""

from typing import Any, Dict, List, Optional, Tuple

from core.desktop.devtools.application.context import (
    derive_domain_explicit,
    get_last_task,
    normalize_task_id,
    resolve_task_reference,
    save_last_task,
)
from core.desktop.devtools.application.recommendations import next_recommendations, quick_overview, suggest_tasks
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.cli_io import structured_error, structured_response
from core.desktop.devtools.interface.i18n import translate
from core.desktop.devtools.interface.serializers import subtask_to_dict, task_to_dict


def _parse_status_and_task(args) -> Tuple[Optional[str], Optional[str]]:
    status = None
    task_id = None
    for candidate in (getattr(args, "arg1", None), getattr(args, "arg2", None)):
        if not candidate:
            continue
        value = candidate.upper()
        if value in ("OK", "WARN", "FAIL"):
            status = value
        else:
            task_id = normalize_task_id(candidate)
    return status, task_id


def _build_filters(args, domain: str) -> Dict[str, str]:
    return {
        "folder": getattr(args, "folder", "") or "",
        "domain": domain or "",
        "phase": getattr(args, "phase", None) or "",
        "component": getattr(args, "component", None) or "",
    }


def _filter_hint(filters: Dict[str, str]) -> str:
    return f" (folder='{filters['folder'] or filters['domain'] or '-'}', phase='{filters['phase'] or '-'}', component='{filters['component'] or '-'}')"


def cmd_update(args) -> int:
    status, task_id = _parse_status_and_task(args)
    last_id, last_domain = get_last_task()
    if status is None:
        return structured_error("update", translate("ERR_STATUS_REQUIRED"))
    if task_id is None:
        task_id = last_id
        if not task_id:
            return structured_error("update", translate("ERR_NO_TASK_AND_LAST"))

    manager = TaskManager()
    domain = derive_domain_explicit(getattr(args, "domain", ""), getattr(args, "phase", None), getattr(args, "component", None)) or last_domain or ""
    ok, error = manager.update_task_status(task_id, status, domain)
    if ok:
        save_last_task(task_id, domain)
        detail = manager.load_task(task_id, domain)
        payload = {"task": task_to_dict(detail, include_subtasks=True) if detail else {"id": task_id}}
        return structured_response(
            "update",
            status=status,
            message=translate("MSG_STATUS_UPDATED", task_id=task_id),
            payload=payload,
            summary=f"{task_id} → {status}",
        )

    payload = {"task_id": task_id, "domain": domain}
    if error and error.get("code") == "not_found":
        return structured_error("update", error.get("message", translate("ERR_TASK_NOT_FOUND", task_id=task_id)), payload=payload)
    return structured_response(
        "update",
        status="ERROR",
        message=(error or {}).get("message", translate("ERR_STATUS_NOT_UPDATED")),
        payload=payload,
        exit_code=1,
    )


def cmd_ok(args) -> int:
    manager = TaskManager()
    try:
        task_id, domain = resolve_task_reference(
            getattr(args, "task_id", None), getattr(args, "domain", None), getattr(args, "phase", None), getattr(args, "component", None)
        )
    except ValueError as exc:
        return structured_error("ok", str(exc))
    index = args.index
    checkpoints: List[Tuple[str, Optional[str], str]] = [
        ("criteria", getattr(args, "criteria_note", None), "criteria_done"),
        ("tests", getattr(args, "tests_note", None), "tests_done"),
        ("blockers", getattr(args, "blockers_note", None), "blockers_done"),
    ]
    for checkpoint, note, _ in checkpoints:
        ok, msg = manager.update_subtask_checkpoint(task_id, index, checkpoint, True, note or "", domain)
        if ok:
            continue
        payload = {"task_id": task_id, "checkpoint": checkpoint, "index": index}
        if msg == "not_found":
            return structured_error("ok", f"Задача {task_id} не найдена", payload=payload)
        if msg == "index":
            return structured_error("ok", translate("ERR_SUBTASK_INDEX"), payload=payload)
        return structured_error("ok", msg or "Не удалось подтвердить чекпоинт", payload=payload)

    ok, msg = manager.set_subtask(task_id, index, True, domain)
    if not ok:
        payload = {"task_id": task_id, "index": index}
        return structured_error("ok", msg or "Не удалось завершить подзадачу", payload=payload)
    detail = manager.load_task(task_id, domain)
    save_last_task(task_id, domain)
    payload: Dict[str, Any] = {
        "task": task_to_dict(detail, include_subtasks=True) if detail else {"id": task_id},
        "subtask_index": index,
    }
    if detail and 0 <= index < len(detail.subtasks):
        payload["subtask"] = subtask_to_dict(detail.subtasks[index])
    return structured_response(
        "ok",
        status="OK",
        message=f"Подзадача {index} полностью подтверждена и закрыта",
        payload=payload,
        summary=f"{task_id} subtask#{index} OK",
    )


def cmd_note(args) -> int:
    manager = TaskManager()
    try:
        task_id, domain = resolve_task_reference(
            getattr(args, "task_id", None), getattr(args, "domain", None), getattr(args, "phase", None), getattr(args, "component", None)
        )
    except ValueError as exc:
        return structured_error("note", str(exc))
    value = not getattr(args, "undo", False)
    ok, msg = manager.update_subtask_checkpoint(task_id, args.index, args.checkpoint, value, getattr(args, "note", "") or "", domain)
    if ok:
        detail = manager.load_task(task_id, domain)
        save_last_task(task_id, domain)
        payload: Dict[str, Any] = {
            "task": task_to_dict(detail, include_subtasks=True) if detail else {"id": task_id},
            "checkpoint": args.checkpoint,
            "index": args.index,
            "state": "DONE" if value else "TODO",
        }
        if detail and 0 <= args.index < len(detail.subtasks):
            payload["subtask"] = subtask_to_dict(detail.subtasks[args.index])
        return structured_response(
            "note",
            status="OK",
            message=f"{args.checkpoint.capitalize()} {'подтверждены' if value else 'сброшены'}",
            payload=payload,
            summary=f"{task_id} {args.checkpoint} idx {args.index}",
        )
    payload = {"task_id": task_id, "checkpoint": args.checkpoint, "index": args.index}
    if msg == "not_found":
        return structured_error("note", f"Задача {task_id} не найдена", payload=payload)
    if msg == "index":
        return structured_error("note", translate("ERR_SUBTASK_INDEX"), payload=payload)
    return structured_error("note", msg or "Операция не выполнена", payload=payload)


def cmd_suggest(args) -> int:
    manager = TaskManager()
    folder = getattr(args, "folder", "") or ""
    domain = derive_domain_explicit(getattr(args, "domain", "") or folder, getattr(args, "phase", None), getattr(args, "component", None))
    filters = _build_filters(args, domain)
    tasks = manager.list_tasks(domain, skip_sync=True)
    payload, _ranked = suggest_tasks(tasks, filters, remember=save_last_task, serializer=task_to_dict)
    hint = _filter_hint(filters)
    if not payload["suggestions"]:
        return structured_response(
            "suggest",
            status="OK",
            message="Все задачи завершены" + hint,
            payload=payload,
            summary="Нет задач для рекомендации",
        )
    return structured_response(
        "suggest",
        status="OK",
        message="Рекомендации сформированы" + hint,
        payload=payload,
        summary=f"{len(payload['suggestions'])} рекомендаций",
    )


def cmd_quick(args) -> int:
    manager = TaskManager()
    folder = getattr(args, "folder", "") or ""
    domain = derive_domain_explicit(getattr(args, "domain", "") or folder, getattr(args, "phase", None), getattr(args, "component", None))
    filters = _build_filters(args, domain)
    tasks = manager.list_tasks(domain, skip_sync=True)
    payload, top = quick_overview(tasks, filters, remember=save_last_task, serializer=task_to_dict)
    hint = _filter_hint(filters)
    if not payload["top"]:
        return structured_response(
            "quick",
            status="OK",
            message="Все задачи выполнены" + hint,
            payload=payload,
            summary="Нет задач",
        )
    return structured_response(
        "quick",
        status="OK",
        message="Быстрый обзор top-3" + hint,
        payload=payload,
        summary=f"Top-{len(top)} задач",
    )


__all__ = ["cmd_update", "cmd_ok", "cmd_note", "cmd_suggest", "cmd_quick"]
