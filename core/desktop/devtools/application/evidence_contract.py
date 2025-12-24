"""Evidence contract (single source of truth).

This module defines the supported evidence artifact kinds and hard limits used by
the MCP intents `evidence_capture` and the task-level evidence "black box" shown
in radar/resume.
"""

from typing import Any, Dict, Final, FrozenSet

MAX_ARTIFACT_BYTES: Final[int] = 256_000
MAX_EVIDENCE_ITEMS: Final[int] = 20

EVIDENCE_ARTIFACT_KINDS: Final[FrozenSet[str]] = frozenset({"cmd_output", "diff", "url"})


def evidence_contract_summary() -> Dict[str, Any]:
    """Return a compact, stable contract for agent ergonomics."""
    return {
        "limits": {
            "max_items": int(MAX_EVIDENCE_ITEMS),
            "max_artifact_bytes": int(MAX_ARTIFACT_BYTES),
        },
        "artifact_kinds": {
            "cmd_output": {
                "required_any_of": ["command", "stdout", "stderr"],
                "optional": ["exit_code", "meta"],
            },
            "diff": {"required_any_of": ["diff", "content"], "optional": ["meta"]},
            "url": {"required_any_of": ["url", "external_uri"], "optional": ["meta"]},
        },
    }

