"""Tests for Phase 1 serializer enhancements."""

import pytest
from core import Step, TaskDetail
from core.desktop.devtools.interface.serializers import step_to_dict, task_to_dict


class TestStepSerializerPhase1:
    """Test Phase 1 fields in step serialization."""

    def test_full_mode_includes_phase1_fields(self):
        """Full mode should include all Phase 1 fields."""
        step = Step(
            completed=False,
            title="Test subtask",
            progress_notes=["note1", "note2"],
            started_at="2025-01-01T10:00:00",
            blocked=True,
            block_reason="Waiting for API",
        )

        result = step_to_dict(step, path="0", compact=False)

        # Verify Phase 1 fields are present
        assert "progress_notes" in result
        assert "started_at" in result
        assert "blocked" in result
        assert "block_reason" in result
        assert "computed_status" in result

        # Verify values
        assert result["progress_notes"] == ["note1", "note2"]
        assert result["started_at"] == "2025-01-01T10:00:00"
        assert result["blocked"] is True
        assert result["block_reason"] == "Waiting for API"
        assert result["computed_status"] == "blocked"

    def test_full_mode_default_values(self):
        """Full mode should use getattr with defaults for backward compatibility."""
        step = Step(
            completed=False,
            title="Test subtask",
        )

        result = step_to_dict(step, path="0", compact=False)

        # Verify defaults
        assert result["progress_notes"] == []
        assert result["started_at"] is None
        assert result["blocked"] is False
        assert result["block_reason"] == ""
        assert result["computed_status"] == "pending"

    def test_compact_mode_includes_status(self):
        """Compact mode should include computed_status."""
        step = Step(
            completed=False,
            title="Test subtask",
            progress_notes=["working on it"],
        )

        result = step_to_dict(step, path="0", compact=True)

        # Should have status field
        assert "status" in result
        assert result["status"] == "in_progress"

    def test_compact_mode_blocked_flag(self):
        """Compact mode should include blocked flag when true."""
        step = Step(
            completed=False,
            title="Test subtask",
            blocked=True,
            block_reason="Waiting for review",
        )

        result = step_to_dict(step, path="0", compact=True)

        # Should have blocked fields
        assert result["blocked"] is True
        assert result["block_reason"] == "Waiting for review"
        assert result["status"] == "blocked"

    def test_compact_mode_blocked_without_reason(self):
        """Compact mode should include blocked flag even without reason."""
        step = Step(
            completed=False,
            title="Test subtask",
            blocked=True,
            block_reason="",
        )

        result = step_to_dict(step, path="0", compact=True)

        # Should have blocked flag but not reason
        assert result["blocked"] is True
        assert "block_reason" not in result  # Empty reason not included

    def test_compact_mode_not_blocked(self):
        """Compact mode should not include blocked fields when false."""
        step = Step(
            completed=False,
            title="Test subtask",
            blocked=False,
        )

        result = step_to_dict(step, path="0", compact=True)

        # Should not have blocked fields
        assert "blocked" not in result

    def test_computed_status_priority(self):
        """Test computed_status reflects correct priority: completed > blocked > in_progress > pending."""
        # Pending
        step = Step(completed=False, title="Test")
        assert step_to_dict(step, compact=True)["status"] == "pending"

        # In progress (has progress_notes)
        step = Step(completed=False, title="Test", progress_notes=["note"])
        assert step_to_dict(step, compact=True)["status"] == "in_progress"

        # Blocked (takes priority over in_progress)
        step = Step(
            completed=False,
            title="Test",
            progress_notes=["note"],
            blocked=True,
        )
        assert step_to_dict(step, compact=True)["status"] == "blocked"

        # Completed (takes priority over all)
        step = Step(
            completed=True,
            title="Test",
            progress_notes=["note"],
            blocked=True,
        )
        assert step_to_dict(step, compact=True)["status"] == "completed"

    def test_backward_compatibility_with_getattr(self):
        """Serializer should handle missing fields gracefully."""
        # Create a minimal subtask (simulating old data)
        step = Step(completed=False, title="Test")

        # Remove Phase 1 fields to simulate old data
        if hasattr(step, "progress_notes"):
            delattr(step, "progress_notes")
        if hasattr(step, "started_at"):
            delattr(step, "started_at")
        if hasattr(step, "blocked"):
            delattr(step, "blocked")
        if hasattr(step, "block_reason"):
            delattr(step, "block_reason")

        # Full mode should not crash
        result_full = step_to_dict(step, compact=False)
        assert result_full["progress_notes"] == []
        assert result_full["started_at"] is None
        assert result_full["blocked"] is False
        assert result_full["block_reason"] == ""

        # Compact mode should not crash
        result_compact = step_to_dict(step, compact=True)
        assert result_compact["status"] == "pending"

    def test_in_progress_detection_by_started_at(self):
        """Subtask should be in_progress if started_at is set."""
        step = Step(
            completed=False,
            title="Test",
            started_at="2025-01-01T10:00:00",
        )

        result = step_to_dict(step, compact=True)
        assert result["status"] == "in_progress"

    def test_in_progress_detection_by_criteria_confirmed(self):
        """Subtask should be in_progress if criteria_confirmed is set."""
        step = Step(
            completed=False,
            title="Test",
            criteria_confirmed=True,
        )

        result = step_to_dict(step, compact=True)
        assert result["status"] == "in_progress"

    def test_progress_notes_as_list(self):
        """Progress notes should be serialized as list."""
        step = Step(
            completed=False,
            title="Test",
            progress_notes=["note1", "note2", "note3"],
        )

        result = step_to_dict(step, compact=False)
        assert isinstance(result["progress_notes"], list)
        assert len(result["progress_notes"]) == 3
        assert result["progress_notes"] == ["note1", "note2", "note3"]


class TestTaskSerializerPhase1:
    """Test task serialization with Phase 1 subtasks."""

    def test_task_with_phase1_subtasks_compact(self):
        """Task with Phase 1 subtasks should serialize correctly in compact mode."""
        task = TaskDetail(
            id="TEST-1",
            title="Test task",
            status="ACTIVE",
        )
        task.steps = [
            Step(
                completed=False,
                title="Subtask 1",
                blocked=True,
                block_reason="Waiting",
            ),
            Step(
                completed=False,
                title="Subtask 2",
                progress_notes=["note"],
            ),
        ]

        result = task_to_dict(task, include_steps=True, compact=True)

        assert len(result["steps"]) == 2

        # First subtask should be blocked
        assert result["steps"][0]["status"] == "blocked"
        assert result["steps"][0]["blocked"] is True
        assert result["steps"][0]["block_reason"] == "Waiting"

        # Second subtask should be in_progress
        assert result["steps"][1]["status"] == "in_progress"

    def test_task_with_phase1_subtasks_full(self):
        """Task with Phase 1 subtasks should serialize correctly in full mode."""
        task = TaskDetail(
            id="TEST-1",
            title="Test task",
            status="ACTIVE",
        )
        task.steps = [
            Step(
                completed=False,
                title="Subtask 1",
                progress_notes=["note1", "note2"],
                started_at="2025-01-01T10:00:00",
                blocked=True,
                block_reason="Blocked",
            ),
        ]

        result = task_to_dict(task, include_steps=True, compact=False)

        step_data = result["steps"][0]
        assert step_data["progress_notes"] == ["note1", "note2"]
        assert step_data["started_at"] == "2025-01-01T10:00:00"
        assert step_data["blocked"] is True
        assert step_data["block_reason"] == "Blocked"
        assert step_data["computed_status"] == "blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
