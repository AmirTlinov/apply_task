from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from .status import Status
from .evidence import Attachment, VerificationCheck


def _new_node_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def ensure_tree_ids(steps: List["Step"]) -> bool:
    """Ensure stable ids for steps/task-nodes across a tree.

    Returns True if any ids were assigned or fixed.
    """
    changed = False
    seen_steps: set[str] = set()
    seen_tasks: set[str] = set()

    def ensure_step(st: Step) -> None:
        nonlocal changed
        step_id = str(getattr(st, "id", "") or "").strip()
        if not step_id or step_id in seen_steps:
            st.id = _new_node_id("STEP")
            changed = True
        seen_steps.add(st.id)

        plan = getattr(st, "plan", None)
        tasks = list(getattr(plan, "tasks", []) or []) if plan else []
        for task in tasks:
            ensure_task(task)

    def ensure_task(task: "TaskNode") -> None:
        nonlocal changed
        node_id = str(getattr(task, "id", "") or "").strip()
        if not node_id or node_id in seen_tasks:
            task.id = _new_node_id("NODE")
            changed = True
        seen_tasks.add(task.id)

        for child in list(getattr(task, "steps", []) or []):
            ensure_step(child)

    for root in list(steps or []):
        ensure_step(root)
    return changed


@dataclass
class Step:
    completed: bool
    title: str
    success_criteria: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    criteria_confirmed: bool = False
    tests_confirmed: bool = False
    # Auto-confirmed flags: True if field was empty at creation (Normal mode)
    criteria_auto_confirmed: bool = False  # Never auto - criteria always required
    tests_auto_confirmed: bool = False     # Auto-OK if tests[] was empty
    criteria_notes: List[str] = field(default_factory=list)
    tests_notes: List[str] = field(default_factory=list)
    project_item_id: str = ""
    created_at: Optional[str] = None  # ISO format timestamp
    completed_at: Optional[str] = None  # ISO format timestamp
    progress_notes: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    blocked: bool = False
    block_reason: str = ""
    plan: Optional["PlanNode"] = None
    id: str = ""
    verification_checks: List[VerificationCheck] = field(default_factory=list)
    verification_outcome: str = ""
    attachments: List[Attachment] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.ensure_plan()
        if not getattr(self, "id", ""):
            self.id = _new_node_id("STEP")

    def ensure_plan(self) -> "PlanNode":
        plan = getattr(self, "plan", None)
        if plan is None:
            plan = PlanNode()
            self.plan = plan
        if getattr(plan, "tasks", None) is None:
            plan.tasks = []
        # Tests are optional; empty tests are auto-confirmed (mirrors file parser behavior).
        if not getattr(plan, "tests", []) and not getattr(plan, "tests_confirmed", False):
            plan.tests_auto_confirmed = True
        return plan

    @classmethod
    def new(
        cls,
        title: str,
        *,
        criteria: Optional[List[str]] = None,
        tests: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        plan: Optional["PlanNode"] = None,
    ) -> Optional["Step"]:
        """Create a new step in Normal mode.

        Normal mode rules:
        - criteria: REQUIRED (at least 1 item)
        - tests: optional (auto-confirmed when empty)
        - blockers: optional (data only; not a completion checkpoint)
        """
        def _normalized(values: Optional[List[str]]) -> List[str]:
            return [v.strip() for v in (values or []) if v and str(v).strip()]

        crit = _normalized(criteria)
        tst = _normalized(tests)
        bl = _normalized(blockers)

        if not crit:
            return None

        return cls(
            completed=False,
            title=title,
            success_criteria=crit,
            tests=tst,
            blockers=bl,
            criteria_auto_confirmed=False,  # Never auto - criteria always required
            tests_auto_confirmed=not tst,   # Auto-OK if tests empty
            created_at=created_at,
            plan=plan,
        )

    def ready_for_completion(self) -> bool:
        """Check if step is ready to be marked as completed.

        Normal mode logic:
        - criteria: must be explicitly confirmed (criteria_confirmed=True)
        - tests: OK if confirmed OR auto_confirmed (empty at creation)
        - plan tasks: all must be done
        - blocked: blocked steps are never ready
        """
        if self.blocked:
            return False
        plan_ready = True
        if self.plan and getattr(self.plan, "tasks", None):
            plan_ready = all(task.is_done() for task in self.plan.tasks)
        criteria_ok = self.criteria_confirmed
        tests_ok = self.tests_confirmed or self.tests_auto_confirmed
        return criteria_ok and tests_ok and plan_ready

    def status_value(self) -> Status:
        if self.completed:
            return Status.DONE
        if self.ready_for_completion():
            return Status.ACTIVE
        return Status.TODO

    @property
    def computed_status(self) -> str:
        if self.completed:
            return "completed"
        if self.blocked:
            return "blocked"
        if (self.progress_notes or self.criteria_confirmed or
            self.tests_confirmed or self.started_at):
            return "in_progress"
        return "pending"

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
            issues.append(f"'{self.title}': не атомарна (разбей на несколько шагов)")
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
        ]
        lines.append("  - Чекпоинты: " + "; ".join(status_tokens))
        if self.criteria_notes:
            lines.append("  - Отметки критериев: " + "; ".join(self.criteria_notes))
        if self.tests_notes:
            lines.append("  - Отметки тестов: " + "; ".join(self.tests_notes))
        if self.created_at:
            lines.append(f"  - Создано: {self.created_at}")
        if self.completed_at:
            lines.append(f"  - Завершено: {self.completed_at}")
        if self.progress_notes:
            lines.append("  - Прогресс: " + "; ".join(self.progress_notes))
        if self.started_at:
            lines.append(f"  - Начато: {self.started_at}")
        if self.blocked:
            lines.append(f"  - Заблокировано: {self.block_reason or 'да'}")
        return "\n".join(lines)


def _flatten_step_tree(steps: List[Step]) -> List[Step]:
    return list(_iter_step_tree(steps))


def _iter_step_tree(steps: List[Step]):
    """Iterate nested steps in a deterministic pre-order (iterative, no recursion)."""
    stack = [iter(list(steps or []))]
    while stack:
        try:
            st = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        yield st
        plan = getattr(st, "plan", None)
        tasks = list(getattr(plan, "tasks", []) or []) if plan else []
        for task in reversed(tasks):
            child_steps = list(getattr(task, "steps", []) or [])
            if child_steps:
                stack.append(iter(child_steps))


def _count_step_tree(steps: List[Step]) -> tuple[int, int]:
    total = 0
    done = 0
    for st in _iter_step_tree(steps):
        total += 1
        if getattr(st, "completed", False):
            done += 1
    return total, done


@dataclass
class TaskNode:
    title: str
    status: str = "TODO"
    priority: str = "MEDIUM"
    description: str = ""
    context: str = ""
    success_criteria: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    criteria_confirmed: bool = False
    tests_confirmed: bool = False
    criteria_auto_confirmed: bool = False  # Never auto - criteria always required
    tests_auto_confirmed: bool = False     # Auto-OK if tests[] was empty
    criteria_notes: List[str] = field(default_factory=list)
    tests_notes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    blocked: bool = False
    blockers: List[str] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    status_manual: bool = False
    id: str = ""
    attachments: List[Attachment] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not getattr(self, "id", ""):
            self.id = _new_node_id("NODE")
        # Auto-confirm tests if empty (Normal mode semantics).
        if not getattr(self, "tests", []) and not getattr(self, "tests_confirmed", False):
            self.tests_auto_confirmed = True

    def calculate_progress(self) -> int:
        total, completed = _count_step_tree(list(self.steps or []))
        if total <= 0:
            return 0
        return int((completed / total) * 100)

    def is_done(self) -> bool:
        if self.blocked:
            return False
        if self.status_manual:
            return str(self.status or "").strip().upper() == "DONE"
        return self.calculate_progress() == 100


@dataclass
class PlanNode:
    title: str = ""
    doc: str = ""
    success_criteria: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    criteria_confirmed: bool = False
    tests_confirmed: bool = False
    criteria_auto_confirmed: bool = False  # Never auto - criteria always required
    tests_auto_confirmed: bool = False     # Auto-OK if tests[] was empty
    criteria_notes: List[str] = field(default_factory=list)
    tests_notes: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    current: int = 0
    tasks: List[TaskNode] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
