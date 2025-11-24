"""CLI handlers for task creation to keep tasks_app slim."""

from typing import Any, Dict, List, Optional

from core import TaskDetail
from application.ports import TaskRepository  # typing only
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.cli_io import structured_error, structured_response, validation_response
from core.desktop.devtools.interface.i18n import translate
from core.desktop.devtools.interface.serializers import task_to_dict
from core.desktop.devtools.interface.subtask_loader import (
    parse_subtasks_flexible,
    validate_flagship_subtasks,
    SubtaskParseError,
    load_subtasks_source,
)
from core.desktop.devtools.application.context import (
    save_last_task,
    derive_domain_explicit,
    normalize_task_id,
    parse_smart_title,
)
from core.desktop.devtools.interface.templates import load_template
from core.desktop.devtools.interface.subtask_validation import (
    validate_subtasks_coverage,
    validate_subtasks_quality,
)


def _fail(args, message: str, payload: Optional[Dict[str, Any]] = None, kind: str = "create") -> int:
    if getattr(args, "validate_only", False):
        return validation_response(kind, False, message, payload)
    return structured_error(kind, message, payload=payload)


def _success_preview(kind: str, task: TaskDetail, message: str = "") -> int:
    task_snapshot = task_to_dict(task, include_subtasks=True)
    payload = {"task": task_snapshot}
    msg = message or translate("MSG_VALIDATION_PASSED")
    return validation_response(kind, True, msg, payload)


def _apply_common_fields(task: TaskDetail, args) -> Optional[int]:
    task.description = (args.description or "").strip()
    if not task.description or task.description.upper() == "TBD":
        return _fail(args, translate("ERR_DESCRIPTION_REQUIRED"))

    task.context = args.context or ""
    if args.tags:
        task.tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    if args.dependencies:
        deps = [dep.strip() for dep in args.dependencies.split(",") if dep.strip()]
        task.dependencies.extend(deps)

    if args.next_steps:
        for step in args.next_steps.split(";"):
            if step.strip():
                task.next_steps.append(step.strip())

    if args.tests:
        for t in args.tests.split(";"):
            if t.strip():
                task.success_criteria.append(t.strip())

    if args.risks:
        for r in args.risks.split(";"):
            if r.strip():
                task.risks.append(r.strip())

    return None


def cmd_create(args) -> int:
    manager = TaskManager()
    args.parent = normalize_task_id(args.parent)
    domain = derive_domain_explicit(getattr(args, "domain", ""), getattr(args, "phase", None), getattr(args, "component", None))

    task = manager.create_task(
        args.title,
        status=args.status,
        priority=args.priority,
        parent=args.parent,
        domain=domain,
        phase=args.phase or "",
        component=args.component or "",
    )

    # общие поля
    err = _apply_common_fields(task, args)
    if err:
        return err

    if args.subtasks:
        try:
            subtasks_payload = load_subtasks_source(args.subtasks)
            task.subtasks = parse_subtasks_flexible(subtasks_payload)
        except SubtaskParseError as e:
            return _fail(args, str(e))

    # обязательные поля
    if not task.success_criteria:
        return _fail(args, translate("ERR_TESTS_REQUIRED"))
    if not task.risks:
        return _fail(args, translate("ERR_RISKS_REQUIRED"))

    flagship_ok, flagship_issues = validate_flagship_subtasks(task.subtasks)
    if not flagship_ok:
        payload = {
            "issues": flagship_issues,
            "requirements": [
                translate("REQ_MIN_SUBTASKS"),
                translate("REQ_MIN_TITLE"),
                translate("REQ_EXPLICIT_CHECKPOINTS"),
                translate("REQ_ATOMIC"),
            ],
        }
        return _fail(args, translate("ERR_FLAGSHIP_SUBTASKS"), payload=payload)

    task.update_status_from_progress()
    if getattr(args, "validate_only", False):
        return _success_preview("create", task)
    manager.save_task(task)
    save_last_task(task.id, task.domain)
    payload = {"task": task_to_dict(task, include_subtasks=True)}
    return structured_response(
        "create",
        status="OK",
        message=translate("MSG_TASK_CREATED", task_id=task.id),
        payload=payload,
        summary=f"{task.id}: {task.title}",
    )


def cmd_smart_create(args) -> int:
    if not args.parent:
        return structured_error("task", translate("ERR_PARENT_REQUIRED"))
    manager = TaskManager()
    title, auto_tags, auto_deps = parse_smart_title(args.title)
    args.parent = normalize_task_id(args.parent)

    domain = derive_domain_explicit(getattr(args, "domain", ""), getattr(args, "phase", None), getattr(args, "component", None))
    task = manager.create_task(
        title,
        status=args.status,
        priority=args.priority,
        parent=args.parent,
        domain=domain,
        phase=args.phase or "",
        component=args.component or "",
    )

    err = _apply_common_fields(task, args)
    if err:
        return err

    task.tags = [t.strip() for t in args.tags.split(",")] if args.tags else auto_tags
    deps = [d.strip() for d in args.dependencies.split(",")] if args.dependencies else auto_deps
    task.dependencies = deps

    template_desc, template_tests = load_template(task.tags[0] if task.tags else "default", manager)
    if not task.description:
        task.description = template_desc
    if args.tests:
        task.success_criteria = [t.strip() for t in args.tests.split(";") if t.strip()]
    elif template_tests:
        task.success_criteria = [template_tests]
    if not task.success_criteria:
        return _fail(args, translate("ERR_TESTS_REQUIRED"))
    if args.risks:
        task.risks = [r.strip() for r in args.risks.split(";") if r.strip()]
    if not task.risks:
        return _fail(args, translate("ERR_RISKS_REQUIRED"))

    if args.subtasks:
        try:
            subtasks_payload = load_subtasks_source(args.subtasks)
            task.subtasks = parse_subtasks_flexible(subtasks_payload)
        except SubtaskParseError as e:
            return _fail(args, str(e))

    flagship_ok, flagship_issues = validate_flagship_subtasks(task.subtasks)
    if not flagship_ok:
        payload = {
            "issues": flagship_issues,
            "requirements": [
                translate("REQ_MIN_SUBTASKS"),
                translate("REQ_MIN_TITLE"),
                translate("REQ_EXPLICIT_CHECKPOINTS"),
                translate("REQ_ATOMIC"),
            ],
        }
        return _fail(args, translate("ERR_FLAGSHIP_SUBTASKS"), payload=payload)

    task.update_status_from_progress()
    if getattr(args, "validate_only", False):
        return _success_preview("task", task)
    manager.save_task(task)
    save_last_task(task.id, task.domain)
    payload = {"task": task_to_dict(task, include_subtasks=True)}
    return structured_response(
        "task",
        status="OK",
        message=translate("MSG_TASK_CREATED", task_id=task.id),
        payload=payload,
        summary=f"{task.id}: {task.title}",
    )
