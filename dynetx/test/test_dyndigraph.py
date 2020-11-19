import unittest
import dynetx as dn


class DynDiGraphTestCase(unittest.TestCase):

    def test_self_loop(self):
        G = dn.DynDiGraph()
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 2, t=0)
        G.add_interaction(0, 0, t=0)
        G.add_interaction(1, 1, t=0)
        G.add_interaction(2, 2, t=0)
        G.add_interaction(2, 2, t=2)
        ints = G.interactions(t=0)
        self.assertEqual(len(ints), 5)
        self.assertEqual(G.has_interaction(0, 0, t=0), True)
        self.assertEqual(G.has_interaction(2, 0, t=0), False)

    def test_dyndigraph_add_interaction(self):
        g = dn.DynDiGraph()
        self.assertIsInstance(g, dn.DynDiGraph)

        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)

        its = g.interactions()
        self.assertEqual(len(its), 1)

        g.add_interactions_from([(1, 3), (1, 5)], t=2)

        its = g.interactions()
        self.assertEqual(len(its), 3)

        its = g.interactions(t=18)
        self.assertEqual(len(its), 1)

        its = g.interactions(t=20)
        self.assertEqual(len(its), 0)

        self.assertEqual(len(list(g.neighbors_iter(1))), 3)
        self.assertEqual(len(list(g.neighbors_iter(1, 7))), 1)
        self.assertEqual(len(list(g.neighbors_iter(1, 0))), 0)
        self.assertEqual(g.order(), len(g.nodes()))

        self.assertEqual(g.has_node(42), False)

        self.assertEqual(g.has_node(42, 3), False)
        g.add_interaction(3, 4, 34)
        g.add_interaction(4, 5, 34)
        g.add_interaction(5, 6, 34)
        g.add_interaction(6, 4, 34)
        try:
            g.time_slice(2, 1)
        except:
            pass

        g.interactions_iter([1, 2])

        try:
            g.add_interaction(1, 5)
        except:
            pass

        try:
            g.add_interactions_from([(1, 4), (3, 6)])
        except:
            pass

        try:
            g.remove_edge(1, 2)
        except:
            pass

        try:
            g.remove_edges_from([(1, 2)])
        except:
            pass
        try:
            g.remove_node(1)
        except:
            pass
        try:
            g.remove_nodes_from([1, 2])
        except:
            pass

        self.assertEqual(g.number_of_interactions(1, 90), 0)

    def test_nodes(self):

        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(0, 2, 5)
        g.add_interaction(0, 3, 5)
        g.add_interaction(0, 4, 5)

        nds = len(g.nodes())
        self.assertEqual(nds, 5)

        g.add_interaction(5, 1, 6)
        g.add_interaction(5, 2, 6)
        g.add_interaction(2, 3, 6)
        g.add_interaction(5, 4, 6)

        nds = len(g.nodes())
        self.assertEqual(nds, 6)

        nds = len(g.nodes(t=6))
        self.assertEqual(nds, 5)

        nds = len(g.nodes(t=9))
        self.assertEqual(nds, 0)

        self.assertEqual(g.has_node(0), True)
        self.assertEqual(g.has_node(0, 5), True)
        self.assertEqual(g.has_node(0, 6), False)
        self.assertEqual(g.has_node(0, 0), False)

    def test_number_of_interactions(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)

        its = g.number_of_interactions()
        self.assertEqual(its, 8)

        its = g.number_of_interactions(0)
        self.assertEqual(its, None)

        its = g.number_of_interactions(0, 1)
        self.assertEqual(its, 1)

        its = g.number_of_interactions(0, 1, 5)
        self.assertEqual(its, 1)

        its = g.number_of_interactions(0, 1, 6)
        self.assertEqual(its, 0)

    def test_has_interaction(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)

        self.assertEqual(g.has_interaction(0, 1), True)
        self.assertEqual(g.has_interaction(1, 0), False)
        self.assertEqual(g.has_interaction(0, 1, 5), True)
        self.assertEqual(g.has_interaction(1, 0, 5), False)
        self.assertEqual(g.has_interaction(0, 1, 6), False)
        self.assertEqual(g.has_interaction(0, 1, 9), False)

    def test_in_out_interactions(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)

        sr = g.in_interactions()
        self.assertEqual(sr, [(0, 1, {'t': [[5, 5]]}), (1, 2, {'t': [[5, 5]]}), (2, 3, {'t': [[5, 5]]}),
                              (3, 4, {'t': [[5, 5]]}), (4, 5, {'t': [[6, 6]]}), (5, 6, {'t': [[6, 6]]}),
                              (6, 7, {'t': [[6, 6]]}), (7, 8, {'t': [[6, 6]]})])

        sr = g.in_interactions([0, 1])
        self.assertEqual(sr, [(0, 1, {'t': [[5, 5]]})])

        sr = g.in_interactions([9, 10])
        self.assertEqual(sr, [])

        sr = g.in_interactions([0, 1], 5)
        self.assertEqual(sr, [(0, 1, {'t': [5]})])

        sr = g.in_interactions([0, 1], 7)
        self.assertEqual(sr, [])

        sr = g.out_interactions()
        self.assertEqual(sr, [(0, 1, {'t': [[5, 5]]}), (1, 2, {'t': [[5, 5]]}), (2, 3, {'t': [[5, 5]]}),
                              (3, 4, {'t': [[5, 5]]}), (4, 5, {'t': [[6, 6]]}), (5, 6, {'t': [[6, 6]]}),
                              (6, 7, {'t': [[6, 6]]}), (7, 8, {'t': [[6, 6]]})])

        sr = g.out_interactions([0])
        self.assertEqual(sr, [(0, 1, {'t': [[5, 5]]})])

        sr = g.out_interactions([9, 10])
        self.assertEqual(sr, [])

        sr = g.out_interactions([0, 1], 5)
        self.assertEqual(sr, [(0, 1, {'t': [5]}), (1, 2, {'t': [5]})])

        sr = g.out_interactions([0, 1], 7)
        self.assertEqual(sr, [])

    def test_update_node_attr(self):
        g = dn.DynDiGraph()

        for n in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            g.add_node(n, Label="A")

        for n in g.nodes():
            g.update_node_attr(n, Label="B")

        for n in g.nodes(data=True):
            self.assertEqual(n[1]['Label'], "B")

        g.update_node_attr_from([0, 1, 2], Label="C")
        self.assertEqual(g._node[0]['Label'], "C")

    def test_neighbors(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)

        ng = len(g.neighbors(0))
        self.assertEqual(ng, 1)

        ng = len(g.neighbors(0, 5))
        self.assertEqual(ng, 1)

        ng = len(g.neighbors(0, 6))
        self.assertEqual(ng, 0)

        ng = len(g.neighbors(0, 0))
        self.assertEqual(ng, 0)

        ng = len(g.predecessors(0))
        self.assertEqual(ng, 0)

        ng = len(g.successors(0))
        self.assertEqual(ng, 1)

        ng = len(g.predecessors(1))
        self.assertEqual(ng, 1)

        ng = len(g.successors(1))
        self.assertEqual(ng, 1)

        ng = len(g.predecessors(1, 5))
        self.assertEqual(ng, 1)

        ng = len(g.successors(1, 5))
        self.assertEqual(ng, 1)

        ng = len(g.predecessors(1, 6))
        self.assertEqual(ng, 0)

        ng = len(g.successors(1, 6))
        self.assertEqual(ng, 0)

    def test_degree(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(0, 2, 5)
        g.add_interaction(0, 3, 5)
        g.add_interaction(0, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(4, 6, 6)
        g.add_interaction(4, 7, 6)
        g.add_interaction(4, 8, 6)

        ng = g.degree(4)
        self.assertEqual(ng, 5)

        ng = g.in_degree(4)
        self.assertEqual(ng, 1)

        ng = g.out_degree(4)
        self.assertEqual(ng, 4)

        ng = g.degree(4, 5)
        self.assertEqual(ng, 1)

        ng = g.in_degree(4, 5)
        self.assertEqual(ng, 1)

        ng = g.out_degree(4, 5)
        self.assertEqual(ng, 0)

        ng = g.degree(4, 6)
        self.assertEqual(ng, 4)

        ng = g.degree(4, 0)
        self.assertEqual(ng, 0)

        ng = g.in_degree(4, 6)
        self.assertEqual(ng, 0)

        ng = g.out_degree(4, 0)
        self.assertEqual(ng, 0)

    def test_number_of_nodes(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(0, 2, 5)
        g.add_interaction(0, 3, 5)
        g.add_interaction(0, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(4, 6, 6)
        g.add_interaction(4, 7, 6)
        g.add_interaction(4, 8, 6)

        nn = g.number_of_nodes()
        self.assertEqual(nn, 9)

        nn = g.number_of_nodes(t=5)
        self.assertEqual(nn, 5)

        nn = g.number_of_nodes(t=0)
        self.assertEqual(nn, 0)

        nds = g.avg_number_of_nodes()
        self.assertEqual(nds, 5)

    def test_time_slice(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(0, 2, 5)
        g.add_interaction(0, 3, 5)
        g.add_interaction(0, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(4, 6, 6)
        g.add_interaction(4, 7, 6)
        g.add_interaction(4, 8, 6)

        h = g.time_slice(5)
        self.assertIsInstance(h, dn.DynDiGraph)
        self.assertEqual(h.number_of_nodes(), 5)
        self.assertEqual(h.number_of_interactions(), 4)

        h = g.time_slice(5, 5)
        self.assertIsInstance(h, dn.DynDiGraph)
        self.assertEqual(h.number_of_nodes(), 5)
        self.assertEqual(h.number_of_interactions(), 4)

        h = g.time_slice(5, 6)
        self.assertIsInstance(h, dn.DynDiGraph)
        self.assertEqual(h.number_of_nodes(), 9)
        self.assertEqual(h.number_of_interactions(), 8)

        h = g.time_slice(0)
        self.assertIsInstance(h, dn.DynDiGraph)
        self.assertEqual(h.number_of_nodes(), 0)
        self.assertEqual(h.number_of_interactions(), 0)

    def test_temporal_snapshots_ids(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)
        tsd =g.temporal_snapshots_ids()

        self.assertEqual(tsd, [5, 6])

    def test_interactions_per_snapshots(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 5)
        g.add_interaction(1, 2, 5)
        g.add_interaction(2, 3, 5)
        g.add_interaction(3, 4, 5)
        g.add_interaction(4, 5, 6)
        g.add_interaction(5, 6, 6)
        g.add_interaction(6, 7, 6)
        g.add_interaction(7, 8, 6)

        tsd = g.interactions_per_snapshots()
        self.assertDictEqual(tsd, {5: 4, 6: 4})

        tsd = g.interactions_per_snapshots(t=5)
        self.assertEqual(tsd, 4)

        tsd = g.interactions_per_snapshots(t=0)
        self.assertEqual(tsd, 0)

    def test_inter_out_event_time(self):
        g = dn.DynDiGraph()
        g.add_interaction(0, 1, 2)
        g.add_interaction(0, 2, 2)
        g.add_interaction(0, 3, 2)
        g.add_interaction(0, 4, 2)
        g.add_interaction(4, 5, 3)
        g.add_interaction(4, 6, 3)
        g.add_interaction(4, 7, 3)
        g.add_interaction(4, 8, 3)
        g.add_interaction(0, 2, 4)

        # complete

        ivt = g.inter_event_time_distribution()
        self.assertDictEqual(ivt, {0: 6, 1: 2})

        ivt = g.inter_event_time_distribution(4)
        self.assertDictEqual(ivt, {0: 3, 1: 1})

        ivt = g.inter_event_time_distribution(0)
        self.assertDictEqual(ivt, {0: 3, 2: 1})

        ivt = g.inter_event_time_distribution(0, 1)
        self.assertDictEqual(ivt, {})

        ivt = g.inter_event_time_distribution(0, 2)
        self.assertDictEqual(ivt, {2: 1})

        ivt = g.inter_event_time_distribution(2, 0)
        self.assertDictEqual(ivt, {2: 1})

        # out

        ivt = g.inter_out_event_time_distribution()
        self.assertDictEqual(ivt, {0: 6, 1: 2})

        ivt = g.inter_out_event_time_distribution(4)
        self.assertDictEqual(ivt, {0: 3})

        ivt = g.inter_out_event_time_distribution(0)
        self.assertDictEqual(ivt, {0: 3, 2: 1})

        ivt = g.inter_out_event_time_distribution(0, 1)
        self.assertDictEqual(ivt, {})

        ivt = g.inter_out_event_time_distribution(0, 2)
        self.assertDictEqual(ivt, {2: 1})

        # in

        ivt = g.inter_in_event_time_distribution()
        self.assertDictEqual(ivt, {0: 6, 1: 2})

        ivt = g.inter_in_event_time_distribution(4)
        self.assertDictEqual(ivt, {})

        ivt = g.inter_in_event_time_distribution(2)
        self.assertDictEqual(ivt, {2: 1})

        ivt = g.inter_in_event_time_distribution(0, 1)
        self.assertDictEqual(ivt, {})

        ivt = g.inter_in_event_time_distribution(2, 0)
        self.assertDictEqual(ivt, {2: 1})

        ivt = g.inter_in_event_time_distribution(0, 2)
        self.assertDictEqual(ivt, {})


    def test_stream_interactions(self):
        g = dn.DynDiGraph()
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        g.add_interactions_from([(1, 3), (1, 5)], t=2, e=3)

        sres = list(g.stream_interactions())

        cres = [(1, 2, '+', 2), (1, 3, '+', 2), (1, 5, '+', 2), (1, 3, '-', 3),
                (1, 5, '-', 3), (1, 2, '-', 6), (1, 2, '+', 7), (1, 2, '-', 15), (1, 2, '+', 18)]
        self.assertEqual(sorted(sres), sorted(cres))

    def test_accumulative_growth(self):
        g = dn.DynDiGraph(edge_removal=False)
        g.add_interaction(1, 2, 2)
        g.add_interaction(1, 2, 2, e=6)
        g.add_interaction(1, 2, 7, e=11)
        g.add_interaction(1, 2, 8, e=15)
        g.add_interaction(1, 2, 18)
        g.add_interaction(1, 2, 19)
        g.add_interactions_from([(1, 3), (1, 5)], t=2, e=3)
        sres = list(g.stream_interactions())
        cres = [(1, 2, '+', 2), (1, 5, '+', 2), (1, 3, '+', 2)]
        self.assertEqual(sorted(sres), sorted(cres))
        self.assertEqual(g.has_interaction(1, 2, 18), True)
        self.assertEqual(g.has_interaction(1, 2, 40), False)
        try:
            g.add_interaction(2, 1, 7)
        except:
            pass

    def test_conversion(self):
        G = dn.DynDiGraph()
        G.add_interaction(0, 1, t=0)
        G.add_interaction(0, 2, t=0)
        G.add_interaction(0, 0, t=0)
        G.add_interaction(1, 1, t=0)
        G.add_interaction(2, 2, t=0)
        G.add_interaction(2, 2, t=2)

        H = G.to_undirected()
        self.assertIsInstance(H, dn.DynGraph)
        self.assertEqual(H.number_of_nodes(), 3)
        self.assertEqual(H.number_of_edges(), 3)

if __name__ == '__main__':
    unittest.main()
