"""Inter-event shuffling temporal reference model.

This generator implements the inter-event shuffling null model from Gauvin
et al. (2022), preserving edge lifetimes while reshuffling the gaps between
their events.
"""

from __future__ import annotations

import random

from ._shared import add_spans, base_stream_graph, copy_nodes, edge_timelines, new_graph

__all__ = ["generate_inter_event_shuffling_graph"]


def generate_inter_event_shuffling_graph(
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
    """Generate a stream graph by shuffling inter-event gaps on each link.

    Returns
    -------
    DynGraph
        Stream graph with preserved edge durations and shuffled gaps.

    References
    ----------
    Gauvin, L., Panisson, A., & Cattuto, C. (2022). Randomized reference
    models for temporal networks. *SIAM Review*, 64(4), 763-830.


    Examples
    --------
    >>> from dynetx.generation.inter_event_shuffling import generate_inter_event_shuffling_graph
    >>> generate_inter_event_shuffling_graph(num_nodes=5, snapshots=2, seed=1)
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

    graph = new_graph()
    copy_nodes(graph, range(num_nodes))
    for u, v, spans in timelines:
        if len(spans) <= 1:
            add_spans(graph, u, v, spans)
            continue
        ordered = sorted(spans, key=lambda span: span[0])
        durations = [max(1, int(end) - int(start) + 1) for start, end in ordered]
        gaps = [max(1, int(ordered[index + 1][0]) - int(ordered[index][0])) for index in range(len(ordered) - 1)]
        rng.shuffle(gaps)
        new_starts = [int(ordered[0][0])]
        for gap in gaps:
            new_starts.append(new_starts[-1] + gap)
        for start, duration in zip(new_starts, durations):
            graph.add_interaction(u, v, t=start, e=start + duration)

    graph.graph["generator"] = "inter_event_shuffling"
    graph.graph["generator_kind"] = "stream"
    graph.graph["reference_model"] = "inter_event_shuffling"
    graph.graph["reference_source"] = base.graph.get("reference_base", "erdos_renyi")
    graph.graph["reference_parameters"] = dict(base.graph.get("reference_parameters", {}))
    graph.graph["topologies"] = ["inter_event_shuffling"]
    return graph
