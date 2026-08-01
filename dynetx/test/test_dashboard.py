import unittest
import math

import dynetx as dn
import dynetx.algorithms as al
from dynetx import dashboard as db
from dynetx.dashboard.server import DashboardServerState


try:
    import cdlib.algorithms as cdlib_algorithms
    import ndlib.models.epidemics as epidemic_models
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    cdlib_algorithms = None
    epidemic_models = None


class DashboardTestCase(unittest.TestCase):

    def setUp(self):
        if cdlib_algorithms is None or epidemic_models is None:
            self.skipTest("cdlib and ndlib are required for dashboard helpers")

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

    def test_dashboard_render_export_and_restore(self):
        g = self._build_graph()
        dashboard = db.build_dashboard(g, t=0)
        self.assertEqual(dashboard.timeline_frames(window=1), [(0, 0), (1, 1)])

        dashboard.set_node_filter(nodes={"A", "B", "C"}, predicate=lambda node, attrs: node != "B")
        filtered = dashboard.current_graph()
        self.assertIn("A", filtered.nodes())
        self.assertNotIn("B", filtered.nodes())

        dashboard.clear_filters()
        stats = dashboard.summary_statistics()
        self.assertEqual(stats["snapshots"], [0, 1])
        self.assertEqual(stats["total_nodes"], 6)
        self.assertEqual(stats["total_interactions"], 6)

        state = dashboard.export_state()
        self.assertEqual(state["graph"]["schema"], "dynetx-temporal")
        restored = db.TemporalDashboard.from_state(state)
        self.assertEqual(restored.selected_snapshot, dashboard.selected_snapshot)
        self.assertEqual(restored.timeline_frames(window=1), dashboard.timeline_frames(window=1))
        self.assertEqual(restored.summary_statistics(), dashboard.summary_statistics())

    def test_dashboard_playback(self):
        g = self._build_graph()
        dashboard = db.build_dashboard(g)

        seen = []
        for session, _ in dashboard.playback(window=1, step=1):
            seen.append(session.selected_snapshot)

        self.assertEqual(seen, [0, 1])

    def test_generate_synthetic_graph_supports_dynamic_topologies(self):
        graph = db.generate_synthetic_graph(
            kind="dynamic",
            num_nodes=8,
            snapshots=4,
            edge_probability=0.4,
            seed=3,
            topologies=["dynamic_er", "dynamic_ba", "dynamic_sbm"],
            dynamic_nodes=True,
            node_churn=0.5,
        )

        self.assertEqual(graph.graph.get("topologies"), ["dynamic_er", "dynamic_ba", "dynamic_sbm"])
        self.assertTrue(graph.graph.get("dynamic_nodes"))
        self.assertGreater(graph.number_of_interactions(), 0)
        self.assertEqual(graph.temporal_snapshots_ids(), [0, 1, 2, 3])


class DashboardServerTestCase(unittest.TestCase):

    def test_rendered_page_preserves_js_newline_escape(self):
        page = DashboardServerState().render_page()
        self.assertIn(r"join('\n')", page)

    def test_stream_view_serialization_for_small_stream_graph(self):
        graph = dn.DynGraph()
        graph.add_interaction("a", "b", t=0)
        graph.add_interaction("a", "b", t=1)
        graph.add_interaction("b", "c", t=1)

        state = DashboardServerState(db.build_dashboard(graph))
        payload = state.current_graph_data()["stream_view"]

        self.assertTrue(payload["eligible"])
        self.assertEqual(payload["time_points"], [0, 1])
        self.assertEqual([node["id"] for node in payload["nodes"]], ["a", "b", "c"])
        self.assertEqual(payload["nodes"][0]["presence"], [[0, 1]])
        self.assertEqual(payload["links"][0]["spans"], [[0, 1]])

    def test_stream_view_uses_full_graph_even_with_selected_snapshot(self):
        graph = dn.DynGraph()
        graph.add_interaction("a", "b", t=0)
        graph.add_interaction("a", "c", t=1)
        graph.add_interaction("b", "c", t=2)

        dashboard = db.build_dashboard(graph)
        dashboard.select_snapshot(1)

        payload = DashboardServerState(dashboard).current_graph_data()["stream_view"]

        self.assertTrue(payload["eligible"])
        self.assertEqual(payload["time_points"], [0, 1, 2])
        self.assertEqual([node["id"] for node in payload["nodes"]], ["a", "b", "c"])

    def test_stream_view_disabled_for_large_graph(self):
        graph = dn.DynGraph()
        for index in range(11):
            graph.add_interaction(index, index + 1, t=0)

        state = DashboardServerState(db.build_dashboard(graph))
        payload = state.current_graph_data()["stream_view"]

        self.assertFalse(payload["eligible"])

    def test_density_values_are_finite(self):
        graph = dn.DynGraph()
        graph.add_interaction("a", "b", t=0)
        graph.add_interaction("a", "c", t=1)
        graph.add_interaction("b", "c", t=1)

        dashboard = db.build_dashboard(graph)
        stats = dashboard.summary_statistics()
        self.assertTrue(all(math.isfinite(value) for value in stats["density"]))
        self.assertTrue(math.isfinite(dashboard.current_density()))


if __name__ == "__main__":
    unittest.main()
