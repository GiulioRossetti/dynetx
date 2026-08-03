"""Link shuffling temporal reference model.

This generator implements the link-shuffling null model from Gauvin et al.
(2022), preserving edge timelines while rewiring them to different node
pairs.
"""

from __future__ import annotations

import random

from ._shared import add_spans, base_stream_graph, copy_nodes, edge_timelines, new_graph, rewired_pair_list

__all__ = ["generate_link_shuffling_graph"]


def generate_link_shuffling_graph(
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
    """Generate a stream graph by rewiring timelines to fresh links.

    Returns
    -------
    DynGraph
        Stream graph with preserved edge timelines but shuffled endpoints.

    References
    ----------
    Gauvin, L., Panisson, A., & Cattuto, C. (2022). Randomized reference
    models for temporal networks. *SIAM Review*, 64(4), 763-830.
    

    Examples
    --------
    >>> from dynetx.generation.link_shuffling import generate_link_shuffling_graph
    >>> generate_link_shuffling_graph(num_nodes=5, snapshots=2, seed=1)
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

    nodes = list(range(num_nodes))
    pairs = rewired_pair_list(rng, nodes, len(timelines))

    graph = new_graph()
    copy_nodes(graph, nodes)
    for (_, _, spans), (u, v) in zip(timelines, pairs):
        add_spans(graph, u, v, spans)

    graph.graph["generator"] = "link_shuffling"
    graph.graph["generator_kind"] = "stream"
    graph.graph["reference_model"] = "link_shuffling"
    graph.graph["reference_source"] = base.graph.get("reference_base", "erdos_renyi")
    graph.graph["reference_parameters"] = dict(base.graph.get("reference_parameters", {}))
    graph.graph["topologies"] = ["link_shuffling"]
    return graph
