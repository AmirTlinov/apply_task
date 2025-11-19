# Синтаксис apply_task

Формализованный, детерминированный синтаксис. Одна операция — одна команда.

## Команды

### Формат вывода

- Все команды (кроме интерактивных `guided`/`tui`) возвращают структурированный JSON:

```json
{
  "command": "show",
  "status": "OK",
  "message": "Детали задачи",
  "timestamp": "...",
  "payload": {
    "task": {
      "id": "TASK-001",
      "title": "...",
      "subtasks": [
        {"title": "...", "completed": false, "criteria_confirmed": true, "...": "..."}
      ]
    }
  }
}
```

- Поле `summary` содержит короткое описание, `payload` — все необходимые данные. Ошибки используют `status: "ERROR"` и тот же контракт.

### Создание задачи
```bash
apply_task "Название #тег1 #тег2 @TASK-XXX"
```

**Smart парсинг:**
- `#тег` → извлекается в теги
- `@TASK-XXX` → извлекается в зависимости
- Подзадачи добавляются вручную: `apply_task subtask TASK-ID --add "..." --criteria "...;..." --tests "...;..." --blockers "...;..."`

**Примеры:**
```bash
apply_task "Fix memory leak #bug #critical"
apply_task "Add OAuth @TASK-015 #feature"
apply_task "Refactor parser #refactoring"
```

### Гибкий ввод подзадач

- `--subtasks '<JSON>'` — как раньше.
- `--subtasks @/path/to/file.json` — чтение из файла (удобно для длинных списков).
- `--subtasks -` — чтение JSON из STDIN (heredoc / pipe).
- `apply_task template subtasks --count 4` выдаёт валидный JSON-шаблон для редактирования и последующей передачи через файл/STDIN.

### Просмотр задачи
```bash
apply_task show              # Последняя задача
apply_task show 001          # TASK-001
```

**Вывод:**
- Заголовок, статус, приоритет, прогресс
- Теги
- Описание
- Подзадачи
- Зависимости

### Список задач
```bash
apply_task list
```

**Вывод:**
```
✓ TASK-001: Название [OK] 100%
! TASK-002: Название [WARN] 50%
✗ TASK-003: Название [FAIL] 0%
```

### Обновление статуса

**Начать работу:**
```bash
apply_task start             # Последняя → WARN
apply_task start 001         # TASK-001 → WARN
```

**Завершить:**
```bash
apply_task done              # Последняя → OK
apply_task done 001          # TASK-001 → OK
```

**Провалить:**
```bash
apply_task fail              # Последняя → FAIL
apply_task fail 001          # TASK-001 → FAIL
```

### Навигация

**Следующая задача:**
```bash
apply_task next
```

Выдаёт топ-3 приоритетных задачи и сохраняет первую как текущую.

### TUI

**Запустить интерфейс:**
```bash
apply_task tui
```

### Макрокоманды чекпоинтов

- `apply_task ok TASK-001 0 --criteria-note "..." --tests-note "..." --blockers-note "..."` — подтверждает все чекпоинты подзадачи и завершает её.
- `apply_task note TASK-001 1 --checkpoint criteria --note "лог"` — добавляет заметку и подтверждает указанный чекпоинт (`--undo` для сброса).
- `apply_task bulk --input payload.json` (`@file`, `-` для STDIN) — выполняет массив операций `{ "task": "...", "index": 0, "criteria": {"done": true, "note": "..."}, "complete": true }`.

### История и повтор

- `apply_task history [N]` — показывает последние N (по умолчанию 5) команд с аргументами.
- `apply_task replay N` — повторяет команду №N (1 — самая свежая) без повторного логирования.

## Прямые команды tasks.py

Для скриптов и расширенного управления:

```bash
./tasks.py tui
./tasks.py list
./tasks.py list --status WARN
./tasks.py show TASK-001
./tasks.py create "Task" --description "..." --tags "..." --subtasks "..."
./tasks.py task "Task #tag"
./tasks.py update TASK-001 OK
./tasks.py analyze TASK-001
./tasks.py next
./tasks.py add-subtask TASK-001 "Subtask detail..." --criteria "metric>=85%;p95<=100ms" --tests "pytest -q tests/api/test_login.py" --blockers "DB access;feature flag"
./tasks.py add-dependency TASK-001 "TASK-002"
./tasks.py edit TASK-001 --description "..."
```

## Форматы ID

Все эквивалентны:
```bash
apply_task show 001
apply_task show TASK-001
apply_task show 1
```

Автоматически нормализуется в `TASK-001`.

## Контекст последней задачи

Файл `.last` хранит ID последней задачи:

```bash
apply_task "New task"        # Создаёт и сохраняет в .last
apply_task show              # Показывает из .last
apply_task start             # Обновляет из .last
apply_task done              # Завершает из .last

apply_task show 015          # Показывает TASK-015 и сохраняет в .last
apply_task done              # Завершает TASK-015
```

## Git привязка

`apply_task` работает с корнем git проекта:

```bash
# Из любой поддиректории
cd my-project/src/deep/nested
apply_task "Fix bug"
# → Создаст в my-project/.tasks/TASK-XXX.task

apply_task list
# → Покажет из my-project/todo.machine.md
```

**Приоритеты поиска tasks.py:**
1. Корень git проекта
2. Текущая директория
3. Родительские директории (до корня git)
4. Директория скрипта

## Workflow

**Базовый цикл:**
```bash
apply_task "Task #tag"       # Создать
apply_task show              # Посмотреть
apply_task start             # Начать
# ... работа ...
apply_task done              # Завершить
apply_task next              # Следующая
```

**С зависимостями:**
```bash
apply_task "Add OAuth @TASK-015 #feature"
apply_task show              # Увидеть зависимость
apply_task start
```

## Разделители

- **Теги:** запятая `,` или `#` в названии
- **Подзадачи:** точка с запятой `;`
- **Зависимости:** запятая `,` или `@` в названии

```bash
# Через smart парсинг
apply_task "Task @TASK-001 @TASK-002 #tag1 #tag2"

# Через параметры tasks.py
./tasks.py create "Task" --tags "tag1,tag2" --dependencies "TASK-001,TASK-002"
```
