import unittest
import dynetx as dn

class StreamPhase6TestCase(unittest.TestCase):
    def test_phase6_metrics(self):
        G = dn.DynGraph()
        # t=0: (0, 1)
        # t=1: (1, 2)
        G.add_interaction(0, 1, t=0)
        G.add_interaction(1, 2, t=1)

        # 1. Closeness Centrality
        closeness = G.stream_closeness_centrality(0, 0)
        # From 0 at t=0:
        # to 1: latency is 0 -> 1.0
        # to 2: latency is 1 (reaches at t=1) -> 1.0 / 1 = 1.0
        # Total = 2.0
        self.assertAlmostEqual(closeness, 2.0)

        # 2. Betweenness Centralities
        bc = G.stream_betweenness_centrality()
        # The path from 0 to 2 is [(0, 1, 0), (1, 2, 1)].
        # Intermediate node: (0, 1) -> 1.0
        self.assertAlmostEqual(bc.get((0, 1)), 1.0)
        self.assertAlmostEqual(bc.get((1, 2)), 0.0)

        node_bc = G.stream_node_betweenness_centrality()
        self.assertAlmostEqual(node_bc.get(1), 1.0)
        self.assertAlmostEqual(node_bc.get(0), 0.0)

        time_bc = G.stream_time_betweenness_centrality()
        self.assertAlmostEqual(time_bc.get(0), 1.0)
        self.assertAlmostEqual(time_bc.get(1), 0.0)

        # 3. Delta-analysis
        # sub from t=0 to t=1 with delta=0 (only t=0)
        sub = G.delta_substream(0, 0)
        self.assertTrue(sub.has_interaction(0, 1, t=0))
        self.assertFalse(sub.has_interaction(1, 2, t=1))

        self.assertAlmostEqual(G.delta_density(0, 0), 1.0)
        self.assertAlmostEqual(G.delta_degree(0, 0, 0), 1.0)

        # 4. Bipartite Dynamic Graph
        BG = dn.BipartiteDynGraph(top_nodes={0, 1}, bottom_nodes={2, 3})
        BG.add_interaction(0, 2, t=0)
        BG.add_interaction(1, 2, t=0)
        BG.add_interaction(0, 3, t=0)
        BG.add_interaction(1, 3, t=0)

        self.assertTrue(BG.is_bipartite())
        self.assertAlmostEqual(BG.bipartite_density(), 1.0) # 4 edges, possible = 2 * 2 = 4 -> 1.0

        proj = BG.bipartite_projection('top')
        # 0 and 1 share neighbors 2 and 3 at t=0, so they should be connected in the projection at t=0
        self.assertTrue(proj.has_interaction(0, 1, t=0))

        # Node 2 has neighbors 0 and 1 at t=0. Do they share a neighbor other than 2? Yes, 3.
        # So redundancy of 2 should be 1.0.
        self.assertAlmostEqual(BG.bipartite_redundancy(2), 1.0)

if __name__ == '__main__':
    unittest.main()
