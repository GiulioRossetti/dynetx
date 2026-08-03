"""Degree-constrained link shuffling temporal reference model.

This generator implements a snapshot-wise degree-preserving randomization in
the spirit of the reference models surveyed by Gauvin et al. (2022).
"""

from __future__ import annotations

import random

import networkx as nx

from ._shared import base_stream_graph, copy_nodes, new_graph

__all__ = ["generate_degree_constrained_link_shuffling_graph"]


def generate_degree_constrained_link_shuffling_graph(
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
    """Generate a snapshot graph by randomizing each snapshot under degree constraints.

    Returns
    -------
    DynGraph
        Snapshot-based dynamic graph with preserved per-snapshot degree
        sequences.

    References
    ----------
    Gauvin, L., Panisson, A., & Cattuto, C. (2022). Randomized reference
    models for temporal networks. *SIAM Review*, 64(4), 763-830.
    

    Examples
    --------
    >>> from dynetx.generation.degree_constrained_link_shuffling import generate_degree_constrained_link_shuffling_graph
    >>> generate_degree_constrained_link_shuffling_graph(num_nodes=5, snapshots=2, seed=1)
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

    graph = new_graph()
    nodes = list(range(num_nodes))
    copy_nodes(graph, nodes)

    for t in base.temporal_snapshots_ids():
        snapshot = nx.Graph()
        snapshot.add_nodes_from(nodes)
        snapshot.add_edges_from((u, v) for u, v, _ in base.interactions_iter(t=t))
        degree_sequence = [snapshot.degree(node) for node in nodes]
        if sum(degree_sequence) == 0:
            continue
        if sum(degree_sequence) % 2 == 1:
            max_index = max(range(len(degree_sequence)), key=degree_sequence.__getitem__)
            degree_sequence[max_index] = max(0, degree_sequence[max_index] - 1)
        try:
            randomized = nx.random_degree_sequence_graph(degree_sequence, seed=rng.randint(0, 2**31 - 1))
        except Exception:
            randomized = nx.havel_hakimi_graph(degree_sequence)
        for u, v in randomized.edges():
            graph.add_interaction(u, v, t=t)

    graph.graph["generator"] = "degree_constrained_link_shuffling"
    graph.graph["generator_kind"] = "snapshot"
    graph.graph["reference_model"] = "degree_constrained_link_shuffling"
    graph.graph["reference_source"] = base.graph.get("reference_base", "erdos_renyi")
    graph.graph["reference_parameters"] = dict(base.graph.get("reference_parameters", {}))
    graph.graph["topologies"] = ["degree_constrained_link_shuffling"]
    return graph
