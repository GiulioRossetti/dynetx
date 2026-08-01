"""Shared result containers for temporal DyNetx workflows."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Mapping

__all__ = [
    "SnapshotAnalyticsResult",
    "WindowAnalyticsResult",
    "CommunityAssignmentResult",
    "DiffusionResult",
]


@dataclass
class SnapshotAnalyticsResult:
    """Container for analytics computed on a single snapshot."""

    snapshot: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class WindowAnalyticsResult:
    """Container for analytics computed over a time window."""

    start: Any
    end: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class CommunityAssignmentResult:
    """Container for community detection outputs."""

    communities: List[Any] = field(default_factory=list)
    membership: Dict[Any, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class DiffusionResult:
    """Container for diffusion simulation outputs."""

    timeline: List[Any] = field(default_factory=list)
    node_states: Dict[Any, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
