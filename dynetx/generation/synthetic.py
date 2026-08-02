"""Synthetic generator dispatcher."""

from __future__ import annotations

import random

import networkx as nx

from .activity_driven import generate_activity_driven_graph
from .activity_driven_memory import generate_activity_driven_memory_graph
from .registry import REFERENCE_MODEL_GENERATORS, REFERENCE_STREAM_MODELS, normalize_reference_model_name

__all__ = ["generate_synthetic_graph"]


def generate_synthetic_graph(
    kind="stream",
    num_nodes=12,
    snapshots=3,
    edge_probability=0.2,
    seed=42,
    topologies=None,
    dynamic_nodes=False,
    node_churn=0.25,
    ba_m=None,
    ws_k=None,
    ws_beta=0.2,
    sbm_groups=None,
    sbm_p_in=None,
    sbm_p_out=None,
    activity_m=2,
    activity_min=0.18,
    activity_max=0.65,
    activity_exponent=2.2,
    contact_duration=1,
    memory_alpha=1.0,
):
    """Generate a synthetic DyNetx graph for dashboard exploration."""
    from dynetx import DynGraph

    if num_nodes <= 1:
        raise ValueError("num_nodes must be greater than 1")
    if snapshots <= 0:
        raise ValueError("snapshots must be a positive integer")
    if not 0 <= edge_probability <= 1:
        raise ValueError("edge_probability must be between 0 and 1")
    if not 0 <= node_churn <= 1:
        raise ValueError("node_churn must be between 0 and 1")

    rng = random.Random(seed)
    nodes = list(range(num_nodes))

    if topologies is None:
        topology_order = [kind]
    elif isinstance(topologies, str):
        topology_order = [topologies]
    else:
        topology_order = [str(topology) for topology in topologies if topology]

    topology_order = [topology.lower() for topology in topology_order if topology]
    if not topology_order:
        topology_order = [kind.lower()]
    if topology_order == ["dynamic"]:
        topology_order = ["dynamic_er"]
    if topology_order == ["complete"]:
        topology_order = ["complete_graph"]
    activity_topologies = {"activity_driven", "activity-driven", "perra_2012", "perra2012"}
    memory_topologies = {"activity_driven_memory", "activity-driven-memory", "karsai_2014", "karsai2014", "memory_reinforced"}

    if len(topology_order) == 1:
        topology = topology_order[0]
        if topology in activity_topologies:
            graph = generate_activity_driven_graph(
                num_nodes=num_nodes,
                snapshots=snapshots,
                seed=seed,
                dynamic_nodes=dynamic_nodes,
                node_churn=node_churn,
                activity_m=activity_m,
                activity_min=activity_min,
                activity_max=activity_max,
                activity_exponent=activity_exponent,
                contact_duration=contact_duration,
            )
            graph.graph["topologies"] = topology_order
            return graph
        if topology in memory_topologies:
            graph = generate_activity_driven_memory_graph(
                num_nodes=num_nodes,
                snapshots=snapshots,
                seed=seed,
                dynamic_nodes=dynamic_nodes,
                node_churn=node_churn,
                activity_m=activity_m,
                activity_min=activity_min,
                activity_max=activity_max,
                activity_exponent=activity_exponent,
                contact_duration=contact_duration,
                memory_alpha=memory_alpha,
            )
            graph.graph["topologies"] = topology_order
            return graph
        reference_topology = normalize_reference_model_name(topology)
        if reference_topology in REFERENCE_MODEL_GENERATORS:
            graph = REFERENCE_MODEL_GENERATORS[reference_topology](
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
            graph.graph["topologies"] = topology_order
            graph.graph["generator_kind"] = graph.graph.get(
                "generator_kind",
                "stream" if reference_topology in REFERENCE_STREAM_MODELS else "snapshot",
            )
            return graph

    graph = DynGraph()

    if topology_order == ["snapshot"]:
        t_values = [0]
    else:
        t_values = list(range(snapshots))

    def _active_nodes():
        if not dynamic_nodes:
            return list(nodes)
        active = [node for node in nodes if rng.random() >= node_churn]
        if len(active) < 2:
            active = rng.sample(nodes, k=min(2, len(nodes)))
        return sorted(active)

    def _add_er_edges(current_nodes, t):
        for idx, src in enumerate(current_nodes):
            for dst in current_nodes[idx + 1:]:
                if rng.random() <= edge_probability:
                    graph.add_interaction(src, dst, t=t)

    def _add_ba_edges(current_nodes, t):
        if len(current_nodes) < 2:
            return
        if len(current_nodes) == 2:
            graph.add_interaction(current_nodes[0], current_nodes[1], t=t)
            return
        if ba_m is None:
            m = max(1, min(len(current_nodes) - 1, int(round(edge_probability * max(1, len(current_nodes) - 1)))))
        else:
            m = max(1, min(len(current_nodes) - 1, int(ba_m)))
        ba_graph = nx.barabasi_albert_graph(len(current_nodes), m, seed=rng.randint(0, 2**31 - 1))
        mapping = {idx: node for idx, node in enumerate(current_nodes)}
        for src, dst in ba_graph.edges():
            graph.add_interaction(mapping[src], mapping[dst], t=t)

    def _add_ws_edges(current_nodes, t):
        if len(current_nodes) < 2:
            return
        if len(current_nodes) == 2:
            graph.add_interaction(current_nodes[0], current_nodes[1], t=t)
            return
        k = ws_k
        if k is None:
            k = max(2, int(round(edge_probability * max(2, len(current_nodes) - 1))))
        k = max(2, min(len(current_nodes) - (len(current_nodes) % 2 == 0 and 2 or 1), int(k)))
        if k % 2 != 0:
            k = max(2, k - 1)
        if k >= len(current_nodes):
            k = len(current_nodes) - 1 if len(current_nodes) % 2 == 0 else len(current_nodes) - 2
        k = max(2, k)
        beta = min(1.0, max(0.0, float(ws_beta)))
        ws_graph = nx.watts_strogatz_graph(len(current_nodes), k, beta, seed=rng.randint(0, 2**31 - 1))
        mapping = {idx: node for idx, node in enumerate(current_nodes)}
        for src, dst in ws_graph.edges():
            graph.add_interaction(mapping[src], mapping[dst], t=t)

    def _add_complete_edges(current_nodes, t):
        for idx, src in enumerate(current_nodes):
            for dst in current_nodes[idx + 1:]:
                graph.add_interaction(src, dst, t=t)

    def _add_sbm_edges(current_nodes, t):
        if len(current_nodes) < 2:
            return
        if sbm_groups is None:
            groups = min(4, max(2, min(len(current_nodes), int(round(max(2, len(current_nodes) / 4))))))
        else:
            groups = min(len(current_nodes), max(2, int(sbm_groups)))
        block_sizes = [len(current_nodes) // groups] * groups
        for index in range(len(current_nodes) % groups):
            block_sizes[index] += 1
        p_in = min(0.95, max(0.25, sbm_p_in if sbm_p_in is not None else edge_probability * 1.5))
        p_out = max(0.01, min(p_in / 5, sbm_p_out if sbm_p_out is not None else edge_probability * 0.25))
        probs = [[p_in if i == j else p_out for j in range(groups)] for i in range(groups)]
        sbm_graph = nx.stochastic_block_model(block_sizes, probs, seed=rng.randint(0, 2**31 - 1))
        mapping = {idx: node for idx, node in enumerate(current_nodes)}
        for src, dst in sbm_graph.edges():
            graph.add_interaction(mapping[src], mapping[dst], t=t)

    topology_handlers = {
        "stream": _add_er_edges,
        "snapshot": _add_er_edges,
        "dynamic_er": _add_er_edges,
        "er": _add_er_edges,
        "erdos_renyi": _add_er_edges,
        "dynamic_ba": _add_ba_edges,
        "ba": _add_ba_edges,
        "barabasi_albert": _add_ba_edges,
        "dynamic_ws": _add_ws_edges,
        "ws": _add_ws_edges,
        "watts_strogatz": _add_ws_edges,
        "dynamic_sbm": _add_sbm_edges,
        "sbm": _add_sbm_edges,
        "stochastic_block_model": _add_sbm_edges,
        "complete_graph": _add_complete_edges,
        "complete": _add_complete_edges,
    }

    for t in t_values:
        current_nodes = _active_nodes()
        topology = topology_order[t % len(topology_order)]
        handler = topology_handlers.get(topology, _add_er_edges)
        before_edges = graph.number_of_interactions()
        handler(current_nodes, t)
        if graph.number_of_interactions() == before_edges and len(current_nodes) >= 2:
            graph.add_interaction(current_nodes[0], current_nodes[1], t=t)

    if graph.number_of_interactions() == 0:
        fallback_nodes = nodes[:2]
        for t in t_values:
            graph.add_interaction(fallback_nodes[0], fallback_nodes[1], t=t)

    graph.graph["topologies"] = topology_order
    graph.graph["dynamic_nodes"] = bool(dynamic_nodes)
    graph.graph["generator_kind"] = "stream" if kind in {"stream", "dynamic"} or any(topology in activity_topologies | memory_topologies for topology in topology_order) else "snapshot"
    return graph
