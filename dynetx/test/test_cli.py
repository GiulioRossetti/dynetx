import json
import threading
import time
import unittest
from unittest import mock
from urllib import request

import dynetx as dn
from dynetx.dashboard import server as dashboard_server
from dynetx.dashboard.server import create_server
from dynetx.readwrite import json_graph


class DashboardServerTestCase(unittest.TestCase):

    def _build_graph(self):
        g = dn.DynGraph()
        for t in (0, 1, 2):
            g.add_interaction("A", "B", t=t)
            g.add_interaction("B", "C", t=t)
            g.add_interaction("A", "C", t=t)
        return g

    def _start_server(self):
        server, _ = create_server(port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.2)
        return server, thread

    def _request_json(self, url, payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=data, headers=headers)
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_dashboard_server_load_generate_and_render(self):
        server, thread = self._start_server()
        base_url = "http://127.0.0.1:{}".format(server.server_address[1])
        try:
            with request.urlopen(base_url + "/", timeout=10) as resp:
                html = resp.read().decode("utf-8")
                self.assertIn("network-svg", html)
                self.assertIn("timeline-interactions-svg", html)
                self.assertIn("timeline-nodes-svg", html)
                self.assertIn("theme-select", html)
                self.assertIn("playback-label", html)
                self.assertIn("generator-panel", html)
                self.assertIn("node-mode", html)
                self.assertIn("node-churn", html)
                self.assertIn("activity_driven", html)
                self.assertIn("activity_driven_memory", html)
                self.assertIn("event_shuffling", html)
                self.assertIn("degree_constrained_link_shuffling", html)

            state = self._request_json(base_url + "/api/state")
            self.assertEqual(state["total_nodes"], 0)

            graph = self._build_graph()
            state = self._request_json(base_url + "/api/load_graph", {"graph": json_graph.node_link_data(graph)})
            self.assertEqual(state["total_nodes"], 3)
            self.assertEqual(state["snapshots"], [0, 1, 2])
            self.assertEqual(state["selection_mode"], "snapshot")

            self._request_json(
                base_url + "/api/select",
                {"snapshot": 1},
            )
            state = self._request_json(base_url + "/api/state")
            self.assertEqual(state["selected_snapshot"], 1)

            state = self._request_json(
                base_url + "/api/select",
                {"window": [0, 1]},
            )
            self.assertEqual(state["selected_window"], [0, 1])
            self.assertEqual(state["selection_mode"], "window")

            state = self._request_json(
                base_url + "/api/step_selection",
                {"delta": 1, "mode": "window"},
            )
            self.assertEqual(state["selected_window"], [1, 2])

            state = self._request_json(
                base_url + "/api/step_selection",
                {"delta": -1, "mode": "snapshot"},
            )
            self.assertEqual(state["selected_snapshot"], 0)

            state = self._request_json(base_url + "/api/clear_selection", {})
            self.assertIsNone(state["selected_snapshot"])
            self.assertIsNone(state["selected_window"])
            self.assertEqual(state["selection_mode"], "all")

            current_graph = self._request_json(base_url + "/api/current_graph")
            self.assertIn("nodes", current_graph)
            self.assertIn("links", current_graph)

            chart_data = self._request_json(base_url + "/api/chart_data")
            self.assertEqual(chart_data["snapshots"], [0, 1, 2])
            self.assertEqual(len(chart_data["interactions"]), 3)
            self.assertEqual(len(chart_data["density"]), 3)

            state = self._request_json(
                base_url + "/api/generate_graph",
                {
                    "kind": "dynamic",
                    "num_nodes": 5,
                    "snapshots": 3,
                    "edge_probability": 0.8,
                    "seed": 1,
                    "topologies": ["dynamic_er", "dynamic_ba", "dynamic_sbm"],
                    "dynamic_nodes": True,
                    "node_churn": 0.5,
                },
            )
            self.assertEqual(state["graph_kind"], "stream")
            self.assertGreater(state["total_interactions"], 0)

            current_graph = self._request_json(base_url + "/api/current_graph")
            self.assertTrue(current_graph["graph"].get("dynamic_nodes"))
            self.assertEqual(current_graph["graph"].get("topologies"), ["dynamic_er", "dynamic_ba", "dynamic_sbm"])

            state = self._request_json(
                base_url + "/api/generate_graph",
                {
                    "kind": "snapshot",
                    "num_nodes": 5,
                    "snapshots": 3,
                    "edge_probability": 0.8,
                    "seed": 2,
                    "topologies": ["degree_constrained_link_shuffling"],
                },
            )
            self.assertEqual(state["graph_kind"], "snapshot")
            self.assertGreater(state["total_interactions"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_dashboard_main_falls_back_when_default_port_is_busy(self):
        class FakeServer:
            def __init__(self, port):
                self.server_address = ("0.0.0.0", port)
                self._closed = False

            def serve_forever(self):
                raise KeyboardInterrupt

            def server_close(self):
                self._closed = True

        fake_server = FakeServer(47123)
        call_count = {"count": 0}

        def fake_create_server(host, port):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise OSError(48, "Address already in use")
            return fake_server, object()

        with mock.patch.object(dashboard_server, "_detect_browser_host", return_value="192.0.2.10"), \
             mock.patch.object(dashboard_server, "create_server", side_effect=fake_create_server), \
             mock.patch.object(dashboard_server.webbrowser, "open") as open_mock:
            result = dashboard_server.main(["--no-browser"])

        self.assertEqual(result, 0)
        self.assertEqual(call_count["count"], 2)
        open_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
