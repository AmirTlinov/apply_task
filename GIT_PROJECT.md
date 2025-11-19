# Привязка к Git проекту

## Концепция

`apply_task` автоматически определяет корень git проекта и работает с `todo.machine.md` и `.tasks/` в корне проекта, независимо от того, из какой поддиректории запущена команда.

## Как это работает

### Приоритеты поиска tasks.py

1. **Git проект (наивысший приоритет)**
   Если находишься внутри git проекта, `apply_task` ищет `tasks.py` в корне git:
   ```bash
   git rev-parse --show-toplevel  # Определяет корень
   ```

2. **Текущая директория**
   Если не git или нет tasks.py в корне git → ищет в текущей

3. **Родительские директории**
   Ищет вверх по дереву до корня git проекта (не выше)

4. **Директория скрипта (fallback)**
   Если ничего не найдено → использует директорию где лежит apply_task

## Примеры использования

### Пример 1: Работа из любой поддиректории

```bash
# Структура проекта
my-project/                    # ← git root
├── tasks.py
├── todo.machine.md
├── .tasks/
├── src/
│   ├── components/
│   │   └── auth/            # ← работаешь здесь
│   └── utils/
└── tests/

# Запускаешь из глубокой поддиректории
cd my-project/src/components/auth

# apply_task автоматически найдёт tasks.py в корне git
apply_task "Fix auth bug #critical"
# ✓ Создана TASK-020 в my-project/.tasks/

apply_task list
# Показывает задачи из my-project/todo.machine.md

apply_task show
# Показывает задачу из my-project/.tasks/
```

### Пример 2: Несколько проектов в одной директории

```bash
# Структура
workspace/
├── project-a/               # ← git проект 1
│   ├── tasks.py
│   └── todo.machine.md
└── project-b/               # ← git проект 2
    ├── tasks.py
    └── todo.machine.md

# В project-a
cd workspace/project-a/src/deep/nested
apply_task list
# Работает с project-a/todo.machine.md

# В project-b
cd workspace/project-b/tests
apply_task list
# Работает с project-b/todo.machine.md

# Нет конфликтов!
```

### Пример 3: Не git проект

```bash
# Если директория не git проект
cd ~/random-folder

apply_task list
# ✗ tasks.py не найден
# 💡 Инициализируй git проект или скопируй tasks.py в текущую директорию
```

## Преимущества

### 1. Нет путаницы

```bash
# Всегда работаешь с задачами своего проекта
cd project-a/src/api
apply_task list          # → project-a/todo.machine.md

cd ../../../project-b/frontend
apply_task list          # → project-b/todo.machine.md
```

### 2. Удобство

```bash
# Не нужно возвращаться в корень
cd my-project/src/components/auth/hooks
apply_task "Add useAuth hook #feature"    # Работает!

# Не нужно указывать пути
apply_task show          # Автоматически из корня git
```

### 3. Согласованность

Все члены команды работают с одним `todo.machine.md` в корне git:

```bash
# Developer 1
cd project/backend
apply_task "Fix API #bug"

# Developer 2
cd project/frontend
apply_task list          # Видит задачу от Developer 1
```

## Установка в новый проект

### Шаг 1: Инициализируй git (если ещё нет)

```bash
cd my-new-project
git init
```

### Шаг 2: Скопируй файлы в корень

```bash
# Из task-tracker проекта
cp /path/to/task-tracker/tasks.py .
cp /path/to/task-tracker/requirements.txt .

# Создай структуру
mkdir .tasks
touch todo.machine.md
```

### Шаг 3: Используй из любого места

```bash
cd src/deep/nested/folder
apply_task "First task #setup"
# ✓ Создана в корне проекта
```

## Отладка

### Проверить где apply_task ищет tasks.py

```bash
# Добавить вывод отладки (временно)
cd your-project/subdir
apply_task list

# Если tasks.py не найден, увидишь:
# ✗ tasks.py не найден
# 📁 Git проект: /home/user/your-project
# 💡 Скопируй tasks.py в корень проекта: /home/user/your-project
```

### Проверить корень git

```bash
git rev-parse --show-toplevel
# /home/user/your-project

# tasks.py должен быть здесь:
ls $(git rev-parse --show-toplevel)/tasks.py
```

### Проверить что apply_task находит tasks.py

```bash
cd your-project/src/deep/folder
apply_task show
# Если работает → нашёл tasks.py в корне git
```

## Особые случаи

### Вложенные git проекты (submodules)

```bash
parent-project/                # ← git root 1
├── tasks.py
└── submodule/                 # ← git root 2 (submodule)
    └── tasks.py

# В parent-project/src
cd parent-project/src
apply_task list
# → Использует parent-project/tasks.py

# В submodule
cd parent-project/submodule
apply_task list
# → Использует parent-project/submodule/tasks.py
```

### Не git проект с tasks.py

```bash
# Если tasks.py есть, но git нет
no-git-folder/
└── tasks.py

cd no-git-folder/subfolder
apply_task list
# ✓ Найдёт tasks.py в родительской директории
```

## Рекомендации

1. **Один tasks.py на git проект**
   Храни tasks.py в корне git проекта

2. **Добавь в .gitignore (опционально)**
   ```gitignore
   .last                    # Контекст последней задачи (локальный)
   # todo.machine.md        # Раскомментируй если не хочешь коммитить
   ```

3. **Коммитируй структуру**
   ```bash
   git add tasks.py todo.machine.md .tasks/
   git commit -m "Add task tracking"
   ```

4. **Для команды**
   Все используют один todo.machine.md из корня git

## Миграция существующих проектов

### Если tasks.py уже в другом месте

```bash
# Было
old-location/tasks.py

# Переместить в корень git
cd $(git rev-parse --show-toplevel)
mv /path/to/old-location/tasks.py .
mv /path/to/old-location/todo.machine.md .
mv /path/to/old-location/.tasks .

# Теперь работает из любого места
cd src/any/folder
apply_task list    # ✓
```
