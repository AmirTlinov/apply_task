# apply_task — детерминированный интерфейс

Используй только CLI `apply_task` для ведения задач,целей и требований проекта/реализации.

Хранилище: `.tasks/` (TASK-xxx.task, допустимы доменные подпапки). `.last` кеширует `TASK@domain` и восстанавливает контекст.

## Критические правила

- Работай только через CLI `apply_task`; прямое редактирование `.tasks/` запрещено.
- Каждая задача обязана быть детально декомпозирована на атомарные (<1 рабочего дня) подцели с измеримым результатом.
- Каждая подзадача содержит: `title`, `criteria` (конкретные метрики/состояния), `tests` (список проверок), `blockers` (обязательный перечень зависимостей/рисков).
- Blockers не могут быть пустыми: фиксируй внешние сервисы, approvals, последовательность, риски.
- Тесты описывай полно: не только команду, но и покрытие, сценарии, наборы данных, ожидаемые метрики (coverage ≥85%, целевые SLA, перф показатели).
- Любые placeholder-формулировки запрещены; указывай конкретные значения, файлы, команды, артефакты.
- Каждую задачу помещай в соответствующий домен/папку `.tasks` через `--domain/-F` (см. [DOMAIN_STRUCTURE.md](DOMAIN_STRUCTURE.md)) или комбинацию `--phase/--component` — структура backlog отражает архитектурные границы.

## Структурированный вывод CLI

- Все неинтерактивные команды `apply_task` и `tasks.py` возвращают единый JSON-блок:

```json
{
  "command": "list",
  "status": "OK",
  "message": "Список задач сформирован",
  "timestamp": "2025-11-19T12:34:56.789Z",
  "summary": "5 задач",
  "payload": {
    "tasks": [
      {
        "id": "TASK-001",
        "title": "...",
        "status": "OK",
        "progress": 100,
        "subtasks": [
          {
            "title": "...",
            "completed": true,
            "criteria_confirmed": true,
            "tests_confirmed": true,
            "blockers_resolved": true
          }
        ]
      }
    ]
  }
}
```

- `payload.task` и `payload.tasks` содержат детальные структуры `TaskDetail`/`SubTask` (все критерии, тесты, блокеры, заметки).
- Ошибки возвращаются с `status: "ERROR"` и тем же форматом (в том числе для `apply_task` shell-ошибок). Интерактивные режимы (`guided`, `tui`) остаются текстовыми.

## Ввод подзадач

- `--subtasks @/abs/path/to/file.json` — загрузка готового JSON из файла.
- `--subtasks -` — читать JSON из STDIN (pipe heredoc и т.п.).
- `apply_task template subtasks --count N` — получить валидный JSON-шаблон для N подзадач (≥3) и вставить его в файл/STDIN.
- После загрузки данные проходят ту же flagship-валидацию (`criteria/tests/blockers`, ≥20 символов, ≥3 подзадачи).

## Макрокоманды и история

- `apply_task ok TASK-ID IDX [--criteria-note ... --tests-note ... --blockers-note ...]` — за одно действие подтверждает все чекпоинты и закрывает подзадачу.
- `apply_task note TASK-ID IDX --checkpoint {criteria|tests|blockers} --note "..." [--undo]` — добавляет доказательство и (при необходимости) подтверждает/сбрасывает чекпоинт.
- `apply_task bulk --input payload.json` (или `-`/`@file`) — выполняет массив чекпоинтов и закрытий по JSON: `{ "task": "...", "index": 0, "criteria": {"done": true, "note": "..."}, ... }`.
- `apply_task history [N]` — показывает последние N (по умолчанию 5) команд с аргументами; `apply_task replay N` автоматически повторяет команду №N (1 — самая свежая).
## Пример создания задачи

```
apply_task "Task Title #tag" \
  --parent TASK-001 \
  --description "Concrete scope" \
  --tests "pytest -q;apply_task help" \
  --risks "risk1;risk2" \
  --subtasks '[JSON schema]'
```

- Всегда задавай `--parent`, `--description`, `--tests`, `--risks`, `--subtasks`.
- В `--subtasks` минимум три записи; каждая ≥20 символов, атомарна, содержит `criteria`, `tests` и обязательные `blockers`.
- Разрешён только JSON-массив объектов. Каждый объект: `title`, `criteria`, `tests`, `blockers?`.

## Командная карта

- `create` — ручное создание задачи с полным набором флагов.
- `guided [--domain/-F ...]` — интерактивный сценарий создания с валидациями.
- `subtask TASK-ID --add "..." --criteria "...;..." --tests "...;..." --blockers "...;..."` — создание подзадачи.
- `subtask TASK-ID --criteria-done/--tests-done/--blockers-done IDX [--note "..."]` — поэтапное подтверждение чекпоинтов.
- `subtask TASK-ID --done/--undo IDX` — завершение/возврат подзадачи (доступно только после трёх подтверждений).
- `clean [--tag ...] [--status OK|WARN|FAIL] [--phase ...] [--dry-run]` — чистка или предпросмотр задач.
- `show [ID]`, `list [--status --progress ctx]` — чтение и агрегированные представления.
- `start|done|fail [ID]` — изменение статуса (START=WARN, DONE=OK, FAIL=FAIL).
- `next`, `quick`, `suggest|sg` — навигация и рекомендации.
- `lint [--fix]` — проверка/исправление структуры .tasks.
- Контекст: `--domain/-F` имеет приоритет над `--phase/--component`; иначе используется `.last`.

## Декомпозиция и контроль

- Статус `OK` возможен только после выполнения всех подзадач и подтверждения критериев/тестов/блокеров.
- Каждая подзадача: ≥20 символов, описывает один измеримый deliverable, явно указывает критерии готовности и ожидаемые артефакты.
- В `blockers` фиксируй внешние команды, инфраструктуру, secrets, предпосылки; пустой список блокеров запрещён.
- Используй `apply_task subtask TASK-ID --add ... --criteria ... --tests ... --blockers ...`, затем по мере прогресса:
  - `apply_task subtask TASK-ID --criteria-done IDX --note "метрики p95 <=80ms, графики в Grafana link"`
  - `apply_task subtask TASK-ID --tests-done IDX --note "pytest -q tests/api/test_login.py::TestHappyFlow"`
  - `apply_task subtask TASK-ID --blockers-done IDX --note "Флаг activated, DBA выдал доступ"`
- Только после трёх чекпоинтов разрешено `apply_task subtask TASK-ID --done IDX`; `--undo` автоматически сбрасывает completion.
- `apply_task lint` обеспечивает целостность .tasks; запускай после каждого изменения структуры задач.

## Тестирование

- План тестов должен покрывать unit + integration + e2e/perf/chaos (где релевантно) и перечислять конкретные файлы/модули.
- Для каждого теста опиши: команду запуска (`pytest tests/api/test_login.py -k happy_path`, `k6 run perf/login.js`, `pytest -m "not slow"` и т.д.), входные данные/фикстуры, ожидаемые метрики (латентность, SLA, потребление памяти), чёткие assertions.
- Требование по покрытию ≥85% и сохранение/улучшение существующих метрик обязательно; документируй способы проверки (coverage HTML, flamegraphs, мониторинг).
- Добавляй проверки откатов/rollback, алертов и логирования, если изменения затрагивают продакшн-код.
- При отметке `--tests-done` обязательно прикладывай ссылку на отчёт/команду/метрику в `--note`, иначе чекпоинт считается недействительным.

## Пример минимального рабочего цикла

1. `apply_task "<title>" ...` — создание в нужной папке/контексте.
2. `apply_task start [ID]` — фиксация старта; `apply_task show [ID]` — сверка плана.
3. Выполняй работу, отмечай прогресс в файле задачи; подзадачи держи атомарными.
4. `apply_task done [ID]` — только после выполнения критериев и наличия доказательств.
5. `apply_task next` — получение следующего приоритета.

## Дополнительно

- `clean --dry-run` отображает кандидатов без удаления; комбинируй с `--tag/--status/--phase`.
- `lint --fix` безопасно чинит форматирование .tasks.
- Никогда не обходи `apply_task`. Любые операции вне CLI считаются нарушением контракта.
