import unittest
import dynetx as dn

class StreamPhase3TestCase(unittest.TestCase):
    def test_phase3_metrics(self):
        G = dn.DynGraph()
        # Add interactions:
        # t=0: triangle (0,1), (0,2), (1,2)
        # t=1: path 1-0-2
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 2, t=0)
        G.add_interaction(1, 2, t=0)
        G.add_interaction(0, 1, t=1)
        G.add_interaction(0, 2, t=1)

        # Local clustering coefficients:
        self.assertAlmostEqual(G.stream_clustering_coefficient(0), 0.5)
        self.assertAlmostEqual(G.stream_clustering_coefficient(1), 1.0)
        self.assertAlmostEqual(G.stream_clustering_coefficient(2), 1.0)

        # Weighted average local clustering coefficient:
        self.assertAlmostEqual(G.average_stream_clustering_coefficient(), 5/6)

        # Global stream transitivity:
        self.assertAlmostEqual(G.stream_transitivity(), 0.75)

        # Time clustering coefficient:
        self.assertAlmostEqual(G.time_clustering_coefficient(), 0.5)

        # Global stream clustering coefficient:
        self.assertAlmostEqual(G.stream_clustering_coefficient_global(), 0.5)

if __name__ == '__main__':
    unittest.main()
