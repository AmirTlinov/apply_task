"""Common serializers for tasks and subtasks."""

from typing import Any, Dict

from core import SubTask, TaskDetail


def subtask_to_dict(subtask: SubTask) -> Dict[str, Any]:
    return {
        "title": subtask.title,
        "completed": subtask.completed,
        "success_criteria": list(subtask.success_criteria),
        "tests": list(subtask.tests),
        "blockers": list(subtask.blockers),
        "criteria_confirmed": subtask.criteria_confirmed,
        "tests_confirmed": subtask.tests_confirmed,
        "blockers_resolved": subtask.blockers_resolved,
        "criteria_notes": list(subtask.criteria_notes),
        "tests_notes": list(subtask.tests_notes),
        "blockers_notes": list(subtask.blockers_notes),
    }


def task_to_dict(task: TaskDetail, include_subtasks: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "progress": task.calculate_progress(),
        "priority": task.priority,
        "domain": task.domain,
        "phase": task.phase,
        "component": task.component,
        "parent": task.parent,
        "tags": list(task.tags),
        "assignee": task.assignee,
        "blocked": task.blocked,
        "blockers": list(task.blockers),
        "description": task.description,
        "context": task.context,
        "success_criteria": list(task.success_criteria),
        "dependencies": list(task.dependencies),
        "next_steps": list(task.next_steps),
        "problems": list(task.problems),
        "risks": list(task.risks),
        "history": list(task.history),
        "subtasks_count": len(task.subtasks),
        "project_remote_updated": task.project_remote_updated,
    }
    if include_subtasks:
        data["subtasks"] = [subtask_to_dict(st) for st in task.subtasks]
    return data
