import networkx as nx
import copy

__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"


class DynGraph(nx.Graph):
    def __init__(self, data=None, **attr):
        super(self.__class__, self).__init__(data, **attr)
        self.time_to_edge = {}
        self.snapshots = {}

    def temporal_snapshots(self):
        return sorted(self.snapshots.keys())

    def number_of_interactions(self, t=None):
        if t is None:
            return self.snapshots
        else:
            try:
                return self.snapshots[t]
            except KeyError:
                raise KeyError("Snapshot not present.")

    def nodes_iter(self, t=None, data=False):
        if t is not None:
            return iter([n for n in self.degree(t=t).values() if n > 0])
        return iter(self.node)

    def nodes(self, t=None, data=False):
        return list(self.nodes_iter(t=t, data=data))

    def edges(self, nbunch=None, t=None, data=False, default=None):
        return list(self.edges_iter(nbunch, t, data, default))

    def edges_iter(self, nbunch=None, t=None, data=False, default=None):
        seen = {}  # helper dict to keep track of multiply stored edges
        if nbunch is None:
            nodes_nbrs = self.adj.items()
        else:
            nodes_nbrs = ((n, self.adj[n]) for n in self.nbunch_iter(nbunch))

        for n, nbrs in nodes_nbrs:
            for nbr in nbrs:
                if t is not None:
                    if nbr not in seen and t in self.adj[n][nbr]['t']:
                        yield (n, nbr, {"t": [t]})
                else:
                    if nbr not in seen:
                        yield (n, nbr, self.adj[n][nbr])
                seen[n] = 1
        del seen

    def add_edge(self, u, v, t=None, e=None, attr_dict=None, **attr):
        if t is None:
            raise nx.NetworkXError(
                "The t argument must be specified.")

        if u not in self.node:
            self.adj[u] = self.adjlist_dict_factory()
            self.node[u] = {}
        if v not in self.node:
            self.adj[v] = self.adjlist_dict_factory()
            self.node[v] = {}

        if type(t) != list:
            t = [t]

        for idt in t:
            if idt not in self.time_to_edge:
                self.time_to_edge[idt] = [(u, v, "+")]
            else:
                self.time_to_edge[idt].append((u, v, "+"))

        if e is not None:
            if e not in self.time_to_edge:
                self.time_to_edge[e] = [(u, v, "-")]
            else:
                self.time_to_edge[e].append((u, v, "-"))

        # add the edge
        datadict = self.adj[u].get(v, self.edge_attr_dict_factory())

        old_t = copy.deepcopy(t)
        if 't' in datadict:
            t.extend(datadict['t'])
            if e is not None:
                t.extend(range(max(t), e))

        if e is not None:
            span = range(max(old_t), e)
            t.extend(span)
            for idt in span:
                if idt not in self.snapshots:
                    self.snapshots[idt] = 1
                else:
                    self.snapshots[idt] += 1
        else:
            for idt in t:
                if idt not in self.snapshots:
                    self.snapshots[idt] = 1
                else:
                    self.snapshots[idt] += 1

        datadict.update({'t': t})
        datadict['t'] = sorted(list(set(t)))

        self.adj[u][v] = datadict
        self.adj[v][u] = datadict

    def add_edges_from(self, ebunch, t=None, attr_dict=None, **attr):
        # set up attribute dict
        if t is None:
            raise nx.NetworkXError(
                "The t argument must be a specified.")
        # process ebunch
        for e in ebunch:
            self.add_edge(e[0], e[1], t)

    def remove_edge(self, u, v, t=None):
        try:
            if t is None:
                del self.adj[v][u]

            edge_pres = self.adj[u][v]['t']
            if t in edge_pres:
                edge_pres.remove(t)
            if len(edge_pres) == 0:
                del self.adj[u][v]
                if u != v:  # self-loop needs only one entry removed
                    del self.adj[v][u]
            else:
                self.adj[u][v]['t'] = edge_pres
        except KeyError:
            raise nx.NetworkXError("The edge %s-%s is not in the graph" % (u, v))

    def remove_edges_from(self, ebunch, t=None):
        for e in ebunch:
            self.remove_edge(e[0], e[1], t)

    def number_of_edges(self, u=None, v=None, t=None):
        if t is None:
            if u is None:
                return int(self.size())
            if v in self.adj[u]:
                return 1
            else:
                return 0
        else:
            if u is None:
                return int(self.size(t))
            if v in self.adj[u]:
                if t in self.adj[u][v]:
                    return 1
                else:
                    return 0

    def has_edge(self, u, v, t=None):
        try:
            if t is None:
                return v in self.adj[u]
            else:
                return v in self.adj[u] and t in self.adj[u][v]['t']
        except KeyError:
            return False

    def neighbors(self, n, t=None):
        try:
            if t is None:
                return list(self.adj[n])
            else:
                return [i for i in self.adj[n] if t in self.adj[n][i]['t']]
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def neighbors_iter(self, n, t=None):
        try:
            if t is None:
                return iter(self.adj[n])
            else:
                return iter([i for i in self.adj[n] if t in self.adj[n][i]['t']])
        except KeyError:
            raise nx.NetworkXError("The node %s is not in the graph." % (n,))

    def degree(self, nbunch=None, t=None):

        if nbunch in self:  # return a single node
            return next(self.degree_iter(nbunch, t))[1]
        else:  # return a dict
            return dict(self.degree_iter(nbunch, t))

    def degree_iter(self, nbunch=None, t=None):
        if nbunch is None:
            nodes_nbrs = self.adj.items()
        else:
            nodes_nbrs = ((n, self.adj[n]) for n in self.nbunch_iter(nbunch))

        if t is None:
            for n, nbrs in nodes_nbrs:
                yield (n, len(nbrs) + (n in nbrs))  # return tuple (n,degree)
        else:
            # edge weighted graph - degree is sum of nbr edge weights
            for n, nbrs in nodes_nbrs:
                edges_t = len([v for v, k in nbrs.items() if t in k['t']])
                yield (n, edges_t)

    def size(self, t=None, weight=None):
        s = sum(self.degree(t=t).values()) / 2
        return int(s)

    def number_of_nodes(self, t=None):
        if t is None:
            return len(self.node)
        else:
            nds = sum([1 for n in self.degree(t=t).values() if n > 0])
            return nds

    def order(self, t=None):
        return self.number_of_nodes(t)

    def has_node(self, n, t=None):
        if t is None:
            try:
                return n in self.node
            except TypeError:
                return False
        else:
            return self.degree([n], t).values()[0] > 0

    def add_star(self, nodes, t=None, **attr):
        nlist = list(nodes)
        v = nlist[0]
        edges = ((v, n) for n in nlist[1:])
        self.add_edges_from(edges, t, **attr)

    def add_path(self, nodes, t=None, **attr):
        nlist = list(nodes)
        edges = zip(nlist[:-1], nlist[1:])
        self.add_edges_from(edges, t, **attr)

    def add_cycle(self, nodes, t=None, **attr):
        nlist = list(nodes)
        edges = zip(nlist, nlist[1:] + [nlist[0]])
        self.add_edges_from(edges, t, **attr)

    def stream_edges(self):
        timestamps = sorted(self.time_to_edge.keys())
        for t in timestamps:
            for e in self.time_to_edge[t]:
                yield (e[0], e[1], e[2], t)

    def time_slice(self, t_from, t_to=None):
        # create new graph and copy subgraph into it
        H = self.__class__()
        if t_to is None:
            t_to = t_from

        # copy node and attribute dictionaries
        for ed in self.edges(data=True):
            ixs, ixe = -1, -1
            e = copy.deepcopy(ed)

            if e[2]['t'][0] > t_from:
                ot_from = e[2]['t'][0]
                ixs = 0
            else:
                ot_from = t_from
            if e[2]['t'][-1] < t_to:
                ot_to = e[2]['t'][-1]
                ixe = len(e[2]['t']) - 1
            else:
                ot_to = t_to

            if ot_from > t_to:
                continue

            if ixs < 0:
                try:
                    ixs = e[2]['t'].index(ot_from)
                except ValueError:
                    continue

            if ixe < 0:
                ixe = ixs
                while e[2]['t'][ixe] < ot_to:
                    ixe += 1

            if ixs == ixe:
                ixe += 1

            attr = e[2]
            attr['t'] = e[2]['t'][ixs:ixe]
            for t in attr['t']:
                H.add_edge(e[0], e[1], t)
        return H
