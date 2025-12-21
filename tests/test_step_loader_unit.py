import io
import json

import pytest

from core.desktop.devtools.interface import step_loader


def test_load_input_source_reads_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")
    result = step_loader._load_input_source(f"@{path}", "payload")
    assert result == "{}"


def test_load_input_source_empty_stdin_raises(monkeypatch):
    monkeypatch.setattr(step_loader.sys, "stdin", io.StringIO(""))
    with pytest.raises(step_loader.StepParseError):
        step_loader._load_input_source("-", "stdin data")


def test_parse_steps_json_bool_and_notes():
    raw = json.dumps(
        [
            {
                "title": "Valid step with flags long title 12345",
                "success_criteria": ["c"],
                "tests": ["t"],
                "blockers": ["b"],
                "criteria_confirmed": "yes",
                "tests_confirmed": "true",
                "criteria_notes": ["note1"],
                "tests_notes": "note2",
                "progress_notes": ["p1", ""],
                "blocked": "false",
            }
        ]
    )
    steps = step_loader.parse_steps_json(raw)
    st = steps[0]
    assert st.criteria_confirmed and st.tests_confirmed
    assert st.criteria_notes == ["note1"]
    assert st.tests_notes == ["note2"]
    assert st.progress_notes == ["p1"]
    assert st.blocked is False


def test_parse_steps_json_requires_list():
    with pytest.raises(step_loader.StepParseError):
        step_loader.parse_steps_json("{}")


def test_parse_steps_json_missing_title():
    raw = json.dumps([{"success_criteria": ["c"]}])
    with pytest.raises(step_loader.StepParseError):
        step_loader.parse_steps_json(raw)


def test_parse_steps_json_missing_criteria():
    raw = json.dumps([{"title": "Valid title long enough 1234567890"}])
    with pytest.raises(step_loader.StepParseError):
        step_loader.parse_steps_json(raw)


def test_validate_flagship_steps_reports_issues():
    raw = json.dumps(
        [
            {"title": "too short", "success_criteria": ["c"], "tests": ["t"], "blockers": ["b"]},
            {"title": "Second step title long enough 12345", "success_criteria": ["c"], "tests": ["t"], "blockers": ["b"]},
            {"title": "Third step title long enough 12345", "success_criteria": ["c"], "tests": ["t"], "blockers": ["b"]},
        ]
    )
    steps = step_loader.parse_steps_json(raw)
    ok, issues = step_loader.validate_flagship_steps(steps)
    assert ok is False
    assert issues


def test_validate_flagship_steps_minimum():
    raw = json.dumps(
        [
            {"title": "First step title long enough 12345", "success_criteria": ["c"], "tests": ["t"], "blockers": ["b"]},
            {"title": "Second step title long enough 12345", "success_criteria": ["c"], "tests": ["t"], "blockers": ["b"]},
        ]
    )
    steps = step_loader.parse_steps_json(raw)
    ok, issues = step_loader.validate_flagship_steps(steps)
    assert ok is False
    assert issues
