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
    """

    def __init__(self, data=None, edge_removal=True, **attr):
        """
        Initialize a graph with interaction, name, graph attributes.
        """
        super(DynGraph, self).__init__(data, **attr)
        self.time_to_edge = defaultdict(int)
        self.snapshots = {}
        self.edge_removal = edge_removal
        self.directed = False

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

    def interactions(self, nbunch=None, t=None):
        """
        Return the list of interaction present in a given snapshot.
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
        """
        Return an iterator over the interaction present in a given snapshot.
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
        """
        Add an interaction between u and v at time t vanishing (optional) at time e.
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

    def number_of_interactions(self, u=None, v=None, t=None):
        """
        Return the number of interaction between two nodes at time t.
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
        """
        Return True if the interaction (u,v) is in the graph at time t.
        """
        try:
            if t is None:
                return v in self._adj[u]
            else:
                return v in self._adj[u] and self.__presence_test(u, v, t)
        except KeyError:
            return False

    def neighbors(self, n, t=None):
        """
        Return a list of the nodes connected to the node n at time t.
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
        """
        Return an iterator over all neighbors of node n at time t.
        """
        try:
            if t is None:
                return iter(self._adj[n])
            else:
                return iter([i for i in self._adj[n] if self.__presence_test(n, i, t)])
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def degree(self, nbunch=None, t=None):
        """
        Return the degree of a node or nodes at time t.
        """
        if nbunch in self:  # return a single node
            return next(self.degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.degree_iter(nbunch, t))

    def degree_iter(self, nbunch=None, t=None):
        """
        Return an iterator for (node, degree) at time t.
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
        """
        Return the number of edges at time t.
        """
        s = sum(self.degree(t=t).values()) / 2
        return int(s)

    def number_of_nodes(self, t=None):
        """
        Return the number of nodes in the t snpashot of a dynamic graph.
        """
        if t is None:
            return len(self._node)
        else:
            nds = sum([1 for n in self.degree(t=t).values() if n > 0])
            return nds

    def avg_number_of_nodes(self):
        """
        Return the number of nodes in the t snpashot of a dynamic graph.
        """
        nds = sum([self.number_of_nodes(t) for t in self.temporal_snapshots_ids()])
        return 0.0 if len(self.snapshots) == 0 else nds / len(self.snapshots)

    def order(self, t=None):
        """
        Return the number of nodes in the t snpashot of a dynamic graph.
        """
        return self.number_of_nodes(t)

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

    def add_star(self, nodes, t=None):
        """
        Add a star at time t.
        """
        nlist = list(nodes)
        v = nlist[0]
        interaction = ((v, n) for n in nlist[1:])
        self.add_interactions_from(interaction, t)

    def add_path(self, nodes, t=None):
        """
        Add a path at time t.
        """
        nlist = list(nodes)
        interaction = zip(nlist[:-1], nlist[1:])
        self.add_interactions_from(interaction, t)

    def add_cycle(self, nodes, t=None):
        """
        Add a cycle at time t.
        """
        nlist = list(nodes)
        interaction = zip(nlist, nlist[1:] + [nlist[0]])
        self.add_interactions_from(interaction, t)

    def to_directed(self, **kwargs):
        """
        Return a directed representation of the graph.
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
        """
        Generate a temporal ordered stream of interactions.
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

    def get_node_snapshots(self, n):
        """
        """
        snaps = []
        for t in self.temporal_snapshots_ids():
            if self.has_node(n, t):
                snaps.append(t)
        return snaps

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
        """

        ucov = 0
        if len(self.snapshots) == 0:
            return 0.0
        for t in self.snapshots:
            ucov += 1 if self.has_node(u, t) else 0
        return ucov / len(self.snapshots)

    def edge_contribution(self, u, v):
        """
        """
        presences = self._adj[u][v]['t']
        count = 0
        for interval in presences:
            count += (interval[-1] - interval[0]) + 1

        return 0.0 if len(self.snapshots) == 0 else count / len(self.snapshots)

    def node_pair_uniformity(self, u, v):
        """
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
        """
        T = len(self.snapshots)
        if T == 0:
            return 0.0
        E = sum(self.size(t) for t in self.snapshots)
        return E / T

    def node_duration(self):
        """
        """
        V = self.nodes()
        if not V:
            return 0.0
        W = sum(len(self.node_presence(v)) for v in V)
        return W / len(V)

    def link_duration(self):
        """
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
        """
        T = len(self.snapshots)
        if T == 0:
            return 0.0
        return len(self.temporal_neighborhood(u)) / T

    def average_stream_degree(self):
        """
        """
        V = self.nodes()
        if not V:
            return 0.0
        return sum(self.stream_degree(v) for v in V) / len(V)

    def expected_stream_degree(self, u):
        """
        """
        T_u = self.node_presence(u)
        if not T_u:
            return 0.0
        total_degree = sum(self.degree([u], t)[u] for t in T_u)
        return total_degree / len(T_u)

    def degree_at_time(self, u, t):
        """
        """
        if not self.has_node(u, t):
            return 0
        return self.degree([u], t)[u]

    def expected_degree_at_time(self, t):
        """
        """
        V_t = [v for v in self.nodes() if self.has_node(v, t)]
        if not V_t:
            return 0.0
        total_deg = sum(self.degree([v], t)[v] for v in V_t)
        return total_deg / len(V_t)

    def global_stream_degree(self):
        """
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
        """
        return self.average_expected_stream_degree()

    def interaction_presence(self, u, v):
        """
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
        """
        import dynetx.algorithms as al
        return al.stream_diameter(self, start=start, end=end)

    def stream_lapse(self, start=None, end=None):
        """
        """
        import dynetx.algorithms as al
        return al.stream_lapse(self, start=start, end=end)

    def stream_flood_time(self, start=None, end=None):
        """
        """
        import dynetx.algorithms as al
        return al.stream_flood_time(self, start=start, end=end)

    def stream_time_to_reach(self, u, v, alpha, start=None, end=None):
        """
        """
        import dynetx.algorithms as al
        return al.stream_time_to_reach(self, u, v, alpha, start=start, end=end)

    def constrained_time_respecting_paths(self, u, v=None, start=None, end=None, gamma=1, gamma_prime=None):
        """
        """
        import dynetx.algorithms as al
        return al.constrained_time_respecting_paths(self, u, v=v, start=start, end=end, gamma=gamma, gamma_prime=gamma_prime)

    def stream_weakly_connected_components(self):
        """
        """
        import dynetx.algorithms as al
        return al.stream_weakly_connected_components(self)

    def stream_strongly_connected_components(self):
        """
        """
        import dynetx.algorithms as al
        return al.stream_strongly_connected_components(self)

    def reachability_stream_graph(self):
        """
        """
        import dynetx.algorithms as al
        return al.reachability_stream_graph(self)

    def cluster_internal_neighborhood(self, cluster, v):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_internal_neighborhood(self, cluster, v)

    def cluster_external_neighborhood(self, cluster, v):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_external_neighborhood(self, cluster, v)

    def cluster_internal_degree(self, cluster, v):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_internal_degree(self, cluster, v)

    def cluster_external_degree(self, cluster, v):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_external_degree(self, cluster, v)

    def cluster_average_internal_degree(self, cluster):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_average_internal_degree(self, cluster)

    def cluster_average_external_degree(self, cluster):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_average_external_degree(self, cluster)

    def intra_cluster_density(self, partition):
        """
        """
        import dynetx.algorithms as al
        return al.intra_cluster_density(self, partition)

    def inter_cluster_density(self, partition):
        """
        """
        import dynetx.algorithms as al
        return al.inter_cluster_density(self, partition)

    def cluster_external_density(self, cluster):
        """
        """
        import dynetx.algorithms as al
        return al.cluster_external_density(self, cluster)

    def quotient_stream(self, partition):
        """
        """
        import dynetx.algorithms as al
        return al.quotient_stream(self, partition)

    def line_stream(self):
        """
        """
        import dynetx.algorithms as al
        return al.line_stream(self)

    def stream_k_core(self, k=None):
        """
        """
        import dynetx.algorithms as al
        return al.stream_k_core(self, k=k)

    def stream_path_tree(self, root_node, root_time, path_type='foremost'):
        """
        """
        import dynetx.algorithms as al
        return al.stream_path_tree(self, root_node, root_time, path_type=path_type)

    def stream_cascade(self, root_node, root_time):
        """
        """
        import dynetx.algorithms as al
        return al.stream_cascade(self, root_node, root_time)

    def stream_closeness_centrality(self, v, t):
        """
        """
        import dynetx.algorithms as al
        return al.stream_closeness_centrality(self, v, t)

    def stream_betweenness_centrality(self):
        """
        """
        import dynetx.algorithms as al
        return al.stream_betweenness_centrality(self)

    def stream_node_betweenness_centrality(self):
        """
        """
        import dynetx.algorithms as al
        return al.stream_node_betweenness_centrality(self)

    def stream_time_betweenness_centrality(self):
        """
        """
        import dynetx.algorithms as al
        return al.stream_time_betweenness_centrality(self)

    def delta_substream(self, t, delta):
        """
        """
        import dynetx.algorithms as al
        return al.delta_substream(self, t, delta)

    def delta_density(self, t, delta):
        """
        """
        import dynetx.algorithms as al
        return al.delta_density(self, t, delta)

    def delta_degree(self, v, t, delta):
        """
        """
        import dynetx.algorithms as al
        return al.delta_degree(self, v, t, delta)

    def pair_density(self, u, v):
        """
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
        """
        return nx.density(self.time_slice(t))

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
        Return the temporal support of nodes.
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
        """
        Remove edge ``(u, v)`` from the graph.
        """
        self._remove_edge_instance(u, v)

    def remove_edges_from(self, ebunch):
        """
        Remove every edge in ``ebunch``.
        """
        for e in ebunch:
            self.remove_edge(e[0], e[1])

    def remove_node(self, u):
        """
        Remove node ``u`` and all of its incident interactions.
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
        """
        Remove every node in ``nbunch``.
        """
        for n in list(nbunch):
            self.remove_node(n)

    def add_edge(self, u, v, attr_dict=None, **attr):
        """
        Add an interaction using the NetworkX edge API.
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
        Add multiple interactions using the NetworkX edge API.
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
        """
        Iterate over the interactions of the graph.
        """
        for u, v, d in self.interactions_iter(nbunch):
            if data:
                yield u, v, d
            else:
                yield u, v

    def edges(self, nbunch=None, data=False, default=None):
        """
        Return the interactions of the graph as a list.
        """
        return list(self.edges_iter(nbunch=nbunch, data=data, default=default))

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
            nbrs.update(self.neighbors(n, t=tid))
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
                attrs = dict(d)
                nxg.add_edge(u, v, **attrs)
        else:
            for u, v, d in self.interactions_iter():
                if self.has_interaction(u, v, t):
                    attrs = {k: val for k, val in d.items() if k != "t"}
                    nxg.add_edge(u, v, **attrs)
        return nxg
