import networkx as nx


__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"


class SNGraph(nx.Graph):

    def __main__(self, data=None, **attr):
        super(self.__class__, self).__init__(data, **attr)

    def add_edge(self, u, v, attr_dict=None, **attr):

        if attr_dict is None or 'time' not in attr_dict:
            raise nx.NetworkXError(
                "Attribute 'time' required")
        else:
            try:
                attr_dict.update(attr)
            except AttributeError:
                raise nx.NetworkXError(
                    "The attr_dict argument must be a dictionary.")

        # add nodes
        if u not in self.node:
            self.adj[u] = self.adjlist_dict_factory()
            self.node[u] = {}
        if v not in self.node:
            self.adj[v] = self.adjlist_dict_factory()
            self.node[v] = {}

        # add the edge
        datadict = self.adj[u].get(v, self.edge_attr_dict_factory())

        if type(attr_dict['time']) is list:
            presences = attr_dict['time']
        else:
            presences = [attr_dict['time']]

        if 'time' in datadict:
            presences.extend(datadict['time'])

        # @todo: handle attributes attached to a single temporal edge
        datadict.update(attr_dict)
        datadict['time'] = sorted(list(set(presences)))

        self.adj[u][v] = datadict
        self.adj[v][u] = datadict

    def time_slice(self, t_from, t_to):

        # create new graph and copy subgraph into it
        H = self.__class__()
        # copy node and attribute dictionaries
        for e in self.edges(data=True):
            if e[2]['time'][0] > t_from:
                ot_from = e[2]['time'][0]
            else:
                ot_from = t_from
            if e[2]['time'][-1] < t_to:
                ot_to = e[2]['time'][-1]
            else:
                ot_to = t_to

            ixs = e[2]['time'].index(ot_from)
            ixe = len(e[2]['time']) - e[2]['time'][::-1].index(ot_to)
            attr = e[2]
            attr['time'] = e[2]['time'][ixs:ixe]
            attr['pres'] = float(len(attr['time']))/((t_to+1)-t_from)
            H.add_edge(int(e[0]), int(e[1]), attr)
        return H

    def remove_edge(self, u, v, t=None):
        try:
            if t is None:
                del self.adj[v][u]

            edge_pres = self.adj[u][v]['time']
            if t in edge_pres:
                edge_pres.remove(t)
            if len(edge_pres) == 0:
                del self.adj[u][v]
                if u != v:  # self-loop needs only one entry removed
                    del self.adj[v][u]
            else:
                self.adj[u][v]['time'] = edge_pres
        except KeyError:
            raise ValueError("The edge %s-%s is not in the graph" % (u, v))

    def has_edge(self, u, v, t=None):
        try:
            if t is None:
                return v in self.adj[u]
            else:
                return v in self.adj[u] and t in self.adj[u][v]['time']
        except KeyError:
            return False

    def neighbors(self, n, time=None):
        try:
            if time is None:
                return list(self.adj[n])
            else:
                return [i for i in self.adj[n] if time in self.adj[n][i]['time']]
        except KeyError:
            raise ValueError("The node %s is not in the graph." % (n,))

    def neighbors_iter(self, n, time=None):
        try:
            if time is None:
                return iter(self.adj[n])
            else:
                return iter([i for i in self.adj[n] if time in self.adj[n][i]['time']])
        except KeyError:
            raise ValueError("The node %s is not in the graph." % (n,))

    def degree(self, nbunch=None, time=None):

        if nbunch in self:      # return a single node
            return next(self.degree_iter(nbunch, time))[1]
        else:           # return a dict
            return dict(self.degree_iter(nbunch, time))

    def degree_iter(self, nbunch=None, time=None):
        if nbunch is None:
            nodes_nbrs = self.adj.items()
        else:
            nodes_nbrs = ((n, self.adj[n]) for n in self.nbunch_iter(nbunch))

        if time is None:
            for n, nbrs in nodes_nbrs:
                yield (n, len(nbrs) + (n in nbrs))  # return tuple (n,degree)
        else:
            # edge weighted graph - degree is sum of nbr edge weights
            for n, nbrs in nodes_nbrs:
                edges_t = len([v for v, k in nbrs.iteritems() if time in k['time']])
                yield (n, edges_t)