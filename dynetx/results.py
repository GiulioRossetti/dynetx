"""Shared result containers for temporal DyNetx workflows.

The dataclasses in this module are lightweight, serializable summaries used by
analysis, community-detection, and diffusion helpers. They intentionally keep
their structure simple so they can be documented and consumed by Sphinx
autodoc, notebooks, and JSON export code without additional adapters.
"""

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
    """Analytics computed on a single snapshot.

    Parameters
    ----------
    snapshot : Any
        Snapshot identifier or metadata describing the evaluated slice.
    metrics : dict[str, Any], optional
        Mapping of metric names to computed values.
    metadata : dict[str, Any], optional
        Additional contextual information, such as the algorithm name or
        parameter settings used during computation.

    Returns
    -------
    SnapshotAnalyticsResult
        A serializable result object.

    Examples
    --------
    >>> from dynetx.results import SnapshotAnalyticsResult
    >>> result = SnapshotAnalyticsResult(snapshot=0, metrics={"density": 0.25})
    >>> result.to_dict()["metrics"]["density"]
    0.25

    References
    ----------
    No specific publication is associated with this container; it is a helper
    type for DyNetx's documented analytics API.
    """

    snapshot: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return the result as a plain dictionary.

        Examples
        --------
        >>> from dynetx.results import SnapshotAnalyticsResult
        >>> SnapshotAnalyticsResult(snapshot=0, metrics={"density": 0.0}).to_dict()
"""
        return asdict(self)


@dataclass
class WindowAnalyticsResult:
    """Analytics computed over a time window.

    Parameters
    ----------
    start : Any
        Inclusive start of the analyzed interval.
    end : Any
        Inclusive end of the analyzed interval.
    metrics : dict[str, Any], optional
        Mapping of metric names to computed values.
    metadata : dict[str, Any], optional
        Additional contextual information, such as the algorithm name or
        parameter settings used during computation.

    Returns
    -------
    WindowAnalyticsResult
        A serializable result object.

    Examples
    --------
    >>> from dynetx.results import WindowAnalyticsResult
    >>> result = WindowAnalyticsResult(start=0, end=3, metrics={"avg_degree": 2})
    >>> result.to_dict()["end"]
    3

    References
    ----------
    No specific publication is associated with this container; it is a helper
    type for DyNetx's documented analytics API.
    """

    start: Any
    end: Any
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return the result as a plain dictionary.

        Examples
        --------
        >>> from dynetx.results import WindowAnalyticsResult
        >>> WindowAnalyticsResult(start=0, end=1, metrics={"density": 0.0}).to_dict()
"""
        return asdict(self)


@dataclass
class CommunityAssignmentResult:
    """Community-detection outputs.

    Parameters
    ----------
    communities : list[Any], optional
        Collection of communities returned by an algorithm.
    membership : dict[Any, Any], optional
        Mapping from node identifiers to community identifiers.
    metadata : dict[str, Any], optional
        Additional contextual information, such as the algorithm name or
        parameter settings used during computation.

    Returns
    -------
    CommunityAssignmentResult
        A serializable result object.

    Examples
    --------
    >>> from dynetx.results import CommunityAssignmentResult
    >>> result = CommunityAssignmentResult(communities=[[1, 2], [3, 4]])
    >>> len(result.communities)
    2

    References
    ----------
    No specific publication is associated with this container; it is a helper
    type for DyNetx's documented analytics API.
    """

    communities: List[Any] = field(default_factory=list)
    membership: Dict[Any, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return the result as a plain dictionary.

        Examples
        --------
        >>> from dynetx.results import CommunityAssignmentResult
        >>> CommunityAssignmentResult(communities=[[0, 1]]).to_dict()
"""
        return asdict(self)


@dataclass
class DiffusionResult:
    """Diffusion simulation outputs.

    Parameters
    ----------
    timeline : list[Any], optional
        Time-ordered simulation trace.
    node_states : dict[Any, Any], optional
        Node status mappings recorded during the simulation.
    metadata : dict[str, Any], optional
        Additional contextual information, such as the model name or
        simulation parameters.

    Returns
    -------
    DiffusionResult
        A serializable result object.

    Examples
    --------
    >>> from dynetx.results import DiffusionResult
    >>> result = DiffusionResult(timeline=[{"t": 0, "infected": 1}])
    >>> result.to_dict()["timeline"][0]["t"]
    0

    References
    ----------
    No specific publication is associated with this container; it is a helper
    type for DyNetx's documented diffusion API.
    """

    timeline: List[Any] = field(default_factory=list)
    node_states: Dict[Any, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return the result as a plain dictionary.

        Examples
        --------
        >>> from dynetx.results import DiffusionResult
        >>> DiffusionResult(timeline=[{"iteration": 0}]).to_dict()
"""
        return asdict(self)
