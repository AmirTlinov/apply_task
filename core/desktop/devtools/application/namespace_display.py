"""Namespace parsing and display formatting.

Storage namespaces are folder names under `~/.tasks/`. Historically they could
contain legacy GitHub prefixes, and some stores may contain both canonical and
repo-only folders. This module provides:

- parsing of namespace into (repo, owner)
- stable display name formatting with collision handling
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class NamespaceParts:
    namespace: str
    repo: str
    owner: str

    @property
    def base(self) -> str:
        return self.repo or self.namespace


def parse_namespace(namespace: str) -> NamespaceParts:
    """Parse namespace into repo + owner (best-effort, display-oriented)."""
    name = (namespace or "").strip()
    if not name:
        return NamespaceParts(namespace="", repo="", owner="")

    raw = name
    # Legacy namespaces: "__github.com_<owner>_<repo>" or "github.com_<owner>_<repo>"
    if raw.startswith("__github.com_"):
        raw = raw[2:]
    if raw.startswith("github.com_"):
        raw = raw[len("github.com_") :].strip("_").strip()

    if raw and "_" in raw and not raw.startswith("_"):
        owner, repo = raw.split("_", 1)
        if owner and repo:
            return NamespaceParts(namespace=name, repo=repo, owner=owner)

    return NamespaceParts(namespace=name, repo=raw or name, owner="")


def build_display_names(namespaces: Iterable[str]) -> Dict[str, str]:
    """Return mapping {namespace: display_name} with collision-safe qualifiers."""
    parts: List[NamespaceParts] = [parse_namespace(ns) for ns in namespaces]
    counts: Dict[str, int] = {}
    for p in parts:
        key = (p.base or p.namespace).lower()
        counts[key] = counts.get(key, 0) + 1

    display: Dict[str, str] = {}
    for p in parts:
        base = p.base or p.namespace
        key = base.lower()
        if counts.get(key, 0) <= 1:
            display[p.namespace] = base
            continue
        qualifier = p.owner or "local"
        display[p.namespace] = f"{base} ({qualifier})"
    return display


__all__ = ["NamespaceParts", "parse_namespace", "build_display_names"]

