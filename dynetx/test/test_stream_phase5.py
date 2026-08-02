import unittest
import dynetx as dn
from dynetx.classes.cluster import Cluster

class StreamPhase5TestCase(unittest.TestCase):
    def test_phase5_metrics(self):
        G = dn.DynGraph()
        # t=0: (0, 1), (1, 2)
        # t=1: (1, 2)
        # t=2: (0, 2)
        G.add_interaction(0, 1, t=0)
        G.add_interaction(1, 2, t=0)
        G.add_interaction(1, 2, t=1)
        G.add_interaction(0, 2, t=2)

        # 1. Cluster neighborhoods and degrees
        # Cluster 1: C1 = {(0,0), (0,1), (1,1)}
        # Cluster 2: C2 = {(1,2), (2,0), (2,2)}
        C1 = Cluster({(0, 0), (0, 1), (1, 1)})
        C2 = Cluster({(1, 2), (2, 0), (2, 2)})

        # Internal neighborhood of node 0 in C1:
        # At t=0: (0, 0) in C1. Neighbors of 0 at t=0: {1}. (0, 1) in C1.
        # So internal neighborhood is {(0, 1)}.
        int_neigh = G.cluster_internal_neighborhood(C1, 0)
        self.assertEqual(int_neigh, Cluster({(0, 1)}))
        self.assertEqual(G.cluster_internal_degree(C1, 0), 1)

        # External neighborhood of node 1 in C1:
        # At t=0: (0, 1) in C1. Neighbors: {0, 2}. (0, 2) is external.
        # At t=1: (1, 1) in C1. Neighbors: {2}. (1, 2) is external.
        # So external neighborhood is {(0, 2), (1, 2)}.
        ext_neigh = G.cluster_external_neighborhood(C1, 1)
        self.assertEqual(ext_neigh, Cluster({(0, 2), (1, 2)}))
        self.assertEqual(G.cluster_external_degree(C1, 1), 2)

        # Average internal/external degrees of C1
        # Nodes in C1: {0, 1}
        # Node 0 internal degree = 1, external degree = 0
        # Node 1: (0, 1) is in C1. Neighbors of 1 at t=0 is {0, 2}. (0,0) in C1. (0,2) not in C1.
        # Node 1: (1, 1) is in C1. Neighbors of 1 at t=1 is {2}. (1,2) not in C1.
        # So Node 1 internal degree = 1 (from (0,0)), external degree = 2 (from (0,2) and (1,2)).
        # Average internal degree of C1 = (1 + 1) / 3 = 2/3.
        # Average external degree of C1 = (0 + 2) / 3 = 2/3.
        self.assertAlmostEqual(G.cluster_average_internal_degree(C1), 2/3)
        self.assertAlmostEqual(G.cluster_average_external_degree(C1), 2/3)

        # 2. Partition densities
        # Intra-cluster density of partition [C1, C2]
        self.assertGreaterEqual(G.intra_cluster_density([C1, C2]), 0.0)
        self.assertGreaterEqual(G.inter_cluster_density([C1, C2]), 0.0)
        self.assertGreaterEqual(G.cluster_external_density(C1), 0.0)

        # 3. Quotient Stream
        Q = G.quotient_stream([C1, C2])
        # Link at t=0: C1 has {0,1}, C2 is empty. No quotient interaction.
        # Link at t=1: C1 has {1}, C2 has {2}. Interaction is (1,2), connecting them at t=1.
        # Link at t=2: C1 is empty, C2 has {0,2}. No quotient interaction.
        # So Q should only have (0,1) at t=1.
        self.assertFalse(Q.has_interaction(0, 1, t=0))
        self.assertTrue(Q.has_interaction(0, 1, t=1))
        self.assertFalse(Q.has_interaction(0, 1, t=2))

        # 4. Line Stream
        L = G.line_stream()
        # At t=0: edges are (0,1) and (1,2). They share node 1.
        # Node (0,1) is tuple (0,1). Node (1,2) is tuple (1,2).
        # L should have a link between (0, 1) and (1, 2) at t=0.
        node_a = (0, 1)
        node_b = (1, 2)
        self.assertTrue(L.has_interaction(node_a, node_b, t=0) or L.has_interaction(node_b, node_a, t=0))

        # 5. k-core
        cores = G.stream_k_core()
        # Core numbers:
        # At t=0: 0,1,2 all have degree 1 or 2. Let's check k-core for k=2.
        # Node 1 has degree 2 (links (0,1) and (1,2)), others have 1. Core number of 1 is 1.
        # So core number for (0, 1) is 1.
        self.assertEqual(cores.get((0, 1)), 1)
        k2 = G.stream_k_core(k=2)
        # Empty since no node has core number >= 2
        self.assertEqual(len(k2), 0)

        # 6. Foremost trees and cascades
        tree = G.stream_path_tree(0, 0, path_type='foremost')
        self.assertTrue(tree.has_interaction(0, 1, t=0))
        self.assertTrue(tree.has_interaction(1, 2, t=1))

        cascade = G.stream_cascade(0, 0)
        self.assertTrue(cascade.has_interaction(0, 1, t=0))
        self.assertTrue(cascade.has_interaction(1, 2, t=1))

if __name__ == '__main__':
    unittest.main()
