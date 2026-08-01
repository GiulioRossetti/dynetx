import unittest

from dynetx.results import (
    CommunityAssignmentResult,
    DiffusionResult,
    SnapshotAnalyticsResult,
    WindowAnalyticsResult,
)
from dynetx.utils.validation import (
    ensure_mapping,
    exclusive_end_to_inclusive,
    inclusive_end_to_exclusive,
    normalize_interaction_interval,
    normalize_time_range,
)


class ValidationAndResultsTestCase(unittest.TestCase):

    def test_time_range_normalization(self):
        self.assertEqual(normalize_time_range(3), (3, 3))
        self.assertEqual(normalize_time_range(3, 7), (3, 7))
        self.assertEqual(normalize_time_range((2, 5)), (2, 5))

        with self.assertRaises(ValueError):
            normalize_time_range(7, 3)

    def test_interaction_interval_normalization(self):
        self.assertEqual(normalize_interaction_interval(4), (4, 4))
        self.assertEqual(normalize_interaction_interval(4, 9), (4, 8))
        self.assertEqual(inclusive_end_to_exclusive(9), 10)
        self.assertEqual(exclusive_end_to_inclusive(10), 9)

        with self.assertRaises(ValueError):
            normalize_interaction_interval((1, 2, 3))

    def test_mapping_validation(self):
        payload = {"a": 1}
        normalized = ensure_mapping(payload, name="payload")
        self.assertEqual(normalized, payload)
        self.assertIsNot(normalized, payload)

        self.assertEqual(ensure_mapping(None), {})

        with self.assertRaises(TypeError):
            ensure_mapping([1, 2, 3], name="payload")

    def test_result_containers(self):
        snapshot = SnapshotAnalyticsResult(snapshot=1, metrics={"density": 0.5}, metadata={"model": "static"})
        window = WindowAnalyticsResult(start=1, end=3, metrics={"coverage": 0.9}, metadata={"label": "w"})
        community = CommunityAssignmentResult(
            communities=[{"A", "B"}],
            membership={"A": 0, "B": 0},
            metadata={"backend": "cdlib"},
        )
        diffusion = DiffusionResult(
            timeline=[0, 1, 2],
            node_states={"A": [0, 1, 1]},
            metadata={"backend": "ndlib"},
        )

        self.assertEqual(snapshot.to_dict()["metrics"]["density"], 0.5)
        self.assertEqual(window.to_dict()["end"], 3)
        self.assertEqual(community.to_dict()["membership"]["A"], 0)
        self.assertEqual(diffusion.to_dict()["timeline"], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
