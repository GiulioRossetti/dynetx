"""Tabular adapters for DyNetx graphs.

These helpers map between DyNetx graphs and pandas DataFrames using a simple
temporal event schema.
"""

from collections import defaultdict

import dynetx as dn
from dynetx.utils.validation import inclusive_end_to_exclusive

__all__ = [
    "to_interaction_dataframe",
    "from_interaction_dataframe",
    "to_snapshot_dataframe",
    "from_snapshot_dataframe",
]


def _require_pandas():
    """Import pandas lazily and raise a helpful error if it is unavailable."""
    try:
        import pandas as pd  # noqa: F401
        return pd
    except Exception as exc:
        raise ImportError("pandas is required for tabular adapters") from exc


def to_interaction_dataframe(G):
    """Return a DataFrame with one row per interaction interval.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Temporal graph to export.

    Returns
    -------
    pandas.DataFrame
        Table with columns for source, target, interval bounds, direction,
        and any edge attributes stored on each interaction.

    Example
    -------
    >>> import dynetx as dn
    >>> from dynetx.readwrite.tabular import to_interaction_dataframe
    >>> G = dn.DynGraph()
    >>> G.add_interaction(1, 2, t=0)
    >>> df = to_interaction_dataframe(G)
    >>> list(df.columns)[:4]
    ['source', 'target', 't_start', 't_end']
    """
    pd = _require_pandas()
    rows = []
    for u, v, d in G.interactions_iter():
        edge_attrs = {k: val for k, val in d.items() if k != "t"}
        for t0, t1 in d.get("t", []):
            rows.append({
                "source": u,
                "target": v,
                "t_start": t0,
                "t_end": t1,
                "directed": G.is_directed(),
                **edge_attrs,
            })
    return pd.DataFrame(rows)


def from_interaction_dataframe(df, directed=False):
    """Build a DyNetx graph from an interaction DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Table containing at least ``source``, ``target`` and ``t_start``.
    directed : bool, optional
        If ``True``, create a ``DynDiGraph``.

    Returns
    -------
    DynGraph or DynDiGraph
        Temporal graph reconstructed from the table.

    Example
    -------
    >>> import pandas as pd
    >>> from dynetx.readwrite.tabular import from_interaction_dataframe
    >>> df = pd.DataFrame([{"source": 1, "target": 2, "t_start": 0, "t_end": 1}])
    >>> G = from_interaction_dataframe(df)
    >>> G.interactions(t=0)
    [(1, 2)]
    """
    pd = _require_pandas()
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    graph = dn.DynDiGraph() if directed else dn.DynGraph()
    for _, row in df.iterrows():
        attrs = {k: row[k] for k in df.columns if k not in {"source", "target", "t_start", "t_end", "directed"} and pd.notna(row[k])}
        t0 = row["t_start"]
        t1 = row["t_end"] if "t_end" in df.columns and pd.notna(row["t_end"]) else None
        graph.add_interaction(row["source"], row["target"], t=t0, e=inclusive_end_to_exclusive(t1), **attrs)
    return graph


def to_snapshot_dataframe(G):
    """Return a DataFrame with one row per active snapshot edge.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Temporal graph to export.

    Returns
    -------
    pandas.DataFrame
        Table with one row for every active edge at every timestamp.
    """
    pd = _require_pandas()
    rows = []
    for u, v, d in G.interactions_iter():
        edge_attrs = {k: val for k, val in d.items() if k != "t"}
        for t0, t1 in d.get("t", []):
            for tid in range(t0, t1 + 1):
                rows.append({
                    "source": u,
                    "target": v,
                    "time": tid,
                    "directed": G.is_directed(),
                    **edge_attrs,
                })
    return pd.DataFrame(rows)


def from_snapshot_dataframe(df, directed=False):
    """Build a DyNetx graph from a snapshot DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Table containing at least ``source``, ``target`` and ``time``.
    directed : bool, optional
        If ``True``, create a ``DynDiGraph``.

    Returns
    -------
    DynGraph or DynDiGraph
        Temporal graph reconstructed from the table.
    """
    pd = _require_pandas()
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    graph = dn.DynDiGraph() if directed else dn.DynGraph()
    for _, row in df.iterrows():
        attrs = {k: row[k] for k in df.columns if k not in {"source", "target", "time", "directed"} and pd.notna(row[k])}
        graph.add_interaction(row["source"], row["target"], t=row["time"], **attrs)
    return graph
