"""Detail tree flattening for TUI (Step → Plan → Task → Step …)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Set, Tuple

from core import PlanNode, Status, Step, TaskNode


DetailNodeKind = Literal["step", "plan", "task"]


def plan_key(step_path: str) -> str:
    step_path = str(step_path or "").strip()
    return f"p:{step_path}" if step_path else "p:"


def node_kind(key: str) -> DetailNodeKind:
    key = str(key or "")
    if key.startswith("p:"):
        return "plan"
    leaf = key.split(".")[-1]
    if leaf.startswith("t:"):
        return "task"
    return "step"


def canonical_path(key: str, kind: Optional[DetailNodeKind] = None) -> str:
    k = str(key or "")
    resolved = kind or node_kind(k)
    if resolved == "plan":
        return k[2:]
    return k


@dataclass(frozen=True)
class DetailNodeEntry:
    key: str
    kind: DetailNodeKind
    node: object  # Step | PlanNode | TaskNode
    level: int
    collapsed: bool
    has_children: bool
    parent_key: Optional[str]

    @property
    def canonical_path(self) -> str:
        return canonical_path(self.key, self.kind)


@dataclass(frozen=True)
class DetailNodeStats:
    progress: int
    children_done: int
    children_total: int
    status: Status


@dataclass(frozen=True)
class _StepAgg:
    total: int
    done: int


def first_child_key(entry: DetailNodeEntry) -> Optional[str]:
    if entry.kind == "step":
        step = entry.node if isinstance(entry.node, Step) else None
        plan = getattr(step, "plan", None) if step else None
        if plan is None:
            return None
        return plan_key(entry.key)
    if entry.kind == "plan":
        plan = entry.node if isinstance(entry.node, PlanNode) else None
        tasks = list(getattr(plan, "tasks", []) or []) if plan else []
        if not tasks:
            return None
        return f"{canonical_path(entry.key, entry.kind)}.t:0"
    if entry.kind == "task":
        task = entry.node if isinstance(entry.node, TaskNode) else None
        steps = list(getattr(task, "steps", []) or []) if task else []
        if not steps:
            return None
        return f"{entry.key}.s:0"
    return None


def flatten_detail_tree(
    root_steps: Sequence[Step],
    *,
    collapsed: Set[str],
    prefix: str = "",
    level: int = 0,
    parent_key: Optional[str] = None,
) -> List[DetailNodeEntry]:
    """Flatten Steps into UI nodes: Step → Plan → Task → Step … (iterative).

    Keys:
    - Step key == canonical step path (s:/t: segments)
    - Task key == canonical task path (…t:X)
    - Plan key == p:<canonical step path>
    """
    out: List[DetailNodeEntry] = []
    frames: List[Tuple[str, object]] = [
        ("steps", (list(root_steps or []), str(prefix or ""), int(level or 0), parent_key, 0))
    ]
    collapsed_set = set(collapsed or set())

    while frames:
        kind, payload = frames.pop()
        if kind == "task":
            task, task_key, task_steps, task_level, task_parent_key = payload
            task_children = list(task_steps or [])
            task_has_children = bool(task_children)
            task_collapsed = task_key in collapsed_set
            out.append(
                DetailNodeEntry(
                    key=task_key,
                    kind="task",
                    node=task,
                    level=task_level,
                    collapsed=task_collapsed,
                    has_children=task_has_children,
                    parent_key=task_parent_key,
                )
            )
            if task_collapsed or not task_children:
                continue
            frames.append(("steps", (task_children, task_key, task_level + 1, task_key, 0)))
            continue

        steps, cur_prefix, cur_level, cur_parent_key, idx = payload
        if idx >= len(steps):
            continue
        st = steps[idx]
        frames.append(("steps", (steps, cur_prefix, cur_level, cur_parent_key, idx + 1)))

        step_path = f"{cur_prefix}.s:{idx}" if cur_prefix else f"s:{idx}"
        step_key = step_path
        plan = getattr(st, "plan", None)
        step_has_children = bool(plan)
        step_collapsed = step_key in collapsed_set
        out.append(
            DetailNodeEntry(
                key=step_key,
                kind="step",
                node=st,
                level=cur_level,
                collapsed=step_collapsed,
                has_children=step_has_children,
                parent_key=cur_parent_key,
            )
        )
        if step_collapsed or not plan:
            continue

        p_key = plan_key(step_path)
        plan_tasks = list(getattr(plan, "tasks", []) or [])
        plan_has_children = bool(plan_tasks)
        plan_collapsed = p_key in collapsed_set
        out.append(
            DetailNodeEntry(
                key=p_key,
                kind="plan",
                node=plan,
                level=cur_level + 1,
                collapsed=plan_collapsed,
                has_children=plan_has_children,
                parent_key=step_key,
            )
        )
        if plan_collapsed:
            continue

        # LIFO: push in reverse order so t:0 is processed first.
        for t_idx in reversed(range(len(plan_tasks))):
            task = plan_tasks[t_idx]
            task_key = f"{step_path}.t:{t_idx}"
            task_steps = list(getattr(task, "steps", []) or [])
            frames.append(("task", (task, task_key, task_steps, cur_level + 2, p_key)))

    return out


def compute_detail_stats(root_steps: Sequence[Step], *, prefix: str = "") -> Dict[str, DetailNodeStats]:
    """Compute cached %/Σ/status for every node under `root_steps` (iterative, no recursion)."""
    step_by_key: Dict[str, Step] = {}
    plan_by_key: Dict[str, PlanNode] = {}
    task_by_key: Dict[str, TaskNode] = {}
    step_children: Dict[str, List[str]] = {}
    task_children: Dict[str, List[str]] = {}
    plan_children_tasks: Dict[str, List[str]] = {}
    step_agg: Dict[str, _StepAgg] = {}

    stack: List[Tuple[Step, str, bool]] = []
    roots = list(root_steps or [])
    prefix = str(prefix or "")
    for idx in reversed(range(len(roots))):
        root_key = f"{prefix}.s:{idx}" if prefix else f"s:{idx}"
        stack.append((roots[idx], root_key, False))

    while stack:
        st, step_key, expanded = stack.pop()
        if expanded:
            total = 1
            done = 1 if getattr(st, "completed", False) else 0
            for child_key in step_children.get(step_key, []):
                agg = step_agg.get(child_key)
                if agg:
                    total += agg.total
                    done += agg.done
            step_agg[step_key] = _StepAgg(total=total, done=done)
            continue

        step_by_key[step_key] = st
        children: List[str] = []
        plan = getattr(st, "plan", None)
        tasks = list(getattr(plan, "tasks", []) or []) if plan else []
        if plan is not None:
            p_key = plan_key(step_key)
            plan_by_key[p_key] = plan
            plan_children_tasks[p_key] = []
            for t_idx, task in enumerate(tasks):
                task_key = f"{step_key}.t:{t_idx}"
                task_by_key[task_key] = task
                plan_children_tasks[p_key].append(task_key)
                task_steps = list(getattr(task, "steps", []) or [])
                direct: List[str] = []
                for s_idx in range(len(task_steps)):
                    child_key = f"{task_key}.s:{s_idx}"
                    children.append(child_key)
                    direct.append(child_key)
                task_children[task_key] = direct

        step_children[step_key] = children

        # Post-order: aggregate after children.
        stack.append((st, step_key, True))
        # Push children for processing.
        for t_idx in reversed(range(len(tasks))):
            task = tasks[t_idx]
            task_key = f"{step_key}.t:{t_idx}"
            task_steps = list(getattr(task, "steps", []) or [])
            for s_idx in reversed(range(len(task_steps))):
                child_key = f"{task_key}.s:{s_idx}"
                stack.append((task_steps[s_idx], child_key, False))

    task_step_agg: Dict[str, _StepAgg] = {}
    task_done: Dict[str, bool] = {}
    for task_key, task in task_by_key.items():
        total = 0
        done = 0
        for child_key in task_children.get(task_key, []):
            agg = step_agg.get(child_key)
            if not agg:
                continue
            total += agg.total
            done += agg.done
        task_step_agg[task_key] = _StepAgg(total=total, done=done)

        blocked = bool(getattr(task, "blocked", False))
        status_manual = bool(getattr(task, "status_manual", False))
        if blocked:
            done_bool = False
        elif status_manual:
            done_bool = str(getattr(task, "status", "") or "").strip().upper() == "DONE"
        else:
            done_bool = total > 0 and done == total
        task_done[task_key] = done_bool

    out: Dict[str, DetailNodeStats] = {}

    # Plan nodes: Σ = done/total tasks (done respects status_manual).
    for p_key, plan in plan_by_key.items():
        task_keys = list(plan_children_tasks.get(p_key, []) or [])
        total = len(task_keys)
        done = sum(1 for tk in task_keys if task_done.get(tk, False))
        progress = int((done / total) * 100) if total else 0
        if total and done == total:
            status = Status.DONE
            progress = 100
        elif done > 0:
            status = Status.ACTIVE
        else:
            status = Status.TODO
        out[p_key] = DetailNodeStats(progress=progress, children_done=done, children_total=total, status=status)

    # Task nodes: Σ = done/total steps (deep, including nested plans).
    for task_key, task in task_by_key.items():
        agg = task_step_agg.get(task_key, _StepAgg(total=0, done=0))
        total = agg.total
        done = agg.done
        progress = int((done / total) * 100) if total else 0
        blocked = bool(getattr(task, "blocked", False))
        status_manual = bool(getattr(task, "status_manual", False))
        if blocked:
            status = Status.TODO
        elif status_manual:
            status = Status.from_string(str(getattr(task, "status", "") or "TODO"))
        else:
            if total and done == total:
                status = Status.DONE
                progress = 100
            elif done > 0:
                status = Status.ACTIVE
            else:
                status = Status.TODO
        out[task_key] = DetailNodeStats(progress=progress, children_done=done, children_total=total, status=status)

    # Step nodes: Σ = done/total descendant steps; status = readiness (criteria/tests + plan tasks done).
    for step_key, step in step_by_key.items():
        agg = step_agg.get(step_key, _StepAgg(total=1, done=1 if getattr(step, "completed", False) else 0))
        total = agg.total
        done_total = agg.done
        progress = int((done_total / total) * 100) if total else 0
        self_done = 1 if getattr(step, "completed", False) else 0
        children_total = max(0, total - 1)
        children_done = max(0, done_total - self_done)

        if getattr(step, "completed", False):
            status = Status.DONE
        else:
            blocked = bool(getattr(step, "blocked", False))
            if blocked:
                status = Status.TODO
            else:
                criteria_ok = bool(getattr(step, "criteria_confirmed", False))
                tests_ok = bool(getattr(step, "tests_confirmed", False)) or bool(getattr(step, "tests_auto_confirmed", False))
                p_key = plan_key(step_key)
                plan_task_keys = list(plan_children_tasks.get(p_key, []) or [])
                plan_ready = all(task_done.get(tk, False) for tk in plan_task_keys) if plan_task_keys else True
                status = Status.ACTIVE if (criteria_ok and tests_ok and plan_ready) else Status.TODO

        out[step_key] = DetailNodeStats(
            progress=progress,
            children_done=children_done,
            children_total=children_total,
            status=status,
        )

    return out


def build_detail_tree(
    root_steps: Sequence[Step],
    *,
    collapsed: Set[str],
    prefix: str = "",
    level: int = 0,
    parent_key: Optional[str] = None,
) -> Tuple[List[DetailNodeEntry], Dict[str, DetailNodeStats]]:
    """Build visible detail entries + cached stats (single source of truth for render)."""
    entries = flatten_detail_tree(
        root_steps,
        collapsed=collapsed,
        prefix=prefix,
        level=level,
        parent_key=parent_key,
    )
    stats = compute_detail_stats(root_steps, prefix=prefix)
    return entries, stats


def find_entry_index(entries: Sequence[DetailNodeEntry], key: str) -> Optional[int]:
    probe = str(key or "")
    for idx, entry in enumerate(entries):
        if entry.key == probe:
            return idx
    return None


def find_parent_key(entries: Sequence[DetailNodeEntry], key: str) -> Optional[str]:
    idx = find_entry_index(entries, key)
    if idx is None:
        return None
    return entries[idx].parent_key


def iter_children(entries: Sequence[DetailNodeEntry], parent_key: str) -> Iterable[DetailNodeEntry]:
    pk = str(parent_key or "")
    for entry in entries:
        if entry.parent_key == pk:
            yield entry
