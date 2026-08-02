import unittest
import dynetx as dn

class StreamPhase1TestCase(unittest.TestCase):
    def test_phase1_metrics(self):
        G = dn.DynGraph()
        # Add interactions:
        # t=0: (0, 1)
        # t=1: (0, 1), (1, 2)
        # t=2: (1, 2)
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 1, t=1)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(1, 2, t=2)

        # Snapshots: 0, 1, 2. |T| = 3.
        # Nodes: 0, 1, 2. |V| = 3.
        # Node presences:
        # 0: {0, 1} (len 2)
        # 1: {0, 1, 2} (len 3)
        # 2: {1, 2} (len 2)
        # |W| = 2 + 3 + 2 = 7
        # Active edges at t=0: 1, t=1: 2, t=2: 1. Total |E| = 4.

        self.assertAlmostEqual(G.link_count(), 4/3)
        self.assertAlmostEqual(G.node_duration(), 7/3)
        # V \otimes V = 3 * 2 / 2 = 3
        self.assertAlmostEqual(G.link_duration(), 4/3)
        # T' = max - min + 1 = 3
        self.assertAlmostEqual(G.compactness(), 7/9)

    def test_empty_graph(self):
        G = dn.DynGraph()
        self.assertEqual(G.link_count(), 0.0)
        self.assertEqual(G.node_duration(), 0.0)
        self.assertEqual(G.link_duration(), 0.0)
        self.assertEqual(G.compactness(), 0.0)

if __name__ == '__main__':
    unittest.main()
