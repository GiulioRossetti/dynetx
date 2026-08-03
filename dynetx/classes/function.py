from __future__ import division

from dynetx.utils import not_implemented
from collections import Counter
from itertools import chain

import networkx as nx


__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"


__all__ = ['nodes', 'interactions', 'degree', 'degree_histogram', 'neighbors',
           'number_of_nodes', 'number_of_interactions', 'density',
           'is_directed', 'freeze', 'is_frozen', 'subgraph',
           'add_star', 'add_path', 'add_cycle',
           'create_empty_copy', 'set_node_attributes',
           'get_node_attributes', 'set_edge_attributes',
           'get_edge_attributes', 'all_neighbors', 'non_neighbors',
           'non_interactions', 'is_empty', 'time_slice', 'stream_interactions', 'interactions_per_snapshots',
           'temporal_snapshots_ids', 'inter_event_time_distribution',
           'temporal_degree', 'avg_temporal_degree', 'has_node_in_range',
           'has_interaction_in_range', 'neighbors_in_range', 'interactions_in_range',
           'window_slices', 'to_networkx_graph']


def nodes(G, t=None):
    """
    Return a list of the nodes in the graph at a given snapshot.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
        >>> G.add_path([0,1,2], 0)
        >>> dn.nodes(G, t=0)
        [0, 1, 2]
        >>> G.add_edge(1, 4, t=1)
        >>> dn.nodes(G, t=0)
        [0, 1, 2]
    """
    return G.nodes(t)


def interactions(G, nbunch=None, t=None):
    """
    Return the list of edges present in a given snapshot.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2], t=0)
        >>> G.add_edge(2,3, t=1)
        >>> dn.interactions(G, t=0)
        [(0, 1), (1, 2)]
        >>> dn.interactions(G)
        [(0, 1), (1, 2), (2, 3)]
        >>> dn.interactions(G, [0,3], t=0)
        [(0, 1)]
    """
    return G.interactions(nbunch, t=t)


def degree(G, nbunch=None, t=None):
    """
    Return the degree of a node or nodes at time t.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> dn.degree(G, 0, t=0)
        1
        >>> dn.degree(G, [0,1], t=1)
        {0: 0, 1: 0}
        >>> list(dn.degree(G, [0,1], t=0).values())
        [1, 2]
    """
    return G.degree(nbunch, t)


def neighbors(G, n, t=None):
    """
    Return a list of the nodes connected to the node n at time t.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> dn.neighbors(G, 0, t=0)
        [1]
        >>> dn.neighbors(G, 0, t=1)
        []
    """
    return G.neighbors(n, t)


def number_of_nodes(G, t=None):
    """
    Return the number of nodes in the t snpashot of a dynamic graph.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
        >>> G.add_path([0,1,2], t=0)
        >>> dn.number_of_nodes(G, 0)
        3
    """
    return G.number_of_nodes(t)


def number_of_interactions(G, u=None, v=None, t=None):
    """
    Return the number of edges between two nodes at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> dn.number_of_interactions(G, t=0)
    """
    return G.number_of_interactions(u, v, t)


def density(G, t=None):
    """
    Return the density of a graph at timestamp t. The density for undirected graphs is
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.density(G)
    """
    n = number_of_nodes(G, t)
    m = number_of_interactions(G, t)
    if m == 0 or m is None or n <= 1:
        return 0

    d = m / (n * (n - 1))
    if not G.is_directed():
        d *= 2
    return d


def degree_histogram(G, t=None):
    """
    Return a list of the frequency of each degree value.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.degree_histogram(G)
    """
    counts = Counter(d for n, d in G.degree(t=t).items())
    return [counts.get(i, 0) for i in range(max(counts) + 1)]


def is_directed(G):
    """
    Return ``True`` if ``G`` is directed.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.is_directed(G)
    """
    return G.is_directed()


def frozen():
    """
    Dummy method for raising errors when trying to modify frozen graphs
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.frozen(G)
    """
    raise nx.NetworkXError("Frozen graph can't be modified")


def freeze(G):
    """
    Modify graph to prevent further change by adding or removing nodes or edges.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.freeze(G)
    """
    G.add_node = frozen
    G.add_nodes_from = frozen
    G.remove_node = frozen
    G.remove_nodes_from = frozen
    G.add_edge = frozen
    G.add_edges_from = frozen
    G.remove_edge = frozen
    G.remove_edges_from = frozen
    G.clear = frozen
    G.frozen = True
    return G


def is_frozen(G):
    """
    Return True if graph is frozen.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.is_frozen(G)
    """
    try:
        return G.frozen
    except AttributeError:
        return False


def add_star(G, nodes, t, **attr):
    """
    Add a star at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> dn.add_star(G, [0,1,2,3], t=0)
    """
    nlist = iter(nodes)
    v = next(nlist)
    edges = ((v, n) for n in nlist)
    G.add_interactions_from(edges, t, **attr)


def add_path(G, nodes, t, **attr):
    """
    Add a path at time t.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()
        >>> dn.add_path(G, [0,1,2,3], t=0)
    """
    nlist = list(nodes)
    edges = zip(nlist[:-1], nlist[1:])
    G.add_interactions_from(edges, t, **attr)


def add_cycle(G, nodes, t, **attr):
    """
    Add a cycle at time t.
    
    Example::
    
    
    
        >>> G = dn.DynGraph()
        >>> dn.add_cycle(G, [0,1,2,3], t=0)
    """
    nlist = list(nodes)
    edges = zip(nlist, nlist[1:] + [nlist[0]])
    G.add_interactions_from(edges, t, **attr)


def subgraph(G, nbunch):
    """
    Return the subgraph induced on nodes in nbunch.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.subgraph(G, [0, 1])
    """
    return G.subgraph(nbunch)


def create_empty_copy(G, with_data=True):
    """
    Return a copy of the graph G with all of the edges removed.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.create_empty_copy(G)
    """
    H = G.__class__()
    H.add_nodes_from(G.nodes(data=with_data))
    if with_data:
        H.graph.update(G.graph)
    return H


def set_node_attributes(G, values, name=None):
    """
    Set node attributes from dictionary of nodes and values
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.set_node_attributes(G, {0: "red"}, name="color")
    """
    # Set node attributes based on type of `values`
    if name is not None:  # `values` must not be a dict of dict
        try:  # `values` is a dict
            for n, v in values.items():
                try:
                    G._node[n][name] = values[n]
                except KeyError:
                    pass
        except AttributeError:  # `values` is a constant
            for n in G:
                G._node[n][name] = values
    else:  # `values` must be dict of dict
        for n, d in values.items():
            try:
                G._node[n].update(d)
            except KeyError:
                pass


def get_node_attributes(G, name):
    """
    Get node attributes from graph
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.get_node_attributes(G, "color")
    """
    return {n: d[name] for n, d in G._node.items() if name in d}


def set_edge_attributes(G, values, name=None):
    """
    Set edge attributes on a dynamic graph.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.set_edge_attributes(G, {0: "red"}, name="color")
    """
    def _edge_data(u, v):
        if G.is_directed():
            if u in G._succ and v in G._succ[u]:
                return G._succ[u][v]
        else:
            if u in G._adj and v in G._adj[u]:
                return G._adj[u][v]
        return None

    def _update_edge(u, v, attrs):
        datadict = _edge_data(u, v)
        if datadict is not None:
            datadict.update(attrs)

    if name is not None:
        if hasattr(values, "items"):
            for key, value in values.items():
                if len(key) >= 2:
                    _update_edge(key[0], key[1], {name: value})
        else:
            for u, v, _ in G.interactions_iter():
                _update_edge(u, v, {name: values})
        return

    if not hasattr(values, "items"):
        raise AttributeError("'values' must be a mapping when 'name' is not provided")

    for key, attrs in values.items():
        if len(key) < 2:
            continue
        u, v = key[0], key[1]
        if isinstance(attrs, dict):
            _update_edge(u, v, attrs)
        else:
            _update_edge(u, v, {key: attrs})


def get_edge_attributes(G, name):
    """
    Return edge attributes from a dynamic graph.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.get_edge_attributes(G, "weight")
    """
    attrs = {}
    if name is None:
        for u, v, d in G.interactions_iter():
            attrs[(u, v)] = dict(d)
    else:
        for u, v, d in G.interactions_iter():
            if name in d:
                attrs[(u, v)] = d[name]
    return attrs


def all_neighbors(graph, node, t=None):
    """
    Returns all of the neighbors of a node in the graph at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.all_neighbors(G, 0, t=0)
    """
    if graph.is_directed():
        values = chain(graph.predecessors(node, t=t), graph.successors(node, t=t))
    else:
        values = graph.neighbors(node, t=t)
    return values


def non_neighbors(graph, node, t=None):
    """
    Returns the non-neighbors of the node in the graph at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.non_neighbors(G, 0, t=0)
    """
    if graph.is_directed():
        values = chain(graph.predecessors(node, t=t), graph.successors(node, t=t))
    else:
        values = graph.neighbors(node, t=t)

    nbors = set(values) | {node}
    return (nnode for nnode in graph if nnode not in nbors)


def non_interactions(graph, t=None):
    """
    Returns the non-existent edges in the graph at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> list(dn.non_interactions(G))
    """
    # if graph.is_directed():
    #    for u in graph:
    #        for v in non_neighbors(graph, u, t):
    #            yield (u, v)
    #else:
    nodes = set(graph)
    while nodes:
        u = nodes.pop()
        for v in nodes - set(graph[u]):
            yield u, v


def is_empty(G):
    """
    Returns ``True`` if ``G`` has no edges.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.is_empty(G)
    """
    return not any(G.adj.values())


def time_slice(G, t_from, t_to=None, **kwargs):
    """
    Return an iterator for (node, degree) at time t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.add_path([0,4,5,6], t=1)
        >>> G.add_path([7,1,2,3], t=2)
        >>> H = dn.time_slice(G, 0)
        >>> H.edges()
        [(0, 1), (1, 2), (1, 3)]
        >>> H = dn.time_slice(G, 0, 1)
        >>> H.edges()
        [(0, 1), (1, 2), (1, 3), (0, 4), (4, 5), (5, 6)]
    """
    return G.time_slice(t_from, t_to, **kwargs)


def stream_interactions(G):
    """
    Generate a temporal ordered stream of interactions.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.add_path([3,4,5,6], t=1)
        >>> list(dn.stream_interactions(G))
        [(0, 1, '+', 0), (1, 2, '+', 0), (2, 3, '+', 0), (3, 4, '+', 1), (4, 5, '+', 1), (5, 6, '+', 1)]
    """
    return G.stream_interactions()


def temporal_degree(G, nbunch=None, t=None):
    """
    Return the temporal support of one or more nodes.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.temporal_degree(G)
    """
    return G.temporal_degree(nbunch=nbunch, t=t)


def avg_temporal_degree(G):
    """
    Return the average temporal support across all nodes.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.avg_temporal_degree(G)
    """
    return G.avg_temporal_degree()


def has_node_in_range(G, n, t_from, t_to=None, mode='any'):
    """
    Check whether node ``n`` appears within a time interval.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.has_node_in_range(G, 0, 0)
    """
    return G.has_node_in_range(n, t_from, t_to=t_to, mode=mode)


def has_interaction_in_range(G, u, v, t_from, t_to=None, mode='any'):
    """
    Check whether interaction ``(u, v)`` appears within a time interval.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.has_interaction_in_range(G, 0, 1, 0)
    """
    return G.has_interaction_in_range(u, v, t_from, t_to=t_to, mode=mode)


def neighbors_in_range(G, n, t_from, t_to=None, mode='any'):
    """
    Return the neighbors of ``n`` observed over a time interval.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.neighbors_in_range(G, 0, 0)
    """
    return G.neighbors_in_range(n, t_from, t_to=t_to, mode=mode)


def interactions_in_range(G, nbunch=None, t_from=None, t_to=None, mode='any', min_count=1):
    """
    Return interactions observed within a time interval.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.interactions_in_range(G, t_from=0, t_to=0)
    """
    return G.interactions_in_range(nbunch=nbunch, t_from=t_from, t_to=t_to, mode=mode, min_count=min_count)


def window_slices(G, window, step=1, include_partial=False):
    """
    Iterate over sliding temporal subgraphs.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> list(dn.window_slices(G, window=1))
    """
    return G.window_slices(window, step=step, include_partial=include_partial)


def to_networkx_graph(G, t=None):
    """
    Convert ``G`` to a static NetworkX graph.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.to_networkx_graph(G, t=0)
    """
    return G.to_networkx_graph(t=t)


def temporal_snapshots_ids(G):
    """
    Return the ordered list of snapshot ids present in the dynamic graph.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.add_path([0,4,5,6], t=1)
        >>> G.add_path([7,1,2,3], t=2)
        >>> dn.temporal_snapshots(G)
        [0, 1, 2]
    """
    return G.temporal_snapshots_ids()


def interactions_per_snapshots(G, t=None):
    """
    Return the number of interactions within snapshot t.
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.add_path([0,4,5,6], t=1)
        >>> G.add_path([7,1,2,3], t=2)
        >>> dn.number_of_interactions(G, t=0)
        3
        >>> dn.interactions_per_snapshots(G)
        {0: 3, 1: 3, 2: 3}
    """
    return G.interactions_per_snapshots(t)


def inter_event_time_distribution(G, u=None, v=None):
    """
    Return the distribution of inter event time. If u and v are None the dynamic graph intere event distribution is returned. If u is specified the inter event time distribution of interactions involving u is returned. If u and v are specified the inter event time distribution of (u, v) interactions is returned
    
    Example::
    
    
    
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> dn.inter_event_time_distribution(G)
    """
    return G.inter_event_time_distribution(u, v)
