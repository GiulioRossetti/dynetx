"""Generator registry for synthetic dynamic graph models."""

from __future__ import annotations

from .activity_driven import generate_activity_driven_graph
from .activity_driven_memory import generate_activity_driven_memory_graph
from .degree_constrained_link_shuffling import generate_degree_constrained_link_shuffling_graph
from .event_shuffling import generate_event_shuffling_graph
from .inter_event_shuffling import generate_inter_event_shuffling_graph
from .link_shuffling import generate_link_shuffling_graph
from .timeline_shuffling import generate_timeline_shuffling_graph
from ._shared import normalize_name

REFERENCE_MODEL_GENERATORS = {
    "event_shuffling": generate_event_shuffling_graph,
    "timeline_shuffling": generate_timeline_shuffling_graph,
    "link_shuffling": generate_link_shuffling_graph,
    "inter_event_shuffling": generate_inter_event_shuffling_graph,
    "degree_constrained_link_shuffling": generate_degree_constrained_link_shuffling_graph,
}

REFERENCE_STREAM_MODELS = {
    "event_shuffling",
    "timeline_shuffling",
    "link_shuffling",
    "inter_event_shuffling",
}

REFERENCE_SNAPSHOT_MODELS = {
    "degree_constrained_link_shuffling",
}


def normalize_reference_model_name(name):
    """Resolve user-facing aliases to a canonical reference-model name.

    Parameters
    ----------
    name : object
        Model name or alias supplied by the caller.

    Returns
    -------
    str
        Canonical generator identifier used by the registry.
    

    Examples
    --------
    >>> from dynetx.generation.registry import normalize_reference_model_name
    >>> normalize_reference_model_name("timeline shuffling")
"""
    normalized = normalize_name(name)
    aliases = {
        "event": "event_shuffling",
        "event_shuffling": "event_shuffling",
        "event_shuffling_graph": "event_shuffling",
        "timeline": "timeline_shuffling",
        "timeline_shuffling": "timeline_shuffling",
        "timeline_shuffling_graph": "timeline_shuffling",
        "link": "link_shuffling",
        "link_shuffling": "link_shuffling",
        "link_shuffling_graph": "link_shuffling",
        "inter_event": "inter_event_shuffling",
        "inter_event_shuffling": "inter_event_shuffling",
        "inter_event_shuffling_graph": "inter_event_shuffling",
        "degree_constrained_link": "degree_constrained_link_shuffling",
        "degree_constrained_link_shuffling": "degree_constrained_link_shuffling",
        "degree_constrained_link_shuffling_graph": "degree_constrained_link_shuffling",
    }
    return aliases.get(normalized, normalized)
