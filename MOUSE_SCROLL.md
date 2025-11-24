# Mouse & scrolling guide

## Vertical scrolling

- Wheel — scrolls the viewport in the task list or detail view. The selection stays within the visible window; the list itself moves.
- In detail/subtask view the wheel moves the selected row (because the viewport already matches the sublist).

## Horizontal scrolling shortcuts

| Shortcut    | Effect                              |
|-------------|-------------------------------------|
| `Shift + wheel` | Scroll left/right (5 characters per tick) |
| `[` / `]`   | Scroll left/right (3 characters)     |
| `Ctrl+← / Ctrl+→` | Scroll left/right (5 characters) |
| `Home`      | Reset offset to zero                 |

Hold Shift while using the mouse wheel anywhere inside the TUI to move content horizontally. If your terminal does not propagate Shift for scroll events, fallback to the bracket or Ctrl+arrow shortcuts.

## Implementation notes

- `self.horizontal_offset` tracks the global offset.
- Rendering helpers trim content: `text = text[self.horizontal_offset:]`.
- Table borders never move; only cell content scrolls.
- The footer shows `Offset: N` when the value is non-zero.

## Testing

```
./tasks.py tui
# Select a task → press Enter
# Use ] or Shift+wheel to scroll titles/descriptions.
# Use Home to reset when leaving detail view.
```

## Terminal compatibility

- Works out of the box in modern terminals (WezTerm, iTerm2, Windows Terminal, most 24-bit terminals).
- Legacy terminals that drop Shift modifiers can still use the keyboard shortcuts listed above.
