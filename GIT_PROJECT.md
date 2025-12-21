# Git-aware workflow

`apply_task` resolves the current project via git and keeps storage deterministic per project, no matter which subdirectory you run it from.

## Project root discovery

- When inside a git repository, the project root is `git rev-parse --show-toplevel`.
- When not in a git repository, the current working directory is treated as the project root.

## Storage selection

- **Global (default)**: `~/.tasks/<namespace>/...`, where `namespace` is derived from the git remote (or folder name if no remote).
- **Local (`--local`)**: `<project>/.tasks/...` inside the project root (portable).

## Examples

### Deep inside a repo

```bash
cd my-project/src/components/auth
apply_task tui
```

### Multiple repos side-by-side

```bash
cd workspace/project-a/src
apply_task tui

cd ../project-b/tests
apply_task tui
```

### Non-git folder (local mode)

```bash
cd ~/random-folder
apply_task tui --local
```

## Troubleshooting

- `apply_task tui` opens the project picker; select the expected project and verify storage is updated.
- If storage looks wrong, try `apply_task tui --local` to force `<project>/.tasks`.

