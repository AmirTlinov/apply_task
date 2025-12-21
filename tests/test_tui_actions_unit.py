from types import SimpleNamespace

from core.desktop.devtools.interface import tui_actions
from core.desktop.devtools.interface.tui_detail_tree import DetailNodeEntry


def test_activate_settings_option_disabled(monkeypatch):
    messages = []

    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(
                settings_selected_index=0,
                edit_buffer=SimpleNamespace(cursor_position=0),
            )

        def _settings_options(self):
            return [{"label": "opt", "value": "", "disabled": True, "disabled_msg": "nope"}]

        def set_status_message(self, msg, ttl=0):
            messages.append(msg)

    tui_actions.activate_settings_option(TUI())
    assert messages == ["nope"]


def test_activate_settings_option_no_options():
    class TUI(SimpleNamespace):
        def _settings_options(self):
            return []

    assert tui_actions.activate_settings_option(TUI()) is None


def test_activate_settings_option_missing_action():
    class TUI(SimpleNamespace):
        def _settings_options(self):
            return [{"label": "opt", "value": ""}]

        settings_selected_index = 0

    assert tui_actions.activate_settings_option(TUI()) is None


def test_activate_settings_option_unknown_action():
    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(settings_selected_index=0)

        def _settings_options(self):
            return [{"label": "opt", "value": "", "action": "unknown"}]

        def _t(self, key, **kwargs):
            return key

        def set_status_message(self, msg, ttl=0):
            self.msg = msg

    tui = TUI()
    tui_actions.activate_settings_option(tui)
    assert getattr(tui, "msg", "") == "STATUS_MESSAGE_OPTION_DISABLED"


def test_activate_settings_option_toggle_sync(monkeypatch):
    state = {}
    monkeypatch.setattr(tui_actions, "update_projects_enabled", lambda desired: state.setdefault("desired", desired))

    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(settings_selected_index=0, edit_buffer=SimpleNamespace(cursor_position=0))

        def _settings_options(self):
            return [{"label": "toggle", "value": "", "action": "toggle_sync"}]

        def _project_config_snapshot(self):
            return {"config_enabled": False}

        def _t(self, key, **kwargs):
            return key

        def set_status_message(self, msg, ttl=0):
            state["status"] = msg

        def force_render(self):
            state["render"] = True

    tui_actions.activate_settings_option(TUI())
    assert state["desired"] is True and state["render"]


def test_delete_current_item_project_allows_deleting_active_project(tmp_path, monkeypatch):
    root = tmp_path / "projects_root"
    root.mkdir()
    active = root / "Owner_repo"
    active.mkdir()
    (active / "TASK-001.task").write_text("id: TASK-001\n", encoding="utf-8")

    # Avoid heavy TaskManager init in unit test.
    monkeypatch.setattr(tui_actions, "TaskManager", lambda p: SimpleNamespace())

    calls = {}

    class TUI(SimpleNamespace):
        def __init__(self):
            proj = SimpleNamespace(id="Owner_repo", name="repo", task_file=str(active))
            super().__init__(
                project_mode=True,
                detail_mode=False,
                tasks=[proj],
                filtered_tasks=[proj],
                selected_index=0,
                projects_root=root,
                tasks_dir=active,
                manager=SimpleNamespace(),
                last_project_index=0,
                last_project_id=None,
                last_project_name=None,
            )

        def set_status_message(self, msg, ttl=0):
            calls["status"] = msg

        def load_projects(self):
            # After deletion, projects list is empty in this unit test.
            self.tasks = []
            self.filtered_tasks = []

        def _ensure_selection_visible(self):
            return None

        def force_render(self):
            calls["render"] = True

    tui = TUI()
    tui_actions.delete_current_item(tui)
    assert not active.exists()
    assert "Проект удален" in calls.get("status", "")
    assert calls.get("render") is True


def test_delete_current_item_project_unlinks_symlink_only(tmp_path, monkeypatch):
    root = tmp_path / "projects_root"
    root.mkdir()
    outside = tmp_path / "outside_target"
    outside.mkdir()
    link = root / "LinkProj"
    link.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(tui_actions, "TaskManager", lambda p: SimpleNamespace())

    class TUI(SimpleNamespace):
        def __init__(self):
            proj = SimpleNamespace(id="LinkProj", name="LinkProj", task_file=str(link))
            super().__init__(
                project_mode=True,
                detail_mode=False,
                tasks=[proj],
                filtered_tasks=[proj],
                selected_index=0,
                projects_root=root,
                tasks_dir=root / ".scratch",
                manager=SimpleNamespace(),
            )

        def set_status_message(self, msg, ttl=0):
            self.msg = msg

        def load_projects(self):
            self.tasks = []
            self.filtered_tasks = []

        def _ensure_selection_visible(self):
            return None

        def force_render(self):
            return None

    tui = TUI()
    tui_actions.delete_current_item(tui)
    assert not link.exists()
    assert outside.exists(), "Deleting project symlink must not delete the target directory"


def test_delete_current_item_list():
    calls = {}

    class Manager:
        def delete_task(self, task_id, domain):
            calls["deleted"] = (task_id, domain)
            return True

    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(filtered_tasks=[SimpleNamespace(id="X", domain="d")], selected_index=0, manager=Manager())

        def load_tasks(self, preserve_selection=False, skip_sync=False):
            calls["loaded"] = (preserve_selection, skip_sync)

        def set_status_message(self, msg, ttl=0):
            calls["status"] = msg

        def _t(self, key, **kwargs):
            return key

    tui_actions.delete_current_item(TUI())
    assert calls["deleted"] == ("X", "d") and calls["loaded"][0] is False
    assert calls["status"] == "STATUS_MESSAGE_DELETED"


def test_delete_current_item_list_fails():
    calls = {}

    class Manager:
        def delete_task(self, task_id, domain):
            calls["deleted"] = (task_id, domain)
            return False

    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(filtered_tasks=[SimpleNamespace(id="Y", domain="d")], selected_index=0, manager=Manager())

        def load_tasks(self, preserve_selection=False, skip_sync=False):
            calls["loaded"] = True

        def set_status_message(self, msg, ttl=0):
            calls["status"] = msg

        def _t(self, key, **kwargs):
            return key

    tui_actions.delete_current_item(TUI())
    assert calls["deleted"] == ("Y", "d")
    assert "loaded" not in calls  # load_tasks should NOT be called on failure
    assert calls["status"] == "ERR_DELETE_FAILED"


def test_delete_current_item_detail():
    class Manager:
        def __init__(self):
            self.deleted = None

        def delete_task_node(self, task_id, path, domain=""):
            self.deleted = (task_id, path, domain)
            return True, None, None

        def load_task(self, task_id, domain="", skip_sync=False):
            return detail

    parent = SimpleNamespace(steps=[], title="p")
    child = SimpleNamespace(steps=[], title="c")
    parent.steps.append(child)
    detail = SimpleNamespace(id="T1", steps=[parent])

    class TUI(SimpleNamespace):
        def __init__(self):
            entry = DetailNodeEntry(
                key="s:0.t:0",
                kind="task",
                node=child,
                level=0,
                collapsed=False,
                has_children=False,
                parent_key=None,
            )
            super().__init__(
                detail_mode=True,
                current_task_detail=detail,
                detail_selected_index=0,
                detail_flat_subtasks=[entry],
                manager=Manager(),
                task_details_cache={},
            )

        def _selected_subtask_entry(self):
            return self.detail_flat_subtasks[0]

        def _rebuild_detail_flat(self):
            self.detail_flat_subtasks = []

        def load_tasks(self, preserve_selection=False, skip_sync=False):
            self.loaded = (preserve_selection, skip_sync)

    tui = TUI()
    tui_actions.delete_current_item(tui)
    assert tui.manager.deleted == ("T1", "s:0.t:0", "")
    assert tui.loaded == (True, True)


def test_delete_current_item_detail_parent_none_updates_cache():
    cache = {}

    class Manager:
        def delete_step_node(self, task_id, path, domain=""):
            cache["deleted"] = (task_id, path, domain)
            return True, None, None

        def load_task(self, task_id, domain="", skip_sync=False):
            return detail

    sub = SimpleNamespace(steps=[], title="solo")
    detail = SimpleNamespace(id="T1", steps=[sub])

    class TUI(SimpleNamespace):
        def __init__(self):
            entry = DetailNodeEntry(
                key="s:0",
                kind="step",
                node=sub,
                level=0,
                collapsed=False,
                has_children=False,
                parent_key=None,
            )
            super().__init__(
                detail_mode=True,
                current_task_detail=detail,
                detail_selected_index=0,
                detail_flat_subtasks=[entry],
                manager=Manager(),
                task_details_cache=cache,
            )

        def _selected_subtask_entry(self):
            return self.detail_flat_subtasks[0]

        def _rebuild_detail_flat(self):
            self.detail_flat_subtasks = []

        def load_tasks(self, preserve_selection=False, skip_sync=False):
            cache["loaded"] = (preserve_selection, skip_sync)

    tui_actions.delete_current_item(TUI())
    assert cache["deleted"] == ("T1", "s:0", "")
    assert cache["loaded"] == (True, True)


def test_delete_current_item_detail_missing_target(monkeypatch):
    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(detail_mode=True, current_task_detail=SimpleNamespace(steps=[]))

        def _selected_subtask_entry(self):
            return DetailNodeEntry(
                key="bad",
                kind="step",
                node=None,
                level=0,
                collapsed=False,
                has_children=False,
                parent_key=None,
            )

    assert tui_actions.delete_current_item(TUI()) is None


def test_delete_current_item_detail_updates_cache_entry():
    cache = {"ID": "old"}

    class Manager:
        def delete_step_node(self, task_id, path, domain=""):
            return True, None, None

        def load_task(self, task_id, domain="", skip_sync=False):
            return detail

    st = SimpleNamespace(steps=[], title="solo")
    detail = SimpleNamespace(id="ID", steps=[st])

    class TUI(SimpleNamespace):
        def __init__(self):
            entry = DetailNodeEntry(
                key="s:0",
                kind="step",
                node=st,
                level=0,
                collapsed=False,
                has_children=False,
                parent_key=None,
            )
            super().__init__(
                detail_mode=True,
                current_task_detail=detail,
                detail_selected_index=0,
                detail_flat_subtasks=[entry],
                manager=Manager(),
                task_details_cache=cache,
            )

        def _selected_subtask_entry(self):
            return self.detail_flat_subtasks[0]

        def _rebuild_detail_flat(self):
            self.detail_flat_subtasks = []

        def load_tasks(self, preserve_selection=False, skip_sync=False):
            pass

    tui_actions.delete_current_item(TUI())
    assert cache["ID"] is detail


def test_delete_current_item_detail_missing_entry():
    class TUI(SimpleNamespace):
        def __init__(self):
            super().__init__(detail_mode=True, current_task_detail=True)

        def _selected_subtask_entry(self):
            return None

    assert tui_actions.delete_current_item(TUI()) is None


def test_activate_settings_option_edit_paths(monkeypatch):
    edits = {}

    class TUI(SimpleNamespace):
        def __init__(self, action):
            super().__init__(
                settings_selected_index=0,
                edit_buffer=SimpleNamespace(cursor_position=0, text=""),
            )
            self._action = action

        def _settings_options(self):
            return [{"label": "opt", "value": "", "action": self._action}]

        def _project_config_snapshot(self):
            return {"number": 7, "workers": 2, "config_enabled": True}

        def _t(self, key, **kwargs):
            return key

        def set_status_message(self, msg, ttl=0):
            edits.setdefault("status", []).append(msg)

        def start_editing(self, ctx, value, idx):
            edits.setdefault("edit", []).append((ctx, value, idx))
            self.edit_buffer.text = value

        def _start_pat_validation(self):
            edits["pat"] = True

        def _cycle_language(self):
            edits["lang"] = True

        def force_render(self):
            edits["render"] = True

    for act in ["edit_pat", "edit_number", "edit_workers", "bootstrap_git", "refresh_metadata", "validate_pat", "cycle_lang"]:
        edits.clear()
        tui_actions.activate_settings_option(TUI(act))
        assert edits  # each action records something
