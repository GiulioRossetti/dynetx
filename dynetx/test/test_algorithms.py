import unittest
import dynetx as dn
import networkx as nx
import dynetx.algorithms as al


def get_network():
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
        g = get_network()
        DAG, sources, targets, _, _ = al.temporal_dag(g, "D", "C", start=1, end=9)
        self.assertIsInstance(DAG, nx.DiGraph)
        self.assertIsInstance(sources, list)
        self.assertIsInstance(targets, list)

        DAG, sources, targets, _, _ = al.temporal_dag(g, "D", start=1, end=9)
        self.assertIsInstance(DAG, nx.DiGraph)
        self.assertIsInstance(sources, list)
        self.assertIsInstance(targets, list)

    def test_ping_pong(self):
        g = dn.DynGraph()
        g.add_interaction("A", "B", 0, 2)
        g.add_interaction("B", "C", 1, 4)
        g.add_interaction("A", "C", 2, 4)
        g.add_interaction("D", "E", 0, 2)
        g.add_interaction("C", "E", 3, 5)
        g.add_interaction("A", "E", 4, 6)

        labs = {"A": 'x',
                "B": 'y',
                "C": 'x',
                "D": 'y',
                "E": 'x',
                }

        for n in g.nodes():
            g.add_node(n, lab=labs[n])

        ress = al.delta_conformity(g, start=0, delta=5, alphas=[1], labels=['lab'],
                                   path_type="shortest")

        ressa = al.delta_conformity(g, start=0, delta=5, alphas=[1], labels=['lab'],
                                    path_type="foremost")

        self.assertIsInstance(ress, dict)
        self.assertIsInstance(ressa, dict)

    def test_time_respecting_paths(self):
        g = get_network()
        pts = al.time_respecting_paths(g, "A", "D", start=1, end=9)

        for p in pts:
            self.assertIsInstance(p, tuple)

        self.assertEqual(len(al.time_respecting_paths(g, "D", "C", start=20, end=40)), 0)

        pts = al.time_respecting_paths(g, "A", "D", start=1, end=9, sample=0.5)

        for p in pts:
            self.assertIsInstance(p, tuple)

    def test_all_time_respecting_paths(self):
        g = get_network()
        pts = al.all_time_respecting_paths(g, start=1, end=9)

        for p in pts:
            self.assertIsInstance(p, tuple)

    def test_annotated_paths(self):
        g = get_network()
        pts = al.time_respecting_paths(g, "D", "C", start=2, end=9)

        for _, ap in pts.items():
            v = al.annotate_paths(ap)
            for k, i in v.items():
                self.assertIn(k, ['shortest', 'fastest', 'foremost', 'fastest_shortest', 'shortest_fastest'])
                self.assertIsInstance(i, list)
