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
    'reachability_stream_graph'
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
