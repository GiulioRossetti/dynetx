"""GraphML interoperability helpers."""

import networkx as nx

import dynetx as dn

__all__ = ["write_graphml", "read_graphml"]


def write_graphml(G, path, t=None):
    """Write a snapshot or aggregate graph to GraphML."""
    nxg = G.to_networkx_graph(t=t)
    nx.write_graphml(nxg, path)


def read_graphml(path, directed=False, t=0):
    """Read GraphML into a DyNetx graph.

    The GraphML structure is treated as a static graph and imported as a
    snapshot at time ``t``.
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
