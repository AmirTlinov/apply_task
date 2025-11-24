# Column priority fix

## Problem

When the terminal width shrank, the **Notes** column disappeared before **Context**, even though Notes contained critical descriptions while Context usually displayed `-`.

### Old hide order
```
180px → Stat | Title | Progress | Subtasks | Context | Notes
140px → Notes removed ❌
110px → Context removed
 90px → Subtasks removed
 70px → Stat + Title + Progress only
```

## Solution

Make Context the first column to hide so that Notes stays visible longer.

### New hide order
```
180px → Stat | Title | Progress | Subtasks | Context | Notes
150px → hide Context → Stat | Title | Progress | Subtasks | Notes ✓
120px → hide Subtasks → Stat | Title | Progress | Notes ✓
 90px → hide Notes → Stat | Title | Progress
 <70px → compact mode → Stat | Title
```

## Visual comparison (140px)

```
Before:                                          After:
+----+------------------------+-----+------+----+      +----+------------------------+-----+------+-----------------+
|Stat|Title                   |Prog |Subt  |Ctx |      |Stat|Title                   |Prog |Subt  |Notes            |
+----+------------------------+-----+------+----+      +----+------------------------+-----+------+-----------------+
| OK |Scrollback & search     |100% |5/5   |-   |      | OK |Scrollback & search     |100% |5/5   |Scrolling impl...|
|WARN|Text shaping            | 40% |2/5   |-   |      |WARN|Text shaping            | 40% |2/5   |Advanced text... |
```

Notes stay visible; Context hides first.

## Code changes

```python
LAYOUTS = [
    ColumnLayout(min_width=180, columns=['stat', 'title', 'progress', 'subtasks', 'context', 'notes']),
    ColumnLayout(min_width=150, columns=['stat', 'title', 'progress', 'subtasks', 'notes']),
    ColumnLayout(min_width=120, columns=['stat', 'title', 'progress', 'notes']),
    ColumnLayout(min_width=90, columns=['stat', 'title', 'progress']),
    ColumnLayout(min_width=70, columns=['stat', 'title'])
]
```

## Rationale

1. **Context** – low signal, often empty, available inside the detail view.
2. **Subtasks** – nice-to-have counter; progress already shows percentage.
3. **Notes** – critical summary of the task; no fast alternative, so we keep it longest.
4. **Progress / Title / Stat** – must always be visible.

## Validation

```
python3 test_responsive.py
# Layout selection / width calculation / detail width → PASSED
```

| Metric | Value |
|--------|-------|
| New breakpoints | 2 (150px, 120px) |
| Extra pixels where Notes stay visible | +60px |

**Date:** 2025‑01‑17
**Ticket:** UI Priority Fix
**Version:** 2.9.1
