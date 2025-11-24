"""Small edit command extracted from tasks_app to cut complexity."""

from core.desktop.devtools.application.context import derive_domain_explicit, normalize_task_id
from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.cli_io import structured_error, structured_response
from core.desktop.devtools.interface.serializers import task_to_dict


def cmd_edit(args) -> int:
    manager = TaskManager()
    domain = derive_domain_explicit(getattr(args, "domain", ""), getattr(args, "phase", None), getattr(args, "component", None))
    task = manager.load_task(normalize_task_id(args.task_id), domain)
    if not task:
        return structured_error("edit", f"Задача {args.task_id} не найдена")
    if getattr(args, "description", None):
        task.description = args.description
    if getattr(args, "context", None):
        task.context = args.context
    if getattr(args, "tags", None):
        task.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if getattr(args, "priority", None):
        task.priority = args.priority
    if getattr(args, "phase", None):
        task.phase = args.phase
    if getattr(args, "component", None):
        task.component = args.component
    if getattr(args, "new_domain", None):
        task.domain = args.new_domain
    manager.save_task(task)
    payload = {"task": task_to_dict(task, include_subtasks=True)}
    return structured_response(
        "edit",
        status="OK",
        message=f"Задача {task.id} обновлена",
        payload=payload,
        summary=f"{task.id} updated",
    )


__all__ = ["cmd_edit"]
