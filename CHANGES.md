# Changes

## 2025-12-18 · Plans → Tasks → Steps (canonical model)

- Canonical structure: **Plan** (`PLAN-###`) contains **Tasks** (`TASK-###`), each task contains a recursive **Steps** tree.
- Blockers are stored as data (`blockers[]`) and are no longer a checkpoint (no “mark blockers done” anywhere).
- MCP/TUI/GUI share one source of truth: intent API + serializers; tools are deterministic and drift-free.
- Storage schema v4: canonical task body section is `## Шаги` / `## Steps`.

## 2025-12-12 · GUI flagship polish

- Added command palette (`Cmd/Ctrl+K`) for navigation + quick actions and task search.
- Added keyboard navigation in Tasks list (`j/k`, `Enter`) with selection highlighting.
- Task status labels now unified across GUI/TUI/MCP as `TODO` / `ACTIVE` / `DONE`.
- Replaced `window.confirm` with consistent confirm dialogs for destructive actions.
- Added inline step title editing (double-click) via `define` intent support for `title`.
- Timeline items are clickable and open task details.
- Improved step checkpoint section responsiveness (buttons wrap, no clipping).

## 2025-12-07 · AI interface enhancements

### New AI intents
- `resume` — restore AI session context with timeline and dependencies after context loss
- `history` — view operation history or task event timeline with markdown format support
- `context` — now supports `format: "markdown"` for prompt-friendly output

### Batch operations
- `batch` intent supports `atomic: true` for all-or-nothing operations.

### Bug fixes
- Fixed `handle_history` AIResponse field violations (error→error_message, message→summary)
- Fixed `handle_resume` tuple unpacking for `get_blocked_by_dependencies`
- Fixed `handle_context` message field usage
- Added missing `params` field to `Suggestion` dataclass

## 2025-11-22 · Nested steps TUI
- Detail view now renders nested steps as an indented tree with typed paths (e.g., `s:0.t:1.s:2`), and selection is tracked by path.
- Step actions in TUI (toggle, edit, delete, open card) now honor nested paths; mouse/keyboard navigation works across depths.
- Added tree folding: use `←/→` in detail view to collapse/expand branches and follow children.

## 2025-11-21 · Docs hygiene
- Added `AGENTS.md` with hard rules and file aliases, linked from README.
