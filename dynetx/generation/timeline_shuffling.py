"""Timeline shuffling temporal reference model.

This generator implements the timeline-shuffling null model from Gauvin et
al. (2022), preserving each edge's temporal profile while reassigning it to a
different node pair.
"""

from __future__ import annotations

import random

from ._shared import add_spans, base_stream_graph, copy_nodes, edge_timelines, new_graph

__all__ = ["generate_timeline_shuffling_graph"]


def generate_timeline_shuffling_graph(
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
    """Generate a stream graph by permuting full interaction timelines.

    Returns
    -------
    DynGraph
        Stream graph with edge timelines reassigned to new node pairs.

    References
    ----------
    Gauvin, L., Panisson, A., & Cattuto, C. (2022). Randomized reference
    models for temporal networks. *SIAM Review*, 64(4), 763-830.
    

    Examples
    --------
    >>> from dynetx.generation.timeline_shuffling import generate_timeline_shuffling_graph
    >>> generate_timeline_shuffling_graph(num_nodes=5, snapshots=2, seed=1)
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
    timelines = edge_timelines(base)
    if not timelines:
        return base

    pairs = [(u, v) for u, v, _ in timelines]
    shuffled_pairs = list(pairs)
    rng.shuffle(shuffled_pairs)

    graph = new_graph()
    copy_nodes(graph, range(num_nodes))
    for (_, _, spans), (u, v) in zip(timelines, shuffled_pairs):
        add_spans(graph, u, v, spans)

    graph.graph["generator"] = "timeline_shuffling"
    graph.graph["generator_kind"] = "stream"
    graph.graph["reference_model"] = "timeline_shuffling"
    graph.graph["reference_source"] = base.graph.get("reference_base", "erdos_renyi")
    graph.graph["reference_parameters"] = dict(base.graph.get("reference_parameters", {}))
    graph.graph["topologies"] = ["timeline_shuffling"]
    return graph
