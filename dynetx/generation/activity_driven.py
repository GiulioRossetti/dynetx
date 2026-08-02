"""Activity-driven synthetic temporal graph generator."""

from __future__ import annotations

from ._shared import copy_nodes, new_graph, sample_power_law, stream_contact_end

__all__ = ["generate_activity_driven_graph"]


def generate_activity_driven_graph(
    num_nodes=12,
    snapshots=3,
    seed=42,
    dynamic_nodes=False,
    node_churn=0.25,
    activity_m=2,
    activity_min=0.18,
    activity_max=0.65,
    activity_exponent=2.2,
    contact_duration=1,
):
    """Generate a stream graph with activity-driven temporal contacts."""
    import random

    if num_nodes <= 1:
        raise ValueError("num_nodes must be greater than 1")
    if snapshots <= 0:
        raise ValueError("snapshots must be a positive integer")
    if not 0 <= node_churn <= 1:
        raise ValueError("node_churn must be between 0 and 1")

    rng = random.Random(seed)
    graph = new_graph()
    nodes = list(range(num_nodes))
    copy_nodes(graph, nodes)

    activity_min = max(1e-3, min(0.99, float(activity_min)))
    activity_max = max(activity_min, min(0.99, float(activity_max)))
    activity_m = max(1, int(activity_m))
    activity_rates = {
        node: min(0.99, sample_power_law(rng, activity_min, activity_max, activity_exponent))
        for node in nodes
    }

    def _active_nodes():
        if not dynamic_nodes:
            return list(nodes)
        active = [node for node in nodes if rng.random() >= node_churn]
        if len(active) < 2:
            active = rng.sample(nodes, k=min(2, len(nodes)))
        return sorted(active)

    max_snapshot = snapshots
    for t in range(snapshots):
        present = _active_nodes()
        active = [node for node in present if rng.random() < activity_rates[node]]
        if not active and present:
            active = [rng.choice(present)]
        seen_pairs = set()
        for source in active:
            candidates = [node for node in present if node != source]
            if not candidates:
                continue
            count = min(activity_m, len(candidates))
            partners = rng.sample(candidates, count) if count < len(candidates) else candidates
            for target in partners:
                pair = tuple(sorted((source, target)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                graph.add_interaction(pair[0], pair[1], t=t, e=stream_contact_end(t, contact_duration, max_snapshot))

    graph.graph["generator"] = "activity_driven"
    graph.graph["activity_parameters"] = {
        "m": activity_m,
        "activity_min": activity_min,
        "activity_max": activity_max,
        "activity_exponent": activity_exponent,
        "contact_duration": int(round(contact_duration)),
    }
    graph.graph["dynamic_nodes"] = bool(dynamic_nodes)
    graph.graph["topologies"] = ["activity_driven"]
    graph.graph["generator_kind"] = "stream"
    return graph

