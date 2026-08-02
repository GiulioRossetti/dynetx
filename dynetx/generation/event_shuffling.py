"""Event shuffling temporal reference model."""

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
    """Generate a stream graph by randomly shuffling event timestamps."""
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

