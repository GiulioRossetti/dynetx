import unittest
import dynetx as dn
from dynetx.readwrite import json_graph
from dynetx.readwrite import graphml
from dynetx.readwrite import tabular
from dynetx.readwrite.edgelist import read_ids
import os
import tempfile


class ReadWriteTestCase(unittest.TestCase):

    def test_snapshots_interactions(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_snapshots(g, "test.txt", delimiter=" ")
        h = dn.read_snapshots("test.txt", nodetype=int, timestamptype=int)
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        dn.write_interactions(h, "test.txt", delimiter=" ")
        h = dn.read_interactions("test.txt", nodetype=int, timestamptype=int, keys=True)
        dn.write_snapshots(h, "test.txt", delimiter=" ")
        os.remove("test.txt")

    def test_snapshots(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_snapshots(g, "test.txt", delimiter=" ")
        h = dn.read_snapshots("test.txt", nodetype=int, timestamptype=int)
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        os.remove("test.txt")

    def test_snapshots_directed(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_snapshots(g, "test.txt", delimiter=" ")
        h = dn.read_snapshots("test.txt", directed=True, nodetype=int, timestamptype=int)
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        os.remove("test.txt")

    def test_interaction_graph(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_interactions(g, "test2.txt", delimiter=" ")
        h = dn.read_interactions("test2.txt", nodetype=int, timestamptype=int)
        self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        os.remove("test2.txt")

    def test_interaction_graph_directed(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_interactions(g, "test2.txt", delimiter=" ")
        h = dn.read_interactions("test2.txt", directed=True, nodetype=int, timestamptype=int)
        self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        os.remove("test2.txt")

    def test_interaction_graph_flag(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_interactions(g, "test3.txt", delimiter=" ")
        h = dn.read_interactions("test3.txt", nodetype=int, timestamptype=int, keys=True)
        # self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        os.remove("test3.txt")

    def test_snapshot_graph_flag(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        dn.write_snapshots(g, "test4.txt", delimiter=" ")
        h = dn.read_snapshots("test4.txt", nodetype=int, timestamptype=int, keys=True)
        # self.assertEqual(list(g.stream_interactions()), list(h.stream_interactions()))
        self.assertEqual(g.number_of_interactions(), h.number_of_interactions())
        os.remove("test4.txt")

    def test_json_directed(self):
        g = dn.DynDiGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(2, 1, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        data = json_graph.node_link_data(g)
        self.assertEqual(data["schema"], "dynetx-temporal")
        self.assertEqual(data["schema_version"], 1)
        h = json_graph.node_link_graph(data)
        self.assertIsInstance(h, dn.DynDiGraph)
        self.assertTrue(h.has_interaction(1, 2, 2))
        self.assertTrue(h.has_interaction(2, 1, 2))

    def test_json_undirected(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2, color="red")
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        data = json_graph.node_link_data(g)
        h = json_graph.node_link_graph(data)
        self.assertIsInstance(h, dn.DynGraph)
        self.assertEqual(h._adj[1][2]["color"], "red")

    def test_graphml_roundtrip(self):
        g = dn.DynGraph()
        g.add_node("a", label="A")
        g.add_interaction("a", "b", t=3, weight=2)

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".graphml")
        handle.close()
        try:
            graphml.write_graphml(g, handle.name, t=3)
            h = graphml.read_graphml(handle.name, t=3)
            self.assertTrue(h.has_interaction("a", "b", 3))
            self.assertEqual(h._node["a"]["label"], "A")
            self.assertEqual(h._adj["a"]["b"]["weight"], 2)
        finally:
            os.remove(handle.name)

    def test_tabular_roundtrip(self):
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is required for tabular adapters")

        g = dn.DynGraph()
        g.add_interaction("a", "b", t=1, weight=2)
        g.add_interaction("a", "b", t=2, weight=2)
        g.add_interaction("b", "c", t=3, weight=5)

        interactions = tabular.to_interaction_dataframe(g)
        snapshots = tabular.to_snapshot_dataframe(g)
        self.assertEqual(len(interactions), 2)
        self.assertEqual(len(snapshots), 3)

        h = tabular.from_interaction_dataframe(interactions)
        self.assertEqual(g.interactions(), h.interactions())
        self.assertEqual(h._adj["a"]["b"]["weight"], 2)

    def test_read_ids_interval_snapshot(self):
        path = "test_ids.txt"
        with open(path, "w") as f:
            f.write("1 2 10 12\n")

        ids = read_ids(path, delimiter=" ", timestamptype=int)
        self.assertEqual(ids, {10: 0, 11: 1, 12: 2})
        os.remove(path)


if __name__ == '__main__':
    unittest.main()
