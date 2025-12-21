"""Unit tests for step fields parsing in task_file_parser.py

Tests parsing of step fields:
- progress_notes: List[str] (semicolon-separated list)
- started_at: Optional[str] (ISO datetime)
- blocked: bool (да/yes/true/1 or нет/no/false/0)
- block_reason: str (text after semicolon when blocked=yes)
"""
import pytest
from pathlib import Path
from infrastructure.task_file_parser import TaskFileParser


def test_parse_progress_notes(tmp_path: Path):
    """Verify progress_notes parsing from semicolon-separated list."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-1
title: Test Task
status: TODO
---

## Шаги
- [ ] Implement feature
  - Прогресс: Fixed bug in parser; Added validation; Updated tests
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].progress_notes == [
        "Fixed bug in parser",
        "Added validation",
        "Updated tests",
    ]


def test_parse_started_at(tmp_path: Path):
    """Verify started_at parsing as ISO datetime string."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-2
title: Test Task
status: TODO
---

## Шаги
- [ ] Work in progress
  - Начато: 2025-01-15T10:30:00
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].started_at == "2025-01-15T10:30:00"


def test_parse_blocked_yes_with_reason(tmp_path: Path):
    """Verify blocked=True with reason parsing."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-3
title: Test Task
status: TODO
---

## Шаги
- [ ] Blocked subtask
  - Заблокировано: да; waiting for API response
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "waiting for API response"


def test_parse_blocked_no(tmp_path: Path):
    """Verify blocked=False when value is 'нет'."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-4
title: Test Task
status: TODO
---

## Шаги
- [ ] Not blocked
  - Заблокировано: нет
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].blocked is False
    assert task.steps[0].block_reason == ""


def test_parse_blocked_russian_da(tmp_path: Path):
    """Verify 'да' is recognized as blocked=True."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-5
title: Test Task
status: TODO
---

## Шаги
- [ ] Blocked with да
  - Заблокировано: да; dependency not met
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "dependency not met"


def test_parse_blocked_english_yes(tmp_path: Path):
    """Verify 'yes' is recognized as blocked=True."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-6
title: Test Task
status: TODO
---

## Шаги
- [ ] Blocked with yes
  - Заблокировано: yes; waiting for review
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "waiting for review"


def test_parse_all_phase1_fields_together(tmp_path: Path):
    """Verify all Phase 1 fields can be parsed in one subtask."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-7
title: Test Task
status: TODO
---

## Шаги
- [ ] Complex step
  - Критерии: Unit tests pass; Code reviewed
  - Тесты: test_feature.py
  - Блокеры: External API dependency
  - Чекпоинты: Критерии=TODO; Тесты=TODO; Блокеры=TODO
  - Создано: 2025-01-10T09:00:00
  - Прогресс: Implemented core logic; Added error handling; Writing tests
  - Начато: 2025-01-11T14:20:00
  - Заблокировано: да; waiting for external API fix
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1

    st = task.steps[0]
    assert st.title == "Complex step"
    assert st.completed is False
    assert st.success_criteria == ["Unit tests pass", "Code reviewed"]
    assert st.tests == ["test_feature.py"]
    assert st.blockers == ["External API dependency"]
    assert st.created_at == "2025-01-10T09:00:00"
    assert st.progress_notes == [
        "Implemented core logic",
        "Added error handling",
        "Writing tests",
    ]
    assert st.started_at == "2025-01-11T14:20:00"
    assert st.blocked is True
    assert st.block_reason == "waiting for external API fix"


def test_parse_empty_progress_notes(tmp_path: Path):
    """Verify empty progress notes list when field is empty."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-8
title: Test Task
status: TODO
---

## Шаги
- [ ] Step with empty progress
  - Прогресс:
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].progress_notes == []


def test_parse_empty_started_at(tmp_path: Path):
    """Verify started_at handles empty value gracefully."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-9
title: Test Task
status: TODO
---

## Шаги
- [ ] Step without start time
  - Начато:
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].started_at is None


def test_parse_blocked_without_reason(tmp_path: Path):
    """Verify blocked=True without reason sets empty block_reason."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-10
title: Test Task
status: TODO
---

## Шаги
- [ ] Blocked without reason
  - Заблокировано: да
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == ""


def test_parse_task_without_phase1_fields(tmp_path: Path):
    """Verify tasks without Phase 1 fields still parse correctly."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-11
title: Minimal Task
status: DONE
---

## Описание
This is a task file without Phase 1 fields.

## Шаги
- [x] First step
  - Критерии: Works correctly
  - Тесты: All pass
  - Блокеры: None
  - Чекпоинты: Критерии=OK; Тесты=OK; Блокеры=OK
  - Создано: 2025-01-01T10:00:00
  - Завершено: 2025-01-05T15:30:00
- [ ] Second step
  - Критерии: Feature implemented
  - Тесты: test_feature.py
  - Чекпоинты: Критерии=TODO; Тесты=TODO; Блокеры=TODO
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert task.title == "Minimal Task"
    assert task.description == "This is a task file without Phase 1 fields."
    assert len(task.steps) == 2

    # First step (completed, no Phase 1 fields)
    st1 = task.steps[0]
    assert st1.title == "First step"
    assert st1.completed is True
    assert st1.created_at == "2025-01-01T10:00:00"
    assert st1.completed_at == "2025-01-05T15:30:00"
    # Phase 1 fields should have default values
    assert st1.progress_notes == []
    assert st1.started_at is None
    assert st1.blocked is False
    assert st1.block_reason == ""

    # Second step (pending, no timestamps)
    st2 = task.steps[1]
    assert st2.title == "Second step"
    assert st2.completed is False
    assert st2.progress_notes == []
    assert st2.started_at is None
    assert st2.blocked is False
    assert st2.block_reason == ""


def test_parse_nested_steps_with_phase1_fields(tmp_path: Path):
    """Verify Phase 1 fields work correctly in nested steps."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-12
title: Test Task
status: TODO
---

## Шаги
- [ ] Parent step
  - Прогресс: Started working on children
  - Начато: 2025-01-12T08:00:00
  - [ ] Child step 1
    - Прогресс: Half done
    - Начато: 2025-01-12T09:00:00
    - Заблокировано: нет
  - [ ] Child step 2
    - Заблокировано: да; waiting for child 1
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1

    parent = task.steps[0]
    assert parent.title == "Parent step"
    assert parent.progress_notes == ["Started working on children"]
    assert parent.started_at == "2025-01-12T08:00:00"
    assert parent.blocked is False

    assert parent.plan and parent.plan.tasks
    assert len(parent.plan.tasks) == 1
    assert len(parent.plan.tasks[0].steps) == 2

    child1 = parent.plan.tasks[0].steps[0]
    assert child1.title == "Child step 1"
    assert child1.progress_notes == ["Half done"]
    assert child1.started_at == "2025-01-12T09:00:00"
    assert child1.blocked is False

    child2 = parent.plan.tasks[0].steps[1]
    assert child2.title == "Child step 2"
    assert child2.blocked is True
    assert child2.block_reason == "waiting for child 1"


def test_parse_progress_notes_with_semicolons_in_text(tmp_path: Path):
    """Verify progress notes with semicolons in text are handled correctly."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-13
title: Test Task
status: TODO
---

## Шаги
- [ ] Step
  - Прогресс: Updated config (added key=value); Fixed issue
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1
    # Semicolons split notes - this is expected behavior
    assert task.steps[0].progress_notes == [
        "Updated config (added key=value)",
        "Fixed issue",
    ]


def test_parse_blocked_case_insensitive(tmp_path: Path):
    """Verify blocked field parsing is case-insensitive."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-14
title: Test Task
status: TODO
---

## Шаги
- [ ] Blocked with Yes
  - Заблокировано: Yes; reason A
- [ ] Blocked with TRUE
  - Заблокировано: TRUE; reason B
- [ ] Blocked with 1
  - Заблокировано: 1; reason C
- [ ] Not blocked with No
  - Заблокировано: No
- [ ] Not blocked with FALSE
  - Заблокировано: FALSE
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 5

    assert task.steps[0].blocked is True
    assert task.steps[0].block_reason == "reason A"

    assert task.steps[1].blocked is True
    assert task.steps[1].block_reason == "reason B"

    assert task.steps[2].blocked is True
    assert task.steps[2].block_reason == "reason C"

    assert task.steps[3].blocked is False
    assert task.steps[3].block_reason == ""

    assert task.steps[4].blocked is False
    assert task.steps[4].block_reason == ""


def test_parse_whitespace_handling(tmp_path: Path):
    """Verify whitespace is properly stripped from parsed values."""
    task_file = tmp_path / "test.task"
    task_file.write_text(
        """---
id: test-15
title: Test Task
status: TODO
---

## Шаги
- [ ] Step with whitespace
  - Прогресс:   note1  ;  note2  ; note3
  - Начато:   2025-01-15T10:30:00
  - Заблокировано:  да  ;  reason with spaces
""",
        encoding="utf-8",
    )

    task = TaskFileParser.parse(task_file)
    assert task is not None
    assert len(task.steps) == 1

    st = task.steps[0]
    assert st.progress_notes == ["note1", "note2", "note3"]
    assert st.started_at == "2025-01-15T10:30:00"
    assert st.blocked is True
    assert st.block_reason == "reason with spaces"
