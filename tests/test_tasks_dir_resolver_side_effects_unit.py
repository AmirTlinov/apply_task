from pathlib import Path

from core.desktop.devtools.interface.tasks_dir_resolver import get_tasks_dir_for_project
from core.desktop.devtools.interface.tui_app import TaskTrackerTUI


def test_get_tasks_dir_for_project_is_side_effect_free_by_default(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)

    expected = Path(home) / ".tasks" / "proj"
    resolved = get_tasks_dir_for_project(use_global=True)
    assert resolved.resolve() == expected.resolve()
    assert not expected.exists()
    assert not (Path(home) / ".tasks").exists()

    created = get_tasks_dir_for_project(use_global=True, create=True)
    assert created.resolve() == expected.resolve()
    assert expected.exists()


def test_tui_does_not_create_namespace_dir_on_startup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)

    expected = Path(home) / ".tasks" / "proj"
    # Instantiate the TUI; it should not create global namespace dirs until the user creates tasks.
    TaskTrackerTUI(tasks_dir=None)
    assert not expected.exists()

