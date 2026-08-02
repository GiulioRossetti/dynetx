"""Temporal analytics helpers for DyNetx.

These functions provide higher-level metrics built on top of the dynamic
graph primitives and the time-respecting path machinery.
"""

from itertools import combinations
from collections import defaultdict

import networkx as nx

from .paths import all_time_respecting_paths, annotate_paths, path_length

__all__ = [
    "temporal_degree_centrality",
    "temporal_clustering",
    "temporal_transitivity",
    "temporal_connected_components",
    "temporal_earliest_arrival_closeness",
    "temporal_betweenness_centrality",
    "path_support",
]


def _snapshot_graph(G, t):
    return G.to_networkx_graph(t=t)


def temporal_degree_centrality(G, normalized=True):
    """Return temporal degree centrality per node.

    The value is the sum of snapshot degrees over all snapshots, optionally
    normalized by the maximum possible degree mass.
    """
    tids = G.temporal_snapshots_ids()
    nodes = G.nodes()
    scores = {n: 0 for n in nodes}
    for t in tids:
        degs = G.degree(t=t)
        for n in nodes:
            scores[n] += degs.get(n, 0)

    if normalized:
        denom = max(1, len(tids) * (len(nodes) - 1))
        scores = {n: v / denom for n, v in scores.items()}
    return scores


def temporal_clustering(G, t=None):
    """Return temporal clustering coefficients.

    If t is provided, compute clustering on that snapshot. Otherwise average
    clustering over all available snapshots.
    """
    if t is not None:
        sg = _snapshot_graph(G, t)
        return nx.clustering(sg.to_undirected() if sg.is_directed() else sg)

    tids = G.temporal_snapshots_ids()
    if len(tids) == 0:
        return {}

    acc = defaultdict(float)
    for tid in tids:
        vals = temporal_clustering(G, t=tid)
        for n in G.nodes():
            acc[n] += vals.get(n, 0.0)
    return {n: acc[n] / len(tids) for n in G.nodes()}


def temporal_transitivity(G, t=None):
    """Return temporal transitivity.

    If t is provided, compute transitivity on that snapshot. Otherwise average
    across snapshots.
    """
    if t is not None:
        sg = _snapshot_graph(G, t)
        return nx.transitivity(sg.to_undirected() if sg.is_directed() else sg)

    tids = G.temporal_snapshots_ids()
    if len(tids) == 0:
        return 0.0
    return sum(temporal_transitivity(G, t=tid) for tid in tids) / len(tids)


def temporal_connected_components(G, t=None):
    """Return connected components over time.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Temporal graph to analyze.
    t : snapshot id, optional
        If provided, return the connected components of that snapshot. If
        omitted, return a mapping from snapshot id to component list.

    Returns
    -------
    list[set] or dict
        Connected components for the selected snapshot or for all snapshots.
    """
    if t is not None:
        sg = _snapshot_graph(G, t)
        base = sg.to_undirected() if sg.is_directed() else sg
        return [set(c) for c in nx.connected_components(base)]

    return {tid: temporal_connected_components(G, t=tid) for tid in G.temporal_snapshots_ids()}


def temporal_earliest_arrival_closeness(G, source, start=None, end=None):
    """Return a simple earliest-arrival closeness score for source."""
    paths = all_time_respecting_paths(G, start=start, end=end)
    arrivals = {}
    for (u, v), plist in paths.items():
        if u != source:
            continue
        best = min(plist, key=lambda p: p[-1][-1])
        arrivals[v] = best[-1][-1]

    if len(arrivals) == 0:
        return 0.0

    base = start if start is not None else (G.temporal_snapshots_ids()[0] if G.temporal_snapshots_ids() else 0)
    return len(arrivals) / sum((arr - base + 1) for arr in arrivals.values())


def temporal_betweenness_centrality(G, normalized=True, start=None, end=None):
    """Approximate temporal betweenness from shortest time-respecting paths."""
    nodes = G.nodes()
    scores = {n: 0.0 for n in nodes}
    pairs = list(combinations(nodes, 2))
    for s, t in pairs:
        paths = all_time_respecting_paths(G, start=start, end=end).get((s, t), [])
        if not paths:
            continue
        annotated = annotate_paths(paths)
        shortest = annotated["shortest"] or []
        if len(shortest) == 0:
            continue
        contrib = 1.0 / len(shortest)
        for path in shortest:
            seq = [path[0][0]] + [edge[1] for edge in path]
            for n in seq[1:-1]:
                scores[n] += contrib

    if normalized and len(nodes) > 2:
        scale = 1 / ((len(nodes) - 1) * (len(nodes) - 2) / 2)
        scores = {n: v * scale for n, v in scores.items()}
    return scores


def path_support(path):
    """Return the number of distinct snapshots used by a temporal path."""
    return len({step[-1] for step in path})
