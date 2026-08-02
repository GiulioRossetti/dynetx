import unittest
import dynetx as dn
from dynetx import Cluster

class StreamPhase2TestCase(unittest.TestCase):
    def test_phase2_cluster_and_neighborhood(self):
        # Create cluster
        c = Cluster()
        c.add_node(0, 1)
        c.add_node(1, 1)
        self.assertIn((0, 1), c)
        self.assertIn((1, 1), c)
        c.remove_node(0, 1)
        self.assertNotIn((0, 1), c)

        # Create Graph
        G = dn.DynGraph()
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 1, t=1)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(1, 2, t=2)

        # Neighborhoods
        n0 = G.temporal_neighborhood(0)
        self.assertEqual(n0, Cluster([(0, 1), (1, 1)]))

        n1 = G.temporal_neighborhood(1)
        self.assertEqual(n1, Cluster([(0, 0), (1, 0), (1, 2), (2, 2)]))

        n2 = G.temporal_neighborhood(2)
        self.assertEqual(n2, Cluster([(1, 1), (2, 1)]))

    def test_phase2_degrees(self):
        G = dn.DynGraph()
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 1, t=1)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(1, 2, t=2)

        # stream_degree
        self.assertAlmostEqual(G.stream_degree(0), 2/3)
        self.assertAlmostEqual(G.stream_degree(1), 4/3)
        self.assertAlmostEqual(G.stream_degree(2), 2/3)

        # average_stream_degree
        self.assertAlmostEqual(G.average_stream_degree(), 8/9)

        # expected_stream_degree
        self.assertAlmostEqual(G.expected_stream_degree(0), 1.0)
        self.assertAlmostEqual(G.expected_stream_degree(1), 4/3)
        self.assertAlmostEqual(G.expected_stream_degree(2), 1.0)

        # degree_at_time
        self.assertEqual(G.degree_at_time(0, 0), 1)
        self.assertEqual(G.degree_at_time(0, 2), 0)

        # expected_degree_at_time
        self.assertAlmostEqual(G.expected_degree_at_time(0), 1.0)
        self.assertAlmostEqual(G.expected_degree_at_time(1), 4/3)

        # global_stream_degree
        self.assertAlmostEqual(G.global_stream_degree(), 8/9)

        # average_expected_stream_degree
        self.assertAlmostEqual(G.average_expected_stream_degree(), 8/7)

        # average_time_degree
        self.assertAlmostEqual(G.average_time_degree(), 8/7)

    def test_phase2_induced_substream(self):
        G = dn.DynGraph()
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 1, t=1)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(1, 2, t=2)

        # Cluster contains (0, 1) [node 1 at t=0], (1, 1) [node 1 at t=1], (1, 2) [node 2 at t=1]
        c = Cluster([(0, 1), (1, 1), (1, 2)])
        sub = G.induced_substream(c)

        # The only active interaction where both ends are present at the same time is (1, 2) at t=1.
        self.assertEqual(sub.number_of_nodes(), 2)
        self.assertEqual(sub.number_of_interactions(), 1)
        self.assertTrue(sub.has_interaction(1, 2, t=1))
        self.assertFalse(sub.has_interaction(0, 1, t=0))

if __name__ == '__main__':
    unittest.main()
