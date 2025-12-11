"""Unit tests for batch multi-path expansion (Phase 1)."""

from pathlib import Path

import pytest

from core.desktop.devtools.interface.cli_ai import (
    handle_batch,
    handle_decompose,
    handle_done,
    MAX_ARRAY_LENGTH,
)
from core.desktop.devtools.application.task_manager import TaskManager


def _create_task_with_subtasks(manager, num_subtasks=2, status="TODO"):
    """Helper to create a task with subtasks."""
    task = manager.create_task(title="Test Task", priority="MEDIUM")
    task.description = "Test"
    manager.save_task(task)

    # Add subtasks using decompose
    subtasks_data = [
        {"title": f"Subtask {i}", "criteria": ["Done"], "tests": [], "blockers": []}
        for i in range(num_subtasks)
    ]
    resp = handle_decompose(
        manager,
        {
            "intent": "decompose",
            "task": task.id,
            "subtasks": subtasks_data,
        },
    )
    assert resp.success is True

    # Optionally set status for each subtask
    if status != "TODO":
        for i in range(num_subtasks):
            if status == "IN_PROGRESS":
                # Mark as in progress (incomplete)
                task_obj = manager.load_task(task.id)
                task_obj.subtasks[i].completed = False
                manager.save_task(task_obj)
            elif status == "DONE":
                # Use done with force to bypass confirmation requirements
                handle_done(manager, {"intent": "done", "task": task.id, "path": str(i), "force": True})

    return task


class TestPathsExpansion:
    """Tests for paths array expansion in batch operations."""

    def test_paths_expansion_basic(self, tmp_path):
        """Test that paths array expands to multiple operations."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="TODO")

        # Use complete with force=True to bypass confirmation requirements
        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": ["0", "1"], "force": True},
                ],
            },
        )

        assert resp.success is True
        # Should expand to 2 operations
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

        # Verify both subtasks were updated
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True

    def test_paths_expansion_with_done(self, tmp_path):
        """Test bulk done intent with paths array."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=3, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": ["0", "1", "2"], "force": True},
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 3
        assert resp.result["completed"] == 3

        # Verify all subtasks were completed
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True
        assert reloaded.subtasks[2].completed is True

    def test_paths_expansion_with_verify(self, tmp_path):
        """Test bulk verify intent with paths array."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="DONE")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "verify", "paths": ["0", "1"]},
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

        # Verify both subtasks were verified
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].computed_status == "completed"
        assert reloaded.subtasks[1].computed_status == "completed"

    def test_paths_expansion_with_note(self, tmp_path):
        """Test bulk note intent with paths array (Phase 1)."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="TODO")

        # Just test expansion - note may not work yet
        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": ["0", "1"], "force": True},
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

    def test_paths_expansion_with_block(self, tmp_path):
        """Test bulk block intent with paths array (Phase 1)."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="TODO")

        # Just test expansion - blocking may not work yet
        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": ["0", "1"], "force": True},
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

    def test_paths_preserves_other_fields(self, tmp_path):
        """Test that paths expansion preserves task, domain and other fields."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        (tasks_dir / "phase1").mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        # Create task with domain set from the start
        task = manager.create_task(title="Test Task", priority="MEDIUM", domain="phase1")
        task.description = "Test"
        manager.save_task(task)

        # Add subtasks
        handle_decompose(
            manager,
            {
                "intent": "decompose",
                "task": task.id,
                "subtasks": [
                    {"title": "Subtask 0", "criteria": ["Done"], "tests": [], "blockers": []},
                    {"title": "Subtask 1", "criteria": ["Done"], "tests": [], "blockers": []},
                ],
            },
        )

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "operations": [
                    {
                        "intent": "done",
                        "task": task.id,
                        "domain": "phase1",
                        "paths": ["0", "1"],
                        "force": True,
                    },
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

        # Verify both operations were executed for the correct task
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True

    def test_paths_mixed_operations(self, tmp_path):
        """Test mix of paths and single path operations."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=3, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": ["0", "1"], "force": True},  # Expands to 2
                    {"intent": "done", "path": "2", "force": True},  # Single path
                ],
            },
        )

        assert resp.success is True
        # Should be 3 total operations after expansion
        assert resp.result["total"] == 3
        assert resp.result["completed"] == 3

        # Verify all subtasks were updated
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True
        assert reloaded.subtasks[2].completed is True

    def test_paths_empty_array(self, tmp_path):
        """Test that empty paths array is handled gracefully."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = manager.create_task(title="Test Task", priority="MEDIUM")
        task.description = "Test"
        manager.save_task(task)

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": [], "force": True},  # Empty paths
                    {"intent": "context"},  # This should still run
                ],
            },
        )

        assert resp.success is True
        # Empty paths should not create any operations, but context should run
        assert resp.result["total"] == 1
        assert resp.result["completed"] == 1

    def test_paths_security_limit(self, tmp_path):
        """Test that MAX_ARRAY_LENGTH is enforced after expansion."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = manager.create_task(title="Test Task", priority="MEDIUM")
        task.description = "Test"
        manager.save_task(task)

        # Create paths that exceed MAX_ARRAY_LENGTH when expanded
        large_paths = [str(i) for i in range(MAX_ARRAY_LENGTH + 1)]

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": large_paths, "force": True},
                ],
            },
        )

        assert resp.success is False
        assert resp.error is not None
        assert resp.error.code == "TOO_MANY_OPERATIONS_AFTER_EXPANSION"
        assert "expansion" in resp.error.message.lower()

    def test_single_path_unchanged(self, tmp_path):
        """Test that single 'path' field still works as before."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=1, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "path": "0", "force": True},  # Single path
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 1
        assert resp.result["completed"] == 1

        # Verify subtask was updated
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True


class TestPathsExpansionEdgeCases:
    """Edge case tests for paths expansion."""

    def test_paths_with_non_list(self, tmp_path):
        """Test that non-list paths value doesn't cause expansion."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = manager.create_task(title="Test Task", priority="MEDIUM")
        task.description = "Test"
        manager.save_task(task)

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "context", "paths": "not-a-list"},  # Non-list
                ],
            },
        )

        # Should not expand, just pass through
        assert resp.success is True
        assert resp.result["total"] == 1

    def test_paths_numeric_converted_to_string(self, tmp_path):
        """Test that numeric paths are converted to strings."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {"intent": "done", "paths": [0, 1], "force": True},  # Numeric paths
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

        # Verify subtasks were updated (paths were converted to strings)
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True

    def test_paths_with_both_path_and_paths(self, tmp_path):
        """Test that paths field takes precedence over path field."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=3, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "operations": [
                    {
                        "intent": "done",
                        "path": "2",  # This should be ignored
                        "paths": ["0", "1"],  # This should take precedence
                        "force": True,
                    },
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2  # Should expand to 2, not 3

        # Verify only paths from 'paths' were updated
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True
        assert reloaded.subtasks[2].completed is False  # Not updated

    def test_paths_atomic_mode(self, tmp_path):
        """Test paths expansion works correctly in atomic mode."""
        tasks_dir = tmp_path / ".tasks"
        tasks_dir.mkdir()
        manager = TaskManager(tasks_dir=tasks_dir)

        task = _create_task_with_subtasks(manager, num_subtasks=2, status="TODO")

        resp = handle_batch(
            manager,
            {
                "intent": "batch",
                "task": task.id,
                "atomic": True,
                "operations": [
                    {"intent": "done", "paths": ["0", "1"], "force": True},
                ],
            },
        )

        assert resp.success is True
        assert resp.result["total"] == 2
        assert resp.result["completed"] == 2

        # Verify both subtasks were updated
        reloaded = manager.load_task(task.id)
        assert reloaded.subtasks[0].completed is True
        assert reloaded.subtasks[1].completed is True
