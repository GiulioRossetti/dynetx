"""Validation and normalization helpers for temporal DyNetx data."""

from __future__ import annotations

from collections.abc import Mapping

__all__ = [
    "normalize_time_range",
    "normalize_interaction_interval",
    "inclusive_end_to_exclusive",
    "exclusive_end_to_inclusive",
    "ensure_mapping",
]


def normalize_time_range(t_from, t_to=None):
    """Return a validated inclusive time range.

    Parameters
    ----------
    t_from : int or 2-sequence
        Lower bound, or a ``(start, end)`` pair when ``t_to`` is omitted.
    t_to : int, optional
        Upper bound. If omitted and ``t_from`` is a pair, the pair is used.
    """
    if t_to is None and isinstance(t_from, (list, tuple)) and len(t_from) == 2:
        t_from, t_to = t_from
    elif t_to is None:
        t_to = t_from

    if t_from is None or t_to is None:
        raise ValueError("Temporal range bounds must be specified")
    if t_from > t_to:
        raise ValueError("Invalid range: t_to must be greater than or equal to t_from")
    return t_from, t_to


def normalize_interaction_interval(t, e=None):
    """Return a validated inclusive interaction interval."""
    if isinstance(t, (list, tuple)) and e is None:
        if len(t) != 2:
            raise ValueError("Interaction interval tuples must contain exactly two bounds")
        start, end = t
    else:
        start = t
        end = t if e is None else e - 1

    if start is None or end is None:
        raise ValueError("Interaction interval bounds must be specified")
    if start > end:
        raise ValueError("Invalid interval: end must be greater than or equal to start")
    return start, end


def inclusive_end_to_exclusive(end):
    """Convert an inclusive end bound to the exclusive end convention used by add_interaction."""
    if end is None:
        return None
    return end + 1


def exclusive_end_to_inclusive(end):
    """Convert an exclusive end bound to an inclusive end bound."""
    if end is None:
        return None
    return end - 1


def ensure_mapping(value, name="value"):
    """Return a shallow copy of a mapping or raise a helpful error."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("{} must be a mapping".format(name))
    return dict(value)
