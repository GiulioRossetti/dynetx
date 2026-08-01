"""Interactive dashboard helpers for temporal DyNetx workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import random

from dynetx.readwrite import json_graph
from dynetx.results import CommunityAssignmentResult, DiffusionResult
from dynetx import visualization as vz

__all__ = [
    "TemporalDashboard",
    "build_dashboard",
    "generate_synthetic_graph",
]


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401
        return plt
    except Exception as exc:  # pragma: no cover - backend availability is environment-specific
        raise ImportError("matplotlib is required for dashboard helpers") from exc


def _serialize_result_mapping(results):
    if results is None:
        return None
    if isinstance(results, Mapping):
        serialized = []
        for key, value in results.items():
            if isinstance(key, tuple):
                key = list(key)
            serialized.append({"key": key, "value": value.to_dict() if hasattr(value, "to_dict") else value})
        return serialized
    return results.to_dict() if hasattr(results, "to_dict") else results


def _deserialize_community_results(payload):
    if payload is None:
        return None
    if isinstance(payload, list):
        out = {}
        for item in payload:
            key = item["key"]
            if isinstance(key, list):
                key = tuple(key)
            out[key] = CommunityAssignmentResult(**item["value"])
        return out
    return CommunityAssignmentResult(**payload)


def _deserialize_diffusion_results(payload):
    if payload is None:
        return None
    if isinstance(payload, list):
        out = {}
        for item in payload:
            key = item["key"]
            if isinstance(key, list):
                key = tuple(key)
            out[key] = DiffusionResult(**item["value"])
        return out
    return DiffusionResult(**payload)


def _sorted_repr(values):
    if values is None:
        return None
    return sorted(values, key=lambda value: repr(value))


def _compose_node_filter(nodes, predicate):
    if nodes is None and predicate is None:
        return None

    def _filter(node, attrs):
        if nodes is not None and node not in nodes:
            return False
        if predicate is not None and not predicate(node, attrs):
            return False
        return True

    return _filter


def _compose_edge_filter(edges, predicate):
    if edges is None and predicate is None:
        return None

    def _filter(u, v, attrs):
        if edges is not None and (u, v) not in edges and (v, u) not in edges:
            return False
        if predicate is not None and not predicate(u, v, attrs):
            return False
        return True

    return _filter


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
):
    """Generate a synthetic DyNetx graph for dashboard exploration."""
    from dynetx import DynGraph
    import networkx as nx

    if num_nodes <= 1:
        raise ValueError("num_nodes must be greater than 1")
    if snapshots <= 0:
        raise ValueError("snapshots must be a positive integer")
    if not 0 <= edge_probability <= 1:
        raise ValueError("edge_probability must be between 0 and 1")
    if not 0 <= node_churn <= 1:
        raise ValueError("node_churn must be between 0 and 1")

    rng = random.Random(seed)
    graph = DynGraph()
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
        probs = [
            [p_in if i == j else p_out for j in range(groups)]
            for i in range(groups)
        ]
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
    return graph


class TemporalDashboard:
    """Stateful dashboard for temporal graphs, communities, and diffusion."""

    def __init__(self, graph=None, t=None, communities=None, diffusion=None, layout="spring", seed=42):
        from dynetx import DynGraph

        self.graph = graph if graph is not None else DynGraph()
        self.layout = layout
        self.seed = seed
        self.communities = communities
        self.diffusion = diffusion

        self.selected_snapshot = None
        self.selected_window = None
        if isinstance(t, (tuple, list)) and len(t) == 2:
            self.selected_window = tuple(t)
        else:
            self.selected_snapshot = t

        self.node_filter_nodes = None
        self.node_filter_predicate = None
        self.edge_filter_edges = None
        self.edge_filter_predicate = None
        self.community_filter_ids = None
        self.metadata_filter = {}

    def set_graph(self, graph):
        self.graph = graph
        self.selected_snapshot = None
        self.selected_window = None
        return self

    def load_graph_data(self, data):
        self.set_graph(json_graph.node_link_graph(data))
        return self

    def select_snapshot(self, t):
        self.selected_snapshot = t
        self.selected_window = None
        return self

    def select_window(self, start, end):
        self.selected_snapshot = None
        self.selected_window = (start, end)
        return self

    def set_node_filter(self, nodes=None, predicate=None):
        self.node_filter_nodes = None if nodes is None else set(nodes)
        self.node_filter_predicate = predicate
        return self

    def set_edge_filter(self, edges=None, predicate=None):
        self.edge_filter_edges = None if edges is None else {tuple(edge) for edge in edges}
        self.edge_filter_predicate = predicate
        return self

    def set_community_filter(self, community_ids=None):
        self.community_filter_ids = None if community_ids is None else set(community_ids)
        return self

    def set_metadata_filter(self, **metadata):
        self.metadata_filter = dict(metadata)
        return self

    def clear_filters(self):
        self.node_filter_nodes = None
        self.node_filter_predicate = None
        self.edge_filter_edges = None
        self.edge_filter_predicate = None
        self.community_filter_ids = None
        self.metadata_filter = {}
        return self

    def current_graph(self):
        kwargs = {}
        node_filter = _compose_node_filter(self.node_filter_nodes, self.node_filter_predicate)
        edge_filter = _compose_edge_filter(self.edge_filter_edges, self.edge_filter_predicate)
        if node_filter is not None:
            kwargs["node_filter"] = node_filter
        if edge_filter is not None:
            kwargs["edge_filter"] = edge_filter
        kwargs["include_isolated"] = self.node_filter_nodes is not None or self.node_filter_predicate is not None

        if self.selected_window is not None:
            start, end = self.selected_window
            return self.graph.time_slice(start, end, **kwargs)
        if self.selected_snapshot is not None:
            return self.graph.time_slice(self.selected_snapshot, **kwargs)
        tids = self.graph.temporal_snapshots_ids()
        if tids:
            return self.graph.time_slice(tids[0], tids[-1], **kwargs)
        return self.graph

    def timeline_frames(self, window=1, step=1, include_partial=False):
        tids = self.graph.temporal_snapshots_ids()
        if len(tids) == 0:
            return []
        if window <= 0:
            raise ValueError("window must be a positive integer")
        if step <= 0:
            raise ValueError("step must be a positive integer")
        frames = []
        start = tids[0]
        end = tids[-1]
        cur = start
        while cur <= end:
            last = cur + window - 1
            if last > end and not include_partial:
                break
            frames.append((cur, min(last, end)))
            cur += step
        return frames

    def playback(self, window=1, step=1, include_partial=False):
        """Iterate through selected timeline windows and their current slices."""
        for start, end in self.timeline_frames(window=window, step=step, include_partial=include_partial):
            self.select_window(start, end) if window > 1 else self.select_snapshot(start)
            yield self, self.current_graph()

    def summary_statistics(self):
        tids = self.graph.temporal_snapshots_ids()
        nodes = [self.graph.number_of_nodes(t) for t in tids] if tids else []
        interactions = [self.graph.interactions_per_snapshots(t) for t in tids] if tids else []
        densities = [self._snapshot_density(t) for t in tids]
        return {
            "snapshots": tids,
            "active_nodes": nodes,
            "interactions": interactions,
            "density": densities,
            "total_nodes": self.graph.number_of_nodes(),
            "total_interactions": self.graph.number_of_interactions(),
        }

    def _snapshot_density(self, t):
        try:
            n = self.graph.number_of_nodes(t)
            if n < 2:
                return 0.0
            m = self.graph.number_of_interactions(t=t)
            if m is None:
                return 0.0
            possible = n * (n - 1)
            if not self.graph.is_directed():
                possible /= 2.0
            return 0.0 if possible <= 0 else float(m) / float(possible)
        except Exception:
            return 0.0

    def current_density(self):
        current = self.current_graph()
        try:
            n = current.number_of_nodes()
            if n < 2:
                return 0.0
            m = current.number_of_interactions()
            possible = n * (n - 1)
            if not current.is_directed():
                possible /= 2.0
            return 0.0 if possible <= 0 else float(m) / float(possible)
        except Exception:
            return 0.0

    def _select_mapped_result(self, results):
        if results is None:
            return None
        if not isinstance(results, Mapping):
            return results

        if self.selected_window is not None and self.selected_window in results:
            result = results[self.selected_window]
        elif self.selected_snapshot is not None and (self.selected_snapshot, self.selected_snapshot) in results:
            result = results[(self.selected_snapshot, self.selected_snapshot)]
        elif self.selected_snapshot is not None and self.selected_snapshot in results:
            result = results[self.selected_snapshot]
        else:
            try:
                result = next(iter(results.values()))
            except StopIteration:
                return None
        return result

    def community_summary(self):
        result = self._select_mapped_result(self.communities)
        if result is None:
            return []
        communities = list(result.communities)
        if self.community_filter_ids is not None:
            communities = [community for idx, community in enumerate(communities) if idx in self.community_filter_ids]
        return communities

    def diffusion_summary(self):
        result = self._select_mapped_result(self.diffusion)
        if result is None:
            return []
        return list(result.timeline)

    def render_snapshot(self, t=None, ax=None):
        graph = self.graph if t is None else self.graph.time_slice(t)
        return vz.draw_snapshot(graph, t=None, ax=ax)

    def render_timeline(self, ax=None):
        return vz.plot_temporal_summary(self.graph, ax=ax, kind="both")

    def render_statistics(self, ax=None):
        plt = _require_matplotlib()
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 4))
        stats = self.summary_statistics()
        if not stats["snapshots"]:
            ax.text(0.5, 0.5, "No temporal data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            return ax
        ax.plot(stats["snapshots"], stats["interactions"], marker="o", label="interactions")
        ax.plot(stats["snapshots"], stats["active_nodes"], marker="o", label="active nodes")
        ax.set_title("Temporal statistics")
        ax.set_xlabel("Time")
        ax.set_ylabel("Count")
        ax.legend(frameon=False)
        ax.grid(alpha=0.2)
        return ax

    def render(self, figsize=(14, 10)):
        plt = _require_matplotlib()
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.ravel()

        snapshot_ax = axes[0]
        timeline_ax = axes[1]
        stats_ax = axes[2]
        info_ax = axes[3]

        current_graph = self.current_graph()
        draw_t = self.selected_snapshot if self.selected_snapshot is not None else None
        if self.selected_window is not None:
            draw_t = self.selected_window
        if draw_t is None and current_graph.temporal_snapshots_ids():
            draw_t = current_graph.temporal_snapshots_ids()[0]
        self.render_snapshot(t=draw_t if not isinstance(draw_t, tuple) else None, ax=snapshot_ax)
        snapshot_ax.set_title("Current graph")

        self.render_timeline(ax=timeline_ax)
        timeline_ax.set_title("Timeline view")

        self.render_statistics(ax=stats_ax)

        info_ax.set_title("Session state")
        info_ax.axis("off")
        info_lines = [
            "Selected snapshot: {}".format(self.selected_snapshot),
            "Selected window: {}".format(self.selected_window),
            "Node filter: {}".format(_sorted_repr(self.node_filter_nodes)),
            "Edge filter: {}".format(_sorted_repr(self.edge_filter_edges)),
            "Community filter: {}".format(_sorted_repr(self.community_filter_ids)),
            "Metadata filter: {}".format(self.metadata_filter or None),
        ]
        info_ax.text(0.01, 0.99, "\n".join(info_lines), ha="left", va="top", family="monospace")

        fig.tight_layout()
        return fig, axes

    def export_state(self):
        return {
            "graph": json_graph.node_link_data(self.graph),
            "layout": self.layout,
            "seed": self.seed,
            "selected_snapshot": self.selected_snapshot,
            "selected_window": list(self.selected_window) if self.selected_window is not None else None,
            "filters": {
                "node_filter_nodes": _sorted_repr(self.node_filter_nodes),
                "edge_filter_edges": [list(edge) for edge in _sorted_repr(self.edge_filter_edges)] if self.edge_filter_edges is not None else None,
                "community_filter_ids": _sorted_repr(self.community_filter_ids),
                "metadata_filter": dict(self.metadata_filter),
            },
            "communities": _serialize_result_mapping(self.communities),
            "diffusion": _serialize_result_mapping(self.diffusion),
        }

    @classmethod
    def from_state(cls, state):
        graph = json_graph.node_link_graph(state["graph"])
        dashboard = cls(
            graph,
            t=tuple(state["selected_window"]) if state.get("selected_window") is not None else state.get("selected_snapshot"),
            communities=_deserialize_community_results(state.get("communities")),
            diffusion=_deserialize_diffusion_results(state.get("diffusion")),
            layout=state.get("layout", "spring"),
            seed=state.get("seed", 42),
        )
        filters = state.get("filters", {})
        dashboard.node_filter_nodes = set(filters["node_filter_nodes"]) if filters.get("node_filter_nodes") is not None else None
        dashboard.edge_filter_edges = {tuple(edge) for edge in filters["edge_filter_edges"]} if filters.get("edge_filter_edges") is not None else None
        dashboard.community_filter_ids = set(filters["community_filter_ids"]) if filters.get("community_filter_ids") is not None else None
        dashboard.metadata_filter = dict(filters.get("metadata_filter", {}))
        return dashboard


def build_dashboard(graph=None, t=None, communities=None, diffusion=None, layout="spring", seed=42):
    """Return a :class:`TemporalDashboard` instance for the given graph."""
    return TemporalDashboard(graph, t=t, communities=communities, diffusion=diffusion, layout=layout, seed=seed)
