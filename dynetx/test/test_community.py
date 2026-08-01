import unittest

import dynetx as dn
import dynetx.algorithms as al
from dynetx.results import CommunityAssignmentResult


try:
    import cdlib.algorithms as cdlib_algorithms
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    cdlib_algorithms = None


class CommunityDetectionTestCase(unittest.TestCase):

    def setUp(self):
        if cdlib_algorithms is None:
            self.skipTest("cdlib is required for community detection helpers")

    def _build_graph(self):
        g = dn.DynGraph()
        for t in (0, 1):
            g.add_interaction("A", "B", t=t)
            g.add_interaction("B", "C", t=t)
            g.add_interaction("C", "A", t=t)
            g.add_interaction("D", "E", t=t)
            g.add_interaction("E", "F", t=t)
            g.add_interaction("F", "D", t=t)
        return g

    def _assert_two_communities(self, result):
        self.assertIsInstance(result, CommunityAssignmentResult)
        self.assertEqual(result.metadata["backend"], "cdlib")
        self.assertIn(result.metadata["graph_kind"], {"snapshot", "window", "aggregate"})
        self.assertEqual(len(result.communities), 2)

        communities = [set(community) for community in result.communities]
        self.assertIn({"A", "B", "C"}, communities)
        self.assertIn({"D", "E", "F"}, communities)
        self.assertEqual({node: len(community_ids) for node, community_ids in result.membership.items()},
                         {node: 1 for node in ["A", "B", "C", "D", "E", "F"]})

    def test_static_community_detection_with_named_algorithm(self):
        g = self._build_graph()

        result = al.community_detection(g, algorithm="greedy_modularity", t=0)

        self._assert_two_communities(result)
        self.assertEqual(result.metadata["graph_kind"], "snapshot")
        self.assertEqual(result.metadata["snapshot"], 0)

    def test_static_community_detection_with_callable_algorithm(self):
        g = self._build_graph()

        result = al.community_detection(g, algorithm=cdlib_algorithms.greedy_modularity, t=(0, 1))

        self._assert_two_communities(result)
        self.assertEqual(result.metadata["graph_kind"], "window")
        self.assertEqual(result.metadata["window"], (0, 1))

    def test_windowed_community_detection_over_time(self):
        g = self._build_graph()

        results = al.community_detection_over_time(g, algorithm="greedy_modularity", window=1, step=1)

        self.assertEqual(list(results), [(0, 0), (1, 1)])
        for key, result in results.items():
            self.assertEqual(key[0], key[1])
            self._assert_two_communities(result)
            self.assertEqual(result.metadata["graph_kind"], "window")
            self.assertEqual(result.metadata["window"], key)


if __name__ == "__main__":
    unittest.main()
