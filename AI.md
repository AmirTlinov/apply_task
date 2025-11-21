# apply_task — hardline rules for AI agents

1) Operate only via `apply_task`. Never edit `.tasks/` directly. Track context via `.last` (`TASK@domain`).

2) Decompose the requirement: one root task + hierarchical subtasks (infinite nesting). Every subtask (any depth) must have:
   - `title` ≥ 20 chars, atomic.
   - `success_criteria` (specific, verifiable).
   - `tests` (commands/suites/data to prove it).
   - `blockers` (dependencies/risks/approvals).
   - Confirm checkpoints only via `ok/note/bulk --path`.

3) Create tasks (imperative flow):
   - Resolve domain (`--domain/-F` required; see [DOMAIN_STRUCTURE.md](DOMAIN_STRUCTURE.md)).
   - Generate subtask skeleton: `apply_task template subtasks --count N > .tmp/subtasks.json`, fill criteria/tests/blockers.
   - Create task:  
     `apply_task create "Title #tags" --domain <d> --description "<what/why/acceptance>" --tests "<proj tests>" --risks "<proj risks>" --subtasks @.tmp/subtasks.json`
   - Add nested levels with `apply_task subtask TASK --add "<title>" --criteria "...;..." --tests "...;..." --blockers "...;..." --parent-path 0.1` (0-based path like `0.1.2`).

4) Maintain subtasks:
   - Add: `apply_task subtask TASK --add "<title>" ... [--parent-path X.Y]`.
   - Checkpoints: `apply_task ok TASK --path X.Y --criteria --note "evidence"` (same for `--tests/--blockers`).
   - Complete subtask only if all checkpoints are OK: `apply_task subtask TASK --done --path X.Y`.
   - Log progress: `apply_task note TASK --path X.Y --note "what changed"`.

5) Task statuses:
   - Start at `fail` (backlog), move to `warn` only after work starts, `ok` only when all subtasks are done.
   - Commands: `apply_task start/done/fail TASK`.

6) Quality gates (apply to all code):
   - Diff coverage ≥ 85%, cyclomatic complexity ≤ 10, no mocks/stubs in production.
   - One file — one responsibility; avoid >300 LOC without a reason.
   - Before delivery: `pytest -q`; log notes with executed tests.
   - Always keep explicit blockers/tests/criteria on every node; missing any means the node is invalid.

7) GitHub Projects (if sync needed):
   - Config `.apply_task_projects.yaml`, token `APPLY_TASK_GITHUB_TOKEN|GITHUB_TOKEN`.
   - If no token/remote, sync stays off; CLI works offline.

Language rule: when talking to the user, mirror their language unless they explicitly request another. Internal task content (titles/descriptions/notes) follow the user’s language; code/tests/documentation stay in English.

Remember: every move through CLI, with explicit criteria/tests/blockers on every tree node. No checkpoints — no done.***

Запомни: любое действие — через CLI, с явными критериями/тестами/блокерами на каждом узле дерева. Нет чекпоинтов = нет done.***
