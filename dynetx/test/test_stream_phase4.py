import unittest
import dynetx as dn
from dynetx.classes.cluster import Cluster

class StreamPhase4TestCase(unittest.TestCase):
    def test_phase4_metrics(self):
        G = dn.DynGraph()
        # Add interactions:
        # t=0: (0, 1)
        # t=1: (1, 2)
        # t=2: (0, 2)
        G.add_interaction(0, 1, t=0)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(0, 2, t=2)

        # 1. Path diagnostics
        self.assertEqual(G.stream_diameter(), 2)
        self.assertEqual(G.stream_lapse(), 1)
        self.assertEqual(G.stream_flood_time(), 1)

        # 2. Time-to-reach
        self.assertEqual(G.stream_time_to_reach(0, 2, alpha=0), 1)
        self.assertEqual(G.stream_time_to_reach(0, 2, alpha=1), 1)
        self.assertEqual(G.stream_time_to_reach(0, 2, alpha=2), 0)

        # 3. Constrained paths
        paths = G.constrained_time_respecting_paths(0, v=2, gamma=1, gamma_prime=0)
        # Standard path P1 (0->1->2) at t=0,1 has time diff 1.
        # Under gamma=1, gamma_prime=0, it is valid because diff is in [1, 1+0].
        # So P1 is returned.
        self.assertIn((0, 2), paths)
        self.assertTrue(any(len(p) == 2 for p in paths[(0, 2)]))

        # 4. Weakly connected components
        weak = G.stream_weakly_connected_components()
        self.assertEqual(len(weak), 1)
        self.assertEqual(len(weak[0]), 6) # (0,0), (0,1), (1,1), (1,2), (2,0), (2,2)

        # 5. Strongly connected components
        strong = G.stream_strongly_connected_components()
        self.assertEqual(len(strong), 6)

        # 6. Reachability stream graph
        R = G.reachability_stream_graph()
        self.assertTrue(R.has_interaction(0, 1, t=0))
        self.assertTrue(R.has_interaction(0, 2, t=0))
        self.assertTrue(R.has_interaction(1, 2, t=1))
        self.assertTrue(R.has_interaction(0, 2, t=2))
        self.assertTrue(R.has_interaction(2, 0, t=2))
        self.assertFalse(R.has_interaction(0, 1, t=2))

if __name__ == '__main__':
    unittest.main()
