"""Diffusion helpers backed by NDlib.

DyNetx delegates the actual epidemic and opinion dynamics to NDlib and keeps
the integration focused on graph conversion, temporal slicing, and stable
result normalization.
"""

from __future__ import annotations

from collections import OrderedDict

from dynetx.results import DiffusionResult
from dynetx.utils.validation import normalize_time_range

__all__ = [
    "simulate_diffusion",
    "simulate_diffusion_over_time",
    "simulate_epidemic",
    "simulate_opinion",
    "diffusion_timeline_records",
]


def _require_ndlib():
    try:
        from ndlib.models.ModelConfig import Configuration
        import ndlib.models.epidemics as epidemic_models
        import ndlib.models.opinions as opinion_models
        return Configuration, epidemic_models, opinion_models
    except Exception as exc:  # pragma: no cover - dependency availability is environment-specific
        raise ImportError("ndlib is required for diffusion helpers") from exc


def _snapshot_graph(G, t=None, as_undirected=True):
    nxg = G.to_networkx_graph(t=t)
    if as_undirected and nxg.is_directed():
        nxg = nxg.to_undirected()
    return nxg


def _resolve_model(model, family=None):
    _, epidemic_models, opinion_models = _require_ndlib()
    if not isinstance(model, str):
        return model

    search_spaces = []
    if family == "epidemic":
        search_spaces.append(epidemic_models)
    elif family == "opinion":
        search_spaces.append(opinion_models)
    else:
        search_spaces.extend([epidemic_models, opinion_models])

    for namespace in search_spaces:
        resolved = getattr(namespace, model, None)
        if callable(resolved):
            return resolved

    raise ValueError("Unknown NDlib model: {}".format(model))


def _configuration_from_mapping(configuration):
    Configuration, _, _ = _require_ndlib()
    if hasattr(configuration, "get_model_configuration"):
        return configuration
    if configuration is None:
        return Configuration()
    if not isinstance(configuration, dict):
        raise TypeError("configuration must be an NDlib Configuration or a mapping")

    cfg = Configuration()
    for key, value in configuration.get("model", {}).items():
        cfg.add_model_parameter(key, value)
    for status_name, nodes in configuration.get("status", {}).items():
        cfg.add_model_initial_configuration(status_name, nodes)
    for param_name, node_values in configuration.get("nodes", {}).items():
        cfg.add_node_set_configuration(param_name, node_values)
    for param_name, edge_values in configuration.get("edges", {}).items():
        cfg.add_edge_set_configuration(param_name, edge_values)
    return cfg


def _pick_default_initial_status(model, nodes):
    if not nodes:
        return {}
    statuses = getattr(model, "available_statuses", {}) or {}
    if not statuses:
        return {}

    preferred = [
        "Infected",
        "Active",
        "Informed",
        "Adopter",
        "Opinionated",
    ]
    for label in preferred:
        if label in statuses:
            return {label: [nodes[0]]}

    ordered = sorted(statuses.items(), key=lambda item: item[1])
    return {ordered[-1][0]: [nodes[0]]}


def _build_configuration(model, configuration=None, model_parameters=None, initial_status=None,
                         node_parameters=None, edge_parameters=None):
    cfg = _configuration_from_mapping(configuration)
    if model_parameters:
        for key, value in model_parameters.items():
            cfg.add_model_parameter(key, value)
    if node_parameters:
        for param_name, node_values in node_parameters.items():
            cfg.add_node_set_configuration(param_name, node_values)
    if edge_parameters:
        for param_name, edge_values in edge_parameters.items():
            cfg.add_edge_set_configuration(param_name, edge_values)

    if initial_status is not None:
        for status_name, nodes in initial_status.items():
            cfg.add_model_initial_configuration(status_name, list(nodes))
    elif not cfg.get_model_configuration():
        nodes = list(model.graph.nodes())
        default_status = _pick_default_initial_status(model, nodes)
        for status_name, assigned_nodes in default_status.items():
            cfg.add_model_initial_configuration(status_name, list(assigned_nodes))
    return cfg


def _label_map(model):
    statuses = getattr(model, "available_statuses", {}) or {}
    return {value: key for key, value in statuses.items()}


def _serialize_configuration(configuration):
    if configuration is None:
        return None
    return {
        "model": dict(configuration.get_model_parameters()),
        "status": {
            status_name: list(nodes)
            for status_name, nodes in configuration.get_model_configuration().items()
        },
        "nodes": {
            param_name: dict(node_values)
            for param_name, node_values in configuration.get_nodes_configuration().items()
        },
        "edges": {
            param_name: dict(edge_values)
            for param_name, edge_values in configuration.get_edges_configuration().items()
        },
    }


def _normalize_iteration(iteration, status_map):
    labels = {}
    for node, status_code in iteration.get("status", {}).items():
        labels[node] = status_map.get(status_code, status_code)

    node_count = {
        status_map.get(status_code, status_code): count
        for status_code, count in iteration.get("node_count", {}).items()
    }
    status_delta = {
        status_map.get(status_code, status_code): delta
        for status_code, delta in iteration.get("status_delta", {}).items()
    }
    return {
        "iteration": iteration.get("iteration"),
        "status": labels,
        "node_count": node_count,
        "status_delta": status_delta,
    }


def _build_diffusion_result(iterations, status_map, graph_kind, model_name, snapshot=None, window=None,
                            seed=None, as_undirected=True, configuration=None, model_parameters=None):
    timeline = []
    node_states = {}
    current_states = {}

    for record in iterations:
        normalized = _normalize_iteration(record, status_map)
        timeline.append(normalized)
        iteration = normalized["iteration"]

        if iteration == 0:
            current_states.update(normalized["status"])
        else:
            current_states.update(normalized["status"])

        for node, label in current_states.items():
            node_states.setdefault(node, []).append({"iteration": iteration, "status": label})

    metadata = {
        "backend": "ndlib",
        "model": model_name,
        "graph_kind": graph_kind,
        "snapshot": snapshot,
        "window": window,
        "seed": seed,
        "as_undirected": as_undirected,
        "status_map": status_map,
        "configuration": _serialize_configuration(configuration),
    }
    return DiffusionResult(timeline=timeline, node_states=node_states, metadata=metadata)


def _run_diffusion(G, model, family=None, t=None, as_undirected=True, steps=10, seed=None,
                   configuration=None, model_parameters=None, initial_status=None,
                   node_parameters=None, edge_parameters=None, graph_kind_override=None, **kwargs):
    model_cls = _resolve_model(model, family=family)
    if t is None:
        nxg = _snapshot_graph(G, as_undirected=as_undirected)
        graph_kind = graph_kind_override or "aggregate"
        snapshot = None
        window = None
    elif isinstance(t, (tuple, list)) and len(t) == 2:
        t_from, t_to = normalize_time_range(t)
        nxg = _snapshot_graph(G.time_slice(t_from, t_to), as_undirected=as_undirected)
        graph_kind = graph_kind_override or "window"
        snapshot = None
        window = (t_from, t_to)
    else:
        nxg = _snapshot_graph(G, t=t, as_undirected=as_undirected)
        graph_kind = graph_kind_override or "snapshot"
        snapshot = t
        window = None

    if steps is None or steps <= 0:
        raise ValueError("steps must be a positive integer")

    if nxg.number_of_nodes() == 0:
        model_name = getattr(model_cls, "__name__", str(model))
        return DiffusionResult(
            timeline=[],
            node_states={},
            metadata={
                "backend": "ndlib",
                "model": model_name,
                "graph_kind": graph_kind,
                "snapshot": snapshot,
                "window": window,
                "seed": seed,
                "as_undirected": as_undirected,
                "status_map": {},
            },
        )

    nd_model = model_cls(nxg, seed=seed)
    cfg = _build_configuration(
        nd_model,
        configuration=configuration,
        model_parameters=model_parameters,
        initial_status=initial_status,
        node_parameters=node_parameters,
        edge_parameters=edge_parameters,
    )
    nd_model.set_initial_status(cfg)
    iterations = nd_model.iteration_bunch(steps, **kwargs)
    model_name = getattr(nd_model, "name", getattr(model_cls, "__name__", str(model)))
    return _build_diffusion_result(
        iterations,
        _label_map(nd_model),
        graph_kind,
        model_name,
        snapshot=snapshot,
        window=window,
        seed=seed,
        as_undirected=as_undirected,
        configuration=cfg,
        model_parameters=model_parameters,
    )


def simulate_diffusion(G, model="SIModel", t=None, as_undirected=True, steps=10, seed=None,
                       configuration=None, model_parameters=None, initial_status=None,
                       node_parameters=None, edge_parameters=None, **kwargs):
    """Run an NDlib diffusion model on a DyNetx graph.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Dynamic graph to simulate on.
    model : str or callable
        NDlib model class or its name.
    t : int or 2-sequence, optional
        Snapshot id or inclusive time range. If omitted, the aggregate graph is
        used.
    as_undirected : bool, optional
        Convert directed graphs to undirected graphs before calling NDlib.
    steps : int, optional
        Number of NDlib iterations to simulate.
    seed : int, optional
        Random seed passed to the NDlib model.
    configuration : ndlib.models.ModelConfig.Configuration or dict, optional
        Prebuilt NDlib configuration or a mapping with ``model``, ``status``,
        ``nodes``, and ``edges`` entries.
    model_parameters, initial_status, node_parameters, edge_parameters : optional
        Convenience overrides merged into the NDlib configuration.
    kwargs : dict
        Additional keyword arguments passed through to ``iteration_bunch``.

    Returns
    -------
    DiffusionResult
        Normalized diffusion timeline and per-node state history.

    References
    ----------
    No single publication is tied to this wrapper; the underlying dynamics are
    delegated to the selected NDlib model.

    Example
    -------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.diffusion import simulate_diffusion
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> result = simulate_diffusion(G, steps=1)
    >>> isinstance(result.timeline, list)
    True
    """
    return _run_diffusion(
        G,
        model,
        family=None,
        t=t,
        as_undirected=as_undirected,
        steps=steps,
        seed=seed,
        configuration=configuration,
        model_parameters=model_parameters,
        initial_status=initial_status,
        node_parameters=node_parameters,
        edge_parameters=edge_parameters,
        **kwargs,
    )


def simulate_epidemic(G, model="SIModel", t=None, as_undirected=True, steps=10, seed=None,
                      configuration=None, model_parameters=None, initial_status=None,
                      node_parameters=None, edge_parameters=None, **kwargs):
    """Run an NDlib epidemic model on a DyNetx graph.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Dynamic graph to simulate on.
    model : str or NDlib model class, optional
        Epidemic model to run.
    t : snapshot id or 2-sequence, optional
        Snapshot or temporal window to analyze.
    as_undirected : bool, optional
        If ``True``, convert directed graphs to undirected graphs before
        running the simulation.
    steps : int, optional
        Number of NDlib iterations.
    seed : int, optional
        Random seed used by the simulation backend.
    configuration : mapping or NDlib Configuration, optional
        Prebuilt model configuration.
    model_parameters : mapping, optional
        Model parameter overrides.
    initial_status : mapping, optional
        Explicit initial node status assignment.
    node_parameters : mapping, optional
        Node-level NDlib parameter assignments.
    edge_parameters : mapping, optional
        Edge-level NDlib parameter assignments.
    kwargs : dict
        Additional keyword arguments passed through to the NDlib iteration API.

    Returns
    -------
    DiffusionResult
        Normalized diffusion timeline and per-node state history.

    References
    ----------
    No single publication is tied to this wrapper; the underlying dynamics are
    delegated to the selected NDlib model.

    Example
    -------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.diffusion import simulate_epidemic
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> result = simulate_epidemic(G, steps=1)
    >>> isinstance(result.timeline, list)
    True
    """
    return _run_diffusion(
        G,
        model,
        family="epidemic",
        t=t,
        as_undirected=as_undirected,
        steps=steps,
        seed=seed,
        configuration=configuration,
        model_parameters=model_parameters,
        initial_status=initial_status,
        node_parameters=node_parameters,
        edge_parameters=edge_parameters,
        **kwargs,
    )


def simulate_opinion(G, model="VoterModel", t=None, as_undirected=True, steps=10, seed=None,
                     configuration=None, model_parameters=None, initial_status=None,
                     node_parameters=None, edge_parameters=None, **kwargs):
    """Run an NDlib opinion-dynamics model on a DyNetx graph.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Dynamic graph to simulate on.
    model : str or NDlib model class, optional
        Opinion-dynamics model to run.
    t : snapshot id or 2-sequence, optional
        Snapshot or temporal window to analyze.
    as_undirected : bool, optional
        If ``True``, convert directed graphs to undirected graphs before
        running the simulation.
    steps : int, optional
        Number of NDlib iterations.
    seed : int, optional
        Random seed used by the simulation backend.
    configuration : mapping or NDlib Configuration, optional
        Prebuilt model configuration.
    model_parameters : mapping, optional
        Model parameter overrides.
    initial_status : mapping, optional
        Explicit initial node status assignment.
    node_parameters : mapping, optional
        Node-level NDlib parameter assignments.
    edge_parameters : mapping, optional
        Edge-level NDlib parameter assignments.
    kwargs : dict
        Additional keyword arguments passed through to the NDlib iteration API.

    Returns
    -------
    DiffusionResult
        Normalized diffusion timeline and per-node state history.

    References
    ----------
    No single publication is tied to this wrapper; the underlying dynamics are
    delegated to the selected NDlib model.

    Example
    -------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.diffusion import simulate_opinion
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> result = simulate_opinion(G, steps=1)
    >>> isinstance(result.timeline, list)
    True
    """
    return _run_diffusion(
        G,
        model,
        family="opinion",
        t=t,
        as_undirected=as_undirected,
        steps=steps,
        seed=seed,
        configuration=configuration,
        model_parameters=model_parameters,
        initial_status=initial_status,
        node_parameters=node_parameters,
        edge_parameters=edge_parameters,
        **kwargs,
    )


def simulate_diffusion_over_time(G, model="SIModel", window=1, step=1, include_partial=False,
                                 as_undirected=True, steps=10, seed=None, configuration=None,
                                 model_parameters=None, initial_status=None, node_parameters=None,
                                 edge_parameters=None, family=None, **kwargs):
    """Run a diffusion model repeatedly over snapshots or windows.

    Returns
    -------
    OrderedDict
        Mapping ``(start, end)`` tuples to :class:`DiffusionResult` objects.

    Example
    -------
    >>> import dynetx as dn
    >>> from dynetx.algorithms.diffusion import simulate_diffusion_over_time
    >>> G = dn.DynGraph()
    >>> G.add_path([0, 1, 2], t=0)
    >>> out = simulate_diffusion_over_time(G, steps=1)
    >>> list(out.keys())
    [(0, 0)]
    """
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if step <= 0:
        raise ValueError("step must be a positive integer")

    out = OrderedDict()
    tids = G.temporal_snapshots_ids()
    if len(tids) == 0:
        return out

    start = tids[0]
    end = tids[-1]
    cur = start
    while cur <= end:
        last = cur + window - 1
        if last > end and not include_partial:
            break
        slice_graph = G.time_slice(cur, min(last, end))
        out[(cur, min(last, end))] = _run_diffusion(
            slice_graph,
            model,
            family=family,
            t=None,
            as_undirected=as_undirected,
            steps=steps,
            seed=seed,
            configuration=configuration,
            model_parameters=model_parameters,
            initial_status=initial_status,
            node_parameters=node_parameters,
            edge_parameters=edge_parameters,
            graph_kind_override="window",
            **kwargs,
        )
        cur += step
    return out


def diffusion_timeline_records(result):
    """Return a serializable list of diffusion timeline records.

    Parameters
    ----------
    result : DiffusionResult
        Result returned by one of the diffusion helpers.

    Returns
    -------
    list
        Timeline records ready for JSON serialization or tabular export.

    Example
    -------
    >>> from dynetx.results import DiffusionResult
    >>> from dynetx.algorithms.diffusion import diffusion_timeline_records
    >>> diffusion_timeline_records(DiffusionResult(timeline=[{"iteration": 0}]))
    [{'iteration': 0}]
    """
    return list(result.timeline)
