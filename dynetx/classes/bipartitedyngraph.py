import networkx as nx
from itertools import combinations
from dynetx.classes.dyngraph import DynGraph

class BipartiteDynGraph(DynGraph):
    """
    Represent bipartite stream graphs with top and bottom node partitions.

    The class extends :class:`dynetx.classes.dyngraph.DynGraph` with simple
    partition management helpers and bipartite-specific summary methods.
    

    Examples
    --------
    >>> import dynetx as dn
    >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
    >>> G.BipartiteDynGraph()
"""
    def __init__(self, top_nodes=None, bottom_nodes=None, **kwargs):
        """Create a bipartite dynamic graph.

        Parameters
        ----------
        top_nodes : iterable, optional
            Initial nodes assigned to the top partition.
        bottom_nodes : iterable, optional
            Initial nodes assigned to the bottom partition.
        **kwargs
            Additional keyword arguments forwarded to ``DynGraph``.

        Returns
        -------
        BipartiteDynGraph
            Empty bipartite dynamic graph with the requested partitions.
        """
        super().__init__(**kwargs)
        self.top = set(top_nodes) if top_nodes is not None else set()
        self.bottom = set(bottom_nodes) if bottom_nodes is not None else set()

    def add_node_to_top(self, node):
        """Add a node to the top partition.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_node_to_top(0)
"""
        self.top.add(node)
        self.bottom.discard(node)

    def add_node_to_bottom(self, node):
        """Add a node to the bottom partition.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_node_to_bottom(1)
"""
        self.bottom.add(node)
        self.top.discard(node)

    def is_bipartite(self):
        """Return ``True`` when every active interaction crosses partitions.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_interaction(0, 1, t=0)
        >>> G.is_bipartite()
"""
        tids = self.temporal_snapshots_ids()
        for t in tids:
            for u, v, _ in self.interactions(t=t):
                u_in_top = u in self.top
                v_in_top = v in self.top
                u_in_bottom = u in self.bottom
                v_in_bottom = v in self.bottom
                if not ((u_in_top and v_in_bottom) or (u_in_bottom and v_in_top)):
                    return False
        return True

    def bipartite_density(self):
        """Return the temporal bipartite density of the graph.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_interaction(0, 1, t=0)
        >>> G.bipartite_density()
"""
        tids = self.temporal_snapshots_ids()
        if not tids:
            return 0.0
        total_edges = 0
        total_possible = 0
        for t in tids:
            edges = self.interactions(t=t)
            total_edges += len(edges)
            active = set(self.nodes(t=t))
            top_t = self.top & active
            bottom_t = self.bottom & active
            total_possible += len(top_t) * len(bottom_t)
        if total_possible == 0:
            return 0.0
        return total_edges / total_possible

    def bipartite_projection(self, target='top'):
        """Return the temporal projection of the graph onto one partition.

        Parameters
        ----------
        target : {"top", "bottom"}, optional
            Partition to project onto.

        Returns
        -------
        DynGraph
            Projection graph with temporal interactions induced by shared
            neighbors.
        

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_interaction(0, 1, t=0)
        >>> G.bipartite_projection(target="top")
"""
        proj = DynGraph(edge_removal=self.edge_removal)
        nodes = self.top if target == 'top' else self.bottom
        other = self.bottom if target == 'top' else self.top
        
        tids = self.temporal_snapshots_ids()
        for t in tids:
            sg = self.to_networkx_graph(t=t)
            active = set(self.nodes(t=t))
            active_target = nodes & active
            active_other = other & active
            
            for w in active_other:
                neighbors = list(sg.neighbors(w))
                target_neighbors = [n for n in neighbors if n in active_target]
                for u, v in combinations(target_neighbors, 2):
                    proj.add_interaction(u, v, t=t)
        return proj

    def bipartite_redundancy(self, v):
        """Return the average bipartite redundancy of node ``v``.

        Examples
        --------
        >>> import dynetx as dn
        >>> G = dn.BipartiteDynGraph(top_nodes=[0], bottom_nodes=[1])
        >>> G.add_interaction(0, 1, t=0)
        >>> G.bipartite_redundancy(0)
"""
        tids = self.temporal_snapshots_ids()
        total_red = 0.0
        count = 0
        for t in tids:
            if self.has_node(v, t):
                sg = self.to_networkx_graph(t=t)
                neighbors = list(sg.neighbors(v))
                if len(neighbors) < 2:
                    continue
                
                shared_count = 0
                for u, w in combinations(neighbors, 2):
                    common = set(sg.neighbors(u)) & set(sg.neighbors(w))
                    common.discard(v)
                    if common:
                        shared_count += 1
                possible = len(neighbors) * (len(neighbors) - 1) / 2
                total_red += shared_count / possible
                count += 1
        if count == 0:
            return 0.0
        return total_red / count
