import networkx as nx
from collections import defaultdict
from itertools import combinations
from dynetx.classes.cluster import Cluster
from dynetx import DynDiGraph

__all__ = [
    'stream_diameter',
    'stream_lapse',
    'stream_flood_time',
    'stream_time_to_reach',
    'constrained_time_respecting_paths',
    'stream_weakly_connected_components',
    'stream_strongly_connected_components',
    'reachability_stream_graph',
    'cluster_internal_neighborhood',
    'cluster_external_neighborhood',
    'cluster_internal_degree',
    'cluster_external_degree',
    'cluster_average_internal_degree',
    'cluster_average_external_degree',
    'intra_cluster_density',
    'inter_cluster_density',
    'cluster_external_density',
    'quotient_stream',
    'line_stream',
    'stream_k_core',
    'stream_path_tree',
    'stream_cascade',
    'stream_closeness_centrality',
    'stream_betweenness_centrality',
    'stream_node_betweenness_centrality',
    'stream_time_betweenness_centrality',
    'delta_substream',
    'delta_density',
    'delta_degree'
]

def stream_diameter(G, start=None, end=None):
    """
        Return the diameter of the stream graph (largest finite distance).
    """
    from dynetx.algorithms.paths import all_time_respecting_paths
    paths = all_time_respecting_paths(G, start=start, end=end)
    if not paths:
        return 0
    max_dist = 0
    for (u, v), plist in paths.items():
        if u == v:
            continue
        windows = {(p[0][2], p[-1][2]) for p in plist}
        for t1, t2 in windows:
            candidates = [len(p) for p in plist if p[0][2] >= t1 and p[-1][2] <= t2]
            if candidates:
                max_dist = max(max_dist, min(candidates))
    return max_dist

def stream_lapse(G, start=None, end=None):
    """
        Return the lapse of the stream graph (largest finite latency).
    """
    from dynetx.algorithms.paths import all_time_respecting_paths
    paths = all_time_respecting_paths(G, start=start, end=end)
    if not paths:
        return 0
    max_lat = 0
    for (u, v), plist in paths.items():
        if u == v:
            continue
        windows = {(p[0][2], p[-1][2]) for p in plist}
        for t1, t2 in windows:
            candidates = [p[-1][2] - p[0][2] for p in plist if p[0][2] >= t1 and p[-1][2] <= t2]
            if candidates:
                max_lat = max(max_lat, min(candidates))
    return max_lat

def stream_time_to_reach(G, u, v, alpha, start=None, end=None):
    """
        Minimum arrival time difference to reach target v from source u starting at or after alpha.
    """
    from dynetx.algorithms.paths import time_respecting_paths
    tids = G.temporal_snapshots_ids()
    if not tids:
        return float('inf')
    
    start_t = None
    for t in sorted(tids):
        if t >= alpha:
            if G.has_node(u, t):
                start_t = t
                break
                
    if start_t is None:
        return float('inf')
        
    plist = time_respecting_paths(G, u, v=v, start=start_t, end=end)
    if not isinstance(plist, dict):
        return float('inf')
        
    paths_uv = plist.get((u, v), [])
    if not paths_uv:
        return float('inf')
    min_arrival = min(p[-1][2] for p in paths_uv)
    return min_arrival - alpha

def stream_flood_time(G, start=None, end=None):
    """
        Return the flood time of the stream graph.
    """
    from dynetx.algorithms.paths import all_time_respecting_paths
    paths = all_time_respecting_paths(G, start=start, end=end)
    V = G.nodes()
    max_ft = 0
    for u in V:
        T_u = G.node_presence(u)
        for alpha in T_u:
            for v in V:
                if u == v:
                    continue
                plist = paths.get((u, v), [])
                candidates = [p[-1][2] for p in plist if p[0][2] >= alpha]
                if candidates:
                    arrival = min(candidates)
                    max_ft = max(max_ft, arrival - alpha)
    return max_ft

def constrained_time_respecting_paths(G, u, v=None, start=None, end=None, gamma=1, gamma_prime=None):
    """
        Find all simple paths from u to v under transmission delay gamma and forwarding delay gamma_prime.
    """
    tids = G.temporal_snapshots_ids()
    if not tids:
        return {}
    if start is None:
        start = tids[0]
    if end is None:
        end = tids[-1]

    results = defaultdict(list)
    tid_type = type(tids[0])
    node_type = type(u)

    def dfs(curr, curr_t, path, visited):
        if v is not None and curr == v:
            results[(u, v)].append(list(path))
            return
        if v is None and curr != u:
            results[(u, curr)].append(list(path))
        
        min_t = curr_t + (gamma if gamma is not None else 1)
        max_t = None
        if gamma_prime is not None:
            max_t = curr_t + (gamma if gamma is not None else 1) + gamma_prime
        
        for t_next in tids:
            if t_next < min_t:
                continue
            if max_t is not None and t_next > max_t:
                continue
            if t_next > end:
                break
            
            if G.has_node(curr, t_next):
                for neighbor in G.neighbors(curr, t_next):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        path.append((node_type(curr), node_type(neighbor), tid_type(t_next)))
                        dfs(neighbor, t_next, path, visited)
                        path.pop()
                        visited.remove(neighbor)

    for t_start in tids:
        if t_start < start:
            continue
        if t_start > end:
            break
        if G.has_node(u, t_start):
            for neighbor in G.neighbors(u, t_start):
                visited = {u, neighbor}
                path = [(node_type(u), node_type(neighbor), tid_type(t_start))]
                dfs(neighbor, t_start, path, visited)

    return results

def stream_weakly_connected_components(G):
    """
        Return the weakly connected components of the stream graph as a list of Clusters.
    """
    flat_components = list(nx.connected_components(G))
    components = []
    for comp in flat_components:
        c = Cluster()
        for u in comp:
            for t in G.node_presence(u):
                c.add((t, u))
        if len(c) > 0:
            components.append(c)
    return components

def stream_strongly_connected_components(G):
    """
        Return the strongly connected components of the stream graph as a list of Clusters.
    """
    tids = G.temporal_snapshots_ids()
    if not tids:
        return []
    
    snapshot_components = {}
    for t in tids:
        sg = G.to_networkx_graph(t=t)
        base = sg.to_undirected() if sg.is_directed() else sg
        snapshot_components[t] = {frozenset(c) for c in nx.connected_components(base)}
    
    all_unique_comps = set()
    for comps in snapshot_components.values():
        all_unique_comps.update(comps)
        
    components = []
    sorted_tids = sorted(tids)
    tid_indices = {t: i for i, t in enumerate(sorted_tids)}
    
    for comp in all_unique_comps:
        active_tids = [t for t in sorted_tids if comp in snapshot_components[t]]
        chunks = []
        if active_tids:
            curr_chunk = [active_tids[0]]
            for t in active_tids[1:]:
                if tid_indices[t] == tid_indices[curr_chunk[-1]] + 1:
                    curr_chunk.append(t)
                else:
                    chunks.append(curr_chunk)
                    curr_chunk = [t]
            chunks.append(curr_chunk)
            
        for chunk in chunks:
            c = Cluster()
            for t in chunk:
                for u in comp:
                    c.add((t, u))
            components.append(c)
            
    return components

def reachability_stream_graph(G):
    """
        Return the reachability stream graph of G.
    """
    R = DynDiGraph(edge_removal=G.edge_removal)
    from dynetx.algorithms.paths import all_time_respecting_paths
    paths = all_time_respecting_paths(G)
    for (u, v), plist in paths.items():
        if u == v:
            continue
        for p in plist:
            t_start = p[0][2]
            R.add_interaction(u, v, t=t_start)
    return R

def cluster_internal_neighborhood(G, cluster, v):
    """
        Return the internal neighborhood of node v involved in cluster as a Cluster.
    """
    c = Cluster()
    v_presence_in_cluster = {t for (t, u) in cluster if u == v}
    for t in v_presence_in_cluster:
        if G.has_node(v, t):
            for neighbor in G.neighbors(v, t):
                if (t, neighbor) in cluster:
                    c.add((t, neighbor))
    return c

def cluster_external_neighborhood(G, cluster, v):
    """
        Return the external neighborhood of node v involved in cluster as a Cluster.
    """
    c = Cluster()
    v_presence_in_cluster = {t for (t, u) in cluster if u == v}
    for t in v_presence_in_cluster:
        if G.has_node(v, t):
            for neighbor in G.neighbors(v, t):
                if (t, neighbor) not in cluster:
                    c.add((t, neighbor))
    return c

def cluster_internal_degree(G, cluster, v):
    """
        Return the internal degree of node v in cluster.
    """
    return len(cluster_internal_neighborhood(G, cluster, v))

def cluster_external_degree(G, cluster, v):
    """
        Return the external degree of node v in cluster.
    """
    return len(cluster_external_neighborhood(G, cluster, v))

def cluster_average_internal_degree(G, cluster):
    """
        Return the average internal degree of cluster.
    """
    nodes = {u for (t, u) in cluster}
    if not cluster:
        return 0.0
    total_int_deg = sum(cluster_internal_degree(G, cluster, v) for v in nodes)
    return total_int_deg / len(cluster)

def cluster_average_external_degree(G, cluster):
    """
        Return the average external degree of cluster.
    """
    nodes = {u for (t, u) in cluster}
    if not cluster:
        return 0.0
    total_ext_deg = sum(cluster_external_degree(G, cluster, v) for v in nodes)
    return total_ext_deg / len(cluster)

def intra_cluster_density(G, partition):
    """
        Intra-cluster density of a partition (list of Clusters).
    """
    total_internal_links = 0
    total_possible_internal_links = 0
    is_directed = G.is_directed()
    
    for C in partition:
        t_nodes = defaultdict(set)
        for t, u in C:
            t_nodes[t].add(u)
            
        internal_links = 0
        for t, nodes in t_nodes.items():
            for u in nodes:
                if G.has_node(u, t):
                    for v in G.neighbors(u, t):
                        if v in nodes:
                            internal_links += 1
        if not is_directed:
            internal_links //= 2
            
        possible = 0
        for t, nodes in t_nodes.items():
            n = len(nodes)
            possible += n * (n - 1)
        if not is_directed:
            possible //= 2
            
        total_internal_links += internal_links
        total_possible_internal_links += possible
        
    if total_possible_internal_links == 0:
        return 0.0
    return total_internal_links / total_possible_internal_links

def inter_cluster_density(G, partition):
    """
        Inter-cluster density of a partition (list of Clusters).
    """
    total_inter_links = 0
    total_possible_inter_links = 0
    is_directed = G.is_directed()
    
    cluster_t_nodes = []
    for C in partition:
        t_nodes = defaultdict(set)
        for t, u in C:
            t_nodes[t].add(u)
        cluster_t_nodes.append(t_nodes)
        
    k = len(partition)
    for i in range(k):
        for j in range(k):
            if i == j:
                continue
            C_i_t = cluster_t_nodes[i]
            C_j_t = cluster_t_nodes[j]
            
            common_ts = set(C_i_t.keys()) & set(C_j_t.keys())
            
            links = 0
            for t in common_ts:
                nodes_i = C_i_t[t]
                nodes_j = C_j_t[t]
                for u in nodes_i:
                    if G.has_node(u, t):
                        for v in G.neighbors(u, t):
                            if v in nodes_j:
                                links += 1
            
            possible = 0
            for t in common_ts:
                possible += len(C_i_t[t]) * len(C_j_t[t])
                
            total_inter_links += links
            total_possible_inter_links += possible
            
    if total_possible_inter_links == 0:
        return 0.0
    return total_inter_links / total_possible_inter_links

def cluster_external_density(G, cluster):
    """Return the external density of a cluster.

    Parameters
    ----------
    G : DynDiGraph
        Stream graph to analyze.
    cluster : Cluster or iterable
        Cluster encoded as temporal node occurrences.

    Returns
    -------
    float
        Fraction of potential external contacts that are present.
    """
    tids = G.temporal_snapshots_ids()
    W = Cluster()
    for t in tids:
        for u in G.nodes(t=t):
            W.add((t, u))
    comp = Cluster(W - cluster)
    return inter_cluster_density(G, [cluster, comp])

def quotient_stream(G, partition):
    """
        Return the quotient stream graph of G induced by partition.
    """
    Q = G.__class__(edge_removal=G.edge_removal)
    cluster_t_nodes = []
    for C in partition:
        t_nodes = defaultdict(set)
        for t, u in C:
            t_nodes[t].add(u)
        cluster_t_nodes.append(t_nodes)
        
    k = len(partition)
    for i in range(k):
        for j in range(i + 1, k):
            C_i_t = cluster_t_nodes[i]
            C_j_t = cluster_t_nodes[j]
            common_ts = set(C_i_t.keys()) & set(C_j_t.keys())
            for t in common_ts:
                has_link = False
                for u in C_i_t[t]:
                    if G.has_node(u, t):
                        for v in G.neighbors(u, t):
                            if v in C_j_t[t]:
                                has_link = True
                                break
                    if has_link:
                        break
                if has_link:
                    Q.add_interaction(i, j, t=t)
    return Q

def line_stream(G):
    """Return the line stream graph of ``G``.

    Parameters
    ----------
    G : DynDiGraph
        Stream graph to transform.

    Returns
    -------
    DynDiGraph
        Stream graph whose nodes are temporal edge occurrences and whose
        edges connect edge occurrences that share exactly one endpoint.
    """
    L = G.__class__(edge_removal=G.edge_removal)
    tids = G.temporal_snapshots_ids()
    for t in tids:
        sg = G.to_networkx_graph(t=t)
        edges = list(sg.edges())
        for (u1, v1), (u2, v2) in combinations(edges, 2):
            shared = {u1, v1} & {u2, v2}
            if shared and len(shared) == 1:
                node_a = tuple(sorted((u1, v1)))
                node_b = tuple(sorted((u2, v2)))
                L.add_interaction(node_a, node_b, t=t)
    return L

def stream_k_core(G, k=None):
    """
        Return the stream k-core or core numbers.
    """
    tids = G.temporal_snapshots_ids()
    if k is not None:
        c = Cluster()
        for t in tids:
            sg = G.to_networkx_graph(t=t)
            core_nodes = nx.k_core(sg, k=k)
            for u in core_nodes:
                c.add((t, u))
        return c
    else:
        core_numbers = {}
        for t in tids:
            sg = G.to_networkx_graph(t=t)
            cores = nx.core_number(sg)
            for u, val in cores.items():
                core_numbers[(t, u)] = val
        return core_numbers

def stream_path_tree(G, root_node, root_time, path_type='foremost'):
    """
        Return foremost/shortest/fastest path trees.
    """
    from dynetx.algorithms.paths import time_respecting_paths, annotate_paths
    plist = time_respecting_paths(G, root_node, start=root_time)
    Tree = G.__class__(edge_removal=G.edge_removal)
    for (u, v), paths in plist.items():
        if u != root_node or u == v:
            continue
        annotated = annotate_paths(paths)
        selected_path = None
        if path_type == 'foremost':
            if annotated.get('foremost'):
                selected_path = annotated['foremost'][0]
        elif path_type == 'shortest':
            if annotated.get('shortest'):
                selected_path = annotated['shortest'][0]
        elif path_type == 'fastest':
            if annotated.get('fastest'):
                selected_path = annotated['fastest'][0]
        if selected_path:
            for hop in selected_path:
                Tree.add_interaction(hop[0], hop[1], t=hop[2])
    return Tree

def stream_cascade(G, root_node, root_time):
    """
        Return the cascade of G starting from root.
    """
    return stream_path_tree(G, root_node, root_time, path_type='foremost')

def stream_closeness_centrality(G, v, t):
    """
        Return the closeness centrality of node v at time t.
    """
    total = 0.0
    for u in G.nodes():
        if u == v:
            continue
        lat = stream_time_to_reach(G, v, u, t)
        if lat != float('inf') and lat > 0:
            total += 1.0 / lat
        elif lat == 0:
            total += 1.0
    return total

def stream_betweenness_centrality(G):
    """
        Return the temporal betweenness centrality of all (t, v) in G.
    """
    from dynetx.algorithms.paths import all_time_respecting_paths
    paths = all_time_respecting_paths(G)
    
    tids = G.temporal_snapshots_ids()
    bc = {}
    for t in tids:
        for v in G.nodes(t=t):
            bc[(t, v)] = 0.0
            
    for (u, w), plist in paths.items():
        if u == w:
            continue
        grouped = defaultdict(list)
        for p in plist:
            grouped[(p[0][2], p[-1][2])].append(p)
            
        for (i, j), paths_ij in grouped.items():
            min_len = min(len(p) for p in paths_ij)
            optimal_paths = [p for p in paths_ij if len(p) == min_len]
            sigma = len(optimal_paths)
            for p in optimal_paths:
                for hop in p[:-1]:
                    t_hop, node = hop[2], hop[1]
                    if (t_hop, node) in bc:
                        bc[(t_hop, node)] += 1.0 / sigma
    return bc

def stream_node_betweenness_centrality(G):
    """
        Return the node betweenness centrality for all nodes in G.
    """
    bc = stream_betweenness_centrality(G)
    node_bc = defaultdict(float)
    for u in G.nodes():
        node_bc[u] = 0.0
    for (t, v), val in bc.items():
        node_bc[v] += val
    return dict(node_bc)

def stream_time_betweenness_centrality(G):
    """
        Return the time betweenness centrality for all snapshots in G.
    """
    bc = stream_betweenness_centrality(G)
    time_bc = defaultdict(float)
    for t in G.temporal_snapshots_ids():
        time_bc[t] = 0.0
    for (t, v), val in bc.items():
        time_bc[t] += val
    return dict(time_bc)

def delta_substream(G, t, delta):
    """
        Return the substream of G restricted to the temporal window [t, t + delta].
    """
    tids = G.temporal_snapshots_ids()
    sub = G.__class__(edge_removal=G.edge_removal)
    start = t
    end = t + delta
    for s in tids:
        if start <= s <= end:
            for u, v, _ in G.interactions(t=s):
                sub.add_interaction(u, v, t=s)
    return sub

def delta_density(G, t, delta):
    """
        Return the density of G in the window [t, t + delta].
    """
    sub = delta_substream(G, t, delta)
    return sub.density()

def delta_degree(G, v, t, delta):
    """
        Return the degree of node v in the window [t, t + delta].
    """
    sub = delta_substream(G, t, delta)
    if sub.has_node(v):
        return sub.stream_degree(v)
    return 0.0
