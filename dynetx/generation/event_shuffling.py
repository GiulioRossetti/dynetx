"""Event shuffling temporal reference model.

This generator implements the event-shuffling null model discussed by
Gauvin et al. (2022), preserving link identities while randomizing the event
times assigned to them.
"""

from __future__ import annotations

import random

from ._shared import base_stream_graph, copy_nodes, event_rows, new_graph

__all__ = ["generate_event_shuffling_graph"]


def generate_event_shuffling_graph(
    num_nodes=12,
    snapshots=3,
    seed=42,
    edge_probability=0.2,
    dynamic_nodes=False,
    node_churn=0.25,
    contact_duration=1,
    activity_min=0.18,
    activity_max=0.65,
    activity_exponent=2.2,
):
    """Generate a stream graph by randomly shuffling event timestamps.

    Parameters
    ----------
    num_nodes : int, optional
        Number of nodes in the generated graph.
    snapshots : int, optional
        Number of temporal snapshots.
    seed : int, optional
        Random seed used for reproducibility.
    edge_probability : float, optional
        Density parameter used when building the reference stream.
    dynamic_nodes : bool, optional
        If ``True``, apply node churn across snapshots.
    node_churn : float, optional
        Probability that a node is absent from a snapshot when churn is
        enabled.
    contact_duration : int, optional
        Duration assigned to each interaction.
    activity_min : float, optional
        Lower bound of the activity-rate distribution.
    activity_max : float, optional
        Upper bound of the activity-rate distribution.
    activity_exponent : float, optional
        Exponent of the bounded power-law activity distribution.

    Returns
    -------
    DynGraph
        Stream graph with shuffled event times.

    References
    ----------
    Gauvin, L., Panisson, A., & Cattuto, C. (2022). Randomized reference
    models for temporal networks. *SIAM Review*, 64(4), 763-830.


    Examples
    --------
    >>> from dynetx.generation.event_shuffling import generate_event_shuffling_graph
    >>> generate_event_shuffling_graph(num_nodes=5, snapshots=2, seed=1)
"""
    rng = random.Random(seed)
    base = base_stream_graph(
        num_nodes=num_nodes,
        snapshots=snapshots,
        seed=seed,
        edge_probability=edge_probability,
        dynamic_nodes=dynamic_nodes,
        node_churn=node_churn,
        contact_duration=contact_duration,
        activity_min=activity_min,
        activity_max=activity_max,
        activity_exponent=activity_exponent,
    )
    events = event_rows(base)
    if not events:
        return base

    shuffled_starts = [event[2] for event in events]
    rng.shuffle(shuffled_starts)

    graph = new_graph()
    copy_nodes(graph, range(num_nodes))
    grouped = {}
    for (u, v, _start, duration), new_start in zip(events, shuffled_starts):
        grouped.setdefault((u, v), []).append((new_start, new_start + duration))
    for (u, v), spans in grouped.items():
        for start, end in sorted(spans, key=lambda span: span[0]):
            graph.add_interaction(u, v, t=start, e=end)

    graph.graph["generator"] = "event_shuffling"
    graph.graph["generator_kind"] = "stream"
    graph.graph["reference_model"] = "event_shuffling"
    graph.graph["reference_source"] = base.graph.get("reference_base", "erdos_renyi")
    graph.graph["reference_parameters"] = dict(base.graph.get("reference_parameters", {}))
    graph.graph["topologies"] = ["event_shuffling"]
    return graph
