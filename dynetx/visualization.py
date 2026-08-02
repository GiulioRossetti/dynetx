"""Visualization helpers for temporal DyNetx graphs.

The functions in this module intentionally stay lightweight and return the
Matplotlib objects they create, so callers can save, embed, or further
customize the plots.
"""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

__all__ = [
    "draw_snapshot",
    "plot_temporal_summary",
    "plot_activity_heatmap",
    "compare_snapshots",
]


def _require_matplotlib():
    """Import Matplotlib lazily and raise a clear error if unavailable."""
    try:
        import matplotlib.pyplot as plt  # noqa: F401
        return plt
    except Exception as exc:
        raise ImportError("matplotlib is required for visualization helpers") from exc


def _snapshot_graph(G, t=None):
    """Return the NetworkX graph for a snapshot or for the full time span."""
    return G.to_networkx_graph(t=t)


def _shared_layout(G, layout="spring", seed=42):
    """Compute a layout once and reuse it across snapshot comparisons."""
    nxg = G.to_networkx_graph() if hasattr(G, "to_networkx_graph") else G
    if layout == "circular":
        return nx.circular_layout(nxg)
    if layout == "kamada_kawai":
        return nx.kamada_kawai_layout(nxg)
    return nx.spring_layout(nxg, seed=seed)


def draw_snapshot(G, t=None, ax=None, layout="spring", pos=None, with_labels=True,
                  node_size=500, node_color="tab:blue", edge_color="0.4",
                  title=None, arrows=None, **kwargs):
    """Draw a single snapshot or the aggregate graph.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
    t : snapshot id, optional
        If omitted, the aggregate graph is drawn.
    ax : matplotlib axes, optional
    layout : str, optional
        Layout used when ``pos`` is not provided.
    pos : dict, optional
        Precomputed node positions to reuse across multiple plots.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used for rendering.

    References
    ----------
    No publication is associated with this rendering helper; it is a
    convenience function for the DyNetx documentation and dashboard.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=kwargs.pop("figsize", (7, 5)))

    nxg = _snapshot_graph(G, t=t)
    if pos is None:
        pos = _shared_layout(nxg, layout=layout)

    if title is None:
        title = "Aggregate graph" if t is None else "Snapshot {}".format(t)

    ax.set_title(title)
    ax.axis("off")
    nx.draw_networkx_nodes(nxg, pos, ax=ax, node_size=node_size, node_color=node_color)
    nx.draw_networkx_edges(nxg, pos, ax=ax, edge_color=edge_color, arrows=arrows if arrows is not None else G.is_directed())
    if with_labels:
        nx.draw_networkx_labels(nxg, pos, ax=ax)
    return ax


def plot_temporal_summary(G, ax=None, kind="interactions", title=None, color="tab:blue", **kwargs):
    """Plot a simple temporal summary series.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Temporal graph to summarize.
    ax : matplotlib.axes.Axes, optional
        Existing axes to draw on.
    kind : {"interactions", "nodes", "both"}, optional
        Series to render.
    title : str, optional
        Plot title.
    color : str, optional
        Matplotlib color for the primary series.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used for rendering.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=kwargs.pop("figsize", (8, 4)))

    tids = G.temporal_snapshots_ids()
    if len(tids) == 0:
        ax.text(0.5, 0.5, "No temporal data", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return ax

    interactions = [G.interactions_per_snapshots(t) for t in tids]
    if kind in ("nodes", "both"):
        nodes = [G.number_of_nodes(t) for t in tids]
    else:
        nodes = None

    if kind == "nodes":
        ax.plot(tids, nodes, marker="o", color=color, label="active nodes")
    elif kind == "both":
        ax.plot(tids, interactions, marker="o", color="tab:blue", label="interactions")
        ax.plot(tids, nodes, marker="o", color="tab:orange", label="active nodes")
        ax.legend(frameon=False)
    else:
        ax.plot(tids, interactions, marker="o", color=color, label="interactions")
        ax.legend(frameon=False)

    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.set_title(title or "Temporal summary")
    ax.grid(alpha=0.2)
    return ax


def plot_activity_heatmap(G, ax=None, title=None, cmap="Blues", sort_nodes=True, **kwargs):
    """Plot a node-by-time activity heatmap.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Temporal graph to summarize.
    ax : matplotlib.axes.Axes, optional
        Existing axes to draw on.
    title : str, optional
        Plot title.
    cmap : str, optional
        Matplotlib colormap name.
    sort_nodes : bool, optional
        If ``True``, order nodes deterministically by their string
        representation.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used for rendering.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=kwargs.pop("figsize", (9, 5)))

    tids = G.temporal_snapshots_ids()
    nodes = list(G.nodes())
    if sort_nodes:
        nodes = sorted(nodes, key=str)

    if len(nodes) == 0 or len(tids) == 0:
        ax.text(0.5, 0.5, "No temporal data", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return ax

    matrix = []
    for n in nodes:
        row = [1 if G.has_node(n, t) else 0 for t in tids]
        matrix.append(row)

    im = ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, **kwargs)
    ax.set_yticks(range(len(nodes)))
    ax.set_yticklabels(nodes)
    ax.set_xticks(range(len(tids)))
    ax.set_xticklabels(tids)
    ax.set_xlabel("Time")
    ax.set_ylabel("Node")
    ax.set_title(title or "Node activity heatmap")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return ax


def compare_snapshots(G, t1, t2, layout="spring", title=None, **kwargs):
    """Draw two snapshots side by side using a shared layout.

    Returns
    -------
    tuple
        Matplotlib figure and axes array.
    """
    plt = _require_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=kwargs.pop("figsize", (12, 5)))
    shared = _shared_layout(G, layout=layout)
    draw_snapshot(G, t=t1, ax=axes[0], layout=layout, pos=shared, title="Snapshot {}".format(t1))
    draw_snapshot(G, t=t2, ax=axes[1], layout=layout, pos=shared, title="Snapshot {}".format(t2))
    if title is not None:
        fig.suptitle(title)
    fig.tight_layout()
    return fig, axes
