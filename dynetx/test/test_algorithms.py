import unittest
import dynetx as dn
import networkx as nx
import dynetx.algorithms as al


def get_netowrk():
    g = dn.DynGraph()
    g.add_interaction("A", "B", 1, 4)
    g.add_interaction("B", "D", 2, 5)
    g.add_interaction("A", "C", 4, 8)
    g.add_interaction("B", "D", 2, 4)
    g.add_interaction("B", "C", 6, 10)
    g.add_interaction("B", "D", 2, 4)
    g.add_interaction("A", "B", 7, 9)
    return g


class AlgorithmsTestCase(unittest.TestCase):

    def test_DAG(self):
        g = get_netowrk()
        DAG, sources, targets , _, _= al.temporal_dag(g, "D", "C", start=1, end=9)
        self.assertIsInstance(DAG, nx.DiGraph)
        self.assertIsInstance(sources, list)
        self.assertIsInstance(targets, list)

    def test_time_respecting_paths(self):
        g = get_netowrk()
        pts = al.time_respecting_paths(g, "D", "C", start=1, end=9)

        for p in pts:
            self.assertIsInstance(p, list)

        with self.assertRaises(ValueError) as _:
            al.time_respecting_paths(g, "D", "C", start=20, end=40)

    def test_all_time_respecting_paths(self):
        g = get_netowrk()
        pts = al.all_time_respecting_paths(g, start=1, end=9)

        for p in pts:
            self.assertIsInstance(p, tuple)

    def test_annotated_paths(self):
        g = get_netowrk()
        pts = list(al.time_respecting_paths(g, "D", "C", start=1, end=9))
        ann_pts = al.annotate_paths(pts)

        for k, v in ann_pts.items():
            self.assertIn(k, ['shortest', 'fastest', 'foremost', 'fastest_shortest', 'shortest_fastest'])
            self.assertIsInstance(v, list)
