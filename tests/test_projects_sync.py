from pathlib import Path

import pytest

import json

from projects_sync import ProjectsSync
from tasks import SubTask, TaskFileParser
import yaml


def test_projects_sync_disabled_without_config(tmp_path):
    sync = ProjectsSync(config_path=tmp_path / "missing.yaml")
    assert sync.enabled is False


def test_projects_sync_body_preview(tmp_path, monkeypatch):
    cfg = tmp_path / "projects.yaml"
    cfg.write_text(
        """
project:
  type: repository
  owner: dummy
  repo: demo
  number: 1
fields:
  status:
    name: Status
    options:
      OK: Done
  progress:
    name: Progress
"""
    )
    monkeypatch.setenv("APPLY_TASK_GITHUB_TOKEN", "token")
    sync = ProjectsSync(config_path=cfg)
    assert sync.enabled is True

    task = DummyTask()
    body = sync._build_body(task)
    assert "TASK-001" in body
    assert "Subtasks" in body


class DummyTask:
    id = "TASK-001"
    title = "Demo"
    status = "OK"
    domain = "demo/core"
    description = "Body"
    success_criteria = ["Ship" ]
    risks = ["Latency"]

    def __init__(self) -> None:
        st = SubTask(False, "Alpha")
        st.criteria_confirmed = True
        st.tests_confirmed = False
        st.blockers_resolved = False
        self.subtasks = [st]

    def calculate_progress(self) -> int:
        return 33


def test_projects_webhook_updates_task(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    task_file = tasks_dir / "TASK-001.task"
    task_file.write_text(
        "---\n"
        "id: TASK-001\n"
        "status: FAIL\n"
        "progress: 0\n"
        "domain: old\n"
        "project_item_id: ITEM-1\n"
        "---\n# Demo\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".apply_task_projects.yaml"
    cfg.write_text(
        """
project:
  type: repository
  owner: dummy
  repo: demo
  number: 1
fields:
  status:
    name: Status
    options:
      OK: Done
  progress:
    name: Progress
"""
    )
    monkeypatch.setenv("APPLY_TASK_GITHUB_TOKEN", "token")
    sync = ProjectsSync(config_path=cfg)
    sync.project_id = "proj"
    sync.project_fields = {
        "status": {"id": "F_STATUS", "typename": "ProjectV2SingleSelectField", "options": {}, "reverse": {"opt-done": "OK"}},
        "progress": {"id": "F_PROGRESS", "typename": "ProjectV2NumberField"},
    }
    payload = json.dumps(
        {
            "action": "edited",
            "projects_v2_item": {"id": "ITEM-1", "project_node_id": "proj"},
            "changes": {"field_value": {"field_node_id": "F_STATUS", "single_select_option_id": "opt-done"}},
        }
    )
    updated = sync.handle_webhook(payload, None, None)
    assert updated.endswith("TASK-001.task")
    metadata = yaml.safe_load(task_file.read_text().split("---", 2)[1])
    assert metadata["status"] == "OK"


def test_pull_task_fields_updates_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    task_file = tasks_dir / "TASK-050.task"
    task_file.write_text(
        "---\n"
        "id: TASK-050\n"
        "status: FAIL\n"
        "progress: 0\n"
        "domain: legacy\n"
        "project_item_id: ITEM-50\n"
        "---\n# Demo\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".apply_task_projects.yaml"
    cfg.write_text(
        """
project:
  type: repository
  owner: dummy
  repo: demo
  number: 1
fields:
  status:
    name: Status
    options:
      OK: Done
  progress:
    name: Progress
  domain:
    name: Domain
"""
    )
    monkeypatch.setenv("APPLY_TASK_GITHUB_TOKEN", "token")
    sync = ProjectsSync(config_path=cfg)
    sync.project_id = "proj"
    sync.project_fields = {
        "status": {"id": "F_STATUS", "typename": "ProjectV2SingleSelectField", "options": {}, "reverse": {"opt-done": "OK"}},
        "progress": {"id": "F_PROGRESS", "typename": "ProjectV2NumberField"},
        "domain": {"id": "F_DOMAIN", "typename": "ProjectV2TextField"},
    }

    task = TaskFileParser.parse(task_file)

    def fake_graphql(query, variables):
        return {
            "node": {
                "status": {"optionId": "opt-done"},
                "progress": {"number": 80},
                "domain": {"text": "new/core"},
            }
        }

    monkeypatch.setattr(sync, "_graphql", fake_graphql)
    changed = sync.pull_task_fields(task)
    assert changed is True
    new_file = Path(".tasks/new/core/TASK-050.task")
    assert new_file.exists()
    metadata = yaml.safe_load(new_file.read_text().split("---", 2)[1])
    assert metadata["status"] == "OK"
    assert metadata["progress"] == 80
    assert metadata["domain"] == "new/core"
