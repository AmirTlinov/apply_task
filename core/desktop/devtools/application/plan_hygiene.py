"""Heuristics to keep Plan/Contract/Steps boundaries clean.

We intentionally use *soft* detection (warnings) instead of hard validation to avoid
breaking legacy data. The goal is cognitive hygiene across MCP/TUI/GUI:

- Contract: intent + done criteria
- Plan: strategy + phases (doc + steps), not TODO checklists
- Steps: executable checklist + checkpoints
"""

from __future__ import annotations

import re
from typing import List


def plan_doc_overlap_reasons(raw_doc: str) -> List[str]:
    """Return overlap reasons when plan doc looks like other artifacts.

    Reasons (stable tokens):
      - contract
      - done_criteria
      - steps
      - checkbox_checklist
      - step_ids
    """
    text = str(raw_doc or "")
    if not text.strip():
        return []
    reasons: List[str] = []
    if re.search(r"(^|\n)#{1,6}\s*(Contract|Контракт)\b", text, flags=re.IGNORECASE):
        reasons.append("contract")
    if re.search(r"(^|\n)#{1,6}\s*(Done criteria|Definition of done|Критерии)\b", text, flags=re.IGNORECASE):
        reasons.append("done_criteria")
    if re.search(r"(^|\n)#{1,6}\s*(Steps|Шаги)\b", text, flags=re.IGNORECASE):
        reasons.append("steps")
    checkbox_count = len(re.findall(r"(^|\n)\s*-\s*\[(x|X| )\]\s+", text))
    if checkbox_count >= 3:
        reasons.append("checkbox_checklist")
    step_id_count = len(re.findall(r"\bSTEP-\d{3,}\b", text, flags=re.IGNORECASE))
    if step_id_count >= 2:
        reasons.append("step_ids")
    return reasons


def plan_steps_overlap_reasons(raw_steps: List[str]) -> List[str]:
    """Return overlap reasons when plan steps look like TODO/subtasks."""
    if not raw_steps:
        return []
    joined = "\n".join([str(s or "") for s in raw_steps])
    if not joined.strip():
        return []
    reasons: List[str] = []
    has_checkbox = bool(re.search(r"(^|\n)\s*-\s*\[(x|X| )\]\s+", joined))
    step_id_count = len(re.findall(r"\bSTEP-\d{3,}\b", joined, flags=re.IGNORECASE))
    if has_checkbox:
        reasons.append("checkbox_checklist")
    if step_id_count >= 2:
        reasons.append("step_ids")
    return reasons


__all__ = ["plan_doc_overlap_reasons", "plan_steps_overlap_reasons"]
