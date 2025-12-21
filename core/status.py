from enum import Enum
from typing import Final, Literal


class Status(Enum):
    TODO = ("TODO", "red", "○")
    ACTIVE = ("ACTIVE", "yellow", "●")
    DONE = ("DONE", "green", "✓")
    UNKNOWN = ("?", "blue", "?")

    @classmethod
    def from_string(cls, value: str) -> "Status":
        val = normalize_status(value, allow_unknown=True)
        for status in cls:
            if status.value[0] == val:
                return status
        return cls.UNKNOWN


StatusCode = Literal["TODO", "ACTIVE", "DONE"]

_CANONICAL_CODES: Final[frozenset[str]] = frozenset({"TODO", "ACTIVE", "DONE"})


def normalize_status(value: str, *, allow_unknown: bool = False) -> str:
    """Normalize status input to internal status code.

    Canonical statuses: TODO, ACTIVE, DONE.

    When allow_unknown=True, returns the normalized token (uppercased, spaces→underscores)
    even if it is not a known status.
    """
    token = (value or "").strip().upper().replace(" ", "_")
    if not token:
        return token
    if token in _CANONICAL_CODES:
        return token
    if allow_unknown:
        return token
    raise ValueError(f"Invalid status: {value!r}")


def status_label(status: str) -> str:
    """Return canonical status token (TODO/ACTIVE/DONE) for any known status input."""
    try:
        return normalize_status(status)
    except ValueError:
        return (status or "").strip()


def normalize_status_code(status: str) -> StatusCode:
    """Normalize any accepted status token to canonical status code (TODO/ACTIVE/DONE)."""
    code = normalize_status(status)
    return code  # type: ignore[return-value]
