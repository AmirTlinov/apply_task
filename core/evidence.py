from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VerificationCheck:
    kind: str
    spec: str
    outcome: str
    observed_at: str = ""
    digest: str = ""
    preview: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "kind": self.kind,
            "spec": self.spec,
            "outcome": self.outcome,
            "observed_at": self.observed_at or "",
            "digest": self.digest or "",
            "preview": self.preview or "",
            "details": dict(self.details or {}),
        }
        return {k: v for k, v in payload.items() if v not in ("", {}, None)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationCheck":
        if not isinstance(data, dict):
            raise ValueError("verification check must be object")
        return cls(
            kind=str(data.get("kind", "") or "").strip(),
            spec=str(data.get("spec", "") or "").strip(),
            outcome=str(data.get("outcome", "") or "").strip(),
            observed_at=str(data.get("observed_at", "") or "").strip() or _now_iso(),
            digest=str(data.get("digest", "") or "").strip(),
            preview=str(data.get("preview", "") or "").strip(),
            details=dict(data.get("details", {}) or {}),
        )


@dataclass
class Attachment:
    kind: str
    path: str = ""
    uri: str = ""
    external_uri: str = ""
    size: int = 0
    digest: str = ""
    observed_at: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "kind": self.kind,
            "path": self.path,
            "uri": self.uri,
            "external_uri": self.external_uri,
            "size": int(self.size or 0),
            "digest": self.digest or "",
            "observed_at": self.observed_at or "",
            "meta": dict(self.meta or {}),
        }
        return {k: v for k, v in payload.items() if v not in ("", 0, {}, None)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        if not isinstance(data, dict):
            raise ValueError("attachment must be object")
        return cls(
            kind=str(data.get("kind", "") or "").strip(),
            path=str(data.get("path", "") or "").strip(),
            uri=str(data.get("uri", "") or "").strip(),
            external_uri=str(data.get("external_uri", "") or "").strip(),
            size=int(data.get("size", 0) or 0),
            digest=str(data.get("digest", "") or "").strip(),
            observed_at=str(data.get("observed_at", "") or "").strip() or _now_iso(),
            meta=dict(data.get("meta", {}) or {}),
        )
