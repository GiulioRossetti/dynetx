"""Compatibility wrapper for temporal reference-model generators."""

from __future__ import annotations

from .activity_driven import generate_activity_driven_graph
from .activity_driven_memory import generate_activity_driven_memory_graph
from .degree_constrained_link_shuffling import generate_degree_constrained_link_shuffling_graph
from .event_shuffling import generate_event_shuffling_graph
from .inter_event_shuffling import generate_inter_event_shuffling_graph
from .link_shuffling import generate_link_shuffling_graph
from .registry import REFERENCE_MODEL_GENERATORS, REFERENCE_SNAPSHOT_MODELS, REFERENCE_STREAM_MODELS, normalize_reference_model_name
from .synthetic import generate_synthetic_graph
from .timeline_shuffling import generate_timeline_shuffling_graph

__all__ = [
    "generate_activity_driven_graph",
    "generate_activity_driven_memory_graph",
    "generate_event_shuffling_graph",
    "generate_timeline_shuffling_graph",
    "generate_link_shuffling_graph",
    "generate_inter_event_shuffling_graph",
    "generate_degree_constrained_link_shuffling_graph",
    "generate_synthetic_graph",
    "REFERENCE_MODEL_GENERATORS",
    "REFERENCE_STREAM_MODELS",
    "REFERENCE_SNAPSHOT_MODELS",
    "normalize_reference_model_name",
]

