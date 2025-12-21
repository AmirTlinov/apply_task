"""Safe plan sanitization helpers.

Goal: keep Notes / Plan / Contract / Meta boundaries clean without silent data loss.

This module provides a best-effort "sanitize" operation that extracts obviously
misplaced content from Plan (doc + steps) into the appropriate fields:
- Contract / done criteria (success_criteria)
- Dependencies (depends_on / dependencies)
- Plan checklist (plan_steps)

It is intentionally conservative: it only acts when heuristics from plan_hygiene
strongly indicate overlap (e.g., pasted Contract headings, ≥3 checkbox items).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from core import TaskDetail, StepEvent
from core.desktop.devtools.application.plan_hygiene import (
    plan_doc_overlap_reasons,
    plan_steps_overlap_reasons,
)
from core.desktop.devtools.application.plan_semantics import mark_plan_updated
from core.desktop.devtools.application.task_editing import validate_depends_on_for_step


_CHECKBOX_LINE_RE = re.compile(r"^\s*[-*]\s*\[(x|X| )\]\s+(.+?)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s*(.+?)\s*$")
_TASK_ID_RE = re.compile(r"\bTASK-\d{3,}\b")


@dataclass(frozen=True)
class PlanSanitizeResult:
    changed: bool
    moved_checklist_items: int = 0
    moved_done_criteria: int = 0
    moved_step_ids_to_depends_on: int = 0
    moved_step_ids_to_dependencies: int = 0
    merged_contract: bool = False
    removed_plan_steps: int = 0
    removed_plan_doc_lines: int = 0
    notes: List[str] = field(default_factory=list)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _heading_kind(title: str) -> Optional[str]:
    t = str(title or "").strip().lower()
    if not t:
        return None
    if "contract" in t or "контракт" in t:
        return "contract"
    if "definition of done" in t or "done criteria" in t or "success criteria" in t:
        return "done_criteria"
    if "критерии" in t or "критерии успеха" in t:
        return "done_criteria"
    if "steps" in t or "шаги" in t:
        return "steps"
    return None


def _strip_list_prefix(line: str) -> str:
    raw = str(line or "")
    s = raw.strip()
    if not s:
        return ""
    # Remove checkbox marker.
    m = _CHECKBOX_LINE_RE.match(s)
    if m:
        return m.group(2).strip()
    # Remove bullet/numbering prefixes.
    s = re.sub(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)", "", raw).strip()
    return s


def _step_id_only_line(line: str) -> Optional[str]:
    s = _strip_list_prefix(line)
    if not s:
        return None
    if re.fullmatch(r"TASK-\d{3,}", s.strip().upper()):
        return s.strip().upper()
    return None


def _parse_done_criteria(lines: List[str]) -> List[str]:
    items: List[str] = []
    for raw in lines:
        s = str(raw or "").strip()
        if not s:
            continue
        s = _strip_list_prefix(s)
        if not s:
            continue
        items.append(s)
    return _dedupe_preserve_order(items)


def _extract_sections(doc_lines: List[str]) -> Tuple[List[Tuple[str, List[str]]], set[int]]:
    """Extract recognized markdown sections by headings.

    Returns:
        (sections, removed_indices)
    """
    removed: set[int] = set()
    sections: List[Tuple[str, List[str]]] = []
    i = 0
    while i < len(doc_lines):
        m = _HEADING_RE.match(str(doc_lines[i] or ""))
        if not m:
            i += 1
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        kind = _heading_kind(title)
        if not kind:
            i += 1
            continue
        start = i
        i += 1
        content_start = i
        while i < len(doc_lines):
            m2 = _HEADING_RE.match(str(doc_lines[i] or ""))
            if m2 and len(m2.group(1)) <= level:
                break
            i += 1
        end = i
        for idx in range(start, end):
            removed.add(idx)
        content = [str(x or "") for x in doc_lines[content_start:end]]
        sections.append((kind, content))
    return sections, removed


def _normalize_doc(lines: List[str]) -> str:
    # Trim right whitespace; keep internal indentation where present.
    raw_lines = [str(l or "").rstrip() for l in lines]
    # Drop leading/trailing blank lines.
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    # Collapse excessive blank runs (3+ -> 2).
    out: List[str] = []
    blank_run = 0
    for line in raw_lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 2:
                out.append("")
            continue
        blank_run = 0
        out.append(line)
    return "\n".join(out).strip()


def sanitize_plan(plan: TaskDetail, manager, *, actor: str = "human") -> PlanSanitizeResult:
    """Sanitize Plan doc/steps for a plan TaskDetail (in-place, best-effort)."""
    original_doc = str(getattr(plan, "plan_doc", "") or "")
    original_steps = list(getattr(plan, "plan_steps", []) or [])
    original_current = int(getattr(plan, "plan_current", 0) or 0)

    doc_reasons = plan_doc_overlap_reasons(original_doc)
    steps_reasons = plan_steps_overlap_reasons(original_steps)

    extracted_contract_parts: List[str] = []
    extracted_done: List[str] = []
    extracted_checklist: List[Tuple[bool, str]] = []
    extracted_step_ids: List[str] = []

    removed_doc_lines = 0
    removed_steps = 0
    notes: List[str] = []

    doc_lines = original_doc.splitlines()
    cleaned_doc_lines: List[str] = list(doc_lines)
    removed_indices: set[int] = set()

    # Extract obvious pasted sections (Contract / Done criteria / Steps).
    if any(r in doc_reasons for r in ("contract", "done_criteria", "steps")):
        sections, removed = _extract_sections(doc_lines)
        removed_indices |= removed
        for kind, content in sections:
            if kind == "contract":
                text = "\n".join(content).strip()
                if text:
                    extracted_contract_parts.append(text)
            elif kind == "done_criteria":
                extracted_done.extend(_parse_done_criteria(content))
            elif kind == "steps":
                for raw in content:
                    m = _CHECKBOX_LINE_RE.match(str(raw or "").strip())
                    if m:
                        extracted_checklist.append((m.group(1).lower() == "x", m.group(2).strip()))
                    else:
                        # Accept simple bullet list as unchecked subtasks.
                        item = _strip_list_prefix(raw)
                        if item:
                            extracted_checklist.append((False, item))

    # Rebuild doc without removed sections.
    if removed_indices:
        cleaned_doc_lines = [line for idx, line in enumerate(doc_lines) if idx not in removed_indices]
        removed_doc_lines += len(removed_indices)

    # Extract checkboxes from remaining doc only when it strongly looks like a checklist.
    if "checkbox_checklist" in doc_reasons:
        next_lines: List[str] = []
        for line in cleaned_doc_lines:
            m = _CHECKBOX_LINE_RE.match(str(line or ""))
            if m:
                extracted_checklist.append((m.group(1).lower() == "x", m.group(2).strip()))
                removed_doc_lines += 1
                continue
            next_lines.append(line)
        cleaned_doc_lines = next_lines

    # Extract step-id-only lines from doc when it looks like an ID list.
    if "step_ids" in doc_reasons:
        next_lines = []
        for line in cleaned_doc_lines:
            dep_id = _step_id_only_line(line)
            if dep_id:
                extracted_step_ids.append(dep_id)
                removed_doc_lines += 1
                continue
            next_lines.append(line)
        cleaned_doc_lines = next_lines

    cleaned_doc = _normalize_doc(cleaned_doc_lines)

    # Sanitize plan_steps: pull checkbox-format or task-id-only entries out of plan.
    cleaned_steps: List[str] = []
    extracted_from_steps: List[str] = []
    for item in original_steps:
        raw = str(item or "").strip()
        if not raw:
            continue
        if "checkbox_checklist" in steps_reasons:
            m = _CHECKBOX_LINE_RE.match(raw)
            if m:
                extracted_checklist.append((m.group(1).lower() == "x", m.group(2).strip()))
                removed_steps += 1
                continue
        if "step_ids" in steps_reasons:
            dep_id = _step_id_only_line(raw)
            if dep_id:
                extracted_from_steps.append(dep_id)
                removed_steps += 1
                continue
            ids = _TASK_ID_RE.findall(raw.upper())
            if ids:
                remainder = _TASK_ID_RE.sub("", raw.upper())
                remainder = remainder.replace(",", "").replace(";", "").replace("|", "").strip()
                if not remainder:
                    extracted_from_steps.extend(ids)
                    removed_steps += 1
                    continue
        cleaned_steps.append(raw)
    extracted_step_ids.extend(extracted_from_steps)
    extracted_step_ids = _dedupe_preserve_order([x for x in extracted_step_ids if x])

    # Apply extracted contract / done criteria / dependencies.
    merged_contract = False
    if extracted_contract_parts:
        extracted_contract = "\n\n".join([p.strip() for p in extracted_contract_parts if p.strip()]).strip()
        if extracted_contract:
            current_contract = str(getattr(plan, "contract", "") or "")
            if not current_contract.strip():
                plan.contract = extracted_contract
                merged_contract = True
            elif extracted_contract.strip() not in current_contract:
                plan.contract = current_contract.rstrip() + "\n\n" + extracted_contract.strip()
                merged_contract = True

    moved_done = 0
    if extracted_done:
        existing = [str(x or "").strip() for x in (getattr(plan, "success_criteria", []) or [])]
        before = set([e for e in existing if e])
        merged = _dedupe_preserve_order([e for e in existing if e] + [e for e in extracted_done if e])
        after = set(merged)
        moved_done = len([x for x in after if x and x not in before])
        plan.success_criteria = merged

    moved_checklist = 0
    if extracted_checklist:
        # In the Plan→Task→Step model, plan checklist belongs to plan_steps (linear).
        titles: List[str] = []
        done_prefix = 0
        for done, title in extracted_checklist:
            t = str(title or "").strip()
            if not t:
                continue
            titles.append(t)
            if done and done_prefix == len(titles) - 1:
                done_prefix += 1
        titles = _dedupe_preserve_order(titles)
        if titles:
            moved_checklist = len(titles)
            cleaned_steps = _dedupe_preserve_order([*cleaned_steps, *titles])
            # Best-effort: infer progress from leading checked items when current is empty.
            if original_current == 0 and done_prefix:
                original_current = done_prefix

    moved_depends_on = 0
    moved_dependencies = 0
    if extracted_step_ids:
        extracted_step_ids = [x for x in extracted_step_ids if x != plan.id]
        if extracted_step_ids:
            all_tasks = manager.list_all_tasks()
            existing_ids = {t.id for t in all_tasks}
            known_ids = [x for x in extracted_step_ids if x in existing_ids]
            unknown_ids = [x for x in extracted_step_ids if x not in existing_ids]

            # Try to attach known IDs into depends_on (validated).
            current_depends_on = list(getattr(plan, "depends_on", []) or [])
            candidate = _dedupe_preserve_order([*current_depends_on, *known_ids])
            payload, err = validate_depends_on_for_step(manager, plan.id, candidate)
            if err:
                notes.append(f"depends_on not updated ({err.code}); moved IDs to Meta.dependencies instead")
                unknown_ids.extend(known_ids)
            else:
                before = set(current_depends_on)
                plan.depends_on = candidate
                moved_depends_on = len([x for x in candidate if x and x not in before])
                for dep_id in candidate:
                    if dep_id in before:
                        continue
                    plan.events.append(StepEvent.dependency_added(dep_id, actor=actor))

            # Attach unresolved IDs as freeform dependencies.
            if unknown_ids:
                existing = [str(x or "").strip() for x in (getattr(plan, "dependencies", []) or [])]
                before = set([x for x in existing if x])
                merged = _dedupe_preserve_order([x for x in existing if x] + _dedupe_preserve_order(unknown_ids))
                after = set(merged)
                moved_dependencies = len([x for x in after if x and x not in before])
                plan.dependencies = merged

    # Write back cleaned plan fields.
    plan_doc_changed = cleaned_doc != original_doc.strip()
    plan_steps_changed = cleaned_steps != original_steps
    if plan_doc_changed:
        plan.plan_doc = cleaned_doc
    if plan_steps_changed:
        plan.plan_steps = list(cleaned_steps)
        plan.plan_current = max(0, min(original_current, len(cleaned_steps)))

    # Ensure contract version history stays consistent if contract/done criteria changed.
    _append_contract_version_if_changed(plan)

    # Mark plan updated only when plan content actually changed.
    if plan_doc_changed or plan_steps_changed:
        mark_plan_updated(plan, actor=actor)

    changed = any(
        [
            plan_doc_changed,
            plan_steps_changed,
            bool(merged_contract),
            bool(moved_done),
            bool(moved_checklist),
            bool(moved_depends_on),
            bool(moved_dependencies),
        ]
    )
    return PlanSanitizeResult(
        changed=changed,
        moved_checklist_items=moved_checklist,
        moved_done_criteria=moved_done,
        moved_step_ids_to_depends_on=moved_depends_on,
        moved_step_ids_to_dependencies=moved_dependencies,
        merged_contract=merged_contract,
        removed_plan_steps=removed_steps,
        removed_plan_doc_lines=removed_doc_lines,
        notes=notes,
    )


def _append_contract_version_if_changed(step: TaskDetail) -> None:
    """Append contract_versions entry when contract/done criteria changed."""
    entries = list(getattr(step, "contract_versions", []) or [])

    def _latest(entries_: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
        best: Optional[Dict[str, Any]] = None
        best_v = 0
        for entry in entries_:
            if not isinstance(entry, dict):
                continue
            try:
                v = int(entry.get("version"))
            except (TypeError, ValueError):
                continue
            if v >= best_v:
                best_v = v
                best = entry
        return best, best_v

    latest, latest_v = _latest(entries)
    if latest is not None:
        latest_text = str(latest.get("text", "") or "")
        latest_done = latest.get("done_criteria") or []
        if not isinstance(latest_done, list):
            latest_done = []
        if latest_text == str(getattr(step, "contract", "") or "") and list(latest_done) == list(getattr(step, "success_criteria", []) or []):
            return

    entries.append(
        {
            "version": int(latest_v) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": str(getattr(step, "contract", "") or ""),
            "done_criteria": list(getattr(step, "success_criteria", []) or []),
        }
    )
    step.contract_versions = entries


__all__ = ["PlanSanitizeResult", "sanitize_plan"]
