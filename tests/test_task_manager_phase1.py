"""Unit 8: Test auto-setting started_at in TaskManager methods.

Phase 1 added started_at field to SubTask. This test module verifies that
started_at is automatically set when:
1. A subtask is marked as completed
2. A checkpoint is confirmed (criteria, tests, blockers)
"""

from pathlib import Path
import pytest

from core.desktop.devtools.application.task_manager import TaskManager
from core import TaskDetail, SubTask


class DummySync:
    """Minimal sync service for testing."""
    def __init__(self):
        self.enabled = False
        self.config = type("Cfg", (), {"workers": 1})


@pytest.fixture
def manager(tmp_path):
    """Create a TaskManager with disabled sync."""
    return TaskManager(tasks_dir=tmp_path / ".tasks", sync_service=DummySync())


@pytest.fixture
def task_with_subtask(manager):
    """Create a task with one subtask that has all checkpoints ready."""
    task = TaskDetail(
        id="TASK-001",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=["blocker 1"],
        criteria_confirmed=True,
        tests_confirmed=True,
        blockers_resolved=True,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)
    return task.id


def test_set_subtask_complete_sets_started_at(manager, task_with_subtask):
    """Test that marking a subtask complete sets started_at if not already set."""
    # Mark subtask as complete (with force to bypass checkpoint validation)
    # Note: We use force=True because auto_* flags are not persisted,
    # so after reload the subtask appears to need checkpoint confirmation
    ok, err = manager.set_subtask(task_with_subtask, 0, completed=True, force=True)
    assert ok is True
    assert err is None

    # Verify started_at was set
    reloaded = manager.load_task(task_with_subtask)
    subtask = reloaded.subtasks[0]
    assert subtask.completed is True
    assert subtask.started_at is not None
    assert subtask.completed_at is not None


def test_set_subtask_complete_preserves_existing_started_at(manager, task_with_subtask):
    """Test that marking complete doesn't overwrite existing started_at."""
    # First, manually set started_at
    task = manager.load_task(task_with_subtask)
    task.subtasks[0].started_at = "2025-01-01 10:00"
    manager.repo.save(task)

    # Mark subtask as complete (with force to bypass checkpoint validation)
    ok, err = manager.set_subtask(task_with_subtask, 0, completed=True, force=True)
    assert ok is True

    # Verify started_at was NOT overwritten
    reloaded = manager.load_task(task_with_subtask)
    subtask = reloaded.subtasks[0]
    assert subtask.started_at == "2025-01-01 10:00"  # Original value preserved


def test_set_subtask_incomplete_no_started_at(manager):
    """Test that marking incomplete doesn't set started_at."""
    # Create task with incomplete subtask
    task = TaskDetail(
        id="TASK-002",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=[],
        criteria_confirmed=False,
        tests_confirmed=False,
        blockers_auto_resolved=True,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # Mark as incomplete (which it already is)
    ok, err = manager.set_subtask("TASK-002", 0, completed=False, force=True)
    assert ok is True

    # Verify started_at was NOT set
    reloaded = manager.load_task("TASK-002")
    subtask = reloaded.subtasks[0]
    assert subtask.started_at is None


def test_checkpoint_criteria_sets_started_at(manager):
    """Test that confirming criteria checkpoint sets started_at."""
    # Create task with subtask
    task = TaskDetail(
        id="TASK-003",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=[],
        criteria_confirmed=False,
        tests_confirmed=False,
        blockers_auto_resolved=True,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # Confirm criteria checkpoint
    ok, err = manager.update_subtask_checkpoint("TASK-003", 0, "criteria", True)
    assert ok is True

    # Verify started_at was set
    reloaded = manager.load_task("TASK-003")
    subtask = reloaded.subtasks[0]
    assert subtask.criteria_confirmed is True
    assert subtask.started_at is not None


def test_checkpoint_tests_sets_started_at(manager):
    """Test that confirming tests checkpoint sets started_at."""
    # Create task with subtask
    task = TaskDetail(
        id="TASK-004",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=[],
        criteria_confirmed=False,
        tests_confirmed=False,
        blockers_auto_resolved=True,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # Confirm tests checkpoint
    ok, err = manager.update_subtask_checkpoint("TASK-004", 0, "tests", True)
    assert ok is True

    # Verify started_at was set
    reloaded = manager.load_task("TASK-004")
    subtask = reloaded.subtasks[0]
    assert subtask.tests_confirmed is True
    assert subtask.started_at is not None


def test_checkpoint_blockers_sets_started_at(manager):
    """Test that resolving blockers checkpoint sets started_at."""
    # Create task with subtask
    task = TaskDetail(
        id="TASK-005",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=["blocker 1"],
        criteria_confirmed=False,
        tests_confirmed=False,
        blockers_resolved=False,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # Resolve blockers checkpoint
    ok, err = manager.update_subtask_checkpoint("TASK-005", 0, "blockers", True)
    assert ok is True

    # Verify started_at was set
    reloaded = manager.load_task("TASK-005")
    subtask = reloaded.subtasks[0]
    assert subtask.blockers_resolved is True
    assert subtask.started_at is not None


def test_checkpoint_preserves_existing_started_at(manager):
    """Test that confirming checkpoint doesn't overwrite existing started_at."""
    # Create task with subtask that already has started_at
    task = TaskDetail(
        id="TASK-006",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=[],
        criteria_confirmed=False,
        tests_confirmed=False,
        blockers_auto_resolved=True,
        created_at="2025-01-01 00:00",
        started_at="2025-01-01 09:00",  # Already set
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # Confirm criteria checkpoint
    ok, err = manager.update_subtask_checkpoint("TASK-006", 0, "criteria", True)
    assert ok is True

    # Verify started_at was NOT overwritten
    reloaded = manager.load_task("TASK-006")
    subtask = reloaded.subtasks[0]
    assert subtask.started_at == "2025-01-01 09:00"  # Original value preserved


def test_checkpoint_unconfirm_no_started_at(manager):
    """Test that unconfirming checkpoint (value=False) doesn't set started_at."""
    # Create task with subtask
    task = TaskDetail(
        id="TASK-007",
        title="Test Task",
        status="FAIL",
        domain="",
        created="2025-01-01 00:00",
        updated="2025-01-01 00:00",
    )
    subtask = SubTask(
        completed=False,
        title="Test Subtask",
        success_criteria=["criterion 1"],
        tests=["test 1"],
        blockers=[],
        criteria_confirmed=True,  # Start confirmed
        tests_confirmed=False,
        blockers_auto_resolved=True,
        created_at="2025-01-01 00:00",
    )
    task.subtasks.append(subtask)
    manager.repo.save(task)

    # UNconfirm criteria checkpoint
    ok, err = manager.update_subtask_checkpoint("TASK-007", 0, "criteria", False)
    assert ok is True

    # Verify started_at was NOT set
    reloaded = manager.load_task("TASK-007")
    subtask = reloaded.subtasks[0]
    assert subtask.criteria_confirmed is False
    assert subtask.started_at is None
