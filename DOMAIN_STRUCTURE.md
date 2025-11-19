## Доменные правила (Hexagonal Monolith)

Проект ведётся как «hexagonal monolith» с вертикальными фич-срезами. Чтобы задачи, код и инфраструктура не расползались хаотично, придерживайся следующей структуры:

```
.tasks/
  domain/
    feature/
      TASK-xxx.task
core/
  <domain>/<feature>/application/...
  <domain>/<feature>/infrastructure/...
  <domain>/<feature>/interface/...
```

### Основные принципы

1. **Домен = папка**. Любая задача создаётся с `--domain=<domain>/<feature>` (флаг `-F`). Путь совпадает с фактической подпапкой в `.tasks/` и с пакетом в коде.  
2. **Вертикальные срезы**. Сначала выбирай домен (`payments`, `chat`, `analytics`), затем фичу (`refunds`, `session-runtime`).  
3. **Слои hexagonal**:
   - `application` — сценарии и orchestration.
   - `domain`/`core` — сущности и политики.
   - `infrastructure` — адаптеры, сети, БД.
   - `interface` — CLI/TUI/API входы.
4. **Задачи → артефакты**. Каждое `TASK-xxx` в `.tasks/domain/feature` должно иметь кодовые изменения в соответствующем пакете.  
5. **Фаза и компонент** используются для итераций/техдолга (фильтры TUI), но не заменяют `--domain`.

### Как выбирать `--domain`

1. Ознакомься с существующими подпапками `.tasks/*`.
2. Если домен нов, создай подпапку и обнови документацию (README/DOMAIN_STRUCTURE).
3. Помни, что TUI показывает колонку «Домен» — проверяй, что твои задачи отображаются в нужной ветке.

### Пример создания задачи

```bash
apply_task "Implement refunds API #feature @TASK-042" \
  --domain payments/refunds \
  --parent TASK-010 \
  --description "Add refund orchestration flow на русском" \
  --tests "pytest -q tests/payments/test_refunds.py" \
  --risks "pci scope;manual approval" \
  --subtasks '@path/to/refunds_subtasks.json'
```

Следи за тем, чтобы описание/подзадачи были на русском, а домен соответствовал архитектурной структуре.

### Активные домены

- `desktop/font-tuning` — настройка рендеринга шрифтов и визуального стека рабочей станции.
- `desktop/devtools` — обслуживание и обновление инструментов разработчика (CLI, SDK, SDK-драйверы) на рабочей станции.
