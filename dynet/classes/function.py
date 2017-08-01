from __future__ import division

from collections import Counter
from itertools import chain
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import networkx as nx


__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"


__all__ = ['nodes', 'edges', 'degree', 'degree_histogram', 'neighbors',
           'number_of_nodes', 'number_of_edges', 'density',
           'is_directed', 'freeze', 'is_frozen', 'subgraph',
           'add_star', 'add_path', 'add_cycle',
           'create_empty_copy', 'set_node_attributes',
           'get_node_attributes', 'set_edge_attributes',
           'get_edge_attributes', 'all_neighbors', 'non_neighbors',
           'non_edges', 'is_empty', 'time_slice', 'stream_edges']


def nodes(G, t=None):
    return G.nodes(t)


def edges(G, nbunch=None, t=None):
    return G.edges(nbunch, t=t)


def degree(G, nbunch=None, t=None):
    return G.degree(nbunch, t)


def neighbors(G, n, t=None):
    return G.neighbors(n, t)


def number_of_nodes(G, t=None):
    return G.number_of_nodes(t)


def number_of_edges(G, t=None):
    return G.number_of_edges(t)


def density(G, t=None):
    n = number_of_nodes(G, t)
    m = number_of_edges(G, t)
    if m == 0 or n <= 1:
        return 0
    d = m / (n * (n - 1))
    if not G.is_directed():
        d *= 2
    return d


def degree_histogram(G, t):
    counts = Counter(d for n, d in G.degree(t))
    return [counts.get(i, 0) for i in range(max(counts) + 1)]


def is_directed(G):
    return G.is_directed()


def frozen(*args):
    raise nx.NetworkXError("Frozen graph can't be modified")


def freeze(G):
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
    try:
        return G.frozen
    except AttributeError:
        return False


def add_star(G, nodes, t, **attr):
    nlist = iter(nodes)
    v = next(nlist)
    edges = ((v, n) for n in nlist)
    G.add_edges_from(edges, t, **attr)


def add_path(G, nodes, t, **attr):
    nlist = list(nodes)
    edges = zip(nlist[:-1], nlist[1:])
    G.add_edges_from(edges, t, **attr)


def add_cycle(G, nodes, t, **attr):
    nlist = list(nodes)
    edges = zip(nlist, nlist[1:] + [nlist[0]])
    G.add_edges_from(edges, t, **attr)


def subgraph(G, nbunch):
    return G.subgraph(nbunch)


def create_empty_copy(G, with_data=True):
    H = G.__class__()
    H.add_nodes_from(G.nodes(data=with_data))
    if with_data:
        H.graph.update(G.graph)
    return H


def set_node_attributes(G, values, name=None):
    # Set node attributes based on type of `values`
    if name is not None:  # `values` must not be a dict of dict
        try:  # `values` is a dict
            for n, v in values.items():
                try:
                    G.node[n][name] = values[n]
                except KeyError:
                    pass
        except AttributeError:  # `values` is a constant
            for n in G:
                G.node[n][name] = values
    else:  # `values` must be dict of dict
        for n, d in values.items():
            try:
                G.node[n].update(d)
            except KeyError:
                pass


def get_node_attributes(G, name):
    return {n: d[name] for n, d in G.node.items() if name in d}


def set_edge_attributes(G, values, name=None):
    if name is not None:
        # `values` does not contain attribute names
        try:
            # if `values` is a dict using `.items()` => {edge: value}
            if G.is_multigraph():
                for (u, v, key), value in values.items():
                    try:
                        G[u][v][key][name] = value
                    except KeyError:
                        pass
            else:
                for (u, v), value in values.items():
                    try:
                        G[u][v][name] = value
                    except KeyError:
                        pass
        except AttributeError:
            # treat `values` as a constant
            for u, v, data in G.edges(data=True):
                data[name] = values
    else:
        # `values` consists of doct-of-dict {edge: {attr: value}} shape
        if G.is_multigraph():
            for (u, v, key), d in values.items():
                try:
                    G[u][v][key].update(d)
                except KeyError:
                    pass
        else:
            for (u, v), d in values.items():
                try:
                    G[u][v].update(d)
                except KeyError:
                    pass


def get_edge_attributes(G, name):
    if G.is_multigraph():
        edges = G.edges(keys=True, data=True)
    else:
        edges = G.edges(data=True)
    return {x[:-1]: x[-1][name] for x in edges if name in x[-1]}


def all_neighbors(graph, node, t=None):
    if graph.is_directed():
        values = chain(graph.predecessors(node), graph.successors(node))
    else:
        values = graph.neighbors(node, t=t)
    return values


def non_neighbors(graph, node, t=None):
    nbors = set(neighbors(graph, node, t=t)) | {node}
    return (nnode for nnode in graph if nnode not in nbors)


def non_edges(graph, t=None):
    if graph.is_directed():
        for u in graph:
            for v in non_neighbors(graph, u, t):
                yield (u, v)
    else:
        nodes = set(graph)
        while nodes:
            u = nodes.pop()
            for v in nodes - set(graph[u]):
                yield (u, v)


def is_empty(G):
    return not any(G._adj.values())


def time_slice(G, t_from, t_to=None):
    return G.time_slice(t_from, t_to)


def stream_edges(G):
    return G.stream_edges()
