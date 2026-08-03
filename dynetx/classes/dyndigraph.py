import networkx as nx
from collections import defaultdict
from dynetx.utils import not_implemented
from dynetx.utils.validation import normalize_time_range, inclusive_end_to_exclusive
from copy import deepcopy

__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"


class DynDiGraph(nx.DiGraph):
    """
    """

    def __init__(self, data=None, edge_removal=True, **attr):
        """
        Initialize a directed graph with interaction, name, graph attributes.
        """
        super(DynDiGraph, self).__init__(data, **attr)
        self.time_to_edge = defaultdict(int)
        self.snapshots = {}
        self.edge_removal = edge_removal
        self.directed = True

    def nodes_iter(self, t=None, data=False):
        """
        Return an iterator over the nodes with respect to a given temporal snapshot.
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
        """
        Return a list of the nodes in the graph at a given snapshot.
        """
        if data:
            return [(k, v) for k, v in self.nodes_iter(t=t, data=data).items()]
        else:
            return [k for k in self.nodes_iter(t=t, data=data)]

    def has_node(self, n, t=None):
        """
        Return True if the graph, at time t, contains the node n.
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

    def get_node_snapshots(self, n):
        """
        """
        snaps = []
        for t in self.temporal_snapshots_ids():
            if self.has_node(n, t):
                snaps.append(t)
        return snaps

    def interactions(self, nbunch=None, t=None):
        """
        Return the list of interaction present in a given snapshot.
        """
        return list(self.interactions_iter(nbunch, t))

    def __presence_test(self, u, v, t):
        if v not in self._succ[u]:
            return False
        spans = self._succ[u][v]['t']
        if self.edge_removal:
            for s in spans:
                if s[0] <= t <= s[1]:
                    return True
        else:
            if spans[0][0] <= t <= max(self.temporal_snapshots_ids()):
                return True

        return False

    def number_of_nodes(self, t=None):
        """
        Return the number of nodes in the t snapshot of a dynamic graph.
        """
        if t is None:
            return len(self._node)
        else:
            nds = sum([1 for n in self.degree(t=t).values() if n > 0])
            return nds

    def avg_number_of_nodes(self):
        """
        Return the number of nodes in the t snapshot of a dynamic graph.
        """
        nds = sum([self.number_of_nodes(t) for t in self.temporal_snapshots_ids()])
        return 0.0 if len(self.snapshots) == 0 else nds/len(self.snapshots)

    def degree_iter(self, nbunch=None, t=None):
        """
        Return an iterator for (node, degree) at time t.
        """

        if nbunch is None:
            nodes_nbrs = ((n, succs, self._pred[n]) for n, succs in self._succ.items())
        else:
            nodes_nbrs = ((n, self._succ[n], self._pred[n]) for n in self.nbunch_iter(nbunch))

        if t is None:
            for n, succ, pred in nodes_nbrs:
                yield n, len(succ) + len(pred)

        else:
            for n, succ, pred in nodes_nbrs:
                edges_succ = len([v for v in succ.keys() if self.__presence_test(n, v, t)])
                edges_pred = len([v for v in pred.keys() if self.__presence_test(v, n, t)])
                yield n, edges_succ + edges_pred

    def degree(self, nbunch=None, t=None):
        """
        Return the degree of a node or nodes at time t.
        """
        if nbunch in self:  # return a single node
            return next(self.degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.degree_iter(nbunch, t))

    def interactions_iter(self, nbunch=None, t=None):
        """
        Return an iterator over the interaction present in a given snapshot.
        """
        if nbunch is None:
            nodes_nbrs_succ = self._succ.items()
        else:
            nodes_nbrs_succ = [(n, self._succ[n]) for n in self.nbunch_iter(nbunch)]

        for n, nbrs in nodes_nbrs_succ:
            for nbr in nbrs:
                if t is not None:
                    if self.__presence_test(n, nbr, t):
                        yield n, nbr, {"t": [t]}
                else:
                    yield n, nbr, self._succ[n][nbr]

    def add_interaction(self, u, v, t=None, e=None, **attr):
        """
        Add an interaction between u and v at time t vanishing (optional) at time e.
        """
        if t is None:
            raise nx.NetworkXError(
                "The t argument must be specified.")

        if u not in self._succ:
            self._succ[u] = self.adjlist_inner_dict_factory()
            self._pred[u] = self.adjlist_inner_dict_factory()
            self._node[u] = {}
        if v not in self._succ:
            self._succ[v] = self.adjlist_inner_dict_factory()
            self._pred[v] = self.adjlist_inner_dict_factory()
            self._node[v] = {}

        raw_t = t
        if type(t) != list:
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
        datadict = self.adj[u].get(v, self.edge_attr_dict_factory())

        if attr:
            datadict.update(attr)

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

        self._succ[u][v] = datadict
        self._pred[v][u] = datadict

    def add_interactions_from(self, ebunch, t=None, e=None, **attr):
        """
        Add all the interaction in ebunch at time t.
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

    def in_interactions_iter(self, nbunch=None, t=None):
        """
        Return an iterator over the in interactions present in a given snapshot.
        """
        if nbunch is None:
            nodes_nbrs_pred = self._pred.items()
        else:
            nodes_nbrs_pred = [(n, self._pred[n]) for n in self.nbunch_iter(nbunch)]

        for n, nbrs in nodes_nbrs_pred:

            for nbr in nbrs:
                if t is not None:
                    if self.__presence_test(nbr, n, t):
                        yield nbr, n, {"t": [t]}
                else:
                    if nbr in self._pred[n]:
                        yield nbr, n, self._pred[n][nbr]

    def out_interactions_iter(self, nbunch=None, t=None):
        """
        Return an iterator over the out interactions present in a given snapshot.
        """
        if nbunch is None:
            nodes_nbrs_succ = self._succ.items()
        else:
            nodes_nbrs_succ = [(n, self._succ[n]) for n in self.nbunch_iter(nbunch)]

        for n, nbrs in nodes_nbrs_succ:
            for nbr in nbrs:
                if t is not None:
                    if self.__presence_test(n, nbr, t):
                        yield n, nbr, {"t": [t]}
                else:
                    if nbr in self._succ[n]:
                        yield n, nbr, self._succ[n][nbr]

    def in_interactions(self, nbunch=None, t=None):
        """
        Return the list of incoming interaction present in a given snapshot.
        """
        return list(self.in_interactions_iter(nbunch, t))

    def out_interactions(self, nbunch=None, t=None):
        """
        Return the list of out interaction present in a given snapshot.
        """
        return list(self.out_interactions_iter(nbunch, t))

    def number_of_interactions(self, u=None, v=None, t=None):
        """
        Return the number of interaction between two nodes at time t.
        """
        if t is None:
            if u is None:
                return int(self.size())
            elif u is not None and v is not None:
                if u in self._succ and v in self._succ[u]:
                    return 1
                else:
                    return 0
        else:
            if u is None:
                return int(self.size(t))
            elif u is not None and v is not None:
                if u in self._succ and v in self._succ[u]:
                    if self.__presence_test(u, v, t):
                        return 1
                    else:
                        return 0

    def has_interaction(self, u, v, t=None):
        """
        Return True if the interaction (u,v) is in the graph at time t.
        """
        try:
            if t is None:
                return v in self._succ[u]
            else:
                return v in self._succ[u] and self.__presence_test(u, v, t)
        except KeyError:
            return False

    def has_successor(self, u, v, t=None):
        """
        Return True if node u has successor v at time t (optional).
        """
        return self.has_interaction(u, v, t)

    def has_predecessor(self, u, v, t=None):
        """
        Return True if node u has predecessor v at time t (optional).
        """
        return self.has_interaction(v, u, t)

    def successors_iter(self, n, t=None):
        """
        """
        try:
            if t is None:
                return iter(self._succ[n])
            else:
                return iter([i for i in self._succ[n] if self.__presence_test(n, i, t)])
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def predecessors_iter(self, n, t=None):
        """
        Return an iterator over predecessors nodes of n at time t (optional).
        """
        try:
            if t is None:
                return iter(self._pred[n])
            else:
                return iter([i for i in self._pred[n] if self.__presence_test(i, n, t)])
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def successors(self, n, t=None):
        """
        Return a list of successor nodes of n at time t (optional).
        """
        return list(self.successors_iter(n, t))

    def predecessors(self, n, t=None):
        """
        Return a list of predecessor nodes of n at time t (optional).
        """
        return list(self.predecessors_iter(n, t))

    # dyndigraph definitions
    neighbors = successors
    neighbors_iter = successors_iter

    def in_degree(self, nbunch=None, t=None):
        """
        Return the in degree of a node or nodes at time t.
        """
        if nbunch in self:  # return a single node
            return next(self.in_degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.in_degree_iter(nbunch, t))

    def in_degree_iter(self, nbunch=None, t=None):
        """
        Return an iterator for (node, in_degree) at time t.
        """
        if nbunch is None:
            nodes_nbrs = self._pred.items()
        else:
            nodes_nbrs = ((n, self._pred[n]) for n in self.nbunch_iter(nbunch))

        if t is None:
            for n, nbrs in nodes_nbrs:
                deg = len(self._pred[n])
                yield n, deg
        else:
            for n, nbrs in nodes_nbrs:
                edges_t = len([v for v in nbrs.keys() if self.__presence_test(v, n, t)])
                if edges_t > 0:
                    yield n, edges_t
                else:
                    yield n, 0

    def out_degree(self, nbunch=None, t=None):
        """
        Return the out degree of a node or nodes at time t.
        """
        if nbunch in self:  # return a single node
            return next(self.out_degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.out_degree_iter(nbunch, t))

    def out_degree_iter(self, nbunch=None, t=None):
        """
        Return an iterator for (node, out_degree) at time t.
        """
        if nbunch is None:
            nodes_nbrs = self._succ.items()
        else:
            nodes_nbrs = ((n, self._succ[n]) for n in self.nbunch_iter(nbunch))

        if t is None:
            for n, nbrs in nodes_nbrs:
                deg = len(self._succ[n])
                yield n, deg
        else:
            for n, nbrs in nodes_nbrs:
                edges_t = len([v for v in nbrs.keys() if self.__presence_test(n, v, t)])
                if edges_t > 0:
                    yield n, edges_t
                else:
                    yield n, 0

    def size(self, t=None):
        """
        Return the number of edges at time t.
        """
        s = sum(self.degree(t=t).values()) / 2
        return int(s)

    def stream_interactions(self):
        """
        Generate a temporal ordered stream of interactions. Only incoming interactions are returned.
        """
        timestamps = sorted(self.time_to_edge.keys())
        for t in timestamps:
            for e in self.time_to_edge[t]:
                yield e[0], e[1], e[2], t

    def time_slice(self, t_from, t_to=None, **kwargs):
        """
        Return a new graph containing nodes and interactions present in ``[t_from, t_to]``.
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
        """
        Updates the attributes of a specified node.
        """
        self._node.setdefault(n, {}).update(data)

    def update_node_attr_from(self, nlist, **data):
        """
        Updates the attributes of a specified node.
        """
        for n in nlist:
            self._node.setdefault(n, {}).update(data)

    def temporal_snapshots_ids(self):
        """
        Return the ordered list of snapshot ids present in the dynamic graph.
        """
        return sorted(self.snapshots.keys())

    def interactions_per_snapshots(self, t=None):
        """
        Return the number of interactions within snapshot t.
        """
        if t is None:
            return dict(self.snapshots)
        else:
            try:
                return self.snapshots[t]
            except KeyError:
                return 0

    def inter_out_event_time_distribution(self, u=None, v=None):
        """
        Return the distribution of inter event time for out interactions. If u and v are None the dynamic graph intere event distribution is returned. If u is specified the inter event time distribution of interactions involving u is returned. If u and v are specified the inter event time distribution of (u, v) interactions is returned
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

                if ext[0] == u:

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
            if v not in self._succ[u]:
                return {}

            evt = self._succ[u][v]['t']
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

    def inter_in_event_time_distribution(self, u=None, v=None):
        """
        Return the distribution of inter event time for in interactions. If u and v are None the dynamic graph intere event distribution is returned. If u is specified the inter event time distribution of interactions involving u is returned. If u and v are specified the inter event time distribution of (u, v) interactions is returned
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

                if ext[1] == u:
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
            if v not in self._pred[u]:
                return {}

            evt = self._pred[u][v]['t']
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

    def inter_event_time_distribution(self, u=None, v=None):
        """
        Return the distribution of inter event time. If u and v are None the dynamic graph intere event distribution is returned. If u is specified the inter event time distribution of interactions involving u is returned. If u and v are specified the inter event time distribution of (u, v) interactions is returned
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

            evt = []
            if v in self._pred[u]:
                evt = self._pred[u][v]['t']
            elif v in self._succ[u]:
                evt = self._succ[u][v]['t']

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

    def remove_edge(self, u, v):
        """
        Remove directed edge ``(u, v)`` from the graph.
        """
        if u not in self._succ or v not in self._succ[u]:
            return
        datadict = self._succ[u][v]
        for interval in datadict.get('t', []):
            for tid in range(interval[0], interval[1] + 1):
                if tid in self.snapshots:
                    self.snapshots[tid] = max(0, self.snapshots[tid] - 1)
                    if self.snapshots[tid] == 0:
                        del self.snapshots[tid]
        for tid in list(self.time_to_edge.keys()):
            for key in [(u, v, "+"), (u, v, "-")]:
                if key in self.time_to_edge.get(tid, {}):
                    del self.time_to_edge[tid][key]
            if len(self.time_to_edge.get(tid, {})) == 0:
                del self.time_to_edge[tid]
        del self._succ[u][v]
        del self._pred[v][u]

    def remove_edges_from(self, ebunch):
        """
        Remove every directed edge in ``ebunch``.
        """
        for e in ebunch:
            self.remove_edge(e[0], e[1])

    def remove_node(self, u):
        """
        Remove node ``u`` and all incoming and outgoing interactions.
        """
        if u not in self._node:
            return
        for v in list(self._succ.get(u, {}).keys()):
            self.remove_edge(u, v)
        for v in list(self._pred.get(u, {}).keys()):
            self.remove_edge(v, u)
        if u in self._succ:
            del self._succ[u]
        if u in self._pred:
            del self._pred[u]
        if u in self._node:
            del self._node[u]

    def remove_nodes_from(self, nbunch):
        """
        Remove every node in ``nbunch``.
        """
        for n in list(nbunch):
            self.remove_node(n)

    def add_edge(self, u, v, attr_dict=None, **attr):
        """
        Add a directed interaction using the NetworkX edge API.
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
        """
        Add multiple directed interactions using the NetworkX edge API.
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
                raise nx.NetworkXError("Each interaction must be a 2-tuple or 3-tuple with attribute dict.")

    def edges_iter(self, nbunch=None, data=False, default=None):
        """
        Iterate over directed interactions.
        """
        for u, v, d in self.interactions_iter(nbunch):
            if data:
                yield u, v, d
            else:
                yield u, v

    def in_edges_iter(self, nbunch=None, data=False, default=None):
        """
        Iterate over incoming interactions.
        """
        for u, v, d in self.in_interactions_iter(nbunch):
            if data:
                yield u, v, d
            else:
                yield u, v

    def out_edges_iter(self, nbunch=None, data=False, default=None):
        """
        Iterate over outgoing interactions.
        """
        for u, v, d in self.out_interactions_iter(nbunch):
            if data:
                yield u, v, d
            else:
                yield u, v

    def in_edges(self, nbunch=None, data=False):
        """
        Return incoming interactions as a list.
        """
        return list(self.in_edges_iter(nbunch=nbunch, data=data))

    def out_edges(self, nbunch=None, data=False):
        """
        Return outgoing interactions as a list.
        """
        return list(self.out_edges_iter(nbunch=nbunch, data=data))

    def node_presence(self, u):
        """
        """
        pres = []
        for t in self.snapshots:
            if self.has_node(u, t):
                pres.append(t)

        return set(pres)

    def temporal_degree(self, nbunch=None, t=None):
        """
        Return the temporal support of one or more nodes.
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
        """
        Return the average temporal support across all nodes.
        """
        vals = list(self.temporal_degree().values())
        return 0.0 if len(vals) == 0 else sum(vals) / len(vals)

    def has_node_in_range(self, n, t_from, t_to=None, mode='any'):
        """
        Check whether node ``n`` is present in a time interval.
        """
        if t_to is None:
            t_to = t_from
        tids = range(t_from, t_to + 1)
        checks = [self.has_node(n, t) for t in tids]
        return any(checks) if mode != 'all' else all(checks)

    def has_interaction_in_range(self, u, v, t_from, t_to=None, mode='any'):
        """
        Check whether interaction ``(u, v)`` is present in a time interval.
        """
        if t_to is None:
            t_to = t_from
        tids = range(t_from, t_to + 1)
        checks = [self.has_interaction(u, v, t) for t in tids]
        return any(checks) if mode != 'all' else all(checks)

    def neighbors_in_range(self, n, t_from, t_to=None, mode='any'):
        """
        Return the neighbors of ``n`` observed in a time interval.
        """
        if t_to is None:
            t_to = t_from
        nbrs = set()
        for tid in range(t_from, t_to + 1):
            nbrs.update(self.successors(n, t=tid))
        if mode == 'all':
            return [v for v in self.nodes() if v != n and all(self.has_interaction(n, v, tid) for tid in range(t_from, t_to + 1))]
        return list(nbrs)

    def interactions_in_range(self, nbunch=None, t_from=None, t_to=None, mode='any', min_count=1):
        """
        Return interactions observed in a time interval.
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
        """
        Yield subgraphs extracted with a sliding temporal window.
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
        """
        Return a NetworkX graph for a snapshot or for the aggregate graph.
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
                nxg.add_edge(u, v, **dict(d))
        else:
            for u, v, d in self.interactions_iter():
                if self.has_interaction(u, v, t):
                    nxg.add_edge(u, v, **{k: val for k, val in d.items() if k != "t"})
        return nxg

    def to_undirected(self, reciprocal=False, **kwargs):
        """
        Return an undirected representation of the dyndigraph.
        """
        from .dyngraph import DynGraph
        H = DynGraph()
        H.name = self.name
        H.add_nodes_from(self)

        if reciprocal is True:
            for u in self._node:
                for v in self._node:
                    if u >= v:
                        try:
                            outc = self._succ[u][v]['t']
                            intc = self._pred[u][v]['t']
                            for o in outc:
                                r = set(range(o[0], o[1] + 1))
                                for i in intc:
                                    r2 = set(range(i[0], i[1] + 1))
                                    inter = list(r & r2)
                                    if len(inter) == 1:
                                        H.add_interaction(u, v, t=inter[0])
                                    elif len(inter) > 1:
                                        H.add_interaction(u, v, t=inter[0], e=inter[-1] + 1)

                        except Exception:
                            pass

        else:
            events = []
            for it in self.interactions_iter():
                for t in it[2]['t']:
                    events.append((it[0], it[1], t[0], t[1]))
            for u, v, t0, t1 in sorted(events, key=lambda x: (x[2], x[3], x[0], x[1])):
                H.add_interaction(u, v, t=t0, e=inclusive_end_to_exclusive(t1))

        H.graph = deepcopy(self.graph)
        H._node = deepcopy(self._node)
        return H

    def add_path(self, nodes, t=None):
        """
        Add a path at time t.
        """
        nlist = list(nodes)
        interaction = zip(nlist[:-1], nlist[1:])
        self.add_interactions_from(interaction, t)
