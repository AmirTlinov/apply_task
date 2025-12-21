"""Unit tests for Phase 1 intent handlers (note, block).

Tests the new handler functions for Phase 1 MCP tools:
- handle_note: Add progress notes to steps
- handle_block: Block/unblock steps
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.intent_api import handle_note, handle_block
from core import Step, TaskDetail


@pytest.fixture
def temp_tasks_dir(tmp_path):
    """Create temporary tasks directory."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return tasks_dir


@pytest.fixture
def manager(temp_tasks_dir):
    """Create TaskManager with temp directory."""
    return TaskManager(tasks_dir=temp_tasks_dir)


@pytest.fixture
def sample_task(manager):
    """Create a sample task with steps."""
    task = TaskDetail(
        id="TASK-001",
        title="Test Task",
        status="pending",
        steps=[
            Step(
                title="Step 0",
                completed=False,
                success_criteria=[],
                tests=[],
                blockers=[],
                progress_notes=[],
                started_at=None,
                blocked=False,
                block_reason="",
            ),
            Step(
                title="Step 1",
                completed=False,
                success_criteria=[],
                tests=[],
                blockers=[],
                progress_notes=["Initial note"],
                started_at="2025-01-01T10:00:00",
                blocked=False,
                block_reason="",
            ),
        ],
    )
    manager.save_task(task)
    return task


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLE_NOTE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def test_handle_note_success(manager, sample_task):
    """Test adding a note successfully."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:0",
        "note": "Implemented authentication logic",
    }

    response = handle_note(manager, data)

    assert response.success is True
    assert response.intent == "note"
    assert response.result["path"] == "s:0"
    assert response.result["note"] == "Implemented authentication logic"
    assert response.result["total_notes"] == 1
    assert response.result["computed_status"] == "in_progress"

    # Verify note was saved
    task = manager.load_task("TASK-001")
    assert len(task.steps[0].progress_notes) == 1
    assert task.steps[0].progress_notes[0] == "Implemented authentication logic"


def test_handle_note_missing_task(manager):
    """Test error on missing task field."""
    data = {
        "intent": "note",
        "path": "s:0",
        "note": "Some note",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.intent == "note"
    assert response.error_code == "MISSING_TASK"
    assert "task" in (response.error_message or "").lower()


def test_handle_note_missing_path(manager, sample_task):
    """Test error on missing path field."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "note": "Some note",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.intent == "note"
    assert response.error_code == "INVALID_PATH"
    assert "path" in (response.error_message or "").lower()


def test_handle_note_missing_note(manager, sample_task):
    """Test error on empty note."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:0",
        "note": "",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.intent == "note"
    assert response.error_code == "MISSING_NOTE"


def test_handle_note_auto_sets_started_at(manager, sample_task):
    """Test that started_at is automatically set when adding first note."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:0",
        "note": "First note",
    }

    # Verify started_at is None initially
    task = manager.load_task("TASK-001")
    assert task.steps[0].started_at is None

    response = handle_note(manager, data)

    assert response.success is True

    # Verify started_at was set
    task = manager.load_task("TASK-001")
    assert task.steps[0].started_at is not None
    # Verify it's a valid ISO format timestamp
    datetime.fromisoformat(task.steps[0].started_at)


def test_handle_note_does_not_override_started_at(manager, sample_task):
    """Test that started_at is not changed if already set."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:1",
        "note": "Additional note",
    }

    # Get original started_at
    task = manager.load_task("TASK-001")
    original_started_at = task.steps[1].started_at
    assert original_started_at == "2025-01-01T10:00:00"

    response = handle_note(manager, data)

    assert response.success is True

    # Verify started_at was NOT changed
    task = manager.load_task("TASK-001")
    assert task.steps[1].started_at == original_started_at


def test_handle_note_invalid_task_id(manager):
    """Test error on invalid task ID."""
    data = {
        "intent": "note",
        "task": "../etc/passwd",
        "path": "s:0",
        "note": "Malicious note",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.error_code == "INVALID_TASK"


def test_handle_note_task_not_found(manager):
    """Test error when task doesn't exist."""
    data = {
        "intent": "note",
        "task": "NONEXISTENT",
        "path": "s:0",
        "note": "Some note",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.error_code == "NOT_FOUND"


def test_handle_note_step_not_found(manager, sample_task):
    """Test error when step path doesn't exist."""
    data = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:99",
        "note": "Some note",
    }

    response = handle_note(manager, data)

    assert response.success is False
    assert response.error_code == "PATH_NOT_FOUND"


def test_handle_note_multiple_notes(manager, sample_task):
    """Test adding multiple notes to same step."""
    data1 = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:0",
        "note": "First note",
    }
    data2 = {
        "intent": "note",
        "task": "TASK-001",
        "path": "s:0",
        "note": "Second note",
    }

    response1 = handle_note(manager, data1)
    assert response1.success is True
    assert response1.result["total_notes"] == 1

    response2 = handle_note(manager, data2)
    assert response2.success is True
    assert response2.result["total_notes"] == 2

    # Verify both notes were saved
    task = manager.load_task("TASK-001")
    assert len(task.steps[0].progress_notes) == 2
    assert task.steps[0].progress_notes[0] == "First note"
    assert task.steps[0].progress_notes[1] == "Second note"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLE_BLOCK TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def test_handle_block_success(manager, sample_task):
    """Test blocking a step successfully."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "Waiting for API documentation",
    }

    response = handle_block(manager, data)

    assert response.success is True
    assert response.intent == "block"
    assert response.result["path"] == "s:0"
    assert response.result["blocked"] is True
    assert response.result["reason"] == "Waiting for API documentation"
    assert response.result["computed_status"] == "blocked"

    # Verify block was saved
    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "Waiting for API documentation"


def test_handle_block_unblock(manager, sample_task):
    """Test unblocking a step."""
    # First block it
    data_block = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "Waiting for something",
    }
    handle_block(manager, data_block)

    # Now unblock it
    data_unblock = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": False,
    }

    response = handle_block(manager, data_unblock)

    assert response.success is True
    assert response.result["blocked"] is False
    assert response.result["reason"] == ""
    assert response.result["computed_status"] in ["pending", "in_progress"]

    # Verify unblock was saved
    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is False
    assert task.steps[0].block_reason == ""


def test_handle_block_with_reason(manager, sample_task):
    """Test blocking with a reason."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "Waiting for database migration",
    }

    response = handle_block(manager, data)

    assert response.success is True
    assert response.result["reason"] == "Waiting for database migration"

    task = manager.load_task("TASK-001")
    assert task.steps[0].block_reason == "Waiting for database migration"


def test_handle_block_missing_task(manager):
    """Test error on missing task field."""
    data = {
        "intent": "block",
        "path": "s:0",
        "blocked": True,
    }

    response = handle_block(manager, data)

    assert response.success is False
    assert response.error_code == "MISSING_TASK"


def test_handle_block_missing_path(manager, sample_task):
    """Test error on missing path field."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "blocked": True,
    }

    response = handle_block(manager, data)

    assert response.success is False
    assert response.error_code == "INVALID_PATH"


def test_handle_block_clears_reason_on_unblock(manager, sample_task):
    """Test that reason is cleared when unblocking."""
    # First block with reason
    data_block = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "Waiting for approval",
    }
    handle_block(manager, data_block)

    # Verify block and reason
    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "Waiting for approval"

    # Unblock
    data_unblock = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": False,
    }
    response = handle_block(manager, data_unblock)

    assert response.success is True
    assert response.result["blocked"] is False
    assert response.result["reason"] == ""

    # Verify reason was cleared
    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is False
    assert task.steps[0].block_reason == ""


def test_handle_block_default_blocked_true(manager, sample_task):
    """Test that blocked defaults to True if not specified."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "reason": "Default block",
    }

    response = handle_block(manager, data)

    assert response.success is True
    assert response.result["blocked"] is True

    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is True


def test_handle_block_invalid_task_id(manager):
    """Test error on invalid task ID."""
    data = {
        "intent": "block",
        "task": "../etc/passwd",
        "path": "s:0",
        "blocked": True,
    }

    response = handle_block(manager, data)

    assert response.success is False
    assert response.error_code == "INVALID_TASK"


def test_handle_block_task_not_found(manager):
    """Test error when task doesn't exist."""
    data = {
        "intent": "block",
        "task": "NONEXISTENT",
        "path": "s:0",
        "blocked": True,
    }

    response = handle_block(manager, data)

    assert response.success is False
    assert response.error_code == "NOT_FOUND"


def test_handle_block_step_not_found(manager, sample_task):
    """Test error when step path doesn't exist."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:99",
        "blocked": True,
    }

    response = handle_block(manager, data)

    assert response.success is False
    assert response.error_code == "PATH_NOT_FOUND"


def test_handle_block_empty_reason_on_block(manager, sample_task):
    """Test blocking with no reason."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "",
    }

    response = handle_block(manager, data)

    assert response.success is True
    assert response.result["blocked"] is True
    assert response.result["reason"] == ""

    task = manager.load_task("TASK-001")
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == ""


def test_handle_block_reason_stripped(manager, sample_task):
    """Test that reason is stripped of whitespace."""
    data = {
        "intent": "block",
        "task": "TASK-001",
        "path": "s:0",
        "blocked": True,
        "reason": "  Waiting for review  ",
    }

    response = handle_block(manager, data)

    assert response.success is True
    assert response.result["reason"] == "Waiting for review"

    task = manager.load_task("TASK-001")
    assert task.steps[0].block_reason == "Waiting for review"
