# Task Tracker — Plans → Tasks → Steps → Plans (TUI + MCP + GUI)

<p align="center">
  <img src="docs/screenshots/hero.png" alt="Apply Task GUI — Steps view" width="1040" />
</p>

Task Tracker (`apply_task`) is a deterministic backlog tool with three first-class interfaces: TUI, MCP, and GUI.

Canonical model:
- **Plan** (`PLAN-###`) — contract + plan checklist (doc/steps/current)
- **Task** (`TASK-###`, `parent=PLAN-###`) — a unit of work inside a plan
- **Step** — checkpointed unit that owns a nested Plan (Plan → Task → Step → …)

The TUI/GUI gives instant visibility into plans, tasks, steps, tests, and blockers, while MCP provides a stable automation surface for AI agents.

**Start here**
- Rules & aliases: [AGENTS.md](AGENTS.md)
- Domain layout: [DOMAIN_STRUCTURE.md](DOMAIN_STRUCTURE.md)
- MCP schemas & examples: [AI_INTENTS.md](AI_INTENTS.md)

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Install into PATH (one-time; isolated)
pipx install .
# or: python -m pip install --user .

# Launch the TUI (auto-opens current project; project picker is still available via ←)
apply_task tui

# Local storage (optional)
apply_task tui --local

# MCP server (for AI assistants)
apply_task mcp
```

## Screenshots

### GUI

| Task detail | Board |
| --- | --- |
| <img src="docs/screenshots/task-detail.png" alt="Task detail modal" width="520" /> | <img src="docs/screenshots/board.png" alt="Board view" width="520" /> |

| Dashboard |
| --- |
| <img src="docs/screenshots/dashboard.png" alt="Dashboard view" width="1040" /> |

### TUI

| Project picker | Tasks list |
| --- | --- |
| <img src="docs/screenshots/tui-projects.png" alt="TUI project picker" width="520" /> | <img src="docs/screenshots/tui-tasks.png" alt="TUI task list" width="520" /> |

| Task detail |
| --- |
| <img src="docs/screenshots/tui-detail.png" alt="TUI task detail" width="1040" /> |

## Why this tool

- **Self-contained** — install with pipx/pip, no external service.
- **Git-aware** — works from any subdirectory, always anchors to the project root.
- **TUI + MCP** — human-friendly interface, stable tool surface for automation.
- **Keyboard & mouse parity** — dual-language hotkeys plus wheel + click navigation.
- **Recursive drill-down** — navigate Plan → Task → Step → Plan with stable paths like `s:0.t:1.s:2`; actions always target the current level.
- **Domain discipline** — tasks live in domain folders inside `.tasks/` (see [DOMAIN_STRUCTURE.md](DOMAIN_STRUCTURE.md)).
- **Guided quality gates** — criteria/tests are explicit checkpoints; blockers are tracked but not “checkable”.

## Interfaces

```bash
# TUI (interactive)
apply_task tui

# MCP (AI tool integration)
apply_task mcp

# GUI (desktop, Tauri)
make gui-dev
make gui-build
```

## Keyboard & mouse quick reference

| Action                       | Keys / Mouse                                  |
|------------------------------|-----------------------------------------------|
| Exit                         | `q`, `й`, `Ctrl+Z`                             |
| Reload                       | `r`, `к`                                       |
| Enter / open                 | `Enter` or double-click                       |
| Back                         | `Esc` or click `[BACK]`                       |
| Navigate                     | `↑↓`, `j`/`о`, `k`/`л`, mouse wheel           |
| Horizontal scroll            | `Shift + wheel`                               |
| Search                       | `/` (type), `Ctrl+U` clear, `Esc` exit        |
| Filters                      | `1` All, `2` In Progress, `3` Backlog, `4` Done|
| Toggle done                  | `Space` or mouse click on checkbox            |
| Edit                          | `e`, `у`                                      |
| Tabs (detail)                | `Tab` (cycle), `←/→` (cycle), `↑↓` scroll     |
| List editor (detail)         | `l`, `д` open · `a` add · `Enter/e` edit · `x/Delete` delete |

## MCP server

For Claude Code and other AI assistants:

```bash
apply_task mcp  # Start MCP stdio server
apply_task mcp --local  # Use <project>/.tasks for the backend
```

Tools are exposed as `tasks_<intent>` (1:1 with the canonical intent API). See `AI_INTENTS.md` for schemas and examples.

Configure in Claude Desktop:
```json
{"mcpServers": {"tasks": {"command": "apply_task", "args": ["mcp"]}}}
```

## Data layout / storage

- By default, all tasks for a git project live in the global directory `~/.tasks/<namespace>`, where `namespace` is derived from the git remote (or folder name if no remote). Local `.tasks` inside the repo is ignored unless you explicitly opt into local mode (`apply_task tui --local` or `apply_task mcp --local`).
- `todo.machine.md` — human overview (`- [x] Title | DONE | note >> .tasks/TASK-001.task`).
- `.tasks/PLAN-###.task` — YAML + Markdown body (contract + plan checklist: `## Контракт`, `## План`).
- `.tasks/TASK-###.task` — YAML + Markdown body (description/context + `## Шаги` tree).
- `.last` — stores the last `TASK@domain` context for shorthand commands.

## Using in another repository

```bash
# Install once (system-wide, isolated)
pipx install .

cd /path/to/repo
# Tasks will still be stored in ~/.tasks/<namespace> for this git project
apply_task tui
```

## Additional docs

- [AI_INTENTS.md](AI_INTENTS.md) — complete AI JSON API reference.
- [AGENTS.md](AGENTS.md) — playbook for AI agents.
- [CHANGES.md](CHANGES.md) — latest UX/feature notes.
- [DOMAIN_STRUCTURE.md](DOMAIN_STRUCTURE.md) — domain/layer layout.
- [SCROLLING.md](SCROLLING.md) — TUI navigation & scrolling design.
- [UI_UX_IMPROVEMENTS.md](UI_UX_IMPROVEMENTS.md) — rationale behind the responsive interface.
- [GIT_PROJECT.md](GIT_PROJECT.md) — git-aware workflow details.

## GitHub Projects v2 sync

`apply_task` can mirror every task into a GitHub Projects v2 board:

1. Save your GitHub PAT once (click `[⚙ Настройки]` next to `[← Назад]` inside the TUI detail pane). The token lives in `~/.apply_task_config.yaml` and is reused across every repository.
2. Copy `apply_task_projects.example.yaml` to `.apply_task_projects.yaml` and edit it:
   ```yaml
   project:
     type: repository
     owner: AmirTlinov
     repo: apply_task
     number: 1
   fields:
     status:
       name: Status
       options:
         DONE: Done
         ACTIVE: "In Progress"
         TODO: Backlog
     progress:
       name: Progress
     domain:
       name: Domain
     steps:
       name: Steps
   ```
3. `APPLY_TASK_GITHUB_TOKEN` / `GITHUB_TOKEN` override the stored PAT (useful for CI runners); otherwise the saved token is used automatically.
4. Any `apply_task` save automatically creates/updates the corresponding Project draft item, including status, percentage, domain text, and a Markdown checklist of steps.
5. Optional reverse sync: expose the webhook endpoint (or rely on the bundled GitHub Action) and every board edit updates the `.task` metadata.

If the config or token is missing, the sync layer silently disables itself. Existing tasks will update as soon as they are touched.

Sample config lives in `apply_task_projects.example.yaml`.
