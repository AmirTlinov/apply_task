#!/usr/bin/env python3
"""Deep nesting regression tests (no recursion limits) for TUI detail tree."""

from core import PlanNode, Step, TaskNode
from core.desktop.devtools.interface.tui_detail_tree import build_detail_tree


def _build_deep_chain(depth: int) -> list[Step]:
    root = Step(False, "root", success_criteria=["c"])
    current = root
    for i in range(depth):
        child = Step(False, f"step-{i}", success_criteria=["c"])
        current.plan = PlanNode(tasks=[TaskNode(title=f"task-{i}", steps=[child])])
        current = child
    return [root]


def test_build_detail_tree_deep_nesting_no_recursion_error():
    # Default Python recursion limit is ~1000; this should still work.
    depth = 1200
    root_steps = _build_deep_chain(depth)

    entries, stats = build_detail_tree(root_steps, collapsed=set())

    # Every level adds: step + plan + task, plus the last leaf step which has an empty plan.
    assert len(entries) == 3 * depth + 2

    leaf_key = "s:0" + ".t:0.s:0" * depth
    assert any(e.key == leaf_key and e.kind == "step" for e in entries)

    root_stats = stats["s:0"]
    assert root_stats.children_total == depth
    assert root_stats.children_done == 0
