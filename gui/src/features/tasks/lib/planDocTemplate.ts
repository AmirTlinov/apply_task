import type { Task } from "@/types/task";

function stripInlineTags(title: string): string {
  return String(title ?? "")
    .replace(/(^|\s)#[\w-]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function formatList(items: string[] | undefined, emptyFallback: string): string {
  const cleaned = (items ?? [])
    .map((v) => String(v ?? "").trim())
    .filter((v) => v.length > 0);

  if (cleaned.length === 0) return emptyFallback;
  return cleaned.map((v) => `- ${v}`).join("\n");
}

export function buildPlanDocTemplate(task: Task): string {
  const title = stripInlineTags(task.title);
  const domain = task.domain ? ` (${task.domain})` : "";

  return [
    `## Plan doc${domain}`,
    "- This document explains the approach and architecture.",
    "- Keep user intent + definition of done in **Contract** (avoid duplicating it here).",
    "- Keep execution checklist in **Steps** (avoid duplicating it here).",
    "",
    "## Constraints",
    "- _Non-goals:_",
    "- _Hard constraints (security/perf/compat):_",
    "- _Assumptions:_",
    "",
    "## Architecture",
    `- _Current state:_`,
    `- _Target state:_`,
    `- _Key decisions:_`,
    `- _Interfaces / contracts:_`,
    "",
    "## Execution map",
    "- _High-level phases (do not copy subtasks here):_",
    "- _Rollout / migration (if any):_",
    "- _Observability / logging (if any):_",
    "",
    "## Verification",
    "- _(add the exact commands that prove correctness)_",
    "",
    "## Risks & mitigations",
    formatList(task.risks, "- _(list risks + concrete mitigations)_"),
    "",
    `## Notes`,
    `- _Owner:_ ai`,
    `- _Task:_ ${task.id} — ${title}`,
    "",
  ].join("\n");
}
