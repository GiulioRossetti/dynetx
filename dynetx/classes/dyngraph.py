"""Base class for undirected dynamic graphs.

The DynGraph class allows any hashable object as a node.
Of each interaction needs be specified the set of timestamps of its presence.

Self-loops are allowed.
"""
from typing import List, Any

import networkx as nx
from collections import defaultdict
from dynetx.utils import not_implemented
from dynetx.utils.validation import normalize_time_range, inclusive_end_to_exclusive
from copy import deepcopy
from itertools import combinations

__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"


class DynGraph(nx.Graph):
    """
    Base class for undirected dynamic graphs.

    A DynGraph stores nodes and timestamped interaction.

    DynGraph hold undirected interaction.  Self loops are allowed.

    Nodes can be arbitrary (hashable) Python objects with optional
    key/value attributes.

    Parameters
    ----------
    data : input graph
        Data to initialize graph.  If data=None (default) an empty
        graph is created.  The data can be an interaction list, or any
        NetworkX graph object.

    attr : keyword arguments, optional (default= no attributes)
        Attributes to add to graph as key=value pairs.

    edge_removal : bool, optional (default=True)
        Specify if the dynamic graph instance should allows edge removal or not.

    See Also
    --------
    DynDiGraph

    Examples
    --------
    Create an empty graph structure (a "null graph") with no nodes and
    no interactions.

    >>> import dynetx as dn
    >>> G = dn.DynGraph()

    G can be grown in several ways.

    **Nodes:**

    Add one node at a time:

    >>> G.add_node(1)

    Add the nodes from any container (a list, dict, set or
    even the lines from a file or the nodes from another graph).

    >>> G.add_nodes_from([2,3])
    >>> G.add_nodes_from(range(100,110))
    >>> H=dn.DynGraph()
    >>> H.add_path([0,1,2,3,4,5,6,7,8,9], t=0)
    >>> G.add_nodes_from(H)

    In addition to strings and integers any hashable Python object
    (except None) can represent a node.

    >>> G.add_node(H)

    **Edges:**

    G can also be grown by adding interaction and specifying their timestamp.

    Add one interaction,

    >>> G.add_interaction(1, 2, t=0)

    a list of interaction

    >>> G.add_interactions_from([(3, 2), (1,3)], t=1)

    If some interaction connect nodes not yet in the graph, the nodes
    are added automatically.

    To traverse all interactions of a graph a time t use the interactions(t) method.

    >>> G.interactions(t=1)
    [(3, 2), (1, 3)]
    """

    def __init__(self, data=None, edge_removal=True, **attr):
        """Initialize a graph with interaction, name, graph attributes.

        Parameters
        ----------
        data : input graph
            Data to initialize graph.  If data=None (default) an empty
            graph is created.  The data can be an interaction list, or any
            NetworkX/DyNetx graph object.  If the corresponding optional Python
            packages are installed the data can also be a NumPy matrix
            or 2d ndarray, a SciPy sparse matrix, or a PyGraphviz graph.
        edge_removal : bool, optional (default=True)
            Specify if the dynamic graph instance should allows edge removal or not.
        attr : keyword arguments, optional (default= no attributes)
            Attributes to add to graph as key=value pairs.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G1 = dn.DynGraph(edge_removal=True)
        """
        super(DynGraph, self).__init__(data, **attr)
        self.time_to_edge = defaultdict(int)
        self.snapshots = {}
        self.edge_removal = edge_removal
        self.directed = False

    def nodes_iter(self, t=None, data=False):
        """Return an iterator over the nodes with respect to a given temporal snapshot.

        Parameters
        ----------
        t : snapshot id (default=None).
            If None the iterator returns all the nodes of the flattened graph.

        data: node data(default=False)

        Returns
        -------
        niter : iterator
            An iterator over nodes.  If data=True the iterator gives
            two-tuples containing (node, node data, dictionary)

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
        >>> G.add_path([0,1,2], 0)

        >>> [n for n, d in G.nodes_iter(t=0)]
        [0, 1, 2]
        """
        if t is not None:
            if not data:
                return [n for n, d in self.degree(t=t).items() if d > 0]
            else:
                return {n: self._node[n] for n, d in self.degree(t=t).items() if d > 0}

        if not data:
            return iter(self._node)
        else:
            return self._node

    def nodes(self, t=None, data=False):
        """Return a list of the nodes in the graph at a given snapshot.

        Parameters
        ----------
        t : snapshot id (default=None)
            If None the the method returns all the nodes of the flattened graph.
        data : boolean, optional (default=False)
               If False return a list of nodes.  If True return a
               two-tuple of node and node data dictionary

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
        >>> G.nodes(t=0)
        [0, 1, 2]
        >>> G.add_edge(1, 4, t=1)
        >>> G.nodes(t=0)
        [0, 1, 2]
        """

        if data:
            return [(k, v) for k, v in self.nodes_iter(t=t, data=data).items()]
        else:
            return [k for k in self.nodes_iter(t=t, data=data)]

    def interactions(self, nbunch=None, t=None):
        """Return the list of interaction present in a given snapshot.

        Edges are returned as tuples
        in the order (node, neighbor).

        Parameters
        ----------
        nbunch : iterable container, optional (default= all nodes)
            A container of nodes.  The container will be iterated
            through once.
        t : snapshot id (default=None)
            If None the the method returns all the edges of the flattened graph.

        Returns
        --------
        interaction_list: list of interaction tuples
            Interactions that are adjacent to any node in nbunch, or a list
            of all interactions if nbunch is not specified.

        See Also
        --------
        edges_iter : return an iterator over the interactions

        Notes
        -----
        Nodes in nbunch that are not in the graph will be (quietly) ignored.
        For directed graphs this returns the out-interaction.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2], t=0)
        >>> G.add_edge(2,3, t=1)
        >>> G.interactions(t=0)
        [(0, 1), (1, 2)]
        >>> G.interactions()
        [(0, 1), (1, 2), (2, 3)]
        >>> G.interactions([0,3], t=0)
        [(0, 1)]
        """
        return list(self.interactions_iter(nbunch, t))

    def __presence_test(self, u, v, t):
        spans = self._adj[u][v]['t']
        if self.edge_removal:
            for s in spans:
                if s[0] <= t <= s[1]:
                    return True
        else:
            if spans[0][0] <= t <= max(self.temporal_snapshots_ids()):
                return True

        return False

    def interactions_iter(self, nbunch=None, t=None):
        """Return an iterator over the interaction present in a given snapshot.

        Edges are returned as tuples
        in the order (node, neighbor).

        Parameters
        ----------
        nbunch : iterable container, optional (default= all nodes)
            A container of nodes.  The container will be iterated
            through once.
        t : snapshot id (default=None)
            If None the the method returns an iterator over the edges of the flattened graph.

        Returns
        -------
        edge_iter : iterator
            An iterator of (u,v) tuples of interaction.

        See Also
        --------
        interaction : return a list of interaction

        Notes
        -----
        Nodes in nbunch that are not in the graph will be (quietly) ignored.
        For directed graphs this returns the out-interaction.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2], 0)
        >>> G.add_interaction(2,3,1)
        >>> [e for e in G.interactions_iter(t=0)]
        [(0, 1), (1, 2)]
        >>> list(G.interactions_iter())
        [(0, 1), (1, 2), (2, 3)]
        """
        seen = {}  # helper dict to keep track of multiply stored interactions
        if nbunch is None:
            nodes_nbrs = self._adj.items()
        else:
            nodes_nbrs = ((n, self._adj[n]) for n in self.nbunch_iter(nbunch))

        for n, nbrs in nodes_nbrs:
            for nbr in nbrs:
                if t is not None:
                    if nbr not in seen and self.__presence_test(n, nbr, t):
                        yield n, nbr, {"t": [t]}
                else:
                    if nbr not in seen:
                        yield n, nbr, self._adj[n][nbr]
            seen[n] = 1
        del seen

    def add_interaction(self, u, v, t=None, e=None, **attr):
        """Add an interaction between u and v at time t vanishing (optional) at time e.

        The nodes u and v will be automatically added if they are
        not already in the graph.

        Parameters
        ----------
        u, v : nodes
            Nodes can be, for example, strings or numbers.
            Nodes must be hashable (and not None) Python objects.
        t : appearance snapshot id, mandatory
        e : vanishing snapshot id, optional (default=None)

        See Also
        --------
        add_edges_from : add a collection of interaction at time t

        Notes
        -----
        Adding an interaction that already exists but with different snapshot id updates the interaction data.

        Examples
        --------
        The following all add the interaction e=(1,2, 0) to graph G:
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(1, 2, 0)           # explicit two-node form
        >>> G.add_interaction( [(1,2)], t=0 ) # add interaction from iterable container

        Specify the vanishing of the interaction

        >>>> G.add_interaction(1, 3, t=1, e=10)

        will produce an interaction present in snapshots [0, 9]
        """
        if t is None:
            raise nx.NetworkXError(
                "The t argument must be specified.")

        if u not in self._node:
            self._adj[u] = self.adjlist_inner_dict_factory()
            self._node[u] = {}
        if v not in self._node:
            self._adj[v] = self.adjlist_inner_dict_factory()
            self._node[v] = {}

        raw_t = t
        if not isinstance(t, list):
            t = [t, t]

        for idt in [t[0]]:
            if self.has_edge(u, v) and not self.edge_removal:
                continue
            else:
                if idt not in self.time_to_edge:
                    self.time_to_edge[idt] = {(u, v, "+"): None}
                else:
                    if (u, v, "+") not in self.time_to_edge[idt]:
                        self.time_to_edge[idt][(u, v, "+")] = None

        if e is not None and self.edge_removal:

            t[1] = e - 1
            if e not in self.time_to_edge:
                self.time_to_edge[e] = {(u, v, "-"): None}
            else:
                self.time_to_edge[e][(u, v, "-")] = None

        # add the interaction
        datadict = self._adj[u].get(v, self.edge_attr_dict_factory())

        if 't' in datadict:
            app = datadict['t']
            max_end = app[-1][1]

            if max_end == app[-1][0] and t[0] == app[-1][0] + 1:

                app[-1] = [app[-1][0], t[1]]
                if app[-1][0] + 1 in self.time_to_edge and (u, v, "+") in self.time_to_edge[app[-1][0] + 1]:
                    del self.time_to_edge[app[-1][0] + 1][(u, v, "+")]

            else:
                if t[0] < app[-1][0]:
                    raise ValueError("The specified interaction extension is broader than "
                                     "the ones already present for the given nodes.")

                if t[0] <= max_end < t[1]:
                    app[-1][1] = t[1]
                    if max_end + 1 in self.time_to_edge:
                        if self.edge_removal:
                            del self.time_to_edge[max_end + 1][(u, v, "-")]
                        del self.time_to_edge[t[0]][(u, v, "+")]

                elif max_end == t[0] - 1:
                    if max_end + 1 in self.time_to_edge and (u, v, "+") in self.time_to_edge[max_end + 1]:
                        del self.time_to_edge[max_end + 1][(u, v, "+")]
                        if self.edge_removal:
                            if max_end + 1 in self.time_to_edge and (u, v, '-') in self.time_to_edge[max_end + 1]:
                                del self.time_to_edge[max_end + 1][(u, v, '-')]
                            if t[1] + 1 in self.time_to_edge:
                                self.time_to_edge[t[1] + 1][(u, v, "-")] = None
                            else:
                                self.time_to_edge[t[1] + 1] = {(u, v, "-"): None}

                    app[-1][1] = t[1]
                else:
                    app.append(t)
        else:
            datadict['t'] = [t]

        if attr:
            datadict.update(attr)

        if e is not None:
            span = range(t[0], t[1] + 1)
            for idt in span:
                if idt not in self.snapshots:
                    self.snapshots[idt] = 1
                else:
                    self.snapshots[idt] += 1
        else:
            tids = raw_t if isinstance(raw_t, list) else [raw_t]
            for idt in tids:
                if idt is not None:
                    if idt not in self.snapshots:
                        self.snapshots[idt] = 1
                    else:
                        self.snapshots[idt] += 1

        self._adj[u][v] = datadict
        self._adj[v][u] = datadict

    def add_interactions_from(self, ebunch, t=None, e=None, **attr):
        """Add all the interaction in ebunch at time t.

        Parameters
        ----------
        ebunch : container of interaction
            Each interaction given in the container will be added to the
            graph. The interaction must be given as as 2-tuples (u,v) or
            3-tuples (u,v,d) where d is a dictionary containing interaction
            data.
        t : appearance snapshot id, mandatory
        e : vanishing snapshot id, optional

        See Also
        --------
        add_edge : add a single interaction

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_edges_from([(0,1),(1,2)], t=0)
        """
        # set up attribute dict
        if t is None:
            raise nx.NetworkXError(
                "The t argument must be a specified.")
        # process ebunch
        for ed in ebunch:
            if len(ed) == 2:
                self.add_interaction(ed[0], ed[1], t, e, **attr)
            elif len(ed) == 3 and isinstance(ed[2], dict):
                edge_attr = dict(attr)
                edge_attr.update(ed[2])
                self.add_interaction(ed[0], ed[1], t, e, **edge_attr)
            else:
                raise nx.NetworkXError("Each interaction must be a 2-tuple or 3-tuple with attribute dict.")

    def number_of_interactions(self, u=None, v=None, t=None):
        """Return the number of interaction between two nodes at time t.

        Parameters
        ----------
        u, v : nodes, optional (default=all interaction)
            If u and v are specified, return the number of interaction between
            u and v. Otherwise return the total number of all interaction.
        t : snapshot id (default=None)
            If None will be returned the number of edges on the flattened graph.


        Returns
        -------
        nedges : int
            The number of interaction in the graph.  If nodes u and v are specified
            return the number of interaction between those nodes. If a single node is specified return None.

        See Also
        --------
        size

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.number_of_interactions()
        3
        >>> G.number_of_interactions(0,1, t=0)
        1
        >>> G.add_edge(3, 4, t=1)
        >>> G.number_of_interactions()
        4
        """
        if t is None:
            if u is None:
                return int(self.size())
            elif u is not None and v is not None:
                if u in self._adj and v in self._adj[u]:
                    return 1
                else:
                    return 0
        else:
            if u is None:
                return int(self.size(t))
            elif u is not None and v is not None:
                if u in self._adj and v in self._adj[u]:
                    if self.__presence_test(u, v, t):
                        return 1
                    else:
                        return 0

    def has_interaction(self, u, v, t=None):
        """Return True if the interaction (u,v) is in the graph at time t.

        Parameters
        ----------
        u, v : nodes
            Nodes can be, for example, strings or numbers.
            Nodes must be hashable (and not None) Python objects.
        t : snapshot id (default=None)
            If None will be returned the presence of the interaction on the flattened graph.


        Returns
        -------
        edge_ind : bool
            True if interaction is in the graph, False otherwise.

        Examples
        --------
        Can be called either using two nodes u,v or interaction tuple (u,v)
        >>> import dynetx as dn
        >>> G = nx.Graph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.has_interaction(0,1, t=0)
        True
        >>> G.has_interaction(0,1, t=1)
        False
        """
        try:
            if t is None:
                return v in self._adj[u]
            else:
                return v in self._adj[u] and self.__presence_test(u, v, t)
        except KeyError:
            return False

    def neighbors(self, n, t=None):
        """Return a list of the nodes connected to the node n at time t.

        Parameters
        ----------
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
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.neighbors(0, t=0)
        [1]
        >>> G.neighbors(0, t=1)
        []
        """
        try:
            if t is None:
                return list(self._adj[n])
            else:
                if n in self._adj:
                    return [i for i in self._adj[n] if self.__presence_test(n, i, t)]
                else:
                    return []
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def neighbors_iter(self, n, t=None):
        """Return an iterator over all neighbors of node n at time t.

        Parameters
        ----------
        n : node
           A node in the graph
        t : snapshot id (default=None)
            If None will be returned an iterator over the neighbors of the node on the flattened graph.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> [n for n in G.neighbors_iter(0, t=0)]
        [1]
        """
        try:
            if t is None:
                return iter(self._adj[n])
            else:
                return iter([i for i in self._adj[n] if self.__presence_test(n, i, t)])
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def degree(self, nbunch=None, t=None):
        """Return the degree of a node or nodes at time t.

        The node degree is the number of interaction adjacent to that node in a given time frame.

        Parameters
        ----------
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
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.degree(0, t=0)
        1
        >>> G.degree([0,1], t=1)
        {0: 0, 1: 0}
        >>> list(G.degree([0,1], t=0).values())
        [1, 2]
        """
        if nbunch in self:  # return a single node
            return next(self.degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.degree_iter(nbunch, t))

    def degree_iter(self, nbunch=None, t=None):
        """Return an iterator for (node, degree) at time t.

        The node degree is the number of edges adjacent to the node in a given timeframe.

        Parameters
        ----------
        nbunch : iterable container, optional (default=all nodes)
            A container of nodes.  The container will be iterated
            through once.

        t : snapshot id (default=None)
            If None will be returned an iterator over the degree of nodes on the flattened graph.


        Returns
        -------
        nd_iter : an iterator
            The iterator returns two-tuples of (node, degree).

        See Also
        --------
        degree

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> list(G.degree_iter(0, t=0))
        [(0, 1)]
        >>> list(G.degree_iter([0,1], t=0))
        [(0, 1), (1, 2)]
        """
        if nbunch is None:
            nodes_nbrs = self._adj.items()
        else:
            nodes_nbrs = ((n, self._adj[n]) for n in self.nbunch_iter(nbunch))

        if t is None:
            for n, nbrs in nodes_nbrs:
                deg = len(self._adj[n])
                yield n, deg
        else:
            for n, nbrs in nodes_nbrs:
                edges_t = len([v for v in nbrs.keys() if self.__presence_test(n, v, t)])
                if edges_t > 0:
                    yield n, edges_t
                else:
                    yield n, 0

    def size(self, t=None):
        """Return the number of edges at time t.

        Parameters
        ----------
        t : snapshot id (default=None)
            If None will be returned the size of the flattened graph.


        Returns
        -------
        nedges : int
            The number of edges

        See Also
        --------
        number_of_edges

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.size(t=0)
        3
        """
        s = sum(self.degree(t=t).values()) / 2
        return int(s)

    def number_of_nodes(self, t=None):
        """Return the number of nodes in the t snpashot of a dynamic graph.

        Parameters
        ----------
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
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2], t=0)
        >>> G.number_of_nodes(0)
        3
        """
        if t is None:
            return len(self._node)
        else:
            nds = sum([1 for n in self.degree(t=t).values() if n > 0])
            return nds

    def avg_number_of_nodes(self):
        """Return the number of nodes in the t snpashot of a dynamic graph.


            Returns
            -------
            nnodes : int
                The average number of nodes in the dynamic graph.


            Examples
            --------
            >>> import dynetx as dn
            >>> G = dn.DynGraph()
            >>> G.add_path([0,1,2], t=0)
            >>> G.add_path([0,1], t=1)
            >>> G.avg_number_of_nodes()
            2.5
        """
        nds = sum([self.number_of_nodes(t) for t in self.temporal_snapshots_ids()])
        return 0.0 if len(self.snapshots) == 0 else nds / len(self.snapshots)

    def order(self, t=None):
        """Return the number of nodes in the t snpashot of a dynamic graph.

        Parameters
        ----------
        t : snapshot id (default=None)
               If None return the number of nodes in the flattened graph.


        Returns
        -------
        nnodes : int
            The number of nodes in the graph.

        See Also
        --------
        number_of_nodes  which is identical

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
        >>> G.add_path([0,1,2], t=0)
        >>> G.order(0)
        3
        """
        return self.number_of_nodes(t)

    def has_node(self, n, t=None):
        """Return True if the graph, at time t, contains the node n.

        Parameters
        ----------
        n : node
        t : snapshot id, default None
            If None, return the presence of the node in the flattened graph.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()   # or DiGraph, MultiGraph, MultiDiGraph, etc
        >>> G.add_path([0,1,2], t=0)
        >>> G.has_node(0, t=0)
        True

        >>> 0 in G
        True

        """
        if t is None:
            try:
                return n in self._node
            except TypeError:
                return False
        else:
            deg = list(self.degree([n], t).values())
            if len(deg) > 0:
                return deg[0] > 0
            else:
                return False

    def add_star(self, nodes, t=None):
        """Add a star at time t.

        The first node in nodes is the middle of the star.  It is connected
        to all other nodes.

        Parameters
        ----------
        nodes : iterable container
            A container of nodes.
        t : snapshot id (default=None)

        See Also
        --------
        add_path, add_cycle

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_star([0,1,2,3], t=0)
        """
        nlist = list(nodes)
        v = nlist[0]
        interaction = ((v, n) for n in nlist[1:])
        self.add_interactions_from(interaction, t)

    def add_path(self, nodes, t=None):
        """Add a path at time t.

        Parameters
        ----------
        nodes : iterable container
            A container of nodes.
        t : snapshot id (default=None)

        See Also
        --------
        add_path, add_cycle

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        """
        nlist = list(nodes)
        interaction = zip(nlist[:-1], nlist[1:])
        self.add_interactions_from(interaction, t)

    def add_cycle(self, nodes, t=None):
        """Add a cycle at time t.

        Parameters
        ----------
        nodes : iterable container
            A container of nodes.
        t : snapshot id (default=None)

        See Also
        --------
        add_path, add_cycle

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_cycle([0,1,2,3], t=0)
        """
        nlist = list(nodes)
        interaction = zip(nlist, nlist[1:] + [nlist[0]])
        self.add_interactions_from(interaction, t)

    def to_directed(self, **kwargs):
        """Return a directed representation of the graph.

        Returns
        -------
        G : DynDiGraph
            A dynamic directed graph with the same name, same nodes, and with
            each edge (u,v,data) replaced by two directed edges
            (u,v,data) and (v,u,data).

        Notes
        -----
        This returns a "deepcopy" of the edge, node, and
        graph attributes which attempts to completely copy
        all of the data and references.

        This is in contrast to the similar D=DynDiGraph(G) which returns a
        shallow copy of the data.

        See the Python copy module for more information on shallow
        and deep copies, http://docs.python.org/library/copy.html.

        Warning: If you have subclassed Graph to use dict-like objects in the
        data structure, those changes do not transfer to the DynDiGraph
        created by this method.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()   # or MultiGraph, etc
        >>> G.add_path([0,1])
        >>> H = G.to_directed()
        >>> H.edges()
        [(0, 1), (1, 0)]

        If already directed, return a (deep) copy

        >>> G = dn.DynDiGraph()   # or MultiDiGraph, etc
        >>> G.add_path([0,1])
        >>> H = G.to_directed()
        >>> H.edges()
        [(0, 1)]
        """
        from .dyndigraph import DynDiGraph
        G = DynDiGraph()
        G.name = self.name
        G.add_nodes_from(self)
        events = []
        for it in self.interactions_iter():
            for t in it[2]['t']:
                events.append((it[0], it[1], t[0], t[1]))
        for u, v, t0, t1 in sorted(events, key=lambda x: (x[2], x[3], x[0], x[1])):
            G.add_interaction(u, v, t=t0, e=inclusive_end_to_exclusive(t1))

        G.graph = deepcopy(self.graph)
        G._node = deepcopy(self._node)
        return G

    def stream_interactions(self):
        """Generate a temporal ordered stream of interactions.


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
        >>> list(G.stream_interactions())
        [(0, 1, '+', 0), (1, 2, '+', 0), (2, 3, '+', 0), (3, 4, '+', 1), (4, 5, '+', 1), (5, 6, '+', 1)]
        """
        timestamps = sorted(self.time_to_edge.keys())
        for t in timestamps:
            for e in self.time_to_edge[t]:
                yield e[0], e[1], e[2], t

    def time_slice(self, t_from, t_to=None, **kwargs):
        """Return a new graph containing nodes and interactions present in
        ``[t_from, t_to]``.

        Parameters
        ----------
        t_from : snapshot id
            Start of the slice.
        t_to : snapshot id, optional
            End of the slice. If omitted, ``t_to`` is set equal to ``t_from``.

        Returns
        -------
        DynGraph
            Graph described by interactions in ``[t_from, t_to]``.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_path([0, 1, 2, 3], t=0)
        >>> G.add_path([0, 4, 5, 6], t=1)
        >>> H = G.time_slice(0, 1)
        >>> H.interactions()
        [(0, 1), (1, 2), (1, 3), (0, 4), (4, 5), (5, 6)]

        Additional keyword arguments
        ---------------------------
        node_filter : callable or mapping, optional
            Filter applied to node attributes before they are copied into the
            slice.
        edge_filter : callable or mapping, optional
            Filter applied to edge attributes before an interaction interval is
            copied into the slice.
        include_isolated : bool, optional
            If ``True``, keep nodes selected by ``node_filter`` even when they
            have no surviving interactions in the slice.
        """
        # create new graph and copy subgraph into it
        H = self.__class__()
        t_from, t_to = normalize_time_range(t_from, t_to)

        node_filter = kwargs.pop("node_filter", None)
        edge_filter = kwargs.pop("edge_filter", None)
        include_isolated = kwargs.pop("include_isolated", False)
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise TypeError("Unexpected keyword arguments: {}".format(unknown))

        def _matches_filter(spec, *args):
            if spec is None:
                return True
            if callable(spec):
                return bool(spec(*args))
            if hasattr(spec, "items"):
                attrs = args[-1]
                return all(attrs.get(k) == v for k, v in spec.items())
            raise TypeError("Filters must be callables or mappings")

        for u, v, ts in self.interactions_iter():
            edge_attrs = {k: val for k, val in ts.items() if k != 't'}
            if not (_matches_filter(node_filter, u, self._node.get(u, {})) and _matches_filter(node_filter, v, self._node.get(v, {}))):
                continue
            if not _matches_filter(edge_filter, u, v, edge_attrs):
                continue
            i_to = t_to
            f_from = t_from
            for a, b in ts['t']:
                if i_to < a or f_from > b:
                    continue

                if f_from >= a and i_to <= b:
                    H.add_interaction(u, v, f_from, inclusive_end_to_exclusive(i_to), **edge_attrs)
                elif a >= f_from and i_to <= b:
                    H.add_interaction(u, v, a, inclusive_end_to_exclusive(i_to), **edge_attrs)
                elif f_from >= a and b <= i_to:
                    H.add_interaction(u, v, f_from, inclusive_end_to_exclusive(b), **edge_attrs)
                elif f_from <= a and b <= i_to:
                    H.add_interaction(u, v, a, inclusive_end_to_exclusive(b), **edge_attrs)

        for n in H.nodes():
            H._node[n] = self._node[n]

        if include_isolated and node_filter is not None:
            for n, attrs in self._node.items():
                if _matches_filter(node_filter, n, attrs) and n not in H._node:
                    H.add_node(n, **attrs)

        return H

    def update_node_attr(self, n, **data):
        """Updates the attributes of a specified node.

            Parameters
            ----------

            n : node id
            **data : the attributes and their new values

            Examples
            --------
            >>> import dynetx as dn
            >>> G = dn.DynGraph()
            >>> G.add_node(0, Label="A")
            >>> G.update_node_attr(0, Label="B")
        """
        self._node.setdefault(n, {}).update(data)

    def get_node_snapshots(self, n):
        """
        Return the snapshot ids for which the given node is in the graph

        :param n: node id
        :return: list of snapshot ids
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.get_node_snapshots()
"""
        snaps = []
        for t in self.temporal_snapshots_ids():
            if self.has_node(n, t):
                snaps.append(t)
        return snaps

    def update_node_attr_from(self, nlist, **data):
        """Updates the attributes of a specified node.

            Parameters
            ----------

            nlist : list of node ids
            **data : the attributes and their new values

            Examples
            --------
            >>> import dynetx as dn
            >>> G = dn.DynGraph()
            >>> G.add_nodes_from([0, 1, 2], Label="A")
            >>> G.update_node_attr_from([0, 2], Label="B")
        """
        for n in nlist:
            self._node.setdefault(n, {}).update(data)

    def temporal_snapshots_ids(self):
        """Return the ordered list of snapshot ids present in the dynamic graph.

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
            >>> G.temporal_snapshots_ids()
            [0, 1, 2]
        """
        return sorted(self.snapshots.keys())

    def interactions_per_snapshots(self, t=None):
        """Return the number of interactions within snapshot t.

        Parameters
        ----------

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
        >>> G.interactions_per_snapshots(t=0)
        3
        >>> G.interactions_per_snapshots()
        {0: 3, 1: 3, 2: 3}
        """
        if t is None:
            return dict(self.snapshots)
        else:
            try:
                return self.snapshots[t]
            except KeyError:
                return 0

    def inter_event_time_distribution(self, u=None, v=None):
        """Return the distribution of inter event time.
        If u and v are None the dynamic graph intere event distribution is returned.
        If u is specified the inter event time distribution of interactions involving u is returned.
        If u and v are specified the inter event time distribution of (u, v) interactions is returned

        Parameters
        ----------

        u : node id
        v : node id

        Returns
        -------

        nd : dictionary
            A dictionary from inter event time to number of occurrences

        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.inter_event_time_distribution()
"""
        dist = {}
        if u is None:
            # global inter event
            first = True
            delta = None
            for ext in self.stream_interactions():
                if first:
                    delta = ext
                    first = False
                    continue
                disp = ext[-1] - delta[-1]
                delta = ext
                if disp in dist:
                    dist[disp] += 1
                else:
                    dist[disp] = 1

        elif u is not None and v is None:
            # node inter event
            delta = (0, 0, 0, 0)
            flag = False
            for ext in self.stream_interactions():
                if ext[0] == u or ext[1] == u:
                    if flag:
                        disp = ext[-1] - delta[-1]
                        delta = ext
                        if disp in dist:
                            dist[disp] += 1
                        else:
                            dist[disp] = 1
                    else:
                        delta = ext
                        flag = True
        else:
            # interaction inter event
            evt = self._adj[u][v]['t']
            delta = []

            for i in evt:
                if i[0] != i[1]:
                    for j in [0, 1]:
                        delta.append(i[j])
                else:
                    delta.append(i[0])

            if len(delta) == 2 and delta[0] == delta[1]:
                return {}

            for i in range(0, len(delta) - 1):
                e = delta[i + 1] - delta[i]
                if e not in dist:
                    dist[e] = 1
                else:
                    dist[e] += 1

        return dist

    def coverage(self):
        """
        Coverage of the temporal graph.

        Returns
        -------
        cov : float
            The ratio of existing nodes w.r.t. the possible ones.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.coverage()
"""
        T = len(self.snapshots)
        V = self.number_of_nodes()
        if T == 0 or V == 0:
            return 0.0
        W = 0
        for t in self.snapshots:
            W += self.number_of_nodes(t)

        return W / (T * V)

    def node_contribution(self, u):
        """
            Node u coverage of the temporal graph.

            Parameters
            ----------

            u : node id, mandatory

            Returns
            -------
            ucov : float
                Probability that u belongs to a randomly selected network timestamp.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.node_contribution()
"""

        ucov = 0
        if len(self.snapshots) == 0:
            return 0.0
        for t in self.snapshots:
            ucov += 1 if self.has_node(u, t) else 0
        return ucov / len(self.snapshots)

    def edge_contribution(self, u, v):
        """
            Edge (u, v) coverage of the temporal graph.

            Parameters
            ----------

            u : node id, mandatory
            v : node id, mandatory

            Returns
            -------
            ecov : float
                Probability that (u, v) belongs to a randomly selected network timestamp.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.edge_contribution()
"""
        presences = self._adj[u][v]['t']
        count = 0
        for interval in presences:
            count += (interval[-1] - interval[0]) + 1

        return 0.0 if len(self.snapshots) == 0 else count / len(self.snapshots)

    def node_pair_uniformity(self, u, v):
        """
            Overlap between the presence times of u and v

            Parameters
            ----------

            u : node id, mandatory
            v : node id, mandatory

            Returns
            -------
            uniformity : float
                Overlap between the presence times of u and v, in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.node_pair_uniformity()
"""

        u_presence = []
        v_presence = []

        for t in self.snapshots:
            if self.has_node(u, t):
                u_presence.append(t)
            if self.has_node(v, t):
                v_presence.append(t)

        if len(u_presence) == 0 and len(v_presence) == 0:
            return 0.0
        unif = len(set(u_presence) & set(v_presence)) / len(set(u_presence) | set(v_presence))
        return unif

    def uniformity(self):
        """
            Temporal network uniformity

            Returns
            -------
            uniformity : float
                Uniformity of the temporal graph in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.uniformity()
"""
        nds = self.nodes()
        numerator, denominator = 0, 0
        for u, v in combinations(nds, 2):
            for t in self.snapshots:
                if self.has_node(u, t) and self.has_node(v, t):
                    numerator += 1
                if self.has_node(u, t) or self.has_node(v, t):
                    denominator += 1
        return 0.0 if denominator == 0 else numerator / denominator

    def density(self):
        """
            Temporal network density: fraction of possible interactions that do exist in the temporal network.

            Returns
            -------
            density : float
                density of the temporal graph in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.density()
"""
        nds = self.nodes()
        numerator, denominator = 0, 0
        for u, v in combinations(nds, 2):
            for t in self.snapshots:
                if self.has_node(u, t) and self.has_node(v, t):
                    denominator += 1
                if self.has_interaction(u, v, t):
                    numerator += 1
        return 0.0 if denominator == 0 else numerator / denominator

    def node_density(self, u):
        """
            Node pair density.
            Intersection among the temporal presence of the edge (u, v) and the joint temporal presences of u and v.

            Parameters
            ----------

            u : node id, mandatory
            v : node id, mandatory

            Returns
            -------
            density : float
                Node pair density, in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.node_density()
"""

        numerator, denominator = 0, 0
        presence_u = self.node_presence(u)

        for t in self.snapshots:
            if self.has_node(u, t):
                numerator += self.degree([u], t)[u]

        for v in self.nodes():
            if v != u:
                denominator += len(self.node_presence(v) & presence_u)

        return 0 if denominator == 0 else numerator / denominator

    def link_count(self):
        """
            Average number of active links over time.

            Returns
            -------
            m : float
                Average number of active links over time, computed as the
                total number of active interactions divided by the number of
                snapshots.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.link_count()
"""
        T = len(self.snapshots)
        if T == 0:
            return 0.0
        E = sum(self.size(t) for t in self.snapshots)
        return E / T

    def node_duration(self):
        """
            Average duration of presence of a node.

            Returns
            -------
            k : float
                Average duration of presence of a node, computed as the total
                node-presence time divided by the number of nodes.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.node_duration()
"""
        V = self.nodes()
        if not V:
            return 0.0
        W = sum(len(self.node_presence(v)) for v in V)
        return W / len(V)

    def link_duration(self):
        r"""
            Average duration of presence of a link.

            Returns
            -------
            l : float
                Average duration of presence of a link, computed as the total
                link-presence time divided by the number of possible node
                pairs.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.link_duration()
"""
        n = self.number_of_nodes()
        if n <= 1:
            return 0.0
        E = sum(self.size(t) for t in self.snapshots)
        if self.is_directed():
            V_otimes_V = n * (n - 1)
        else:
            V_otimes_V = n * (n - 1) / 2.0
        return E / V_otimes_V

    def compactness(self):
        """
            Compactness of the stream graph.

            Returns
            -------
            c : float
                Compactness of the stream graph, defined as the ratio between
                the active node-time pairs and the product of active time span
                and active nodes.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.compactness()
"""
        V = self.nodes()
        if not V or not self.snapshots:
            return 0.0
        tids = self.temporal_snapshots_ids()
        if not tids:
            return 0.0
        T_prime = max(tids) - min(tids) + 1
        V_prime = len(V)
        W = sum(len(self.node_presence(v)) for v in V)
        return W / (T_prime * V_prime)

    def induced_substream(self, cluster):
        """
            Return the induced substream of the graph by the given cluster.

            Parameters
            ----------
            cluster : Cluster or iterable of (t, node) tuples
                The cluster inducing the substream.

            Returns
            -------
            subG : DynGraph
                The induced substream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.induced_substream()
"""
        C = set(cluster)
        subG = self.__class__(edge_removal=self.edge_removal)
        for t, u in C:
            if self.has_node(u, t):
                for v in self.neighbors(u, t):
                    if (t, v) in C:
                        subG.add_interaction(u, v, t=t)
        for n in subG.nodes():
            if n in self._node:
                subG._node[n] = dict(self._node[n])
        return subG

    def temporal_neighborhood(self, u):
        """
            Return the temporal neighborhood of node u as a Cluster of (t, neighbor) pairs.

            Parameters
            ----------
            u : node id

            Returns
            -------
            neighborhood : Cluster
                The temporal neighborhood of node u.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.temporal_neighborhood()
"""
        from dynetx.classes.cluster import Cluster
        neighborhood = Cluster()
        for t in self.snapshots:
            if self.has_node(u, t):
                for v in self.neighbors(u, t):
                    neighborhood.add((t, v))
        return neighborhood

    def stream_degree(self, u):
        """
            Node degree over time.

            Parameters
            ----------
            u : node id

            Returns
            -------
            deg : float
                The node stream degree, normalized by the number of
                snapshots.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_degree()
"""
        T = len(self.snapshots)
        if T == 0:
            return 0.0
        return len(self.temporal_neighborhood(u)) / T

    def average_stream_degree(self):
        """
            Average node degree d(V) = (1/n) * sum(d(v)).

            Returns
            -------
            avg_deg : float
                The average node degree over all nodes active at least once.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.average_stream_degree()
"""
        V = self.nodes()
        if not V:
            return 0.0
        return sum(self.stream_degree(v) for v in V) / len(V)

    def expected_stream_degree(self, u):
        """
            Expected degree of node u when present.

            Parameters
            ----------
            u : node id

            Returns
            -------
            exp_deg : float
                The expected degree when present.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.expected_stream_degree()
"""
        T_u = self.node_presence(u)
        if not T_u:
            return 0.0
        total_degree = sum(self.degree([u], t)[u] for t in T_u)
        return total_degree / len(T_u)

    def degree_at_time(self, u, t):
        """
            Instantaneous degree of node u at time t.

            Parameters
            ----------
            u : node id
            t : timestamp

            Returns
            -------
            deg : int
                Instantaneous degree of node u at time t.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.degree_at_time()
"""
        if not self.has_node(u, t):
            return 0
        return self.degree([u], t)[u]

    def expected_degree_at_time(self, t):
        """
            Average degree of nodes active at time t.

            Parameters
            ----------
            t : timestamp

            Returns
            -------
            exp_deg : float
                The average degree of active nodes at time t.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.expected_degree_at_time()
"""
        V_t = [v for v in self.nodes() if self.has_node(v, t)]
        if not V_t:
            return 0.0
        total_deg = sum(self.degree([v], t)[v] for v in V_t)
        return total_deg / len(V_t)

    def global_stream_degree(self):
        """
            Global stream degree d(S).

            Returns
            -------
            glob_deg : float
                The global stream degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.global_stream_degree()
"""
        V = self.nodes()
        T = len(self.snapshots)
        if not V or T == 0:
            return 0.0
        E = sum(self.size(t) for t in self.snapshots)
        denom = T * len(V)
        factor = 1.0 if self.is_directed() else 2.0
        return factor * E / denom

    def average_expected_stream_degree(self):
        """
            Average expected degree of the stream graph.

            Returns
            -------
            avg_exp_deg : float
                The average expected degree of the stream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.average_expected_stream_degree()
"""
        V = self.nodes()
        if not V:
            return 0.0
        W = sum(len(self.node_presence(v)) for v in V)
        if W == 0:
            return 0.0
        E = sum(self.size(t) for t in self.snapshots)
        factor = 1.0 if self.is_directed() else 2.0
        return factor * E / W

    def average_time_degree(self):
        """
            Average time degree d(T).

            Returns
            -------
            avg_time_deg : float
                The average time degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.average_time_degree()
"""
        return self.average_expected_stream_degree()

    def interaction_presence(self, u, v):
        """
            Return the set of snapshot IDs in which interaction (u, v) is active.

            Parameters
            ----------
            u, v : node ids

            Returns
            -------
            presence : set
                Set of snapshot IDs.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.interaction_presence()
"""
        if u not in self._adj or v not in self._adj[u]:
            return set()
        spans = self._adj[u][v]['t']
        tids = self.temporal_snapshots_ids()
        res = set()
        for t in tids:
            for s in spans:
                if s[0] <= t <= s[1]:
                    res.add(t)
                    break
        return res

    def stream_clustering_coefficient(self, u):
        """
            Clustering coefficient of node u.

            Parameters
            ----------
            u : node id

            Returns
            -------
            cc : float
                Clustering coefficient of node u.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_clustering_coefficient()
"""
        neighbors_u = self.neighbors(u)
        if len(neighbors_u) < 2:
            return 0.0
        numerator = 0
        denominator = 0
        presences = {v: self.interaction_presence(u, v) for v in neighbors_u}
        for v, w in combinations(neighbors_u, 2):
            common_uv_uw = presences[v] & presences[w]
            if not common_uv_uw:
                continue
            denominator += len(common_uv_uw)
            T_vw = self.interaction_presence(v, w)
            numerator += len(common_uv_uw & T_vw)
        return 0.0 if denominator == 0 else numerator / denominator

    def average_stream_clustering_coefficient(self):
        """
            Weighted average clustering coefficient over all nodes.

            Returns
            -------
            avg_cc : float
                Weighted average clustering coefficient.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.average_stream_clustering_coefficient()
"""
        V = self.nodes()
        if not V:
            return 0.0
        W = sum(len(self.node_presence(v)) for v in V)
        if W == 0:
            return 0.0
        total = 0.0
        for v in V:
            total += len(self.node_presence(v)) * self.stream_clustering_coefficient(v)
        return total / W

    def stream_transitivity(self):
        """
            Global transitivity ratio tr(S).

            Returns
            -------
            tr : float
                Global transitivity ratio.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_transitivity()
"""
        V = self.nodes()
        if len(V) < 3:
            return 0.0
        total_triangles = 0
        total_triplets = 0
        for u in V:
            neighbors_u = self.neighbors(u)
            if len(neighbors_u) < 2:
                continue
            presences = {v: self.interaction_presence(u, v) for v in neighbors_u}
            for v, w in combinations(neighbors_u, 2):
                common_uv_uw = presences[v] & presences[w]
                if not common_uv_uw:
                    continue
                total_triplets += len(common_uv_uw)
                T_vw = self.interaction_presence(v, w)
                total_triangles += len(common_uv_uw & T_vw)
        return 0.0 if total_triplets == 0 else total_triangles / total_triplets

    def time_clustering_coefficient(self):
        """
            Time clustering coefficient of the stream graph.

            Returns
            -------
            time_cc : float
                Time clustering coefficient.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.time_clustering_coefficient()
"""
        tids = self.temporal_snapshots_ids()
        if not tids:
            return 0.0
        total = 0.0
        for t in tids:
            sg = self.to_networkx_graph(t=t)
            total += nx.average_clustering(sg.to_undirected() if sg.is_directed() else sg)
        return total / len(tids)

    def stream_clustering_coefficient_global(self):
        """
            Clustering coefficient of the stream graph.

            Returns
            -------
            stream_cc : float
                Clustering coefficient of the stream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_clustering_coefficient_global()
"""
        V = self.nodes()
        tids = self.temporal_snapshots_ids()
        if not V or not tids:
            return 0.0
        total = 0.0
        for t in tids:
            sg = self.to_networkx_graph(t=t)
            base = sg.to_undirected() if sg.is_directed() else sg
            cc_dict = nx.clustering(base)
            total += sum(cc_dict.get(v, 0.0) for v in V)
        return total / (len(tids) * len(V))

    def stream_diameter(self, start=None, end=None):
        """
            Return the diameter of the stream graph (largest finite distance).

            Parameters
            ----------
            start, end : timestamps, optional
                Temporal window.

            Returns
            -------
            diam : int
                The stream diameter.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_diameter()
"""
        import dynetx.algorithms as al
        return al.stream_diameter(self, start=start, end=end)

    def stream_lapse(self, start=None, end=None):
        """
            Return the lapse of the stream graph (largest finite latency).

            Parameters
            ----------
            start, end : timestamps, optional
                Temporal window.

            Returns
            -------
            lapse : int
                The stream lapse.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_lapse()
"""
        import dynetx.algorithms as al
        return al.stream_lapse(self, start=start, end=end)

    def stream_flood_time(self, start=None, end=None):
        """
            Return the flood time of the stream graph.

            Parameters
            ----------
            start, end : timestamps, optional
                Temporal window.

            Returns
            -------
            ft : int
                The stream flood time.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_flood_time()
"""
        import dynetx.algorithms as al
        return al.stream_flood_time(self, start=start, end=end)

    def stream_time_to_reach(self, u, v, alpha, start=None, end=None):
        """
            Minimum arrival time difference to reach target v from source u starting at or after alpha.

            Parameters
            ----------
            u, v : node ids
            alpha : timestamp
            start, end : timestamps, optional

            Returns
            -------
            t_to_reach : float
                Foremost time-to-reach.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_time_to_reach()
"""
        import dynetx.algorithms as al
        return al.stream_time_to_reach(self, u, v, alpha, start=start, end=end)

    def constrained_time_respecting_paths(self, u, v=None, start=None, end=None, gamma=1, gamma_prime=None):
        """
            Find all simple paths from u to v under transmission delay gamma and forwarding delay gamma_prime.

            Parameters
            ----------
            u, v : node ids
            start, end : timestamps, optional
            gamma : int, optional (default=1)
            gamma_prime : int, optional (default=None)

            Returns
            -------
            paths : dict
                A dictionary mapping node pairs to lists of paths.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.constrained_time_respecting_paths()
"""
        import dynetx.algorithms as al
        return al.constrained_time_respecting_paths(self, u, v=v, start=start, end=end, gamma=gamma, gamma_prime=gamma_prime)

    def stream_weakly_connected_components(self):
        """
            Return the weakly connected components of the stream graph as a list of Clusters.

            Returns
            -------
            comp : list of Clusters
                The weakly connected components.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_weakly_connected_components()
"""
        import dynetx.algorithms as al
        return al.stream_weakly_connected_components(self)

    def stream_strongly_connected_components(self):
        """
            Return the strongly connected components of the stream graph as a list of Clusters.

            Returns
            -------
            comp : list of Clusters
                The strongly connected components.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_strongly_connected_components()
"""
        import dynetx.algorithms as al
        return al.stream_strongly_connected_components(self)

    def reachability_stream_graph(self):
        """
            Return the reachability stream graph of this graph.

            Returns
            -------
            R : DynDiGraph
                The reachability stream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.reachability_stream_graph()
"""
        import dynetx.algorithms as al
        return al.reachability_stream_graph(self)

    def cluster_internal_neighborhood(self, cluster, v):
        """
            Return the internal neighborhood of node v involved in cluster as a Cluster.

            Parameters
            ----------
            cluster : Cluster
            v : node id

            Returns
            -------
            c : Cluster
                The internal neighborhood.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_internal_neighborhood()
"""
        import dynetx.algorithms as al
        return al.cluster_internal_neighborhood(self, cluster, v)

    def cluster_external_neighborhood(self, cluster, v):
        """
            Return the external neighborhood of node v involved in cluster as a Cluster.

            Parameters
            ----------
            cluster : Cluster
            v : node id

            Returns
            -------
            c : Cluster
                The external neighborhood.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_external_neighborhood()
"""
        import dynetx.algorithms as al
        return al.cluster_external_neighborhood(self, cluster, v)

    def cluster_internal_degree(self, cluster, v):
        """
            Return the internal degree of node v in cluster.

            Parameters
            ----------
            cluster : Cluster
            v : node id

            Returns
            -------
            deg : int
                The internal degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_internal_degree()
"""
        import dynetx.algorithms as al
        return al.cluster_internal_degree(self, cluster, v)

    def cluster_external_degree(self, cluster, v):
        """
            Return the external degree of node v in cluster.

            Parameters
            ----------
            cluster : Cluster
            v : node id

            Returns
            -------
            deg : int
                The external degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_external_degree()
"""
        import dynetx.algorithms as al
        return al.cluster_external_degree(self, cluster, v)

    def cluster_average_internal_degree(self, cluster):
        """
            Return the average internal degree of cluster.

            Parameters
            ----------
            cluster : Cluster

            Returns
            -------
            avg_deg : float
                The average internal degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_average_internal_degree()
"""
        import dynetx.algorithms as al
        return al.cluster_average_internal_degree(self, cluster)

    def cluster_average_external_degree(self, cluster):
        """
            Return the average external degree of cluster.

            Parameters
            ----------
            cluster : Cluster

            Returns
            -------
            avg_deg : float
                The average external degree.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_average_external_degree()
"""
        import dynetx.algorithms as al
        return al.cluster_average_external_degree(self, cluster)

    def intra_cluster_density(self, partition):
        """
            Intra-cluster density of a partition (list of Clusters).

            Parameters
            ----------
            partition : list of Clusters

            Returns
            -------
            density : float
                Intra-cluster density.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.intra_cluster_density()
"""
        import dynetx.algorithms as al
        return al.intra_cluster_density(self, partition)

    def inter_cluster_density(self, partition):
        """
            Inter-cluster density of a partition (list of Clusters).

            Parameters
            ----------
            partition : list of Clusters

            Returns
            -------
            density : float
                Inter-cluster density.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.inter_cluster_density()
"""
        import dynetx.algorithms as al
        return al.inter_cluster_density(self, partition)

    def cluster_external_density(self, cluster):
        """
            External density of a cluster.

            Parameters
            ----------
            cluster : Cluster

            Returns
            -------
            density : float
                External density.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.cluster_external_density()
"""
        import dynetx.algorithms as al
        return al.cluster_external_density(self, cluster)

    def quotient_stream(self, partition):
        """
            Return the quotient stream graph of this graph induced by partition.

            Parameters
            ----------
            partition : list of Clusters

            Returns
            -------
            Q : DynGraph
                Quotient stream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.quotient_stream()
"""
        import dynetx.algorithms as al
        return al.quotient_stream(self, partition)

    def line_stream(self):
        """
            Return the line stream graph of G.

            Returns
            -------
            L : DynGraph
                Line stream graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.line_stream()
"""
        import dynetx.algorithms as al
        return al.line_stream(self)

    def stream_k_core(self, k=None):
        """
            Return the stream k-core or core numbers.

            Parameters
            ----------
            k : int, optional
                If specified, return the k-core. Otherwise, return core numbers dict.

            Returns
            -------
            core : Cluster or dict
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_k_core()
"""
        import dynetx.algorithms as al
        return al.stream_k_core(self, k=k)

    def stream_path_tree(self, root_node, root_time, path_type='foremost'):
        """
            Return foremost/shortest/fastest path trees.

            Parameters
            ----------
            root_node : node id
            root_time : timestamp
            path_type : str, optional (default='foremost')

            Returns
            -------
            Tree : DynGraph
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_path_tree()
"""
        import dynetx.algorithms as al
        return al.stream_path_tree(self, root_node, root_time, path_type=path_type)

    def stream_cascade(self, root_node, root_time):
        """
            Return the cascade of G starting from root.

            Parameters
            ----------
            root_node : node id
            root_time : timestamp

            Returns
            -------
            Tree : DynGraph
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_cascade()
"""
        import dynetx.algorithms as al
        return al.stream_cascade(self, root_node, root_time)

    def stream_closeness_centrality(self, v, t):
        """
            Return the closeness centrality of node v at time t.

            Parameters
            ----------
            v : node id
            t : timestamp

            Returns
            -------
            closeness : float
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_closeness_centrality()
"""
        import dynetx.algorithms as al
        return al.stream_closeness_centrality(self, v, t)

    def stream_betweenness_centrality(self):
        """
            Return the temporal betweenness centrality of all (t, v) in G.

            Returns
            -------
            bc : dict
                Mapping (t, v) -> betweenness centrality.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_betweenness_centrality()
"""
        import dynetx.algorithms as al
        return al.stream_betweenness_centrality(self)

    def stream_node_betweenness_centrality(self):
        """
            Return the node betweenness centrality for all nodes in G.

            Returns
            -------
            node_bc : dict
                Mapping node -> betweenness centrality.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_node_betweenness_centrality()
"""
        import dynetx.algorithms as al
        return al.stream_node_betweenness_centrality(self)

    def stream_time_betweenness_centrality(self):
        """
            Return the time betweenness centrality for all snapshots in G.

            Returns
            -------
            time_bc : dict
                Mapping snapshot -> betweenness centrality.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.stream_time_betweenness_centrality()
"""
        import dynetx.algorithms as al
        return al.stream_time_betweenness_centrality(self)

    def delta_substream(self, t, delta):
        """
            Return the substream of G restricted to the temporal window [t, t + delta].

            Parameters
            ----------
            t : timestamp
            delta : float/int
                Window size.

            Returns
            -------
            sub : DynGraph
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.delta_substream()
"""
        import dynetx.algorithms as al
        return al.delta_substream(self, t, delta)

    def delta_density(self, t, delta):
        """
            Return the density of G in the window [t, t + delta].

            Parameters
            ----------
            t : timestamp
            delta : float/int
                Window size.

            Returns
            -------
            density : float
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.delta_density()
"""
        import dynetx.algorithms as al
        return al.delta_density(self, t, delta)

    def delta_degree(self, v, t, delta):
        """
            Return the degree of node v in the window [t, t + delta].

            Parameters
            ----------
            v : node id
            t : timestamp
            delta : float/int
                Window size.

            Returns
            -------
            deg : float
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.delta_degree()
"""
        import dynetx.algorithms as al
        return al.delta_degree(self, v, t, delta)

    def pair_density(self, u, v):
        """
            Node pair density.
            Intersection among the temporal presence of the edge (u, v) and the joint temporal presences of u and v.

            Parameters
            ----------

            u : node id, mandatory
            v : node id, mandatory

            Returns
            -------
            density : float
                Node pair density, in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.pair_density()
"""

        numerator, denominator = 0, 0

        for t in self.snapshots:
            if self.has_node(u, t) and self.has_node(v, t):
                denominator += 1
            if self.has_interaction(u, v, t):
                numerator += 1

        return 0 if denominator == 0 else numerator / denominator

    def snapshot_density(self, t):
        """
            Density of a temporal network at time t.

            Returns
            -------
            density : float
                density of the temporal graph at time t, in [0, 1]
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.snapshot_density()
"""
        return nx.density(self.time_slice(t))

    def node_presence(self, u):
        """
            Timestamps of presence for node u

            Returns
            -------
            density : set
                temporal ids
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.node_presence(0)
"""
        pres = []
        for t in self.snapshots:
            if self.has_node(u, t):
                pres.append(t)

        return set(pres)

    def temporal_degree(self, nbunch=None, t=None):
        """Return the temporal support of nodes.

        If t is provided, this behaves like degree(t=t). Otherwise it returns
        the number of snapshots in which each node is active.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.temporal_degree(0, t=0)
"""
        if t is not None:
            return self.degree(nbunch, t=t)

        if nbunch is None:
            nodes = self.nodes()
        elif nbunch in self:
            nodes = [nbunch]
        else:
            nodes = list(self.nbunch_iter(nbunch))

        return {n: len(self.node_presence(n)) for n in nodes}

    def avg_temporal_degree(self):
        """Return the average temporal support across all nodes.

        Returns
        -------
        float
            Mean number of snapshots in which a node is active.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.avg_temporal_degree()
"""
        vals = list(self.temporal_degree().values())
        return 0.0 if len(vals) == 0 else sum(vals) / len(vals)

    def _remove_edge_instance(self, u, v):
        if u not in self._adj or v not in self._adj[u]:
            return

        datadict = self._adj[u][v]
        for interval in datadict.get('t', []):
            for tid in range(interval[0], interval[1] + 1):
                if tid in self.snapshots:
                    self.snapshots[tid] = max(0, self.snapshots[tid] - 1)
                    if self.snapshots[tid] == 0:
                        del self.snapshots[tid]

        for tid in list(self.time_to_edge.keys()):
            for key in [(u, v, "+"), (u, v, "-"), (v, u, "+"), (v, u, "-")]:
                if key in self.time_to_edge.get(tid, {}):
                    del self.time_to_edge[tid][key]
            if len(self.time_to_edge.get(tid, {})) == 0:
                del self.time_to_edge[tid]

        del self._adj[u][v]
        if u != v and v in self._adj and u in self._adj[v]:
            del self._adj[v][u]

    def remove_edge(self, u, v):
        """Remove edge ``(u, v)`` from the graph.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.remove_edge(0, 1)
"""
        self._remove_edge_instance(u, v)

    def remove_edges_from(self, ebunch):
        """Remove every edge in ``ebunch``.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.remove_edges_from([(0, 1)])
"""
        for e in ebunch:
            self.remove_edge(e[0], e[1])

    def remove_node(self, u):
        """Remove node ``u`` and all of its incident interactions.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.remove_node(1)
"""
        if u not in self._node:
            return
        for v in list(self._adj.get(u, {}).keys()):
            self.remove_edge(u, v)
        if u in self._adj:
            del self._adj[u]
        if u in self._node:
            del self._node[u]

    def remove_nodes_from(self, nbunch):
        """Remove every node in ``nbunch``.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.remove_nodes_from([1])
"""
        for n in list(nbunch):
            self.remove_node(n)

    def add_edge(self, u, v, attr_dict=None, **attr):
        """Add an interaction using the NetworkX edge API.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
"""
        attrs = {}
        if attr_dict:
            attrs.update(attr_dict)
        attrs.update(attr)
        t = attrs.pop("t", None)
        e = attrs.pop("e", None)
        if t is None:
            raise nx.NetworkXError("The t argument must be specified.")
        self.add_interaction(u, v, t=t, e=e, **attrs)

    def add_edges_from(self, ebunch, attr_dict=None, **attr):
        """Add multiple interactions using the NetworkX edge API.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interactions_from([(0, 1)], t=0)
"""
        attrs = {}
        if attr_dict:
            attrs.update(attr_dict)
        attrs.update(attr)
        for e in ebunch:
            if len(e) == 2:
                self.add_edge(e[0], e[1], **attrs)
            elif len(e) == 3 and isinstance(e[2], dict):
                merged = dict(attrs)
                merged.update(e[2])
                self.add_edge(e[0], e[1], **merged)
            else:
                raise nx.NetworkXError("Each edge must be a 2-tuple or 3-tuple with attribute dict.")

    def edges_iter(self, nbunch=None, data=False, default=None):
        """Iterate over the interactions of the graph.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> list(G.edges_iter(t=0))
"""
        for u, v, d in self.interactions_iter(nbunch):
            if data:
                yield u, v, d
            else:
                yield u, v

    def edges(self, nbunch=None, data=False, default=None):
        """Return the interactions of the graph as a list.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> list(G.edges(t=0))
"""
        return list(self.edges_iter(nbunch=nbunch, data=data, default=default))

    def has_node_in_range(self, n, t_from, t_to=None, mode='any'):
        """Check whether node ``n`` is present in a time interval.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.has_node_in_range(0, 0)
"""
        if t_to is None:
            t_to = t_from
        tids = range(t_from, t_to + 1)
        checks = [self.has_node(n, t) for t in tids]
        return any(checks) if mode != 'all' else all(checks)

    def has_interaction_in_range(self, u, v, t_from, t_to=None, mode='any'):
        """Check whether interaction ``(u, v)`` is present in a time interval.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.has_interaction_in_range(0, 1, 0)
"""
        if t_to is None:
            t_to = t_from
        tids = range(t_from, t_to + 1)
        checks = [self.has_interaction(u, v, t) for t in tids]
        return any(checks) if mode != 'all' else all(checks)

    def neighbors_in_range(self, n, t_from, t_to=None, mode='any'):
        """Return the neighbors of ``n`` observed in a time interval.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.neighbors_in_range(0, 0)
"""
        if t_to is None:
            t_to = t_from
        nbrs = set()
        for tid in range(t_from, t_to + 1):
            nbrs.update(self.neighbors(n, t=tid))
        if mode == 'all':
            return [v for v in self.nodes() if v != n and all(self.has_interaction(n, v, tid) for tid in range(t_from, t_to + 1))]
        return list(nbrs)

    def interactions_in_range(self, nbunch=None, t_from=None, t_to=None, mode='any', min_count=1):
        """Return interactions observed in a time interval.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.interactions_in_range(t_from=0, t_to=0)
"""
        if t_from is None:
            t_from = min(self.temporal_snapshots_ids() or [0])
        if t_to is None:
            t_to = t_from
        res = []
        for u, v, d in self.interactions_iter(nbunch):
            count = sum(1 for tid in range(t_from, t_to + 1) if self.has_interaction(u, v, tid))
            if mode == 'all':
                if count == (t_to - t_from + 1):
                    res.append((u, v, d))
            elif min_count > 1:
                if count >= min_count:
                    res.append((u, v, d))
            else:
                if count > 0:
                    res.append((u, v, d))
        return res

    def window_slices(self, window, step=1, include_partial=False):
        """Yield subgraphs extracted with a sliding temporal window.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> list(G.window_slices(window=1))
"""
        tids = self.temporal_snapshots_ids()
        if len(tids) == 0:
            return
        start = tids[0]
        end = tids[-1]
        cur = start
        while cur <= end:
            last = cur + window - 1
            if last > end and not include_partial:
                break
            yield self.time_slice(cur, min(last, end))
            cur += step

    def to_networkx_graph(self, t=None):
        """Return a NetworkX graph for a snapshot or for the aggregate graph.

        Parameters
        ----------
        t : snapshot id, optional
            If provided, export only the selected snapshot.

        Returns
        -------
        networkx.Graph
            Static representation of the dynamic graph.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.DynGraph()
        >>> G.add_interaction(0, 1, t=0)
        >>> G.to_networkx_graph(t=0)
"""
        if self.is_directed():
            nxg = nx.DiGraph()
        else:
            nxg = nx.Graph()
        nxg.graph.update(self.graph)
        for n, d in self.nodes(data=True):
            nxg.add_node(n, **d)
        if t is None:
            for u, v, d in self.interactions_iter():
                attrs = dict(d)
                nxg.add_edge(u, v, **attrs)
        else:
            for u, v, d in self.interactions_iter():
                if self.has_interaction(u, v, t):
                    attrs = {k: val for k, val in d.items() if k != "t"}
                    nxg.add_edge(u, v, **attrs)
        return nxg
