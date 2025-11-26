# Changes

## 2025-11-22 · Nested subtasks TUI
- Detail view now renders nested subtasks as an indented tree with `--path` prefixes (e.g., `0.1.2`), and selection is tracked by path.
- Subtask actions in TUI (toggle, edit, delete, open card) now honor nested paths; mouse/keyboard navigation works across depths.
- Added tree folding: use `←/→` in detail view to collapse/expand branches and follow children.

## 2025-11-21 · Docs hygiene
- Added `AGENTS.md` with hard rules and file aliases, linked from README.
- Added `automation` shortcuts (task-template/create/checkpoint/health/projects-health) with defaults in `.tmp`.
