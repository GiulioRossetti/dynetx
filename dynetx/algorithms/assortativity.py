from itertools import combinations
from tqdm import tqdm
from collections import defaultdict
import dynetx as dn
from .paths import *
import networkx as nx

__all__ = ["delta_conformity", "sliding_delta_conformity"]


def __label_frequency(g: dn.DynGraph, u: object, nodes: list, labels: list, hierarchies: dict = None,
                      t_dist: dict = None, start=None) -> float:
    """
    Compute the similarity of node profiles
    :param g: a networkx Graph object
    :param u: node id
    :param labels: list of node categorical labels
    :param hierarchies: dict of labels hierarchies
    :return: node profiles similarity score in [-1, 1]
    """
    s = 1

    for label in labels:

        a_u = g._node[u][label]

        if isinstance(a_u, dict):
            a_u = a_u[start]

        # set of nodes at given distance
        sgn = {}
        for v in nodes:

            a_v = g._node[v][label]

            if isinstance(a_v, dict):
                t = t_dist[v]
                if t in a_v:
                    a_v = a_v[t]
                else:
                    continue

            # indicator function that exploits label hierarchical structure
            sgn[v] = 1 if a_u == a_v else __distance(label, a_u, a_v, hierarchies)
            v_neigh = list(g.neighbors(v, t_dist[v]))
            # compute the frequency for the given node at distance n over neighbors label

            f_label = 0
            for x in v_neigh:
                a_x = g._node[x][label]
                # tx = t_dist[x]
                if isinstance(a_x, dict):
                    a_x = a_x[t_dist[v]]
                if a_x == a_v:
                    f_label += 1

            f_label = (f_label / len(v_neigh)) if len(v_neigh) > 0 else 0
            f_label = f_label if f_label > 0 else 1
            sgn[v] *= f_label
        s *= sum(sgn.values()) / len(nodes)

    return s


def __distance(label: str, v1: str, v2: str, hierarchies: dict = None) -> float:
    """
    Compute the distance of two labels in a plain hierarchy
    :param label: label name
    :param v1: first label value
    :param v2: second label value
    :param hierarchies: labels hierarchies
    """
    if hierarchies is None or label not in hierarchies:
        return -1

    return -abs(hierarchies[label][v1] - hierarchies[label][v2]) / (len(hierarchies[label]) - 1)


def __normalize(u: object, scores: list, max_dist: int, alphas: list):
    """
    Normalize the computed scores in [-1, 1]
    :param u: node
    :param scores: datastructure containing the computed scores for u
    :param alphas: list of damping factor
    :return: scores updated
    """
    for alpha in alphas:
        norm = sum([(d ** -alpha) for d in range(1, max_dist + 1)])

        for profile in scores["%.2f" % alpha]:
            scores["%.2f" % alpha][profile][u] /= norm

    return scores


def __remap_path_distances(temporal_distances):
    """
    Mapping shortest paths temporal distances in hop distances

    :param temporal_distances: a dictionary of <node_id, reach_time>
    :return: a dictionary <node_id, hop_distance>
    """
    res = {}
    tids = sorted(set(temporal_distances.values()))
    tids = {t: pos + 1 for pos, t in enumerate(tids)}
    for k, v in list(temporal_distances.items()):
        res[k] = tids[v]
    return res


def delta_conformity(dg, start: int, delta: int, alphas: list, labels: list, profile_size: int = 1,
                     hierarchies: dict = None, path_type="shortest", progress_bar: bool = False,
                     sample: float = 1) -> dict:
    """
    Compute the Delta-Conformity for the considered dynamic graph
    :param dg: a dynetx Graph object composed by a single component
    :param start: the starting temporal id
    :param delta: the max duration of time respecting paths
    :param alphas: list of damping factors
    :param labels: list of node categorical labels
    :param profile_size:
    :param hierarchies: label hierarchies
    :param path_type: time respecting path type. String among: shortest, fastest, foremost, fastest_shortest and shortest_fastest (default: shortest)
    :param progress_bar: wheter to show the progress bar, default false
    :return: conformity value for each node in [-1, 1]

    -- Example --
    >> g = dn.DynGraph()
    >>
    >>  labels = ['SI', 'NO']
    >>  nodes = ['A', 'B', 'C', 'D']
    >>
    >> for node in nodes:
    >>      g.add_node(node, labels=random.choice(labels))
    >>
    >>  g.add_interaction("A", "B", 1, 4)
    >>  g.add_interaction("B", "D", 2, 5)
    >>  g.add_interaction("A", "C", 4, 8)
    >>  g.add_interaction("B", "D", 2, 4)
    >>  g.add_interaction("B", "C", 6, 10)
    >>  g.add_interaction("B", "D", 2, 4)
    >>  g.add_interaction("A", "B", 7, 9)
    >>
    >>  res = al.delta_conformity(g, 1, 5, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1, path_type="fastest")

    """

    if profile_size > len(labels):
        raise ValueError("profile_size must be <= len(labels)")

    if len(alphas) < 1 or len(labels) < 1:
        raise ValueError("At list one value must be specified for both alphas and labels")

    profiles = []
    for i in range(1, profile_size + 1):
        profiles.extend(combinations(labels, i))

    g = dg.time_slice(t_from=start, t_to=start + delta)

    res = {"%.2f" % a: {"_".join(profile): {n: 0 for n in g.nodes(t=start)} for profile in profiles} for a in alphas}

    tids = g.temporal_snapshots_ids()
    if len(tids) == 0:
        return None

    mid = max(tids)
    mmid = min(tids)

    sp = all_time_respecting_paths(g, max(start, mmid), min(mid, delta + start), sample=sample, min_t=mmid)

    t_distances = defaultdict(lambda: defaultdict(int))
    for k, v in list(sp.items()):
        ss = [x[-1] for x in annotate_paths(v)[path_type]]
        ss = [x[-1] for x in ss]
        t_distances[k[0]][k[1]] = min(ss)

    distances = defaultdict(lambda: defaultdict(int))
    for k in t_distances:
        distances[k] = __remap_path_distances(t_distances[k])

    for u in tqdm(g.nodes(t=start), disable=not progress_bar):

        sp = dict(distances[u])

        dist_to_nodes = defaultdict(list)
        for node, dist in list(sp.items()):
            dist_to_nodes[dist].append(node)
        sp = dist_to_nodes

        for dist, nodes in list(sp.items()):
            if dist != 0:
                for profile in profiles:
                    sim = __label_frequency(g, u, nodes, list(profile), hierarchies, t_distances[u], start)

                    for alpha in alphas:
                        partial = sim / (dist ** alpha)
                        p_name = "_".join(profile)
                        res["%.2f" % alpha][p_name][u] += partial

        if len(sp) > 0:
            res = __normalize(u, res, max(sp.keys()), alphas)

    return res


def sliding_delta_conformity(dg, delta: int, alphas: list, labels: list, profile_size: int = 1,
                             hierarchies: dict = None, path_type="shortest", progress_bar: bool = False,
                             sample: float = 1) -> dict:
    """
    Compute the Delta-Conformity for the considered dynamic graph on a sliding window of predefined size

    :param dg: a dynetx Graph object composed by a single component
    :param delta: the max duration of time respecting paths
    :param alphas: list of damping factors
    :param labels: list of node categorical labels
    :param profile_size:
    :param hierarchies: label hierarchies
    :param path_type: time respecting path type. String among: shortest, fastest, foremost, fastest_shortest and shortest_fastest (default: shortest)
    :param progress_bar: wheter to show the progress bar, default false
    :return: conformity trend value for each node

    -- Example --

    >> g = dn.DynGraph()
    >>
    >>  labels = ['SI', 'NO']
    >>  nodes = ['A', 'B', 'C', 'D']
    >>
    >> for node in nodes:
    >>      g.add_node(node, labels=random.choice(labels))
    >>
    >>  g.add_interaction("A", "B", 1, 4)
    >>  g.add_interaction("B", "D", 2, 5)
    >>  g.add_interaction("A", "C", 4, 8)
    >>  g.add_interaction("B", "D", 2, 4)
    >>  g.add_interaction("B", "C", 6, 10)
    >>  g.add_interaction("B", "D", 2, 4)
    >>  g.add_interaction("A", "B", 7, 9)
    >>
    >>  res = al.sliding_delta_conformity(g, 2, list(np.arange(1, 4, 0.2)), ['labels'], profile_size=1, path_type="fastest")

    """
    tids = dn.temporal_snapshots_ids(dg)

    alpha_attribute_node_to_seq = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for t in tqdm(tids, disable=not progress_bar):
        if t + delta < tids[-1]:
            dconf = delta_conformity(dg, t, delta, alphas, labels, profile_size, hierarchies, path_type,
                                     progress_bar=not progress_bar, sample=sample)
            if dconf is None:
                continue
            for alpha, data in list(dconf.items()):
                for attribute, node_values in list(data.items()):
                    for n, v in list(node_values.items()):
                        alpha_attribute_node_to_seq[alpha][attribute][n].append((t + delta, v))

    return alpha_attribute_node_to_seq
