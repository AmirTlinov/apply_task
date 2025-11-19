# Subtask column visibility

## Issue

The **Subtasks** column (completed/total counter) disappeared on screens narrower than 150 px, making it hard to gauge progress.

## Fix

Subtasks now remains visible down to **80 px** wide terminals.

| Width | Columns                                | Subtasks? |
|-------|----------------------------------------|-----------|
| ≥180  | Stat, Title, Progress, Subtasks, Context, Notes | ✓ |
| 150–179 | Stat, Title, Progress, Subtasks, Notes        | ✓ |
| 120–149 | Stat, Title, Progress, Subtasks, Notes        | ✓ |
| 100–119 | Stat, Title, Progress, Subtasks               | ✓ |
| 80–99  | Stat, Title, Progress, Subtasks (compact width)| ✓ |
| <80    | Stat, Title, Progress                         | ✗ |

## Code

```python
LAYOUTS = [
    ColumnLayout(min_width=180, columns=['stat','title','progress','subtasks','context','notes']),
    ColumnLayout(min_width=150, columns=['stat','title','progress','subtasks','notes']),
    ColumnLayout(min_width=120, columns=['stat','title','progress','subtasks','notes']),
    ColumnLayout(min_width=100, columns=['stat','title','progress','subtasks']),
    ColumnLayout(min_width=80,  columns=['stat','title','progress','subtasks'], stat_w=5, prog_w=5, subt_w=6),
    ColumnLayout(min_width=0,   columns=['stat','title','progress'], stat_w=4, prog_w=5),
]
```

## Rationale

Subtasks conveys real progress (“3/8”), so it outranks Context. Notes still disappear earlier on tiny screens, but Subtasks survives to 80 px with a 6-character compact width.

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Minimum width for Subtasks | 150 px | 80 px |
| Compact mode | — | Yes |

**Date:** 2025‑01‑17 · **Version:** 2.9.2 · See also [PRIORITY_FIX.md](PRIORITY_FIX.md)
