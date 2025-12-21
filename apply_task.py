#!/usr/bin/env python3
"""apply_task — launcher for MCP/TUI/GUI.

The CRUD CLI surface has been removed to avoid drift between interfaces.

Use:
- `apply_task tui` — interactive TUI
- `apply_task mcp` — MCP stdio server
- `apply_task gui` — GUI helpers (Tauri)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version


def _print_help() -> None:
    sys.stdout.write(
        "\n".join(
            [
                "apply_task — launcher for MCP/TUI/GUI",
                "",
                "Usage:",
                "  apply_task tui [--theme THEME] [--local|--global] [--mono-select]",
                "  apply_task mcp [--tasks-dir DIR] [--local|--global]",
                "  apply_task gui [--dev|--build]",
                "  apply_task --version",
                "",
            ]
        )
        + "\n"
    )


def _print_version() -> None:
    try:
        sys.stdout.write(pkg_version("apply-task") + "\n")
    except PackageNotFoundError:
        sys.stdout.write("0.0.0\n")


def _cmd_tui(argv: list[str]) -> int:
    from core.desktop.devtools.interface.tui_app import TaskTrackerTUI
    from core.desktop.devtools.interface.tui_themes import DEFAULT_THEME, THEMES

    parser = argparse.ArgumentParser(prog="apply_task tui", add_help=True)
    parser.add_argument("--theme", default=DEFAULT_THEME, choices=sorted(THEMES.keys()))
    parser.add_argument("--mono-select", action="store_true", help="Use monochrome selection highlight.")
    storage = parser.add_mutually_exclusive_group()
    storage.add_argument("--local", dest="use_global", action="store_false", help="Use local storage <project>/.tasks.")
    storage.add_argument("--global", "-g", dest="use_global", action="store_true", help="Use global storage ~/.tasks (default).")
    parser.set_defaults(use_global=True)
    args = parser.parse_args(argv)

    tui = TaskTrackerTUI(
        tasks_dir=None,
        theme=str(args.theme),
        mono_select=bool(args.mono_select),
        use_global=bool(args.use_global),
    )
    tui.run()
    return 0


def _cmd_mcp(argv: list[str]) -> int:
    from core.desktop.devtools.interface import mcp_server

    return int(mcp_server.main(argv) or 0)


def _cmd_gui(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="apply_task gui", add_help=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dev", action="store_true", help="Run GUI in dev mode (pnpm tauri dev).")
    mode.add_argument("--build", action="store_true", help="Build GUI (pnpm tauri build).")
    args = parser.parse_args(argv)
    target = "gui-build" if bool(args.build) else "gui-dev"
    try:
        return int(subprocess.run(["make", target]).returncode)
    except FileNotFoundError:
        sys.stderr.write("make not found. Run GUI via `cd gui && pnpm tauri dev`.\n")
        return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    if args[0] in ("-V", "--version", "version"):
        _print_version()
        return 0

    cmd, rest = args[0], args[1:]
    if cmd == "tui":
        return _cmd_tui(rest)
    if cmd == "mcp":
        return _cmd_mcp(rest)
    if cmd == "gui":
        return _cmd_gui(rest)

    sys.stderr.write(f"Unknown command: {cmd}\n")
    _print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

