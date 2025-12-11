"""Tests for SubTask Phase 1 fields (progress_notes, started_at, blocked, block_reason)."""
import pytest
from core.subtask import SubTask


class TestSubTaskNewFields:
    """Test the new Phase 1 fields and their defaults."""

    def test_default_values(self):
        """Test that new fields have correct default values."""
        st = SubTask(completed=False, title="Test Task")
        assert st.progress_notes == []
        assert st.started_at is None
        assert st.blocked is False
        assert st.block_reason == ""

    def test_computed_status_pending(self):
        """Test computed_status returns 'pending' for new subtask."""
        st = SubTask(completed=False, title="Test Task")
        assert st.computed_status == "pending"

    def test_computed_status_completed(self):
        """Test computed_status returns 'completed' when subtask is completed."""
        st = SubTask(completed=True, title="Test Task")
        assert st.computed_status == "completed"

    def test_computed_status_blocked(self):
        """Test computed_status returns 'blocked' when subtask is blocked."""
        st = SubTask(completed=False, title="Test Task", blocked=True, block_reason="Waiting for API")
        assert st.computed_status == "blocked"

    def test_computed_status_in_progress_with_notes(self):
        """Test computed_status returns 'in_progress' when progress_notes exist."""
        st = SubTask(completed=False, title="Test Task", progress_notes=["Started implementation"])
        assert st.computed_status == "in_progress"

    def test_computed_status_in_progress_with_confirmed(self):
        """Test computed_status returns 'in_progress' with confirmed checkpoints."""
        st = SubTask(completed=False, title="Test Task", criteria_confirmed=True)
        assert st.computed_status == "in_progress"

    def test_computed_status_in_progress_with_started_at(self):
        """Test computed_status returns 'in_progress' when started_at is set."""
        st = SubTask(completed=False, title="Test Task", started_at="2025-01-01T12:00:00")
        assert st.computed_status == "in_progress"

    def test_blocked_priority_over_in_progress(self):
        """Test that blocked status takes priority over in_progress indicators."""
        st = SubTask(
            completed=False,
            title="Test Task",
            blocked=True,
            block_reason="Blocked reason",
            progress_notes=["Some progress"],
            criteria_confirmed=True
        )
        assert st.computed_status == "blocked"


class TestSubTaskMarkdown:
    """Test markdown serialization of new fields."""

    def test_progress_notes_in_markdown(self):
        """Test that progress_notes appear in markdown output."""
        st = SubTask(
            completed=False,
            title="Test Task",
            progress_notes=["Note 1", "Note 2", "Note 3"]
        )
        md = st.to_markdown()
        assert "Прогресс: Note 1; Note 2; Note 3" in md

    def test_started_at_in_markdown(self):
        """Test that started_at appears in markdown output."""
        st = SubTask(
            completed=False,
            title="Test Task",
            started_at="2025-01-01T12:00:00"
        )
        md = st.to_markdown()
        assert "Начато: 2025-01-01T12:00:00" in md

    def test_blocked_with_reason_in_markdown(self):
        """Test that blocked status with reason appears in markdown output."""
        st = SubTask(
            completed=False,
            title="Test Task",
            blocked=True,
            block_reason="Waiting for external API"
        )
        md = st.to_markdown()
        assert "Заблокировано: Waiting for external API" in md

    def test_blocked_without_reason_in_markdown(self):
        """Test that blocked status without reason shows 'да'."""
        st = SubTask(
            completed=False,
            title="Test Task",
            blocked=True,
            block_reason=""
        )
        md = st.to_markdown()
        assert "Заблокировано: да" in md

    def test_all_new_fields_in_markdown(self):
        """Test that all new fields appear together in markdown."""
        st = SubTask(
            completed=False,
            title="Test Task",
            progress_notes=["Progress 1", "Progress 2"],
            started_at="2025-01-01T12:00:00",
            blocked=True,
            block_reason="Dependency issue"
        )
        md = st.to_markdown()
        assert "Прогресс: Progress 1; Progress 2" in md
        assert "Начато: 2025-01-01T12:00:00" in md
        assert "Заблокировано: Dependency issue" in md

    def test_markdown_order_after_timestamps(self):
        """Test that new fields appear after created_at and completed_at."""
        st = SubTask(
            completed=True,
            title="Test Task",
            created_at="2025-01-01T10:00:00",
            completed_at="2025-01-01T14:00:00",
            progress_notes=["Progress"],
            started_at="2025-01-01T11:00:00"
        )
        md = st.to_markdown()
        lines = md.split("\n")

        created_idx = next(i for i, line in enumerate(lines) if "Создано:" in line)
        completed_idx = next(i for i, line in enumerate(lines) if "Завершено:" in line)
        progress_idx = next(i for i, line in enumerate(lines) if "Прогресс:" in line)
        started_idx = next(i for i, line in enumerate(lines) if "Начато:" in line)

        assert created_idx < progress_idx
        assert completed_idx < progress_idx
        assert created_idx < started_idx
        assert completed_idx < started_idx
