"""Interactive dashboard helpers for temporal DyNetx workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from dynetx.generation import (
    generate_activity_driven_graph,
    generate_activity_driven_memory_graph,
    generate_degree_constrained_link_shuffling_graph,
    generate_event_shuffling_graph,
    generate_inter_event_shuffling_graph,
    generate_link_shuffling_graph,
    generate_synthetic_graph,
    generate_timeline_shuffling_graph,
)
from dynetx.readwrite import json_graph
from dynetx.results import CommunityAssignmentResult, DiffusionResult
from dynetx import visualization as vz

__all__ = [
    "TemporalDashboard",
    "build_dashboard",
    "generate_activity_driven_graph",
    "generate_activity_driven_memory_graph",
    "generate_event_shuffling_graph",
    "generate_timeline_shuffling_graph",
    "generate_link_shuffling_graph",
    "generate_inter_event_shuffling_graph",
    "generate_degree_constrained_link_shuffling_graph",
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
class TemporalDashboard:
    """
    Stateful dashboard for temporal graphs, communities, and diffusion.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> from dynetx.dashboard import TemporalDashboard
        >>> G = dn.DynGraph()
        >>> dashboard = TemporalDashboard(G)
        >>> dashboard.TemporalDashboard()
    """

    def __init__(self, graph=None, t=None, communities=None, diffusion=None, layout="spring", seed=42):
        """
        Initialize a dashboard session.
        """
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
        """
        Replace the active graph and clear the current selection.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.set_graph(G)
        """
        self.graph = graph
        self.selected_snapshot = None
        self.selected_window = None
        return self

    def load_graph_data(self, data):
        """
        Load a graph from node-link data and set it as active.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.load_graph_data({})
        """
        self.set_graph(json_graph.node_link_graph(data))
        return self

    def select_snapshot(self, t):
        """
        Select a single snapshot for rendering and summary methods.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.select_snapshot(0)
        """
        self.selected_snapshot = t
        self.selected_window = None
        return self

    def select_window(self, start, end):
        """
        Select an inclusive temporal window for rendering.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.select_window(0, 0)
        """
        self.selected_snapshot = None
        self.selected_window = (start, end)
        return self

    def set_node_filter(self, nodes=None, predicate=None):
        """
        Restrict rendered graphs to a subset of nodes.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.set_node_filter([0])
        """
        self.node_filter_nodes = None if nodes is None else set(nodes)
        self.node_filter_predicate = predicate
        return self

    def set_edge_filter(self, edges=None, predicate=None):
        """
        Restrict rendered graphs to a subset of edges.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.set_edge_filter([(0, 1)])
        """
        self.edge_filter_edges = None if edges is None else {tuple(edge) for edge in edges}
        self.edge_filter_predicate = predicate
        return self

    def set_community_filter(self, community_ids=None):
        """
        Restrict community summaries to the requested ids.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.set_community_filter([0])
        """
        self.community_filter_ids = None if community_ids is None else set(community_ids)
        return self

    def set_metadata_filter(self, **metadata):
        """
        Store metadata constraints used by the dashboard state.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.set_metadata_filter(kind="stream")
        """
        self.metadata_filter = dict(metadata)
        return self

    def clear_filters(self):
        """
        Clear node, edge, community, and metadata filters.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.clear_filters()
        """
        self.node_filter_nodes = None
        self.node_filter_predicate = None
        self.edge_filter_edges = None
        self.edge_filter_predicate = None
        self.community_filter_ids = None
        self.metadata_filter = {}
        return self

    def current_graph(self):
        """
        Return the graph slice corresponding to the current selection.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.current_graph()
        """
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
        """
        Return the temporal windows used by playback.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.timeline_frames(window=1)
        """
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
        """
        Iterate through temporal windows and their graph slices.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> list(dashboard.playback(window=1))
        """
        for start, end in self.timeline_frames(window=window, step=step, include_partial=include_partial):
            self.select_window(start, end) if window > 1 else self.select_snapshot(start)
            yield self, self.current_graph()

    def summary_statistics(self):
        """
        Return a compact summary of the loaded temporal graph.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.summary_statistics()
        """
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
        """Return the density of snapshot ``t``."""
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
        """
        Return the density of the currently selected graph slice.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.current_density()
        """
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
        """Select the result object matching the current temporal selection."""
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
        """
        Return the communities associated with the current selection.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.community_summary()
        """
        result = self._select_mapped_result(self.communities)
        if result is None:
            return []
        communities = list(result.communities)
        if self.community_filter_ids is not None:
            communities = [community for idx, community in enumerate(communities) if idx in self.community_filter_ids]
        return communities

    def diffusion_summary(self):
        """
        Return the diffusion timeline associated with the current selection.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.diffusion_summary()
        """
        result = self._select_mapped_result(self.diffusion)
        if result is None:
            return []
        return list(result.timeline)

    def render_snapshot(self, t=None, ax=None):
        """
        Render the current snapshot or slice onto ``ax``.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.render_snapshot(t=0)
        """
        graph = self.graph if t is None else self.graph.time_slice(t)
        return vz.draw_snapshot(graph, t=None, ax=ax)

    def render_timeline(self, ax=None):
        """
        Render the timeline summary plot.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.render_timeline()
        """
        return vz.plot_temporal_summary(self.graph, ax=ax, kind="both")

    def render_statistics(self, ax=None):
        """
        Render a compact plot of interactions and active nodes.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.render_statistics()
        """
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
        """
        Render the dashboard into a Matplotlib figure.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.render()
        """
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
        """
        Serialize the dashboard into a JSON-friendly dictionary.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> dashboard.export_state()
        """
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
        """
        Reconstruct a dashboard from a serialized state dictionary.
        
        Example::
        
        
        
            >>> import dynetx as dn
            >>> from dynetx.dashboard import TemporalDashboard
            >>> G = dn.DynGraph()
            >>> dashboard = TemporalDashboard(G)
            >>> state = dashboard.export_state()
            >>> TemporalDashboard.from_state(state)
        """
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
    """
    Return a configured :class:`TemporalDashboard` instance.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> from dynetx.dashboard import build_dashboard
        >>> G = dn.DynGraph()
        >>> build_dashboard(G)
    """
    return TemporalDashboard(graph, t=t, communities=communities, diffusion=diffusion, layout=layout, seed=seed)
