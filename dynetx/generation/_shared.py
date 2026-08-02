"""Shared helpers for synthetic dynamic graph generators."""

from __future__ import annotations

from collections import defaultdict
import random


def new_graph():
    from dynetx import DynGraph

    return DynGraph()


def normalize_name(name):
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def sample_power_law(rng, minimum, maximum, exponent):
    minimum = float(minimum)
    maximum = float(maximum)
    exponent = float(exponent)
    if minimum <= 0:
        minimum = 1e-3
    if maximum < minimum:
        maximum = minimum
    if maximum == minimum:
        return minimum
    if abs(exponent - 1.0) < 1e-12:
        return minimum * ((maximum / minimum) ** rng.random())
    power = 1.0 - exponent
    low = minimum ** power
    high = maximum ** power
    return (low + (high - low) * rng.random()) ** (1.0 / power)


def stream_contact_end(start, duration, max_snapshot):
    duration = max(1, int(round(duration)))
    return min(start + duration, max_snapshot)


def active_nodes(rng, nodes, dynamic_nodes, node_churn):
    if not dynamic_nodes:
        return list(nodes)
    active = [node for node in nodes if rng.random() >= node_churn]
    if len(active) < 2:
        active = rng.sample(nodes, k=min(2, len(nodes)))
    return sorted(active)


def copy_nodes(graph, nodes):
    for node in nodes:
        graph.add_node(node)


def base_stream_graph(
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
    if num_nodes <= 1:
        raise ValueError("num_nodes must be greater than 1")
    if snapshots <= 0:
        raise ValueError("snapshots must be a positive integer")
    if not 0 <= node_churn <= 1:
        raise ValueError("node_churn must be between 0 and 1")
    if not 0 <= edge_probability <= 1:
        raise ValueError("edge_probability must be between 0 and 1")

    rng = random.Random(seed)
    graph = new_graph()
    nodes = list(range(num_nodes))
    copy_nodes(graph, nodes)

    activity_min = max(1e-3, min(0.99, float(activity_min)))
    activity_max = max(activity_min, min(0.99, float(activity_max)))
    contact_duration = max(1, int(round(contact_duration)))
    activity_rates = {
        node: min(0.99, sample_power_law(rng, activity_min, activity_max, activity_exponent))
        for node in nodes
    }

    for t in range(snapshots):
        present = active_nodes(rng, nodes, dynamic_nodes, node_churn)
        active = [node for node in present if rng.random() < activity_rates[node]]
        if not active and len(present) >= 2:
            active = [rng.choice(present)]

        seen_pairs = set()
        for source in active:
            candidates = [node for node in present if node != source]
            if not candidates:
                continue
            for target in candidates:
                if rng.random() > edge_probability:
                    continue
                pair = tuple(sorted((source, target)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                graph.add_interaction(pair[0], pair[1], t=t, e=stream_contact_end(t, contact_duration, snapshots))

        if not seen_pairs and len(present) >= 2:
            graph.add_interaction(present[0], present[1], t=t, e=stream_contact_end(t, contact_duration, snapshots))

    graph.graph["reference_base"] = "erdos_renyi"
    graph.graph["reference_parameters"] = {
        "num_nodes": num_nodes,
        "snapshots": snapshots,
        "edge_probability": edge_probability,
        "dynamic_nodes": bool(dynamic_nodes),
        "node_churn": float(node_churn),
        "contact_duration": contact_duration,
    }
    return graph


def edge_timelines(graph):
    timelines = []
    for u, v, attrs in graph.interactions_iter():
        spans = [tuple(span) for span in attrs.get("t", [])]
        if spans:
            timelines.append((u, v, spans))
    return timelines


def event_rows(graph):
    events = []
    for u, v, attrs in graph.interactions_iter():
        for start, end in attrs.get("t", []):
            events.append((u, v, int(start), max(1, int(end) - int(start) + 1)))
    return events


def add_spans(graph, u, v, spans):
    for start, end in spans:
        graph.add_interaction(u, v, t=int(start), e=int(end) + 1)


def rewired_pair_list(rng, nodes, count):
    pairs = [(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i + 1, len(nodes))]
    if not pairs:
        return []
    rng.shuffle(pairs)
    if count <= len(pairs):
        return pairs[:count]
    result = list(pairs)
    while len(result) < count:
        result.append(rng.choice(pairs))
    return result

