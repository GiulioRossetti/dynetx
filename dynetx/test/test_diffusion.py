import unittest

import dynetx as dn
import dynetx.algorithms as al
from dynetx.results import DiffusionResult


try:
    import ndlib.models.epidemics as epidemic_models
    import ndlib.models.opinions as opinion_models
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    epidemic_models = None
    opinion_models = None


class DiffusionTestCase(unittest.TestCase):

    def setUp(self):
        if epidemic_models is None or opinion_models is None:
            self.skipTest("ndlib is required for diffusion helpers")

    def _build_graph(self):
        g = dn.DynGraph()
        g.add_interaction("A", "B", t=0)
        g.add_interaction("B", "C", t=0)
        g.add_interaction("A", "C", t=0)
        g.add_interaction("A", "B", t=1)
        g.add_interaction("B", "C", t=1)
        g.add_interaction("A", "C", t=1)
        return g

    def test_epidemic_diffusion_snapshot(self):
        g = self._build_graph()

        result = al.simulate_epidemic(
            g,
            model="SIModel",
            t=0,
            steps=3,
            seed=1,
            model_parameters={"beta": 1.0},
            initial_status={"Infected": ["A"]},
        )

        self.assertIsInstance(result, DiffusionResult)
        self.assertEqual(result.metadata["backend"], "ndlib")
        self.assertEqual(result.metadata["graph_kind"], "snapshot")
        self.assertEqual(result.metadata["snapshot"], 0)
        self.assertEqual(len(result.timeline), 3)
        self.assertEqual(result.timeline[0]["status"]["A"], "Infected")
        self.assertEqual(result.node_states["A"][0]["status"], "Infected")
        self.assertEqual(result.node_states["C"][-1]["status"], "Infected")
        self.assertEqual(al.diffusion_timeline_records(result), result.timeline)

    def test_opinion_diffusion_with_configuration(self):
        g = self._build_graph()

        result = al.simulate_opinion(
            g,
            model="VoterModel",
            t=(0, 1),
            steps=3,
            seed=1,
            configuration={
                "status": {
                    "Infected": ["A"],
                    "Susceptible": ["B", "C"],
                }
            },
        )

        self.assertIsInstance(result, DiffusionResult)
        self.assertEqual(result.metadata["backend"], "ndlib")
        self.assertEqual(result.metadata["graph_kind"], "window")
        self.assertEqual(result.metadata["window"], (0, 1))
        self.assertEqual(len(result.timeline), 3)
        self.assertEqual(result.timeline[0]["status"]["A"], "Infected")
        self.assertEqual(set(result.node_states), {"A", "B", "C"})

    def test_windowed_diffusion_over_time(self):
        g = self._build_graph()

        results = al.simulate_diffusion_over_time(
            g,
            model="SIModel",
            family="epidemic",
            window=1,
            step=1,
            steps=2,
            seed=1,
            model_parameters={"beta": 1.0},
            initial_status={"Infected": ["A"]},
        )

        self.assertEqual(list(results), [(0, 0), (1, 1)])
        for key, result in results.items():
            self.assertIsInstance(result, DiffusionResult)
            self.assertEqual(result.metadata["graph_kind"], "window")
            self.assertEqual(key[0], key[1])
            self.assertEqual(len(result.timeline), 2)


if __name__ == "__main__":
    unittest.main()
