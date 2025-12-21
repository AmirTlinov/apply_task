from pathlib import Path

from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.tasks_dir_resolver import migrate_legacy_github_namespaces
from infrastructure.task_file_parser import TaskFileParser


def test_migrate_merges_repo_only_into_canonical_dir(tmp_path: Path):
    root = tmp_path / "tasks_root"
    root.mkdir()

    canonical = root / "Owner_repo"
    repo_only = root / "repo"
    canonical.mkdir()
    repo_only.mkdir()

    # Both dirs will start numbering from TASK-001, creating an ID collision to resolve.
    canon_mgr = TaskManager(canonical)
    canon_plan = canon_mgr.create_plan("Canon plan")
    canon_mgr.save_task(canon_plan)
    t1 = canon_mgr.create_task("Canon task", parent=canon_plan.id)
    canon_mgr.save_task(t1)

    legacy_mgr = TaskManager(repo_only)
    legacy_plan = legacy_mgr.create_plan("Legacy plan")
    legacy_mgr.save_task(legacy_plan)
    t2 = legacy_mgr.create_task("Legacy task", parent=legacy_plan.id)
    legacy_mgr.save_task(t2)

    migrate_legacy_github_namespaces(root)

    assert not repo_only.exists()
    task_files = sorted([p for p in canonical.rglob("TASK-*.task") if ".snapshots" not in p.parts and ".trash" not in p.parts])
    plan_files = sorted([p for p in canonical.rglob("PLAN-*.task") if ".snapshots" not in p.parts and ".trash" not in p.parts])
    assert len(task_files) == 2
    assert len(plan_files) == 2

    parsed_ids = set()
    for file_path in task_files:
        parsed = TaskFileParser.parse(file_path)
        assert parsed is not None
        assert parsed.id == file_path.stem
        parsed_ids.add(parsed.id)
    # Original canonical ID stays, legacy colliding task is renamed forward.
    assert t1.id in parsed_ids
    assert any(x != t1.id for x in parsed_ids)

    parsed_plan_ids = set()
    for file_path in plan_files:
        parsed = TaskFileParser.parse(file_path)
        assert parsed is not None
        assert parsed.id == file_path.stem
        parsed_plan_ids.add(parsed.id)
    assert canon_plan.id in parsed_plan_ids
    assert any(x != canon_plan.id for x in parsed_plan_ids)

    # Parent references remain consistent after plan/task renames.
    migrated = [TaskFileParser.parse(p) for p in task_files]
    assert all(t is not None for t in migrated)
    migrated_map = {t.id: t for t in migrated if t is not None}
    assert migrated_map[t1.id].parent == canon_plan.id
    legacy_task_id = next(x for x in parsed_ids if x != t1.id)
    legacy_plan_id = next(x for x in parsed_plan_ids if x != canon_plan.id)
    assert migrated_map[legacy_task_id].parent == legacy_plan_id
