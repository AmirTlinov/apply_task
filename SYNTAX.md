# apply_task syntax

Deterministic CLI surface: one operation → one command. All non-interactive commands emit JSON.

## Output contract

```json
{
  "command": "show",
  "status": "OK",
  "message": "Task detail",
  "timestamp": "...",
  "payload": { "task": { ... } }
}
```

Errors return `status: "ERROR"` with the same schema and an explanatory message. Interactive modes (`tui`, `guided`) keep textual output, but they still read/write the same files.

## Core commands

```bash
apply_task "Fix memory leak #bug #critical"
apply_task "Add OAuth @TASK-015 #feature"
apply_task "Refactor parser #refactoring"
```

- `#tag` becomes a label.
- `@TASK-XXX` becomes a dependency.
- Subtasks are either added via CLI (`apply_task subtask TASK --add ...`) or supplied as JSON with `--subtasks`.

### Creating a fully-specified task

```bash
apply_task "Task Title #tag" \
  --parent TASK-001 \
  --description "Concrete scope" \
  --tests "pytest -q;coverage xml" \
  --risks "risk1;risk2" \
  --subtasks @payload/subtasks.json
```

Flags `--parent`, `--description`, `--tests`, `--risks`, `--subtasks` are mandatory for flagship quality. Subtasks payload must contain ≥3 detailed items.

### Subtasks input helpers

- `--subtasks '<JSON>'` – inline string.
- `--subtasks @file.json` – load from a file.
- `--subtasks -` – read from STDIN.
- `apply_task template subtasks --count N` – emit a JSON skeleton for editing.

### Viewing/listing

```bash
apply_task show           # last task from .last
apply_task show 001       # TASK-001
apply_task list           # backlog summary
```

List output (TUI/CLI) shows status glyph, title, status code, and percentage. Details include tags, description, subtasks, dependencies, blockers.

### Status updates

```bash
apply_task start [TASK]   # FAIL → WARN
apply_task done [TASK]    # WARN → OK
apply_task fail [TASK]    # → FAIL
```

### Navigation

```bash
apply_task next           # show the next 3 priority tasks and focus the first
```

### TUI

```bash
apply_task tui            # launch full-screen interface
apply_task tui --theme dark-contrast
```

### Checkpoint macros

- `apply_task ok TASK IDX --criteria-note "..." --tests-note "..." --blockers-note "..."`
- `apply_task note TASK IDX --checkpoint tests --note "log" [--undo]`
- `apply_task bulk --input payload.json` (also `-` for STDIN / `@path` for files)

JSON payload example:

```json
{
  "task": "TASK-123",
  "index": 0,
  "criteria": {"done": true, "note": "metrics logged"},
  "tests": {"done": true, "note": "pytest -q"},
  "blockers": {"done": false},
  "complete": false
}
```

### History & replay

```bash
apply_task history [N]    # last N commands (default 5)
apply_task replay N       # re-run command #N (1 = latest)
```

## Direct tasks.py commands (for scripts)

```bash
./tasks.py tui
./tasks.py list --status WARN
./tasks.py show TASK-001
./tasks.py create "Task" --description "..." --tags "tag1,tag2" --subtasks @file.json
./tasks.py task "Task #tag"          # smart parser (tags/deps from title)
./tasks.py add-subtask TASK "..." --criteria "metric>=85%" --tests "pytest -q" --blockers "DB access"
./tasks.py add-dependency TASK "TASK-002"
./tasks.py edit TASK --description "..."
```

## ID formats

`001`, `1`, `TASK-001` — everything is normalized to `TASK-001`.

## Last-task context

`.last` keeps the last `TASK@domain`, so `apply_task show`, `start`, `done`, `fail` can operate without retyping IDs.

## Git awareness

Search order for `tasks.py`:
1. git root (`git rev-parse --show-toplevel`)
2. current directory
3. parents up to the root
4. directory containing the CLI script

This makes `apply_task` usable from any nested folder in the repo.
