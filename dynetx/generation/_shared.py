"""Shared helpers for synthetic dynamic graph generators.

The functions in this module are internal building blocks used by the
dedicated synthetic generators. They keep the model implementations small and
make the generation submodule easier to extend.
"""

from __future__ import annotations

from collections import defaultdict
import random


def new_graph():
    """Return a fresh ``DynGraph`` instance for synthetic generation.

    Returns
    -------
    DynGraph
        Empty dynamic graph ready to receive synthetic interactions.


    Examples
    --------
    >>> from dynetx.generation._shared import new_graph
    >>> new_graph(num_nodes=5, snapshots=2, seed=1)
"""
    from dynetx import DynGraph

    return DynGraph()


def normalize_name(name):
    """Normalize a human-readable model name to a canonical identifier.

    Parameters
    ----------
    name : object
        Name or label to normalize.

    Returns
    -------
    str
        Lowercase identifier with spaces and hyphens replaced by underscores.


    Examples
    --------
    >>> from dynetx.generation._shared import normalize_name
    >>> normalize_name(num_nodes=5, snapshots=2, seed=1)
"""
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def sample_power_law(rng, minimum, maximum, exponent):
    """Sample a value from a bounded power-law distribution.

    Parameters
    ----------
    rng : random.Random
        Random number generator used for sampling.
    minimum : float
        Lower bound of the support.
    maximum : float
        Upper bound of the support.
    exponent : float
        Power-law exponent.

    Returns
    -------
    float
        Sampled value in the requested interval.


    Examples
    --------
    >>> from dynetx.generation._shared import sample_power_law
    >>> sample_power_law(num_nodes=5, snapshots=2, seed=1)
"""
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
    """Return the inclusive end timestamp of a stream contact.

    Parameters
    ----------
    start : int
        Contact start time.
    duration : int
        Contact duration.
    max_snapshot : int
        Maximum snapshot identifier available in the stream.

    Returns
    -------
    int
        Inclusive end timestamp clipped to the available range.


    Examples
    --------
    >>> from dynetx.generation._shared import stream_contact_end
    >>> stream_contact_end(num_nodes=5, snapshots=2, seed=1)
"""
    duration = max(1, int(round(duration)))
    return min(start + duration, max_snapshot)


def active_nodes(rng, nodes, dynamic_nodes, node_churn):
    """Select the nodes active at a given snapshot.

    Parameters
    ----------
    rng : random.Random
        Random number generator.
    nodes : iterable
        All candidate nodes.
    dynamic_nodes : bool
        If ``True``, apply node churn to produce a varying active set.
    node_churn : float
        Probability that a node disappears from a snapshot.

    Returns
    -------
    list
        Active node identifiers sorted for deterministic output.


    Examples
    --------
    >>> from dynetx.generation._shared import active_nodes
    >>> active_nodes(num_nodes=5, snapshots=2, seed=1)
"""
    if not dynamic_nodes:
        return list(nodes)
    active = [node for node in nodes if rng.random() >= node_churn]
    if len(active) < 2:
        active = rng.sample(nodes, k=min(2, len(nodes)))
    return sorted(active)


def copy_nodes(graph, nodes):
    """Add ``nodes`` to ``graph`` preserving their identifiers.

    Examples
    --------
    >>> from dynetx.generation._shared import copy_nodes
    >>> copy_nodes(num_nodes=5, snapshots=2, seed=1)
"""
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
    """Build a baseline random stream graph used by reference models.

    Parameters
    ----------
    num_nodes : int, optional
        Number of nodes to create.
    snapshots : int, optional
        Number of temporal snapshots.
    seed : int, optional
        Random seed.
    edge_probability : float, optional
        Probability of creating a candidate interaction.
    dynamic_nodes : bool, optional
        Whether nodes may temporarily disappear.
    node_churn : float, optional
        Probability that a node is absent from a snapshot when node churn is
        enabled.
    contact_duration : int, optional
        Duration assigned to each interaction.
    activity_min : float, optional
        Lower bound of the activity-rate distribution.
    activity_max : float, optional
        Upper bound of the activity-rate distribution.
    activity_exponent : float, optional
        Power-law exponent controlling activity heterogeneity.

    Returns
    -------
    DynGraph
        Synthetic dynamic graph storing temporal interaction spans.


    Examples
    --------
    >>> from dynetx.generation._shared import base_stream_graph
    >>> base_stream_graph(num_nodes=5, snapshots=2, seed=1)
"""
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
    """Return the interaction timelines stored in ``graph``.

    Returns
    -------
    list[tuple]
        List of ``(u, v, spans)`` tuples where ``spans`` is the temporal
        support attached to the edge.


    Examples
    --------
    >>> from dynetx.generation._shared import edge_timelines
    >>> edge_timelines(num_nodes=5, snapshots=2, seed=1)
"""
    timelines = []
    for u, v, attrs in graph.interactions_iter():
        spans = [tuple(span) for span in attrs.get("t", [])]
        if spans:
            timelines.append((u, v, spans))
    return timelines


def event_rows(graph):
    """Expand a stream graph into per-event rows.

    Returns
    -------
    list[tuple]
        Tuples of ``(u, v, start, duration)``.


    Examples
    --------
    >>> from dynetx.generation._shared import event_rows
    >>> event_rows(num_nodes=5, snapshots=2, seed=1)
"""
    events = []
    for u, v, attrs in graph.interactions_iter():
        for start, end in attrs.get("t", []):
            events.append((u, v, int(start), max(1, int(end) - int(start) + 1)))
    return events


def add_spans(graph, u, v, spans):
    """Add a sequence of inclusive spans to ``graph`` for edge ``(u, v)``.

    Examples
    --------
    >>> from dynetx.generation._shared import add_spans
    >>> add_spans(num_nodes=5, snapshots=2, seed=1)
"""
    for start, end in spans:
        graph.add_interaction(u, v, t=int(start), e=int(end) + 1)


def rewired_pair_list(rng, nodes, count):
    """Return ``count`` node pairs, reusing pairs when necessary.

    Parameters
    ----------
    rng : random.Random
        Random number generator.
    nodes : iterable
        Candidate node identifiers.
    count : int
        Number of pairs to return.

    Returns
    -------
    list[tuple]
        Pairs sampled without replacement when possible.


    Examples
    --------
    >>> from dynetx.generation._shared import rewired_pair_list
    >>> rewired_pair_list(num_nodes=5, snapshots=2, seed=1)
"""
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
