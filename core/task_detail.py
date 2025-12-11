from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from pathlib import Path
from datetime import datetime, timezone
import yaml

from .subtask import SubTask
from .task_event import TaskEvent


@dataclass
class TaskDetail:
    id: str
    title: str
    status: str
    status_manual: bool = False  # True when status was explicitly set by user and should not be auto-recalculated
    description: str = ""
    domain: str = ""
    phase: str = ""
    component: str = ""
    parent: Optional[str] = None
    priority: str = "MEDIUM"
    created: str = ""
    updated: str = ""
    tags: List[str] = field(default_factory=list)
    assignee: str = ""
    progress: int = 0
    blocked: bool = False
    blockers: List[str] = field(default_factory=list)
    context: str = ""
    success_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    subtasks: List[SubTask] = field(default_factory=list)
    project_item_id: Optional[str] = None
    project_draft_id: Optional[str] = None
    project_remote_updated: Optional[str] = None
    project_issue_number: Optional[str] = None
    _source_path: Optional[str] = None
    _source_mtime: float = 0.0
    history: List[str] = field(default_factory=list)  # Legacy text history
    events: List[TaskEvent] = field(default_factory=list)  # Structured event log
    depends_on: List[str] = field(default_factory=list)  # Task IDs this task depends on

    def calculate_progress(self) -> int:
        def flatten(nodes):
            out = []
            for st in nodes:
                out.append(st)
                out.extend(flatten(st.children))
            return out
        flat = flatten(self.subtasks)
        if not flat:
            return self.progress
        completed = sum(1 for st in flat if st.completed)
        return int((completed / len(flat)) * 100)

    @property
    def folder(self) -> str:
        return self.domain

    @folder.setter
    def folder(self, value: str) -> None:
        self.domain = value

    @property
    def filepath(self) -> Path:
        if self._source_path:
            return Path(self._source_path)
        base = Path(".tasks")
        return (base / self.domain / f"{self.id}.task").resolve() if self.domain else base / f"{self.id}.task"

    def update_status_from_progress(self) -> None:
        if self.status_manual:
            return
        prog = self.calculate_progress()
        self.progress = prog
        if self.blocked:
            self.status = "FAIL"
        elif prog == 100:
            self.status = "OK"
        elif prog > 0:
            self.status = "WARN"
        else:
            self.status = "FAIL"

    def to_file_content(self) -> str:
        metadata = {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "domain": self.domain or None,
            "phase": self.phase or None,
            "component": self.component or None,
            "parent": self.parent,
            "priority": self.priority,
            "created": self.created or self._now_iso(),
            "updated": self.updated or self._now_iso(),
            "tags": self.tags,
            "assignee": self.assignee or "ai",
            "progress": self.calculate_progress(),
        }
        if self.blocked:
            metadata["blocked"] = True
            metadata["blockers"] = self.blockers
        if self.project_item_id:
            metadata["project_item_id"] = self.project_item_id
        if self.project_draft_id:
            metadata["project_draft_id"] = self.project_draft_id
        if self.project_remote_updated:
            metadata["project_remote_updated"] = self.project_remote_updated
        if self.project_issue_number:
            metadata["project_issue_number"] = self.project_issue_number
        subtask_ids = [st.project_item_id for st in self.subtasks]
        if any(subtask_ids):
            metadata["subtask_project_ids"] = subtask_ids
        if self.status_manual:
            metadata["status_manual"] = True
        if self.depends_on:
            metadata["depends_on"] = self.depends_on
        if self.events:
            metadata["events"] = [e.to_dict() for e in self.events]

        lines = ["---", yaml.dump(metadata, allow_unicode=True, default_flow_style=False).strip(), "---", ""]
        lines.append(f"# {self.title}\n")

        def add_section(title: str, content: List[str]) -> None:
            if content:
                lines.append(f"## {title}")
                lines.extend(content)
                lines.append("")

        if self.description:
            lines.append("## Описание")
            lines.append(self.description)
            lines.append("")
        if self.context:
            lines.append("## Контекст")
            lines.append(self.context)
            lines.append("")
        if self.subtasks:
            lines.append("## Подзадачи")
            def dump_subtask(st: SubTask, indent: int = 0):
                pad = "  " * indent
                lines.append(f"{pad}- [{'x' if st.completed else ' '}] {st.title}")
                pad_detail = pad + "  "
                if st.success_criteria:
                    lines.append(f"{pad_detail}- Критерии: " + "; ".join(st.success_criteria))
                if st.tests:
                    lines.append(f"{pad_detail}- Тесты: " + "; ".join(st.tests))
                if st.blockers:
                    lines.append(f"{pad_detail}- Блокеры: " + "; ".join(st.blockers))
                status_tokens = [
                    f"Критерии={'OK' if st.criteria_confirmed else 'TODO'}",
                    f"Тесты={'OK' if st.tests_confirmed else 'TODO'}",
                    f"Блокеры={'OK' if st.blockers_resolved else 'TODO'}",
                ]
                lines.append(f"{pad_detail}- Чекпоинты: " + "; ".join(status_tokens))
                if st.criteria_notes:
                    lines.append(f"{pad_detail}- Отметки критериев: " + "; ".join(st.criteria_notes))
                if st.tests_notes:
                    lines.append(f"{pad_detail}- Отметки тестов: " + "; ".join(st.tests_notes))
                if st.blockers_notes:
                    lines.append(f"{pad_detail}- Отметки блокеров: " + "; ".join(st.blockers_notes))
                # Phase 1 fields
                if st.progress_notes:
                    lines.append(f"{pad_detail}- Прогресс: " + "; ".join(st.progress_notes))
                if st.started_at:
                    lines.append(f"{pad_detail}- Начато: {st.started_at}")
                if st.blocked or st.block_reason:
                    block_value = "да" if st.blocked else "нет"
                    if st.block_reason:
                        lines.append(f"{pad_detail}- Заблокировано: {block_value}; {st.block_reason}")
                    else:
                        lines.append(f"{pad_detail}- Заблокировано: {block_value}")
                for child in st.children:
                    dump_subtask(child, indent + 1)
            for st in self.subtasks:
                dump_subtask(st, 0)
            lines.append("")
        add_section("Текущие проблемы", [f"{i + 1}. {p}" for i, p in enumerate(self.problems)])
        add_section("Следующие шаги", [f"- {s}" for s in self.next_steps])
        add_section("Критерии успеха", [f"- {c}" for c in self.success_criteria])
        add_section("Зависимости", [f"- {d}" for d in self.dependencies])
        add_section("Риски", [f"- {r}" for r in self.risks])
        add_section("История", [f"- {h}" for h in self.history])

        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def subtask_to_task_detail(subtask: SubTask, parent_id: str, path: str) -> "TaskDetail":
    """Convert a SubTask to TaskDetail for unified navigation."""
    status = "OK" if subtask.completed else ("WARN" if subtask.ready_for_completion() else "FAIL")
    return TaskDetail(
        id=f"{parent_id}/{path}",
        title=subtask.title,
        status=status,
        description="",
        parent=parent_id,
        subtasks=subtask.children,
        success_criteria=subtask.success_criteria,
        blockers=subtask.blockers,
    )
