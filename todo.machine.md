# Project Status Tracker

## Core Systems

- [x] 1. Scrollback & search | OK | Scrollback + search >> .tasks/TASK-001.task
- [x] 2. Cursor tracker (VTE) | OK | Cursor + ANSI snapshot
- [x] 3. ANSI grid parser | OK | 8/16/256/RGB + CSI
- [x] 4. ANSI SGR attrs | OK | Bold/Faint/Inverse/Underline
- [x] 5. Text renderer (atlas/SDF/MSDF) | OK | Atlas 2048x2048 + IPU 40%
- [!] 6. Text shaping… | WARN | Monospace + rustybuzz >> .tasks/TASK-006.task
- [x] 7. Render batching… | OK | ColorGrid + glyph batches
- [x] 8. Renderer: WGPU pipelines | OK | rect/underline/text pipelines
- [x] 9. Widget integration… | OK | Adapter/SessionManager flow

## Integration & Quality

- [!] 10. IME cursor mapping | WARN | IME rect from props
- [!] 11. Input: selection | WARN | Базовое выделение мышью
- [!] 12. Input: clipboard | WARN | Copy/paste подключены (Ctrl+Shift+C/V)
- [!] 13. Input: mouse reporting (SGR) | WARN | SGR отправляется (кнопки/модиф.)
- [!] 14. Alternate screen buffer | WARN | Alt buffer реализован
- [!] 15. Perf: dirty regions | WARN | Dirty bounds tracking + hashes
- [x] 16. Perf: frame pacing/telemetry | OK | Adaptive pacer present
- [x] 17. Assets & hashing | OK | apex_assets + BLAKE3

## Advanced Features

- [!] 18. Accessibility (roles/hit) | WARN | a11y crate без интеграции
- [!] 19. Headless parity & CLI fixtures | WARN | Частичная parity
- [!] 20. Platform I/O & DPI | WARN | Без полного DPI и ввода
- [!] 21. Keyboard/Mouse completeness | WARN | Часть путей отсутствует
- [!] 22. Layout/Scene invariants | WARN | Diff/валидация сцены
- [!] 23. CPU fallback/offscreen | WARN | Fallback не автоматизирован
- [!] 24. Complex text (Ligatures/bidi/CJK) | WARN | Ограниченное покрытие
- [x] 25. DEC private modes | FAIL | Нет DECRST/DECSET >> .tasks/TASK-015.task
- [!] 26. Telemetry & regression hashes | WARN | Метрики частичные
- [x] 27. Safety & log sanitization | FAIL | Нет фильтра управляющих
- [x] 28. Config/themes/profiles | WARN | Мало конфигов
- [x] 29. Persistence & recovery | FAIL | Нет сохранения состояния
- [!] 30. Configurable hotkeys & UX | WARN | Горячие клавиши неполные
