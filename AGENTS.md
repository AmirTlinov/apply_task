# AGENTS playbook (English, strict)

## Core principles

- **Workflow**: use `apply_task` only; keep tasks atomic (<1 day); log checkpoints with notes; run `pytest -q` before delivery.
- **Communication**: answer users in their language; code/docs in English, concise.
- **Architecture**: hexagonal monolith, vertical slices; domain = folder `domain/feature`; layers `application/domain/infrastructure/interface` (see `DOMAIN_STRUCTURE.md`).
- **Quality**: diff coverage ≥85%, cyclomatic complexity ≤10, no mocks/stubs in prod, one file = one responsibility, Conventional Commits.

## Storage

Tasks live in `~/.tasks/<namespace>` derived from git remote (or folder name). Local `.tasks` inside the repo is ignored. TUI starts with project picker from global store.

## Launchers

```bash
# TUI
apply_task tui
apply_task tui --local   # <project>/.tasks (portable)

# MCP server (AI tool integration)
apply_task mcp
apply_task mcp --local
```

## MCP tools

The canonical automation surface is MCP: tools are exposed as `tasks_<intent>` (1:1 with the intent API). See `AI_INTENTS.md` for schemas and examples.

## MCP server

```bash
apply_task mcp  # Start MCP stdio server for Claude Code
```

## GitHub Projects

Config `.apply_task_projects.yaml`, token `APPLY_TASK_GITHUB_TOKEN|GITHUB_TOKEN`; without token sync is off.

## File aliases

- `README.md` — what the tool is and how to start.
- `DOMAIN_STRUCTURE.md` — domain/layer layout.
- `AI_INTENTS.md` — MCP tools / intent schemas and examples.
- `CHANGES.md` — UX/features history.
