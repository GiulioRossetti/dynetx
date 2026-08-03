"""Community detection helpers backed by CDlib.

DyNetx intentionally delegates the actual algorithms to CDlib and focuses on
temporal slicing, graph conversion, and result normalization.
"""

from __future__ import annotations

from collections import OrderedDict

from dynetx.results import CommunityAssignmentResult
from dynetx.utils.validation import normalize_time_range

__all__ = [
    "community_detection",
    "community_detection_over_time",
]


def _require_cdlib():
    try:
        import cdlib.algorithms as cdlib_algorithms
        return cdlib_algorithms
    except Exception as exc:
        raise ImportError("cdlib is required for community detection helpers") from exc


def _resolve_algorithm(algorithm):
    cdlib_algorithms = _require_cdlib()
    if callable(algorithm):
        return algorithm
    if isinstance(algorithm, str):
        try:
            resolved = getattr(cdlib_algorithms, algorithm)
        except AttributeError as exc:
            raise ValueError("Unknown CDlib algorithm: {}".format(algorithm)) from exc
        if not callable(resolved):
            raise ValueError("CDlib algorithm '{}' is not callable".format(algorithm))
        return resolved
    raise TypeError("algorithm must be a callable or a CDlib algorithm name")


def _snapshot_graph(G, t=None, as_undirected=True):
    nxg = G.to_networkx_graph(t=t)
    if as_undirected and nxg.is_directed():
        nxg = nxg.to_undirected()
    return nxg


def _normalize_communities_result(result, algorithm_name, graph_kind, window=None, snapshot=None):
    communities = [list(c) for c in result.communities]
    membership = {node: list(comms) for node, comms in result.to_node_community_map().items()}
    metadata = {
        "backend": "cdlib",
        "algorithm": getattr(result, "method_name", algorithm_name),
        "method_parameters": getattr(result, "method_parameters", {}),
        "graph_kind": graph_kind,
        "window": window,
        "snapshot": snapshot,
        "node_coverage": getattr(result, "node_coverage", None),
        "overlap": getattr(result, "overlap", None),
    }
    return CommunityAssignmentResult(
        communities=communities,
        membership=membership,
        metadata=metadata,
    )


def community_detection(G, algorithm="louvain", t=None, as_undirected=True, **kwargs):
    """Run a CDlib community detection algorithm on a DyNetx graph.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
    algorithm : str or callable
        CDlib algorithm name or a callable returning a CDlib NodeClustering.
    t : int or 2-sequence, optional
        Snapshot id or inclusive time range. If omitted, the aggregate graph is
        used.
    as_undirected : bool, optional
        Convert directed graphs to undirected graphs before calling CDlib.
    kwargs : dict
        Additional keyword arguments passed through to the CDlib algorithm.

    Examples
    --------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.community import community_detection
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> community_detection(G, t=0)
"""
    if t is None:
        nxg = _snapshot_graph(G, as_undirected=as_undirected)
        graph_kind = "aggregate"
        window = None
        snapshot = None
    elif isinstance(t, (tuple, list)) and len(t) == 2:
        t_from, t_to = normalize_time_range(t)
        nxg = _snapshot_graph(G.time_slice(t_from, t_to), as_undirected=as_undirected)
        graph_kind = "window"
        window = (t_from, t_to)
        snapshot = None
    else:
        nxg = _snapshot_graph(G, t=t, as_undirected=as_undirected)
        graph_kind = "snapshot"
        window = None
        snapshot = t

    algo = _resolve_algorithm(algorithm)
    result = algo(nxg, **kwargs)
    return _normalize_communities_result(result, getattr(algo, "__name__", str(algorithm)), graph_kind, window=window, snapshot=snapshot)


def _window_bounds(G, window, step=1, include_partial=False):
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if step <= 0:
        raise ValueError("step must be a positive integer")
    tids = G.temporal_snapshots_ids()
    if len(tids) == 0:
        return
    start = tids[0]
    end = tids[-1]
    cur = start
    while cur <= end:
        last = cur + window - 1
        if last > end and not include_partial:
            break
        yield cur, min(last, end)
        cur += step


def community_detection_over_time(G, algorithm="louvain", window=1, step=1, include_partial=False,
                                  as_undirected=True, **kwargs):
    """Run CDlib community detection repeatedly over snapshots or windows.

    If ``window`` is 1, the helper behaves like per-snapshot detection. For
    larger windows, it performs sliding-window community detection and returns
    a mapping keyed by ``(start, end)`` tuples.


    Examples
    --------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.community import community_detection_over_time
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> community_detection_over_time(G, window=1)
"""
    out = OrderedDict()
    algo = _resolve_algorithm(algorithm)

    for start, end in _window_bounds(G, window, step=step, include_partial=include_partial):
        slice_graph = G.time_slice(start, end)
        nxg = _snapshot_graph(slice_graph, as_undirected=as_undirected)
        result = algo(nxg, **kwargs)
        out[(start, end)] = _normalize_communities_result(
            result,
            getattr(algo, "__name__", str(algorithm)),
            "window",
            window=(start, end),
            snapshot=None,
        )
    return out
