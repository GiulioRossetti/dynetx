import unittest
import dynetx as dn


class FunctionTestCase(unittest.TestCase):

    def test_functions(self):
        g = dn.DynGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)

        self.assertEqual(len(dn.nodes(g)), 2)
        self.assertEqual(len(dn.nodes(g, t=0)), 0)
        self.assertEqual(len(dn.nodes(g, t=2)), 2)
        self.assertEqual(len(dn.interactions(g)), 1)
        self.assertEqual(len(dn.interactions(g, t=0)), 0)
        self.assertEqual(len(dn.interactions(g, t=2)), 1)
        self.assertDictEqual(dn.degree(g), {1: 1, 2: 1})
        self.assertDictEqual(dn.degree(g, t=0), {1: 0, 2: 0})
        self.assertDictEqual(dn.degree(g, [1, 2]), {1: 1, 2: 1})
        self.assertEqual(len(dn.neighbors(g, 1)), 1)
        self.assertEqual(len(dn.neighbors(g, 1, t=2)), 1)
        self.assertEqual(len(dn.neighbors(g, 1, t=0)), 0)
        self.assertEqual(dn.number_of_nodes(g), 2)
        self.assertEqual(dn.number_of_nodes(g, t=0), 0)
        self.assertEqual(dn.number_of_nodes(g, t=2), 2)
        self.assertEqual(dn.number_of_interactions(g, t=0), 0)
        self.assertEqual(dn.number_of_interactions(g, t=2), 1)
        self.assertEqual(dn.number_of_interactions(g), 1)
        self.assertEqual(dn.density(g), 1.0)
        self.assertEqual(dn.density(g, t=0), 0)
        self.assertEqual(dn.density(g, t=2), 0)
        self.assertEqual(dn.degree_histogram(g), [0,2])
        self.assertEqual(dn.degree_histogram(g, t=0), [2])
        self.assertEqual(dn.degree_histogram(g, t=2), [0,2])
        self.assertEqual(dn.is_directed(g), False)

        dn.add_cycle(g, [1, 2, 3, 4], t=30)
        dn.add_path(g, [4, 6, 7, 8], t=40)
        dn.add_star(g, [1, 2, 3, 4], t=50)
        dn.subgraph(g, [1, 3, 4])
        dn.create_empty_copy(g)

        self.assertEqual(len(dn.all_neighbors(g, 1, t=0)), 0)
        self.assertEqual(len(dn.all_neighbors(g, 1)), 3)
        self.assertEqual(len(dn.all_neighbors(g, 1, t=2)), 1)
        dn.non_neighbors(g, 1, t=0)
        dn.non_neighbors(g, 1)
        dn.non_neighbors(g, 1, t=2)
        dn.non_interactions(g, 2)
        dn.non_interactions(g, 0)
        dn.non_interactions(g)
        dn.is_empty(g)
        dn.time_slice(g, 2, 4)
        dn.stream_interactions(g)
        dn.temporal_snapshots_ids(g)
        dn.interactions_per_snapshots(g, 0)
        dn.interactions_per_snapshots(g, 2)
        dn.interactions_per_snapshots(g)
        dn.inter_event_time_distribution(g)
        dn.inter_event_time_distribution(g, 1)
        dn.inter_event_time_distribution(g, 1, 2)
        dn.set_node_attributes(g, values={n: 0 for n in g.nodes()}, name="test")
        dn.get_node_attributes(g, name="test")
        try:
            dn.set_edge_attributes()
        except:
            pass
        try:
            dn.get_edge_attributes()
        except:
            pass

        dn.freeze(g)
        dn.is_frozen(g)



if __name__ == '__main__':
    unittest.main()
