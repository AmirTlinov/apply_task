"""Interface-level constants for tasks TUI/MCP/GUI."""

from core.desktop.devtools.interface.constants_i18n import LANG_PACK  # noqa: F401

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

AI_HELP = """apply_task — hardline rules for AI agents

1) Operate only via MCP tools / TUI. Never edit `.tasks/` directly. Track context via `.last` (TASK@domain).
2) Model: Plan → Task → Step→Plan→Task→Step (infinite depth). Plan stores Contract + Plan checklist. Task stores the Steps tree.
3) Preserve "why / what done means": store the latest user request in Contract and keep an execution Plan (MCP tools: tasks_contract/tasks_plan).
4) Decompose: steps are recursive. Every step: title ≥20 chars; success_criteria; tests; blockers. Checkpoints only for criteria/tests (blockers are data, not checkable).
5) Create flow (MCP): `tasks_create` (plan/task) → `tasks_decompose` (steps) → `tasks_task_add` (nested tasks) → `tasks_define/tasks_task_define` (details).
6) Completion discipline: a step can be completed only when its criteria/tests are confirmed (`tasks_verify`), then mark completion (`tasks_progress`). Blockers are tracked but never "checked off".
7) Quality gates: diff coverage ≥85%; cyclomatic complexity ≤10; no mocks/stubs in prod; one file = one responsibility; prefer <300 LOC. Before delivery run `pytest -q` and log executed tests.
Language: reply to user in their language unless asked otherwise. Task text/notes follow user language; code/tests/docs stay in English. Explicit blockers/tests/criteria on every node. No checkpoints — no done.
"""
