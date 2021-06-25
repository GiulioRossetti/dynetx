import networkx as nx
import itertools
import tqdm
import random
import numpy as np

__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"

__all__ = ['time_respecting_paths', 'all_time_respecting_paths', 'annotate_paths', 'temporal_dag', 'path_duration',
           'path_length']


def temporal_dag(G, u, v=None, start=None, end=None):
    """
        Creates a rooted temporal DAG assuming interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
            The graph to use for computing DAG
        u : a node id
            A node in G
        v : a node id
            A node in G, default None
        start : temporal id
            min temporal id for bounding the DAG, default None
        end : temporal id to conclude the search
            max temporal id for bounding the DAG, default None

        Returns
        --------
        DAG: a directed graph
            A DAG rooted in u (networkx DiGraph object)
        sources: source node ids
            List of temporal occurrences of u
        targets: target node ids
            List of temporal occurrences of v
        node_type: type
            network node_type
        tid_type: type
            network temporal id type

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> DAG, sources, targets, _, _ = al.temporal_dag(g, "D", "C", start=1, end=9)

    """
    ids = G.temporal_snapshots_ids()
    if len(ids) == 0:
        return nx.DiGraph(), [], [], int, int

    tid_type = type(ids[0])
    node_type = type(u)

    # correcting missing values
    if end is None:
        end = ids[-1]

    if start is None:
        start = ids[0]

    if start < min(ids) or start > end or end > max(ids) or start > max(ids):
        raise ValueError(f"The specified interval {[start, end]} is not a proper subset of the network timestamps "
                         f"{[min(ids), max(ids)]}.")

    # adjusting temporal window
    start = list([i >= start for i in ids]).index(True)
    end = end if end == ids[-1] else list([i > end for i in ids]).index(True)
    ids = ids[start:end]

    # creating empty DAG
    DG = nx.DiGraph()
    DG.add_node(u)
    active = {u: None}
    sources, targets = {}, {}

    for tid in ids:
        to_remove = []
        to_add = []
        for an in active:
            neighbors = {f"{n}_{tid}": None for n in G.neighbors(node_type(str(an).split("_")[0]), tid)}
            if v is not None:
                if f"{v}_{tid}" in neighbors:
                    targets[f"{v}_{tid}"] = None
            else:
                for k in neighbors:
                    targets[k] = None

            if len(neighbors) == 0 and an != u:
                to_remove.append(an)

            for n in neighbors:
                if isinstance(an, node_type):
                    if not isinstance(an, str) or (isinstance(an, str) and '_' not in an):
                        an = f"{an}_{tid}"
                        sources[an] = None

                DG.add_edge(an, n)
                to_add.append(n)

        for n in to_add:
            active[n] = None

        for rm in to_remove:
            del active[rm]

    return DG, list(sources), list(targets), node_type, tid_type


def time_respecting_paths(G, u, v=None, start=None, end=None, sample=1):
    """
        Computes all the simple time respecting paths among u and v within [start, stop].
        It assumes interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
            The graph to use for computing DAG
        u : a node id
            A node in G
        v : a node id
            A node in G
        start : temporal id
            min temporal id for bounding the DAG, default None
        end : temporal id to conclude the search
            max temporal id for bounding the DAG, default None
        sample : percentage of connected node pairs for which compute the time respecting paths. Default 1.

        Returns
        --------
        paths: list
            The list of paths, each one expressed as a list of timestamped interactions

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> paths = al.time_respecting_paths(g, "D", "C", start=1, end=9)

    """
    if not G.has_node(u, start):
        return []

    DAG, sources, targets, n_type, t_type = temporal_dag(G, u, v=v, start=start, end=end)

    pairs = [(x, y) for x in sources for y in targets]
    if sample < 1:
        to_sample = int(len(pairs) * sample)
        pairs_idx = np.random.choice(len(pairs), size=to_sample, replace=False)
        pairs = np.array(pairs)[pairs_idx]

    paths = []
    for pair in pairs:
        path = list(nx.all_simple_paths(DAG, pair[0], pair[1]))

        for p in path:
            pt = []
            for first, second in zip(p, p[1:]):
                u = first.split("_")
                if len(u) == 2:
                    u = u[0]
                else:
                    u = "_".join(u[0:-1])

                v = second.split("_")
                if len(v) == 2:
                    t = v[1]
                    v = v[0]
                else:
                    t = v[-1]
                    v = "_".join(v[0:-1])

                pt.append((n_type(u), n_type(v), t_type(t)))
            paths.append(pt)
    return paths


def all_time_respecting_paths(G, start=None, end=None, sample=1, min_t=None):
    """
        Computes all the simple paths among network node pairs.
        It assumes interaction chains of length 1 within each network snapshot.

        Parameters
        ----------
        G : a DynGraph or DynDiGraph object
            The graph to use for computing DAG
        start : temporal id
            min temporal id for bounding the DAG, default None
        end : temporal id to conclude the search
            max temporal id for bounding the DAG, default None
        sample : percentage of paths to compute. Default, 1
        min_t : temporal id for the source nodes, Default, None (all possible tids in [start, end])

        Returns
        --------
        paths: dictionary
            A dictionary that associate to each node pair (u,v) the list of paths connecting them.

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> paths = al.all_time_respecting_paths(g, start=1, end=9)

    """
    res = {}

    for u in tqdm.tqdm(G.nodes(t=min_t)):
        paths = list(time_respecting_paths(G, u, v=None, start=start, end=end, sample=sample))
        if len(paths) > 0:
            for path in paths:
                v = path[-1][1]
                res[(u, v)] = paths

    return res


def annotate_paths(paths):
    """
        Annotate a set of paths identifying peculiar types of paths.

        - **shortest**: topological shortest paths
        - **fastest**: paths that have minimal duration
        - **foremost**: first paths that reach the destination
        - **shortest fastest**: minimum length path among minimum duration ones
        - **fastest shortest**: minimum duration path among minimum length ones

        Parameters
        ----------
        paths : list
            a list of paths among a same node pair

        Returns
        --------
        annotated: dictionary
            A mapping for shortest, fastest, foremost, fastest_shortest and shortest_fastest paths.

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> paths = al.time_respecting_paths(g, "D", "C", start=1, end=9)
        >>> annotated = al.annotate_paths(paths)

    """
    annotated = {"shortest": None, "fastest": None, "shortest_fastest": None,
                 "fastest_shortest": None, "foremost": None}

    min_to_reach = None
    shortest = None
    fastest = None

    for path in paths:
        length = path_length(path)
        duration = path_duration(path)
        reach = path[-1][-1]

        if shortest is None or length < shortest:
            shortest = length
            annotated['shortest'] = [path]
        elif length == shortest:
            annotated['shortest'].append(path)

        if fastest is None or duration < fastest:
            fastest = duration
            annotated['fastest'] = [path]
        elif duration == fastest:
            annotated['fastest'].append(path)

        if min_to_reach is None or reach < min_to_reach:
            min_to_reach = reach
            annotated['foremost'] = [path]
        elif reach == min_to_reach:
            annotated['foremost'].append(path)

    fastest_shortest = {tuple(path): path_duration(path) for path in annotated['shortest']}
    minval = min(fastest_shortest.values())
    fastest_shortest = list([x for x in fastest_shortest if fastest_shortest[x] == minval])

    shortest_fastest = {tuple(path): path_length(path) for path in annotated['fastest']}
    minval = min(shortest_fastest.values())
    shortest_fastest = list([x for x in shortest_fastest if shortest_fastest[x] == minval])

    annotated['fastest_shortest'] = [list(p) for p in fastest_shortest]
    annotated['shortest_fastest'] = [list(p) for p in shortest_fastest]

    return annotated


def path_length(path):
    """
        Computes the topological length of a given path.

        Parameters
        ----------
        path : a path
            list of interactions forming a path among a node pair

        Returns
        --------
        length: int
            The number of interactions composing the path

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> paths = al.time_respecting_paths(g, "D", "C", start=1, end=9)
        >>> for p in paths:
        >>>     print(al.path_length(p))

    """
    return len(path)


def path_duration(path):
    """
        Computes the timespan of a given path.

        Parameters
        ----------
        path : a path
            list of interactions forming a path among a node pair

        Returns
        --------
        duration: int
            The duration of the path

        Examples
        --------

        >>> import dynetx as dn
        >>> g = dn.DynGraph()
        >>> g.add_interaction("A", "B", 1, 4)
        >>> g.add_interaction("B", "D", 2, 5)
        >>> g.add_interaction("A", "C", 4, 8)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("B", "C", 6, 10)
        >>> g.add_interaction("B", "D", 2, 4)
        >>> g.add_interaction("A", "B", 7, 9)
        >>> paths = al.time_respecting_paths(g, "D", "C", start=1, end=9)
        >>> for p in paths:
        >>>     print(al.path_duration(p))

    """
    return path[-1][-1] - path[0][-1]
