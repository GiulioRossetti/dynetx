import unittest
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import dynetx as dn
from dynetx import visualization as vz


class VisualizationTestCase(unittest.TestCase):

    def _build_graph(self):
        g = dn.DynGraph()
        g.add_interaction("A", "B", 0)
        g.add_interaction("B", "C", 1)
        g.add_interaction("A", "C", 1)
        g.add_interaction("A", "B", 2)
        return g

    def _assert_exportable(self, fig):
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        self.assertGreater(buffer.tell(), 0)
        buffer.close()

    def test_draw_snapshot(self):
        g = self._build_graph()
        ax = vz.draw_snapshot(g, t=1)
        self.assertIsNotNone(ax)
        self.assertGreater(len(ax.collections), 0)
        self._assert_exportable(ax.figure)

    def test_temporal_summary(self):
        g = self._build_graph()
        ax = vz.plot_temporal_summary(g, kind="both")
        self.assertIsNotNone(ax)
        self.assertGreaterEqual(len(ax.lines), 2)
        self._assert_exportable(ax.figure)

    def test_activity_heatmap(self):
        g = self._build_graph()
        ax = vz.plot_activity_heatmap(g)
        self.assertIsNotNone(ax)
        self._assert_exportable(ax.figure)

    def test_compare_snapshots(self):
        g = self._build_graph()
        fig, axes = vz.compare_snapshots(g, 0, 1)
        self.assertEqual(len(axes), 2)
        self._assert_exportable(fig)


if __name__ == "__main__":
    unittest.main()
