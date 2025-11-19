# Улучшение видимости Subtasks в маленьких окнах

## Проблема

Колонка **Subtasks** (счётчик подзадач) исчезала на экранах < 150px, что затрудняло отслеживание прогресса по подзадачам.

## Решение

Колонка **Subtasks теперь видна начиная с 80px** (было 150px).

### Новая логика отображения

| Ширина экрана | Видимые колонки | Subtasks видна? |
|---------------|-----------------|-----------------|
| ≥ 180px | Stat, Title, Prog, **Subt**, Context, Notes | ✓ |
| 150-179px | Stat, Title, Prog, **Subt**, Notes | ✓ |
| 120-149px | Stat, Title, Prog, **Subt**, Notes | ✓ |
| 100-119px | Stat, Title, Prog, **Subt** | ✓ |
| 80-99px | Stat, Title, Prog, **Subt** (компактная) | ✓ |
| < 80px | Stat, Title, Prog | ✗ |

## Визуальные примеры

### Экран 120px (средний)

**Было:**
```
+----+--------------------------------+-----+----------------------------------+
|Stat|Title                           |Prog |Notes                             |
+----+--------------------------------+-----+----------------------------------+
| OK |Scrollback & search             |100% |Реализация системы прокрутки...   |
|WARN|Text shaping                    | 40% |Продвинутый рендеринг...          |
+----+--------------------------------+-----+----------------------------------+
       ❌ Не видно сколько подзадач выполнено
```

**Стало:**
```
+----+------------------------+-----+------+----------------------------------+
|Stat|Title                   |Prog |Subt  |Notes                             |
+----+------------------------+-----+------+----------------------------------+
| OK |Scrollback & search     |100% |5/5   |Реализация системы прокрутки...   |
|WARN|Text shaping            | 40% |2/5   |Продвинутый рендеринг...          |
+----+------------------------+-----+------+----------------------------------+
       ✓ Видно прогресс подзадач!
```

### Экран 90px (маленький)

**Было:**
```
+----+--------------------------------+-----+
|Stat|Title                           |Prog |
+----+--------------------------------+-----+
| OK |Scrollback & search             |100% |
|WARN|Text shaping                    | 40% |
+----+--------------------------------+-----+
       ❌ Нет информации о подзадачах
```

**Стало:**
```
+----+-------------------------+-----+------+
|Stat|Title                    |Prog |Subt  |
+----+-------------------------+-----+------+
| OK |Scrollback & search      |100% |5/5   |
|WARN|Text shaping             | 40% |2/5   |
+----+-------------------------+-----+------+
       ✓ Subtasks видна даже на маленьком экране!
```

## Технические изменения

### tasks.py (строки 774-781)

```python
# Было:
LAYOUTS = [
    ColumnLayout(min_width=180, ...),
    ColumnLayout(min_width=150, columns=['stat', 'title', 'progress', 'subtasks', 'notes']),
    ColumnLayout(min_width=120, columns=['stat', 'title', 'progress', 'notes']),  # ❌ Subtasks исчезла
    ColumnLayout(min_width=90, columns=['stat', 'title', 'progress']),
    ...
]

# Стало:
LAYOUTS = [
    ColumnLayout(min_width=180, columns=['stat', 'title', 'progress', 'subtasks', 'context', 'notes']),
    ColumnLayout(min_width=150, columns=['stat', 'title', 'progress', 'subtasks', 'notes']),
    ColumnLayout(min_width=120, columns=['stat', 'title', 'progress', 'subtasks', 'notes']),  # ✓ Subtasks осталась
    ColumnLayout(min_width=100, columns=['stat', 'title', 'progress', 'subtasks']),  # ✓ Subtasks осталась
    ColumnLayout(min_width=80, columns=['stat', 'title', 'progress', 'subtasks'], stat_w=5, prog_w=5, subt_w=6),  # ✓ Компактная
    ColumnLayout(min_width=0, columns=['stat', 'title', 'progress'], stat_w=4, prog_w=5),  # Минимум
]
```

## Обоснование

### Почему Subtasks важна?

1. **Прогресс работы** — показывает сколько подзадач выполнено (например, "3/8")
2. **Планирование** — помогает оценить объём оставшейся работы
3. **Визуальный контроль** — быстрая оценка состояния без перехода в detail view
4. **Приоритетность** — важнее Context (который часто "-")

### Компромиссы

- **120px+** → Subtasks + Notes (всё важное видно)
- **100-119px** → Subtasks, но без Notes (приоритет прогрессу)
- **80-99px** → Subtasks компактная (ширина 6 вместо 7)
- **< 80px** → Минимум (только Stat, Title, Prog)

## Приоритеты колонок (итоговые)

От самой важной к менее важной:

1. **Stat** — статус (всегда видна)
2. **Title** — название задачи (всегда видна)
3. **Progress** — процент выполнения (всегда видна до 80px)
4. **Subtasks** — счётчик подзадач (видна с 80px) ⬅️ **УЛУЧШЕНО**
5. **Notes** — описание (видна с 120px)
6. **Context** — папка/компонент (видна с 180px)

## Метрики

| Метрика | Было | Стало | Улучшение |
|---------|------|-------|-----------|
| Min ширина для Subtasks | 150px | 80px | **-70px** |
| Breakpoints | 4 | 5 | +1 |
| Компактный режим Subtasks | Нет | Да (6 символов) | ✓ |

## Проверка

```bash
$ python3 tasks.py --help
✓ Синтаксис корректен

# Визуальная проверка
$ python3 -c "from tasks import ResponsiveLayoutManager; [print(f'{w}px: {ResponsiveLayoutManager.select_layout(w).columns}') for w in [60, 80, 100, 120]]"
60px: ['stat', 'title', 'progress']
80px: ['stat', 'title', 'progress', 'subtasks']  ✓
100px: ['stat', 'title', 'progress', 'subtasks']  ✓
120px: ['stat', 'title', 'progress', 'subtasks', 'notes']  ✓
```

## Итог

✅ **Subtasks видна на маленьких экранах начиная с 80px**
✅ **Компактный режим (6 символов) для экранов 80-99px**
✅ **Сохранены все важные колонки (Title + Progress + Subtasks)**

---

**Дата:** 2025-01-17
**Версия:** 2.9.2
**Связанные фиксы:** PRIORITY_FIX.md
