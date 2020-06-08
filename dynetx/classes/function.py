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
           'temporal_snapshots_ids', 'inter_event_time_distribution']


def nodes(G, t=None):
    """Return a list of the nodes in the graph at a given snapshot.

            Parameters
            ----------

            G : Graph opject
                DyNetx graph object

            t : snapshot id (default=None)
                If None the the method returns all the nodes of the flattened graph.

            Returns
            -------
            nlist : list
                A list of nodes.  If data=True a list of two-tuples containing
                (node, node data dictionary).

            Examples
            --------
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
    """Return the list of edges present in a given snapshot.

           Edges are returned as tuples
           in the order (node, neighbor).

           Parameters
           ----------

           G : Graph opject
                DyNetx graph object

           nbunch : iterable container, optional (default= all nodes)
               A container of nodes.  The container will be iterated
               through once.

           t : snapshot id (default=None)
               If None the the method returns all the edges of the flattened graph.

           Returns
           --------
           edge_list: list of edge tuples
               Edges that are adjacent to any node in nbunch, or a list
               of all edges if nbunch is not specified.

           Notes
           -----
           Nodes in nbunch that are not in the graph will be (quietly) ignored.
           For directed graphs this returns the out-edges.

           Examples
           --------
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
    """Return the degree of a node or nodes at time t.

            The node degree is the number of edges adjacent to that node.

            Parameters
            ----------

            G : Graph opject
                DyNetx graph object

            nbunch : iterable container, optional (default=all nodes)
                A container of nodes.  The container will be iterated
                through once.

            t : snapshot id (default=None)
                If None will be returned the degree of nodes on the flattened graph.


            Returns
            -------
            nd : dictionary, or number
                A dictionary with nodes as keys and degree as values or
                a number if a single node is specified.

            Examples
            --------
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
    """Return a list of the nodes connected to the node n at time t.

            Parameters
            ----------

            G : Graph opject
                DyNetx graph object

            n : node
               A node in the graph

            t : snapshot id (default=None)
                If None will be returned the neighbors of the node on the flattened graph.


            Returns
            -------
            nlist : list
                A list of nodes that are adjacent to n.

            Raises
            ------
            NetworkXError
                If the node n is not in the graph.

            Examples
            --------
            >>> G = dn.DynGraph()
            >>> G.add_path([0,1,2,3], t=0)
            >>> dn.neighbors(G, 0, t=0)
            [1]
            >>> dn.neighbors(G, 0, t=1)
            []
            """
    return G.neighbors(n, t)


def number_of_nodes(G, t=None):
    """Return the number of nodes in the t snpashot of a dynamic graph.

            Parameters
            ----------

            G : Graph opject
                DyNetx graph object

            t : snapshot id (default=None)
                   If None return the number of nodes in the flattened graph.


            Returns
            -------
            nnodes : int
                The number of nodes in the graph.

            See Also
            --------
            order  which is identical

            Examples
            --------
            >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
            >>> G.add_path([0,1,2], t=0)
            >>> dn.number_of_nodes(G, 0)
            3
            """
    return G.number_of_nodes(t)


def number_of_interactions(G, u=None, v=None, t=None):
    """Return the number of edges between two nodes at time t.

        Parameters
        ----------
        G : a dynetx graph object
        u : node, optional (default=all edges)
        v : node, optional (default=all edges)
        t : snapshot id (default=None)
            If None will be returned the number of edges on the flattened graph.

        If u and v are specified, return the number of edges between u and v.
        Otherwise return the total number of all edges.

        Returns
        -------
        nedges : int
            The number of edges in the graph.  If nodes u and v are specified
            return the number of edges between those nodes.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> dn.number_of_interactions(G, t=0)
        """
    return G.number_of_interactions(u, v, t)


def density(G, t=None):
    r"""Return the density of a graph at timestamp t.
        The density for undirected graphs is

        .. math::
           d = \frac{2m}{n(n-1)},

        and for directed graphs is

        .. math::
           d = \frac{m}{n(n-1)},

        where `n` is the number of nodes and `m`  is the number of edges in `G`.

        Parameters
        ----------

        G : Graph opject
            DyNetx graph object


        t : snapshot id (default=None)
            If None the density will be computed on the flattened graph.


        Notes
        -----

        The density is 0 for a graph without edges and 1 for a complete graph.

        Self loops are counted in the total number of edges so graphs with self
        loops can have density higher than 1.
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
    """Return a list of the frequency of each degree value.

        Parameters
        ----------

        G : Graph opject
            DyNetx graph object


        t : snapshot id (default=None)
            snapshot id


        Returns
        -------
        hist : list
           A list of frequencies of degrees.
           The degree values are the index in the list.

        Notes
        -----
        Note: the bins are width one, hence len(list) can be large
        (Order(number_of_edges))
        """
    counts = Counter(d for n, d in G.degree(t=t).items())
    return [counts.get(i, 0) for i in range(max(counts) + 1)]


def is_directed(G):
    """ Return True if graph is directed."""
    return G.is_directed()


def frozen():
    """Dummy method for raising errors when trying to modify frozen graphs"""
    raise nx.NetworkXError("Frozen graph can't be modified")


def freeze(G):
    """Modify graph to prevent further change by adding or removing nodes or edges.

        Node and edge data can still be modified.

        Parameters
        ----------

            G : graph
                A NetworkX graph


        Notes
        -----
        To "unfreeze" a graph you must make a copy by creating a new graph object.

        See Also
        --------
        is_frozen
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
    """Return True if graph is frozen.

        Parameters
        ----------
            G : graph
                A DyNetx graph

        See Also
        --------
        freeze
        """
    try:
        return G.frozen
    except AttributeError:
        return False


def add_star(G, nodes, t, **attr):
    """Add a star at time t.

        The first node in nodes is the middle of the star.  It is connected
        to all other nodes.

        Parameters
        ----------
        G : graph
            A DyNetx graph

        nodes : iterable container
            A container of nodes.

        t : snapshot id (default=None)
            snapshot id

        See Also
        --------
        add_path, add_cycle

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> dn.add_star(G, [0,1,2,3], t=0)
    """
    nlist = iter(nodes)
    v = next(nlist)
    edges = ((v, n) for n in nlist)
    G.add_interactions_from(edges, t, **attr)


def add_path(G, nodes, t, **attr):
    """Add a path at time t.

            Parameters
            ----------
            G : graph
                A DyNetx graph

            nodes : iterable container
                A container of nodes.

            t : snapshot id (default=None)
                snapshot id

            See Also
            --------
            add_path, add_cycle

            Examples
            --------
            >>> G = dn.DynGraph()
            >>> dn.add_path(G, [0,1,2,3], t=0)
            """
    nlist = list(nodes)
    edges = zip(nlist[:-1], nlist[1:])
    G.add_interactions_from(edges, t, **attr)


def add_cycle(G, nodes, t, **attr):
    """Add a cycle at time t.

            Parameters
            ----------

            G : graph
                A DyNetx graph

            nodes : iterable container
                A container of nodes.

            t : snapshot id (default=None)
                snapshot id

            See Also
            --------
            add_path, add_cycle

            Examples
            --------
            >>> G = dn.DynGraph()
            >>> dn.add_cycle(G, [0,1,2,3], t=0)
            """
    nlist = list(nodes)
    edges = zip(nlist, nlist[1:] + [nlist[0]])
    G.add_interactions_from(edges, t, **attr)


def subgraph(G, nbunch):
    """Return the subgraph induced on nodes in nbunch.

        Parameters
        ----------
        G : graph
           A DyNetx graph

        nbunch : list, iterable
           A container of nodes that will be iterated through once (thus
           it should be an iterator or be iterable).  Each element of the
           container should be a valid node type: any hashable type except
           None.  If nbunch is None, return all edges data in the graph.
           Nodes in nbunch that are not in the graph will be (quietly)
           ignored.

    """
    return G.subgraph(nbunch)


def create_empty_copy(G, with_data=True):
    """Return a copy of the graph G with all of the edges removed.
        Parameters
        ----------

        G : graph
           A DyNetx graph

        with_data :  bool (default=True)
           Include data.

        Notes
        -----
        Graph and edge data is not propagated to the new graph.
        """
    H = G.__class__()
    H.add_nodes_from(G.nodes(data=with_data))
    if with_data:
        H.graph.update(G.graph)
    return H


def set_node_attributes(G, values, name=None):
    """Set node attributes from dictionary of nodes and values

        Parameters
        ----------
        G : DyNetx Graph

        name : string
           Attribute name

        values: dict
           Dictionary of attribute values keyed by node. If `values` is not a
           dictionary, then it is treated as a single attribute value that is then
           applied to every node in `G`.

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
    """Get node attributes from graph

        Parameters
        ----------
        G : DyNetx Graph

        name : string
           Attribute name

        Returns
        -------
        Dictionary of attributes keyed by node.
    """
    return {n: d[name] for n, d in G._node.items() if name in d}


@not_implemented()
def set_edge_attributes(values, name=None):
    pass


@not_implemented()
def get_edge_attributes(G, name):
    pass


def all_neighbors(graph, node, t=None):
    """ Returns all of the neighbors of a node in the graph at time t.

        If the graph is directed returns predecessors as well as successors.

        Parameters
        ----------

        graph : DyNetx graph
            Graph to find neighbors.

        node : node
            The node whose neighbors will be returned.

        t : snapshot id (default=None)
            If None the neighbors are identified on the flattened graph.

        Returns
        -------

        neighbors : iterator
            Iterator of neighbors
    """
    if graph.is_directed():
        values = chain(graph.predecessors(node, t=t), graph.successors(node, t=t))
    else:
        values = graph.neighbors(node, t=t)
    return values


def non_neighbors(graph, node, t=None):
    """Returns the non-neighbors of the node in the graph at time t.

        Parameters
        ----------
        graph : DyNetx graph
            Graph to find neighbors.

        node : node
            The node whose neighbors will be returned.

        t : snapshot id (default=None)
            If None the non-neighbors are identified on the flattened graph.


        Returns
        -------
        non_neighbors : iterator
            Iterator of nodes in the graph that are not neighbors of the node.
        """
    if graph.is_directed():
        values = chain(graph.predecessors(node, t=t), graph.successors(node, t=t))
    else:
        values = graph.neighbors(node, t=t)

    nbors = set(values) | {node}
    return (nnode for nnode in graph if nnode not in nbors)


def non_interactions(graph, t=None):
    """Returns the non-existent edges in the graph at time t.

        Parameters
        ----------

        graph : NetworkX graph.
            Graph to find non-existent edges.

        t : snapshot id (default=None)
            If None the non-existent edges are identified on the flattened graph.


        Returns
        -------
        non_edges : iterator
        Iterator of edges that are not in the graph.
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
    """Returns ``True`` if ``G`` has no edges.

        Parameters
        ----------

        G : graph
            A DyNetx graph.

        Returns
        -------

        bool
            ``True`` if ``G`` has no edges, and ``False`` otherwise.

        Notes
        -----
        An empty graph can have nodes but not edges. The empty graph with zero
        nodes is known as the null graph. This is an O(n) operation where n is the
        number of nodes in the graph.
        """
    return not any(G.adj.values())


def time_slice(G, t_from, t_to=None):
    """Return an iterator for (node, degree) at time t.

                The node degree is the number of edges adjacent to the node.

                Parameters
                ----------

                G : graph
                    A DyNetx graph.

                t_from : snapshot id, mandatory

                t_to : snapshot id, optional (default=None)
                    If None t_to will be set equal to t_from

                Returns
                -------
                H : a DynGraph object
                    the graph described by interactions in [t_from, t_to]

                Examples
                --------
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
    return G.time_slice(t_from, t_to)


def stream_interactions(G):
    """Generate a temporal ordered stream of interactions.

            Parameters
            ----------

            G : graph
                A DyNetx graph.

            Returns
            -------

            nd_iter : an iterator
                The iterator returns a 4-tuples of (node, node, op, timestamp).

            Examples
            --------
            >>> import dynetx as dn
            >>> G = dn.DynGraph()
            >>> G.add_path([0,1,2,3], t=0)
            >>> G.add_path([3,4,5,6], t=1)
            >>> list(dn.stream_interactions(G))
            [(0, 1, '+', 0), (1, 2, '+', 0), (2, 3, '+', 0), (3, 4, '+', 1), (4, 5, '+', 1), (5, 6, '+', 1)]
            """
    return G.stream_interactions()


def temporal_snapshots_ids(G):
    """Return the ordered list of snapshot ids present in the dynamic graph.

        Parameters
        ----------

        G : graph
            A DyNetx graph.

        Returns
        -------

        nd : list
            a list of snapshot ids

        Examples
        --------
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
    """Return the number of interactions within snapshot t.

        Parameters
        ----------

        G : graph
            A DyNetx graph.

        t : snapshot id (default=None)
            If None will be returned total number of interactions across all snapshots

        Returns
        -------

        nd : dictionary, or number
            A dictionary with snapshot ids as keys and interaction count as values or
            a number if a single snapshot id is specified.

        Examples
        --------
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
    """Return the distribution of inter event time.
     If u and v are None the dynamic graph intere event distribution is returned.
     If u is specified the inter event time distribution of interactions involving u is returned.
     If u and v are specified the inter event time distribution of (u, v) interactions is returned

     Parameters
     ----------
     G : graph
            A DyNetx graph.
     u : node id
     v : node id

     Returns
     -------

     nd : dictionary
         A dictionary from inter event time to number of occurrences
    """
    return G.inter_event_time_distribution(u, v)
