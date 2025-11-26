from dataclasses import dataclass, field
from typing import List, Optional
from .status import Status


@dataclass
class SubTask:
    completed: bool
    title: str
    success_criteria: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    criteria_confirmed: bool = False
    tests_confirmed: bool = False
    blockers_resolved: bool = False
    # Auto-confirmed flags: True if field was empty at creation (Normal mode)
    criteria_auto_confirmed: bool = False  # Never auto - criteria always required
    tests_auto_confirmed: bool = False     # Auto-OK if tests[] was empty
    blockers_auto_resolved: bool = False   # Auto-OK if blockers[] was empty
    criteria_notes: List[str] = field(default_factory=list)
    tests_notes: List[str] = field(default_factory=list)
    blockers_notes: List[str] = field(default_factory=list)
    project_item_id: str = ""
    children: List["SubTask"] = field(default_factory=list)
    created_at: Optional[str] = None  # ISO format timestamp
    completed_at: Optional[str] = None  # ISO format timestamp

    def ready_for_completion(self) -> bool:
        """Check if subtask is ready to be marked as completed.

        Normal mode logic:
        - criteria: must be explicitly confirmed (criteria_confirmed=True)
        - tests: OK if confirmed OR auto_confirmed (empty at creation)
        - blockers: OK if resolved OR auto_resolved (empty at creation)
        - children: all must be completed
        """
        children_ready = all(ch.completed for ch in self.children) if self.children else True
        criteria_ok = self.criteria_confirmed
        tests_ok = self.tests_confirmed or self.tests_auto_confirmed
        blockers_ok = self.blockers_resolved or self.blockers_auto_resolved
        return criteria_ok and tests_ok and blockers_ok and children_ready

    def status_value(self) -> Status:
        if self.completed:
            return Status.OK
        if self.ready_for_completion():
            return Status.WARN
        return Status.FAIL

    def is_valid_flagship(self) -> tuple[bool, list[str]]:
        """Quality checks matching legacy validation."""
        issues: list[str] = []
        if not self.success_criteria:
            issues.append(f"'{self.title}': нет критериев выполнения")
        if not self.tests:
            issues.append(f"'{self.title}': нет тестов для проверки")
        if not self.blockers:
            issues.append(f"'{self.title}': нет блокеров/зависимостей")
        if len(self.title) < 20:
            issues.append(f"'{self.title}': слишком короткое описание (минимум 20 символов)")
        atomic_violators = ["и затем", "потом", "после этого", "далее", ", и ", " and then", " then "]
        if any(v in self.title.lower() for v in atomic_violators):
            issues.append(f"'{self.title}': не атомарна (разбей на несколько подзадач)")
        return len(issues) == 0, issues

    def to_markdown(self) -> str:
        lines = [f"- [{'x' if self.completed else ' '}] {self.title}"]
        if self.success_criteria:
            lines.append("  - Критерии: " + "; ".join(self.success_criteria))
        if self.tests:
            lines.append("  - Тесты: " + "; ".join(self.tests))
        if self.blockers:
            lines.append("  - Блокеры: " + "; ".join(self.blockers))
        # Checkpoint status with auto-confirmed support
        def _status(confirmed: bool, auto: bool) -> str:
            if confirmed:
                return "OK"
            if auto:
                return "AUTO"
            return "TODO"
        status_tokens = [
            f"Критерии={_status(self.criteria_confirmed, self.criteria_auto_confirmed)}",
            f"Тесты={_status(self.tests_confirmed, self.tests_auto_confirmed)}",
            f"Блокеры={_status(self.blockers_resolved, self.blockers_auto_resolved)}",
        ]
        lines.append("  - Чекпоинты: " + "; ".join(status_tokens))
        if self.criteria_notes:
            lines.append("  - Отметки критериев: " + "; ".join(self.criteria_notes))
        if self.tests_notes:
            lines.append("  - Отметки тестов: " + "; ".join(self.tests_notes))
        if self.blockers_notes:
            lines.append("  - Отметки блокеров: " + "; ".join(self.blockers_notes))
        if self.created_at:
            lines.append(f"  - Создано: {self.created_at}")
        if self.completed_at:
            lines.append(f"  - Завершено: {self.completed_at}")
        return "\n".join(lines)
