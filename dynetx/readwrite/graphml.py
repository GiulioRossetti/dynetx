"""GraphML interoperability helpers."""

import networkx as nx

import dynetx as dn

__all__ = ["write_graphml", "read_graphml"]


def write_graphml(G, path, t=None):
    """Write a snapshot or aggregate graph to GraphML.

    Parameters
    ----------
    G : DynGraph or DynDiGraph
        Graph to export.
    path : str or file-like
        Destination path.
    t : snapshot id, optional
        If provided, export the selected snapshot instead of the aggregate
        graph.

    Returns
    -------
    None

    Examples
    --------
    >>> import dynetx as dn
    >>> from dynetx.readwrite.graphml import write_graphml
    >>> G = dn.DynGraph()
    >>> G.add_interaction(1, 2, t=0)
    >>> write_graphml(G, "graph.graphml", t=0)
    """
    nxg = G.to_networkx_graph(t=t)
    nx.write_graphml(nxg, path)


def read_graphml(path, directed=False, t=0):
    """Read GraphML into a DyNetx graph.

    The GraphML structure is treated as a static graph and imported as a
    snapshot at time ``t``.


    Examples
    --------
    >>> import dynetx as dn
    >>> from dynetx.readwrite.graphml import read_graphml
    >>> G = dn.DynGraph()
    >>> G.add_interaction(0, 1, t=0)
    >>> read_graphml("graph.graphml")
"""
    nxg = nx.read_graphml(path)
    graph = dn.DynDiGraph() if directed or nxg.is_directed() else dn.DynGraph()
    graph.graph.update(nxg.graph)
    for n, d in nxg.nodes(data=True):
        graph.add_node(n, **dict(d))
    for u, v, d in nxg.edges(data=True):
        attrs = dict(d)
        attrs.pop("t", None)
        attrs.pop("e", None)
        graph.add_interaction(u, v, t=t, **attrs)
    return graph
