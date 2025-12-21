"""Structured step events for timeline tracking and audit.

Events provide a chronological log of all significant changes to a root step,
enabling:
- Timeline view of step history
- Audit trail for checkpoint discipline
- Analytics on step duration and bottlenecks
- Session restoration for AI agents
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Event types
EVENT_CREATED = "created"
EVENT_CHECKPOINT = "checkpoint"  # criteria/tests/blockers confirmed
EVENT_STATUS = "status"  # status changed (TODO/ACTIVE/DONE)
EVENT_BLOCKED = "blocked"  # task became blocked
EVENT_UNBLOCKED = "unblocked"  # task became unblocked
EVENT_STEP_DONE = "step_done"  # nested step completed
EVENT_COMMENT = "comment"  # manual note added
EVENT_DEPENDENCY_ADDED = "dependency_added"
EVENT_DEPENDENCY_RESOLVED = "dependency_resolved"
EVENT_CONTRACT_UPDATED = "contract_updated"
EVENT_PLAN_UPDATED = "plan_updated"
EVENT_PLAN_ADVANCED = "plan_advanced"
EVENT_OVERRIDE = "override"

# Actors
ACTOR_AI = "ai"
ACTOR_HUMAN = "human"
ACTOR_SYSTEM = "system"


@dataclass
class StepEvent:
    """A single event in step history.

    Attributes:
        timestamp: ISO 8601 timestamp when event occurred
        event_type: Type of event (created, checkpoint, status, etc.)
        actor: Who caused the event (ai, human, system)
        target: What was affected ("" for root-level, "step:0.1" for nested)
        data: Event-specific payload
    """

    timestamp: str
    event_type: str
    actor: str = ACTOR_AI
    target: str = ""  # "" = root level, "step:0.1.2" for nested
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def now(cls, event_type: str, actor: str = ACTOR_AI, target: str = "", **data) -> "StepEvent":
        """Create event with current timestamp."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            actor=actor,
            target=target,
            data=data,
        )

    @classmethod
    def created(cls, actor: str = ACTOR_AI) -> "StepEvent":
        """Create 'step created' event."""
        return cls.now(EVENT_CREATED, actor)

    @classmethod
    def checkpoint(
        cls,
        checkpoint_type: str,
        path: str,
        note: str = "",
        actor: str = ACTOR_AI,
    ) -> "StepEvent":
        """Create checkpoint confirmation event.

        Args:
            checkpoint_type: 'criteria', 'tests', or 'blockers'
            path: Step path (e.g., "0" or "0.1.2")
            note: Optional evidence/note
            actor: Who confirmed
        """
        return cls.now(
            EVENT_CHECKPOINT,
            actor,
            target=f"step:{path}",
            checkpoint=checkpoint_type,
            note=note,
        )

    @classmethod
    def status_changed(cls, old_status: str, new_status: str, actor: str = ACTOR_AI) -> "StepEvent":
        """Create status change event."""
        return cls.now(EVENT_STATUS, actor, old=old_status, new=new_status)

    @classmethod
    def step_done(cls, path: str, actor: str = ACTOR_AI) -> "StepEvent":
        """Create nested step completion event."""
        return cls.now(EVENT_STEP_DONE, actor, target=f"step:{path}")

    @classmethod
    def blocked(cls, reason: str, blocker_step: Optional[str] = None, actor: str = ACTOR_SYSTEM) -> "StepEvent":
        """Create blocked event."""
        return cls.now(EVENT_BLOCKED, actor, reason=reason, blocker_step=blocker_step)

    @classmethod
    def unblocked(cls, actor: str = ACTOR_SYSTEM) -> "StepEvent":
        """Create unblocked event."""
        return cls.now(EVENT_UNBLOCKED, actor)

    @classmethod
    def dependency_added(cls, depends_on: str, actor: str = ACTOR_AI) -> "StepEvent":
        """Create dependency added event."""
        return cls.now(EVENT_DEPENDENCY_ADDED, actor, depends_on=depends_on)

    @classmethod
    def dependency_resolved(cls, depends_on: str, actor: str = ACTOR_SYSTEM) -> "StepEvent":
        """Create dependency resolved event."""
        return cls.now(EVENT_DEPENDENCY_RESOLVED, actor, depends_on=depends_on)

    @classmethod
    def comment(cls, text: str, actor: str = ACTOR_AI) -> "StepEvent":
        """Create comment/note event."""
        return cls.now(EVENT_COMMENT, actor, text=text)

    @classmethod
    def override(cls, action: str, reason: str, target: str = "", actor: str = ACTOR_AI) -> "StepEvent":
        """Create override event (force path)."""
        return cls.now(EVENT_OVERRIDE, actor, target=target, action=action, reason=reason)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "target": self.target,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepEvent":
        """Deserialize from dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            event_type=data.get("event_type", ""),
            actor=data.get("actor", ACTOR_AI),
            target=data.get("target", ""),
            data=data.get("data", {}),
        )

    @classmethod
    def from_legacy_history(cls, history_line: str) -> "StepEvent":
        """Convert legacy history string to event.

        Legacy format: "2025-12-07: created" or just "created"
        """
        # Try to parse timestamp prefix
        if ": " in history_line and history_line[:10].replace("-", "").isdigit():
            timestamp_part = history_line.split(": ", 1)[0]
            text_part = history_line.split(": ", 1)[1] if ": " in history_line else history_line
        else:
            timestamp_part = ""
            text_part = history_line

        return cls(
            timestamp=timestamp_part or "",
            event_type="legacy",
            actor=ACTOR_AI,
            target="",
            data={"text": text_part},
        )

    def format_timeline(self) -> str:
        """Format event for timeline display."""
        ts = self.timestamp[:19].replace("T", " ") if self.timestamp else "unknown"

        if self.event_type == EVENT_CREATED:
            return f"[{ts}] Step created"
        elif self.event_type == EVENT_CHECKPOINT:
            checkpoint = self.data.get("checkpoint", "?")
            note = self.data.get("note", "")
            note_suffix = f" — {note}" if note else ""
            return f"[{ts}] {self.target}: {checkpoint} confirmed{note_suffix}"
        elif self.event_type == EVENT_STATUS:
            return f"[{ts}] Status: {self.data.get('old')} → {self.data.get('new')}"
        elif self.event_type == EVENT_STEP_DONE:
            return f"[{ts}] {self.target} completed"
        elif self.event_type == EVENT_BLOCKED:
            reason = self.data.get("reason", "")
            blocker = self.data.get("blocker_step", "")
            return f"[{ts}] Blocked: {reason}" + (f" (by {blocker})" if blocker else "")
        elif self.event_type == EVENT_UNBLOCKED:
            return f"[{ts}] Unblocked"
        elif self.event_type == EVENT_DEPENDENCY_ADDED:
            return f"[{ts}] Dependency added: {self.data.get('depends_on')}"
        elif self.event_type == EVENT_DEPENDENCY_RESOLVED:
            return f"[{ts}] Dependency resolved: {self.data.get('depends_on')}"
        elif self.event_type == EVENT_COMMENT:
            return f"[{ts}] Note: {self.data.get('text', '')}"
        elif self.event_type == EVENT_CONTRACT_UPDATED:
            version = self.data.get("version", "?")
            note = self.data.get("note", "")
            note_suffix = f" — {note}" if note else ""
            return f"[{ts}] Contract v{version} updated{note_suffix}"
        elif self.event_type == EVENT_PLAN_UPDATED:
            steps = self.data.get("steps", None)
            steps_count = len(steps) if isinstance(steps, list) else self.data.get("steps_count", "?")
            current = self.data.get("current", "?")
            return f"[{ts}] Plan updated: {current}/{steps_count}"
        elif self.event_type == EVENT_PLAN_ADVANCED:
            current = self.data.get("current", "?")
            total = self.data.get("total", "?")
            return f"[{ts}] Plan advanced: {current}/{total}"
        elif self.event_type == EVENT_OVERRIDE:
            action = self.data.get("action", "?")
            reason = self.data.get("reason", "")
            target = self.target or ""
            target_prefix = f"{target} " if target else ""
            return f"[{ts}] {target_prefix}override: {action}" + (f" — {reason}" if reason else "")
        elif self.event_type == "legacy":
            return f"[{ts}] {self.data.get('text', '')}"
        else:
            return f"[{ts}] {self.event_type}: {self.data}"


def events_to_timeline(events: List[StepEvent]) -> str:
    """Format list of events as human-readable timeline."""
    if not events:
        return "No events recorded."

    lines = []
    for event in sorted(events, key=lambda e: e.timestamp or ""):
        lines.append(event.format_timeline())

    return "\n".join(lines)


__all__ = [
    "StepEvent",
    "events_to_timeline",
    # Event types
    "EVENT_CREATED",
    "EVENT_CHECKPOINT",
    "EVENT_STATUS",
    "EVENT_BLOCKED",
    "EVENT_UNBLOCKED",
    "EVENT_STEP_DONE",
    "EVENT_COMMENT",
    "EVENT_DEPENDENCY_ADDED",
    "EVENT_DEPENDENCY_RESOLVED",
    "EVENT_CONTRACT_UPDATED",
    "EVENT_PLAN_UPDATED",
    "EVENT_PLAN_ADVANCED",
    # Actors
    "ACTOR_AI",
    "ACTOR_HUMAN",
    "ACTOR_SYSTEM",
]
