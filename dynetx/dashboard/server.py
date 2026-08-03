"""Browser dashboard server for temporal DyNetx graphs."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct execution path
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import base64
import hashlib
import json
import socket
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dynetx.dashboard import TemporalDashboard, build_dashboard
from dynetx.generation import generate_synthetic_graph
from dynetx.readwrite import json_graph

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
_LOGO_PATH = Path(__file__).resolve().parents[2] / "docs" / "dynetx_logo_full.png"
_LOGO_DATA_URI = "data:image/png;base64,{}".format(
    base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
) if _LOGO_PATH.exists() else ""

__all__ = [
    "DashboardServerState",
    "create_server",
    "build_parser",
    "main",
]


def _read_json_body(handler):
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw) if raw else {}


def _write_json(handler, payload, status=HTTPStatus.OK):
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _write_html(handler, payload, status=HTTPStatus.OK):
    data = payload.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _detect_browser_host():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            host = sock.getsockname()[0]
            if host and host != "0.0.0.0":
                return host
        finally:
            sock.close()
    except Exception:
        pass
    return "127.0.0.1"


class DashboardServerState:
    """In-memory dashboard session state shared by the HTTP handlers.

    Examples
    --------
    >>> from dynetx.dashboard.server import DashboardServerState
    >>> state = DashboardServerState()
    >>> state.DashboardServerState()
"""

    def __init__(self, dashboard=None):
        """Initialize the shared state object."""
        self.dashboard = dashboard if dashboard is not None else build_dashboard()
        self.lock = threading.RLock()

    def load_graph(self, graph_data):
        """Load graph data and reset the current selection.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.load_graph({})
"""
        with self.lock:
            self.dashboard.load_graph_data(graph_data)
            self._default_selection()
            return self.summary()

    def generate_graph(self, kind="stream", num_nodes=12, snapshots=3, edge_probability=0.2, seed=42, topologies=None, dynamic_nodes=False, node_churn=0.25, ba_m=None, ws_k=None, ws_beta=0.2, sbm_groups=None, sbm_p_in=None, sbm_p_out=None, activity_m=2, activity_min=0.18, activity_max=0.65, activity_exponent=2.2, contact_duration=1, memory_alpha=1.0):
        """Generate a synthetic graph and load it into the dashboard.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.generate_graph(kind="stream", num_nodes=5, snapshots=2, seed=1)
"""
        with self.lock:
            self.dashboard.set_graph(
                generate_synthetic_graph(
                    kind=kind,
                    num_nodes=num_nodes,
                    snapshots=snapshots,
                    edge_probability=edge_probability,
                    seed=seed,
                    topologies=topologies,
                    dynamic_nodes=dynamic_nodes,
                    node_churn=node_churn,
                    ba_m=ba_m,
                    ws_k=ws_k,
                    ws_beta=ws_beta,
                    sbm_groups=sbm_groups,
                    sbm_p_in=sbm_p_in,
                    sbm_p_out=sbm_p_out,
                    activity_m=activity_m,
                    activity_min=activity_min,
                    activity_max=activity_max,
                    activity_exponent=activity_exponent,
                    contact_duration=contact_duration,
                    memory_alpha=memory_alpha,
                )
            )
            self._default_selection()
            return self.summary()

    def select(self, snapshot=None, window=None):
        """Update the active dashboard selection.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.select(snapshot=0)
"""
        with self.lock:
            if window is not None:
                self.dashboard.select_window(*window)
            elif snapshot is not None:
                self.dashboard.select_snapshot(snapshot)
            return self.summary()

    def clear_selection(self):
        """Clear any active snapshot or window selection.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.clear_selection()
"""
        with self.lock:
            self.dashboard.selected_snapshot = None
            self.dashboard.selected_window = None
            return self.summary()

    def step_snapshot(self, delta=1):
        """Advance the current snapshot selection by ``delta`` steps.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.step_snapshot()
"""
        with self.lock:
            tids = self.dashboard.graph.temporal_snapshots_ids()
            if not tids:
                return self.summary()
            current = self.dashboard.selected_snapshot
            if current is None:
                current = tids[0]
            try:
                idx = tids.index(current)
            except ValueError:
                idx = 0
            idx = max(0, min(len(tids) - 1, idx + delta))
            self.dashboard.select_snapshot(tids[idx])
            return self.summary()

    def step_window(self, delta=1):
        """Advance the current window selection by ``delta`` steps.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.step_window()
"""
        with self.lock:
            tids = self.dashboard.graph.temporal_snapshots_ids()
            if not tids:
                return self.summary()
            if self.dashboard.selected_window is not None:
                start, end = self.dashboard.selected_window
                width = max(1, end - start)
            else:
                start = self.dashboard.selected_snapshot if self.dashboard.selected_snapshot is not None else tids[0]
                width = 0
            try:
                idx = tids.index(start)
            except ValueError:
                idx = 0
            idx = max(0, min(len(tids) - 1, idx + delta))
            new_start = tids[idx]
            new_end = new_start + width
            new_end = min(new_end, tids[-1])
            if width == 0:
                self.dashboard.select_snapshot(new_start)
            else:
                self.dashboard.select_window(new_start, new_end)
            return self.summary()

    def _default_selection(self):
        """Select a deterministic default snapshot when data is available."""
        tids = self.dashboard.graph.temporal_snapshots_ids()
        if tids:
            self.dashboard.select_snapshot(tids[0])
        else:
            self.dashboard.selected_snapshot = None
            self.dashboard.selected_window = None

    def summary(self):
        """Return the dashboard state as a JSON-serializable dictionary.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.summary()
"""
        with self.lock:
            stats = self.dashboard.summary_statistics()
            tids = stats["snapshots"]
            graph_kind = self.dashboard.graph.graph.get("generator_kind")
            if graph_kind not in {"stream", "snapshot"}:
                graph_kind = "snapshot" if len(tids) <= 1 else "stream"
            return {
                "graph_kind": graph_kind,
                "selected_snapshot": self.dashboard.selected_snapshot,
                "selected_window": self.dashboard.selected_window,
                "selection_mode": "window" if self.dashboard.selected_window is not None else ("snapshot" if self.dashboard.selected_snapshot is not None else "all"),
                "snapshots": tids,
                "active_nodes": stats["active_nodes"],
                "interactions": stats["interactions"],
                "density": stats["density"],
                "current_density": self.dashboard.current_density(),
                "total_nodes": stats["total_nodes"],
                "total_interactions": stats["total_interactions"],
            }

    def export_state(self):
        """Return the current dashboard export payload.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.export_state()
"""
        with self.lock:
            return self.dashboard.export_state()

    def current_graph_data(self):
        """Return the serialized graph and stream-view payload.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.current_graph_data()
"""
        with self.lock:
            payload = json_graph.node_link_data(self.dashboard.current_graph())
            payload["graph"] = dict(self.dashboard.graph.graph)
            payload["layout_graph"] = json_graph.node_link_data(self.dashboard.graph)
            payload["graph_signature"] = self._graph_signature()
            payload["stream_view"] = self._build_stream_view()
            return payload

    def _graph_signature(self):
        """Return a stable hash of the loaded graph."""
        payload = json_graph.node_link_data(self.dashboard.graph)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha1(raw).hexdigest()

    def _build_stream_view(self):
        """Build the stream-graph payload used by the browser renderer."""
        graph = self.dashboard.graph
        graph_payload = json_graph.node_link_data(graph)
        tids = list(graph.temporal_snapshots_ids())
        nodes = sorted(graph.nodes(), key=lambda value: repr(value))
        node_index = {node: index for index, node in enumerate(nodes)}
        time_index = {time: index for index, time in enumerate(tids)}

        def _compress_presence(node):
            spans = []
            start = None
            for index, time in enumerate(tids):
                if graph.has_node(node, time):
                    if start is None:
                        start = index
                elif start is not None:
                    spans.append([start, index - 1])
                    start = None
            if start is not None:
                spans.append([start, len(tids) - 1])
            return spans

        def _compress_edge_spans():
            spans = []
            for link in graph_payload.get("links", []):
                start = time_index.get(link.get("t"))
                end = time_index.get(link.get("e"), start)
                if start is None or end is None:
                    continue
                spans.append({
                    "source": link.get("source"),
                    "target": link.get("target"),
                    "spans": [[start, end]],
                })
            return spans

        eligible = len(nodes) <= 10 and len(tids) > 0
        return {
            "eligible": eligible,
            "nodes": [
                {
                    "id": node,
                    "index": node_index[node],
                    "presence": _compress_presence(node),
                }
                for node in nodes
            ],
            "links": _compress_edge_spans(),
            "time_points": tids,
        }

    def chart_data(self):
        """Return the time-series data used by the dashboard charts.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.chart_data()
"""
        with self.lock:
            stats = self.dashboard.summary_statistics()
            snapshots = stats["snapshots"]
            return {
                "snapshots": snapshots,
                "active_nodes": stats["active_nodes"],
                "interactions": stats["interactions"],
                "density": stats["density"],
                "selected_snapshot": self.dashboard.selected_snapshot,
                "selected_window": self.dashboard.selected_window,
                "selection_mode": "window" if self.dashboard.selected_window is not None else ("snapshot" if self.dashboard.selected_snapshot is not None else "all"),
            }

    def render_page(self):
        """Render the dashboard HTML page.

        Examples
        --------
        >>> from dynetx.dashboard.server import DashboardServerState
        >>> state = DashboardServerState()
        >>> state.render_page()
"""
        return _DASHBOARD_HTML.replace("__LOGO_DATA_URI__", _LOGO_DATA_URI)


def _dashboard_context(handler):
    """Return the dashboard state object attached to the HTTP server."""
    return handler.server.app


def _make_handler():
    """Build the request-handler class used by the dashboard server."""
    class DashboardRequestHandler(BaseHTTPRequestHandler):
        server_version = "DyNetxDashboard/0.1"

        def log_message(self, format, *args):  # pragma: no cover - keep runtime quiet
            return

        def do_GET(self):
            app = _dashboard_context(self)
            parsed = urlparse(self.path)
            route = parsed.path

            if route == "/":
                return _write_html(self, app.render_page())
            if route == "/api/state":
                return _write_json(self, app.summary())
            if route == "/api/current_graph":
                return _write_json(self, app.current_graph_data())
            if route == "/api/chart_data":
                return _write_json(self, app.chart_data())
            if route == "/api/export_state":
                return _write_json(self, app.export_state())

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self):
            app = _dashboard_context(self)
            parsed = urlparse(self.path)
            payload = _read_json_body(self)

            try:
                if parsed.path == "/api/load_graph":
                    graph_data = payload.get("graph", payload)
                    return _write_json(self, app.load_graph(graph_data))
                if parsed.path == "/api/generate_graph":
                    network_model = payload.get("network_model")
                    topologies = payload.get("topologies")
                    if topologies is None:
                        topology = payload.get("topology", network_model)
                        topologies = [topology] if topology is not None else None
                    return _write_json(
                        self,
                        app.generate_graph(
                            kind=payload.get("kind", "stream"),
                            num_nodes=int(payload.get("num_nodes", 12)),
                            snapshots=int(payload.get("snapshots", 3)),
                            edge_probability=float(payload.get("edge_probability", 0.2)),
                            seed=int(payload.get("seed", 42)),
                            topologies=topologies,
                            dynamic_nodes=bool(payload.get("dynamic_nodes", False)),
                            node_churn=float(payload.get("node_churn", 0.25)),
                            ba_m=int(payload.get("ba_m")) if payload.get("ba_m") not in {None, ""} else None,
                            ws_k=int(payload.get("ws_k")) if payload.get("ws_k") not in {None, ""} else None,
                            ws_beta=float(payload.get("ws_beta", 0.2)),
                            sbm_groups=int(payload.get("sbm_groups")) if payload.get("sbm_groups") not in {None, ""} else None,
                            sbm_p_in=float(payload.get("sbm_p_in")) if payload.get("sbm_p_in") not in {None, ""} else None,
                            sbm_p_out=float(payload.get("sbm_p_out")) if payload.get("sbm_p_out") not in {None, ""} else None,
                            activity_m=int(payload.get("activity_m", 2)),
                            activity_min=float(payload.get("activity_min", 0.18)),
                            activity_max=float(payload.get("activity_max", 0.65)),
                            activity_exponent=float(payload.get("activity_exponent", 2.2)),
                            contact_duration=int(payload.get("contact_duration", 1)),
                            memory_alpha=float(payload.get("memory_alpha", 1.0)),
                        ),
                    )
                if parsed.path == "/api/select":
                    snapshot = payload.get("snapshot")
                    if snapshot is not None:
                        snapshot = int(snapshot)
                    window = payload.get("window")
                    if window is not None:
                        window = (int(window[0]), int(window[1]))
                    return _write_json(self, app.select(snapshot=snapshot, window=window))
                if parsed.path == "/api/step_selection":
                    delta = int(payload.get("delta", 1))
                    mode = payload.get("mode", "snapshot")
                    if mode == "window":
                        return _write_json(self, app.step_window(delta=delta))
                    return _write_json(self, app.step_snapshot(delta=delta))
                if parsed.path == "/api/clear_selection":
                    return _write_json(self, app.clear_selection())
            except Exception as exc:
                return _write_json(self, {"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

            self.send_error(HTTPStatus.NOT_FOUND)

    return DashboardRequestHandler


def create_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Create a dashboard HTTP server and its shared state.

    Parameters
    ----------
    host : str, optional
        Interface to bind.
    port : int, optional
        TCP port to bind.

    Returns
    -------
    tuple
        ``(server, state)`` where ``server`` is a ``ThreadingHTTPServer``
        instance and ``state`` is the shared ``DashboardServerState``.
    

    Examples
    --------
    >>> from dynetx.dashboard.server import create_server
    >>> create_server(port=0)
"""
    app = DashboardServerState()
    handler = _make_handler()
    server = ThreadingHTTPServer((host, port), handler)
    server.app = app
    return server, app


def _launch_server(host, port):
    """Create the server, falling back to an ephemeral port when needed."""
    try:
        return create_server(host=host, port=port), port
    except OSError as exc:
        if port != DEFAULT_PORT or getattr(exc, "errno", None) not in {48, 98}:
            raise
        return create_server(host=host, port=0), 0


def build_parser():
    """Return the command-line parser for the dashboard entry point.

    Examples
    --------
    >>> from dynetx.dashboard.server import build_parser
    >>> build_parser()
"""
    parser = argparse.ArgumentParser(
        prog="dynetx_dashboard",
        description="Launch the DyNetx browser dashboard.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser window")
    return parser


def main(argv=None):
    """Run the dashboard server from the command line.

    Parameters
    ----------
    argv : list[str], optional
        Argument vector to parse instead of ``sys.argv``.

    Returns
    -------
    int
        Process exit status.
    

    Examples
    --------
    >>> from dynetx.dashboard.server import main
    >>> main(["--no-browser"])
"""
    parser = build_parser()
    args = parser.parse_args(argv)
    bind_host = args.host
    browser_host = args.host
    if args.host in {"127.0.0.1", "localhost", "::1", "::", "0.0.0.0"}:
        bind_host = "0.0.0.0"
        browser_host = _detect_browser_host()
    (server, _), bound_port = _launch_server(bind_host, args.port)
    if bound_port == 0:
        browser_host = browser_host or _detect_browser_host()
    url = "http://{}:{}/".format(browser_host, server.server_address[1])
    print("DyNetx dashboard running at {}".format(url))
    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - interactive runtime behavior
        pass
    finally:
        server.server_close()
    return 0


_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DyNetx Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: light;
      --bg: radial-gradient(circle at top right, #f8fafc, #e2e8f0);
      --ink: #1e293b;
      --muted: #475569;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --panel: rgba(255, 255, 255, 0.85);
      --panel-border: #cbd5e1;
      --panel-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
      --input-bg: #ffffff;
      --input-border: #cbd5e1;
      --input-focus-border: #4f46e5;
      --input-focus-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
      
      --card-bg: #f8fafc;
      --card-border: #cbd5e1;
      --card-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
      
      --tab-bg: transparent;
      --tab-color: #475569;
      --tab-active-bg: #4f46e5;
      --tab-active-color: #ffffff;
      --tab-active-border: #4f46e5;
      
      --btn-secondary-bg: #ffffff;
      --btn-secondary-border: #cbd5e1;
      --btn-secondary-color: #334155;
      --btn-secondary-hover-bg: #f1f5f9;
      --btn-secondary-hover-border: #94a3b8;
      
      --logo-filter: invert(0.85);
      --scrollbar-track: #cbd5e1;
      --scrollbar-thumb: #94a3b8;
    }

    body[data-theme="night"] {
      color-scheme: dark;
      --bg: radial-gradient(circle at top right, #1e1b4b, #0f172a);
      --ink: #f8fafc;
      --muted: #94a3b8;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --panel: rgba(30, 41, 59, 0.45);
      --panel-border: rgba(255, 255, 255, 0.05);
      --panel-shadow: 0 25px 70px rgba(2, 6, 23, 0.45);
      --input-bg: rgba(2, 6, 23, 0.4);
      --input-border: rgba(15, 23, 42, 1);
      --input-focus-border: rgba(99, 102, 241, 0.8);
      --input-focus-shadow: 0 10px rgba(99, 102, 241, 0.5);
      
      --card-bg: rgba(2, 6, 23, 0.4);
      --card-border: rgba(15, 23, 42, 1);
      --card-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
      
      --tab-bg: transparent;
      --tab-color: #94a3b8;
      --tab-active-bg: rgba(30, 41, 59, 0.8);
      --tab-active-color: #ffffff;
      --tab-active-border: rgba(255, 255, 255, 0.1);
      
      --btn-secondary-bg: rgba(30, 41, 59, 0.45);
      --btn-secondary-border: rgba(255, 255, 255, 0.05);
      --btn-secondary-color: #cbd5e1;
      --btn-secondary-hover-bg: rgba(15, 23, 42, 0.8);
      --btn-secondary-hover-border: rgba(255, 255, 255, 0.1);
      
      --logo-filter: none;
      --scrollbar-track: #1e293b;
      --scrollbar-thumb: #475569;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: 'Outfit', sans-serif;
      color: var(--ink);
      background: var(--bg);
      overflow-x: hidden;
    }
    /* Custom scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: var(--scrollbar-track);
    }
    ::-webkit-scrollbar-thumb {
      background: var(--scrollbar-thumb);
      border-radius: 3px;
    }
    button, input, select {
      font: inherit;
    }
    button {
      border: 0;
      border-radius: 8px;
      padding: 10px 14px;
      background: linear-gradient(180deg, var(--accent), var(--accent-hover));
      color: white;
      cursor: pointer;
      box-shadow: 0 6px 16px rgba(79, 70, 229, 0.18);
      font-weight: 500;
      transition: background-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
    }
    button:hover {
      box-shadow: 0 8px 20px rgba(79, 70, 229, 0.24);
    }
    button.secondary {
      background: rgba(79, 70, 229, 0.06);
      color: var(--btn-secondary-color);
      border: 1px solid rgba(79, 70, 229, 0.14);
      box-shadow: none;
      transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }
    button.secondary:hover {
      background: rgba(79, 70, 229, 0.12);
      color: var(--ink);
      border-color: rgba(79, 70, 229, 0.22);
    }
    input[type="number"], input[type="file"], select {
      width: 100%;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid var(--input-border);
      background: var(--input-bg);
      color: var(--ink);
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    input[type="number"]:focus, input[type="file"]:focus, select:focus {
      outline: none;
      border-color: var(--input-focus-border);
      box-shadow: var(--input-focus-shadow);
    }
    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }
    pre {
      margin: 0;
      overflow: auto;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: var(--card-bg);
      color: var(--ink);
      font-size: 12px;
      line-height: 1.5;
    }
    svg {
      width: 100%;
      display: block;
    }
    .app-shell {
      display: grid;
      grid-template-columns: 406px minmax(0, 1fr);
      gap: 0;
      min-height: 100vh;
      padding: 0;
      position: relative;
    }
    .glass-panel {
      background: var(--panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--panel-border);
      box-shadow: var(--panel-shadow);
    }
    .sidebar {
      position: sticky;
      top: 0;
      align-self: start;
      min-height: 100vh;
      border-radius: 0;
      padding: 28px;
      display: grid;
      gap: 30px;
      align-content: start;
      border-right: 1px solid var(--panel-border);
    }
    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--panel-border);
    }
    .brand-logo {
      display: block;
      height: 40px;
      width: auto;
      object-fit: contain;
      filter: var(--logo-filter);
    }
    .sidebar-tools {
      display: flex;
      gap: 10px;
    }
    .icon-button {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      border: 1px solid var(--btn-secondary-border);
      background: var(--btn-secondary-bg);
      color: var(--btn-secondary-color);
      font-size: 16px;
      line-height: 1;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .icon-button > span {
      display: inline-block;
      line-height: 1;
      transform: translateY(-0.5px);
    }
    .icon-button > span {
      display: inline-block;
      line-height: 1;
      transform: translateY(-0.5px);
    }
    .icon-button:hover {
      background: var(--btn-secondary-hover-bg);
      color: var(--ink);
      border-color: var(--btn-secondary-hover-border);
    }
    .brand-subtitle, .card-kicker, .muted, .summary {
      color: var(--muted);
    }
    .stack {
      display: grid;
      gap: 22px;
    }
    .sidebar-collapsed .app-shell {
      grid-template-columns: 88px minmax(0, 1fr);
    }
    .sidebar-collapsed .sidebar {
      padding: 20px 10px;
      justify-items: center;
      gap: 16px;
    }
    .sidebar-collapsed .sidebar .stack {
      display: none;
    }
    .sidebar-collapsed .brand {
      width: 100%;
      padding-bottom: 0;
      border-bottom: 0;
      flex-direction: column;
      align-items: center;
    }
    .sidebar-collapsed .brand-logo {
      max-width: 56px;
      height: auto;
    }
    .sidebar-collapsed .sidebar-tools {
      width: 100%;
      justify-content: center;
      flex-wrap: wrap;
    }
    .sidebar .card {
      padding: 16px !important;
      border: 1px solid var(--panel-border) !important;
      background: rgba(255, 255, 255, 0.42) !important;
      box-shadow: none !important;
      border-radius: 16px !important;
    }
    .sidebar .card-header {
      margin-bottom: 12px;
    }
    .sidebar .controls {
      gap: 10px;
    }
    .sidebar .toolbar {
      gap: 8px;
    }
    .sidebar .summary {
      line-height: 1.35;
    }
    .sidebar .section-label {
      margin-bottom: 6px;
    }
    .sidebar h2 {
      font-size: 14px;
      line-height: 1.2;
    }
    details.generator {
      overflow: visible;
    }
    details.generator > summary {
      list-style: none;
      cursor: pointer;
      user-select: none;
      padding: 0 0 12px;
      margin: 0 0 12px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--panel-border);
    }
    details.generator > summary::-webkit-details-marker {
      display: none;
    }
    details.generator[open] > summary {
      margin-bottom: 12px;
    }
    .sidebar-subtitle {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
      margin: 0 0 10px;
    }
    .generator-advanced {
      display: none;
      flex-direction: column;
      gap: 12px;
    }
    .sidebar-grid {
      display: grid;
      gap: 10px;
    }
    .sidebar-grid.two-col {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .model-param {
      display: none;
    }
    .model-param.active {
      display: grid;
      gap: 10px;
    }
    .model-hint {
      font-size: 11px;
      line-height: 1.45;
      color: var(--muted);
      margin-top: -2px;
    }
    .network-meta {
      margin-top: 6px;
      font-size: 13px;
      color: var(--muted);
      line-height: 1.35;
    }
    .compact-icon-button {
      width: 34px;
      height: 34px;
      padding: 0;
      font-size: 16px;
    }
    .mode-toggle {
      min-width: 34px;
    }
    .card {
      padding: 16px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: var(--card-bg);
      box-shadow: var(--card-shadow);
    }
    .card h2 {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
      color: var(--ink);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    .summary {
      font-size: 13px;
      line-height: 1.5;
    }
    details.generator {
      padding: 0;
      overflow: hidden;
    }
    details.generator > summary {
      list-style: none;
      cursor: pointer;
      user-select: none;
      padding: 16px;
      margin: -16px -16px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    details.generator > summary::-webkit-details-marker {
      display: none;
    }
    details.generator[open] > summary {
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 14px;
    }
    .controls {
      display: grid;
      gap: 10px;
    }
    label {
      display: grid;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .workspace {
      display: grid;
      gap: 14px;
      align-content: start;
      padding: 16px;
    }
    .view-tabs {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .view-tab {
      border: 1px solid transparent;
      background: transparent;
      color: var(--tab-color);
      box-shadow: none;
      border-radius: 8px;
      padding: 8px 16px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: color 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
    }
    .view-tab:hover {
      color: var(--ink);
    }
    .view-tab.active {
      background: var(--tab-active-bg);
      border: 1px solid var(--tab-active-border);
      color: var(--tab-active-color);
    }
    .nav-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .metric-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .metric {
      padding: 12px 14px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: var(--card-bg);
    }
    .metric-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .metric-value {
      font-size: 18px;
      font-weight: 700;
      color: var(--ink);
    }
    .metric-subvalue {
      margin-top: 2px;
      font-size: 11px;
      color: var(--muted);
      line-height: 1.3;
    }
    .control-strip {
      border-radius: 8px;
      padding: 12px 16px;
      display: grid;
      gap: 16px;
    }
    .playback-block {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }
    .step-stack {
      display: grid;
      gap: 2px;
      min-width: 98px;
    }
    .step-stack .summary {
      font-size: 12px;
      color: var(--muted);
      font-weight: 600;
    }
    .slider-shell {
      display: flex;
      align-items: center;
      gap: 16px;
      min-width: 0;
      flex: 1 1 auto;
    }
    .slider-shell input[type="range"] {
      flex: 1 1 auto;
      min-width: 140px;
    }
    .layout-shell {
      display: flex;
      align-items: center;
      gap: 10px;
      white-space: nowrap;
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }
    .layout-select {
      width: 210px;
    }
    .workspace-grid {
      display: grid;
      gap: 14px;
      grid-template-columns: minmax(0, 1fr);
      align-items: start;
    }
    .network-card {
      padding-bottom: 14px;
    }
    .plot-shell {
      padding: 0;
      overflow: hidden;
    }
    .plot-card {
      display: grid;
      gap: 0;
    }
    .plot-shell svg {
      min-height: 300px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
    }
    body[data-theme="night"] .plot-shell svg {
      background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(15, 23, 42, 0.84)) !important;
      border-color: rgba(148, 163, 184, 0.18) !important;
      box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.04);
    }
    .plot-shell.network svg {
      min-height: 560px;
    }
    .timeline-grid {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
      align-items: stretch;
    }
    .timeline-chart {
      position: relative;
      display: grid;
      gap: 0;
      min-width: 0;
    }
    .timeline-chart svg {
      display: block;
      width: 100%;
      height: auto;
      aspect-ratio: 980 / 460;
      min-height: 0;
      border-radius: 8px;
      overflow: visible;
    }
    .plot-tooltip {
      position: absolute;
      z-index: 3;
      display: none;
      max-width: 220px;
      padding: 8px 10px;
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.92);
      color: #f8fafc;
      border: 1px solid rgba(148, 163, 184, 0.28);
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.25);
      pointer-events: none;
      font-size: 12px;
      line-height: 1.35;
      white-space: nowrap;
    }
    body[data-theme="night"] .plot-tooltip {
      background: rgba(2, 6, 23, 0.96);
      border-color: rgba(148, 163, 184, 0.34);
    }
    .mode-toggle.active {
      background: var(--accent-hover);
      border-color: var(--accent-hover);
      color: white;
    }
    body.fullscreen-active {
      overflow: hidden;
    }
    body.fullscreen-active .sidebar,
    body.fullscreen-active .control-strip,
    body.fullscreen-active .metric-grid,
    body.fullscreen-active .workspace-grid > *:not(.fullscreen-panel-active) {
      display: none !important;
    }
    body.fullscreen-active .workspace {
      padding: 12px;
    }
    body.fullscreen-active .fullscreen-panel-active {
      position: fixed;
      inset: 12px;
      z-index: 1000;
      margin: 0;
      width: auto;
      height: auto;
      overflow: auto;
      box-shadow: 0 30px 90px rgba(15, 23, 42, 0.35);
    }
    body.fullscreen-active .fullscreen-panel-active .plot-shell svg {
      min-height: calc(100vh - 130px);
      height: calc(100vh - 130px);
    }
    .split-grid {
      width: 100%;
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1fr);
    }
    .card pre {
      min-height: 150px;
    }
    .pill {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(79, 70, 229, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.25);
      color: var(--accent);
      font-size: 11px;
      font-weight: 600;
    }
    .pill.alt {
      background: rgba(56, 189, 248, 0.15);
      border-color: rgba(56, 189, 248, 0.25);
      color: #0284c7;
    }
    body[data-theme="night"] .pill {
      color: #a5b4fc;
    }
    body[data-theme="night"] .pill.alt {
      color: #7dd3fc;
    }
    body[data-theme="night"] .plot-shell svg text {
      fill: #e2e8f0;
    }
    body[data-theme="night"] .plot-shell svg .plot-axis,
    body[data-theme="night"] .plot-shell svg .plot-tick {
      stroke: rgba(203, 213, 225, 0.55);
    }
    body[data-theme="night"] .plot-shell svg .plot-label {
      fill: #cbd5e1;
    }
    body[data-theme="night"] .plot-shell svg .plot-line {
      stroke: #7dd3fc;
    }
    body[data-theme="night"] .plot-shell svg .plot-fill {
      fill: rgba(96, 165, 250, 0.16);
    }
    body[data-theme="night"] .plot-shell svg .plot-marker {
      fill: #fbbf24;
    }
    .card-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .mini-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .section-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--muted);
      margin: 0 0 10px;
    }
    .selection-hint {
      font-size: 12px;
      line-height: 1.5;
      color: var(--muted);
    }
    .theme-select {
      min-width: 120px;
    }
    body[data-theme="day"] ::-webkit-scrollbar-track {
      background: #cbd5e1;
    }
    body[data-theme="day"] ::-webkit-scrollbar-thumb {
      background: #94a3b8;
    }
    body[data-theme="day"] img[alt="DyNetx"] {
      filter: invert(0.85) !important;
    }
    body[data-theme="day"] .glass-panel {
      background: rgba(255, 255, 255, 0.85) !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
      border: 1px solid #cbd5e1 !important;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05) !important;
    }
    body[data-theme="day"] .sidebar {
      border-right-color: #cbd5e1;
    }
    body[data-theme="day"] .navbar {
      background-color: #f1f5f9 !important;
      border-bottom: 1px solid #cbd5e1 !important;
    }
    body[data-theme="day"] input[type="number"], 
    body[data-theme="day"] input[type="file"], 
    body[data-theme="day"] select {
      background-color: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      color: #1e293b !important;
    }
    body[data-theme="day"] input[type="number"]:focus, 
    body[data-theme="day"] input[type="file"]:focus, 
    body[data-theme="day"] select:focus {
      border-color: #4f46e5 !important;
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
    }
    body[data-theme="day"] label {
      color: #475569 !important;
    }
    body[data-theme="day"] .card h2 {
      color: #0f172a !important;
    }
    body[data-theme="day"] .view-tab {
      color: #475569 !important;
    }
    body[data-theme="day"] .view-tab:hover {
      color: #0f172a !important;
    }
    body[data-theme="day"] .view-tab.active {
      background-color: #4f46e5 !important;
      color: #ffffff !important;
      border: 1px solid #4f46e5 !important;
    }
    body[data-theme="day"] button.secondary {
      background-color: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      color: #334155 !important;
    }
    body[data-theme="day"] button.secondary:hover {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
      border-color: #94a3b8 !important;
    }
    body[data-theme="day"] button.bg-indigo-600 {
      background-color: #4f46e5 !important;
      color: #ffffff !important;
    }
    body[data-theme="day"] button.bg-indigo-600:hover {
      background-color: #4338ca !important;
    }
    body[data-theme="day"] .card {
      background-color: #f8fafc !important;
      border: 1px solid #cbd5e1 !important;
      box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05) !important;
    }
    body[data-theme="day"] .metric {
      background-color: #ffffff !important;
      border-color: #cbd5e1 !important;
    }
    body[data-theme="day"] .metric-label {
      color: #475569 !important;
    }
    body[data-theme="day"] .metric-value {
      color: #0f172a !important;
    }
    body[data-theme="day"] .plot-shell svg {
      background: #ffffff !important;
      border-color: #cbd5e1 !important;
    }
    body[data-theme="day"] .icon-button {
      background-color: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      color: #475569 !important;
    }
    body[data-theme="day"] .icon-button:hover {
      background-color: #f1f5f9 !important;
      color: #0f172a !important;
      border-color: #94a3b8 !important;
    }
    body[data-theme="day"] .pill {
      background-color: rgba(79, 70, 229, 0.1) !important;
      border-color: rgba(79, 70, 229, 0.2) !important;
      color: #4f46e5 !important;
    }
    body[data-theme="day"] .summary,
    body[data-theme="day"] .selection-hint,
    body[data-theme="day"] .metric-subvalue,
    body[data-theme="day"] .section-label,
    body[data-theme="day"] .layout-shell,
    body[data-theme="day"] .step-stack .summary {
      color: #475569 !important;
    }
    body .sidebar .card {
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
    }

    @media (max-width: 1120px) {
      .app-shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        position: static;
      }
      .metric-grid,
      .split-grid {
        grid-template-columns: 1fr 1fr;
      }
      .floating-controls-grid {
        grid-template-columns: 1fr 1fr;
      }
      .timeline-grid {
        grid-template-columns: 1fr;
      }
      .navbar {
        flex-direction: column;
      }
      .nav-actions {
        justify-content: flex-start;
      }
    }
    @media (max-width: 760px) {
      .metric-grid,
      .split-grid {
        grid-template-columns: 1fr;
      }
      .topology-grid,
      .floating-controls-grid {
        grid-template-columns: 1fr;
      }
      .app-shell {
        padding: 0;
      }
      .sidebar {
        padding: 18px 14px;
      }
      .brand-logo {
        max-width: 200px;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar glass-panel">
        <div class="brand">
        <img class="brand-logo" src="__LOGO_DATA_URI__" alt="DyNetx">
        <div class="sidebar-tools">
          <button class="icon-button" onclick="toggleTheme()" aria-label="Toggle theme">☾</button>
          <button class="icon-button" onclick="toggleSidebar()" id="sidebar-toggle-btn" aria-label="Collapse sidebar" title="Collapse sidebar">◀</button>
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-header">
            <h2>Source</h2>
          </div>
          <div class="controls">
            <label>Load temporal graph JSON
              <input id="graph-file" type="file" accept=".json,application/json">
            </label>
            <div class="toolbar">
              <button onclick="loadGraphFile()">Load Graph</button>
              <button class="secondary" onclick="refreshState()">Refresh</button>
            </div>
          </div>
        </div>

        <div class="card generator" id="generator-panel">
          <div class="card-header">
            <h2>Synthetic generator</h2>
          </div>
          <div class="controls">
            <div class="sidebar-grid two-col">
              <label>Type
                <select id="graph-kind" onchange="handleGeneratorSelectionChange()">
                  <option value="stream">Stream graph</option>
                  <option value="snapshot">Snapshot graph</option>
                </select>
              </label>
              <label>Network model
                <select id="network-model" onchange="handleGeneratorSelectionChange()">
                  <option value="erdos_renyi">Erdos-Renyi</option>
                  <option value="barabasi_albert">Barabasi-Albert</option>
                  <option value="watts_strogatz">Watts-Strogatz</option>
                  <option value="complete_graph">Complete</option>
                  <option value="stochastic_block_model">Stochastic block</option>
                  <option value="activity_driven">Activity driven</option>
                  <option value="activity_driven_memory">Activity + memory</option>
                  <option value="event_shuffling">Event shuffling</option>
                  <option value="timeline_shuffling">Timeline shuffling</option>
                  <option value="link_shuffling">Link shuffling</option>
                  <option value="inter_event_shuffling">Inter-event shuffling</option>
                  <option value="degree_constrained_link_shuffling">Degree-constrained link shuffling</option>
                </select>
              </label>
            </div>
              <div class="sidebar-subtitle">Choose the type and topology first. The remaining controls appear once you start configuring the generator.</div>
              <div id="generator-advanced-fields" class="generator-advanced">
              <div id="model-hint" class="model-hint">Random edges with probability p at each snapshot.</div>
              <div class="model-param" data-model="erdos_renyi">
                <label>Edge probability
                  <input id="edge-probability" type="number" min="0" max="1" step="0.05" value="0.2">
                </label>
              </div>
              <div class="model-param" data-model="barabasi_albert">
                <label>Attachment edges m
                  <input id="ba-m" type="number" min="1" step="1" value="2">
                </label>
              </div>
              <div class="model-param" data-model="watts_strogatz">
                <div class="sidebar-grid two-col">
                  <label>Neighbors k
                    <input id="ws-k" type="number" min="2" step="1" value="4">
                  </label>
                  <label>Rewire probability
                    <input id="ws-beta" type="number" min="0" max="1" step="0.05" value="0.2">
                  </label>
                </div>
              </div>
              <div class="model-param" data-model="stochastic_block_model">
                <div class="sidebar-grid two-col">
                  <label>Communities
                    <input id="sbm-groups" type="number" min="2" step="1" value="3">
                  </label>
                  <label>Intra p
                    <input id="sbm-p-in" type="number" min="0" max="1" step="0.05" value="0.5">
                  </label>
                  <label>Inter p
                    <input id="sbm-p-out" type="number" min="0" max="1" step="0.01" value="0.05">
                  </label>
                </div>
              </div>
              <div class="model-param" data-model="complete_graph">
                <div class="model-hint">Complete graphs do not require extra parameters.</div>
              </div>
              <div class="model-param" data-model="activity_driven">
                <div class="sidebar-grid two-col">
                  <label>Activation links m
                    <input id="activity-m" type="number" min="1" step="1" value="2">
                  </label>
                  <label>Contact duration
                    <input id="contact-duration" type="number" min="1" step="1" value="1">
                  </label>
                  <label>Activity min
                    <input id="activity-min" type="number" min="0.01" max="1" step="0.01" value="0.18">
                  </label>
                  <label>Activity max
                    <input id="activity-max" type="number" min="0.01" max="1" step="0.01" value="0.65">
                  </label>
                  <label>Activity exponent
                    <input id="activity-exponent" type="number" min="1" max="5" step="0.1" value="2.2">
                  </label>
                </div>
              </div>
              <div class="model-param" data-model="activity_driven_memory">
                <div class="sidebar-grid two-col">
                  <label>Activation links m
                    <input id="activity-m-memory" type="number" min="1" step="1" value="2">
                  </label>
                  <label>Contact duration
                    <input id="contact-duration-memory" type="number" min="1" step="1" value="1">
                  </label>
                  <label>Activity min
                    <input id="activity-min-memory" type="number" min="0.01" max="1" step="0.01" value="0.18">
                  </label>
                  <label>Activity max
                    <input id="activity-max-memory" type="number" min="0.01" max="1" step="0.01" value="0.65">
                  </label>
                  <label>Activity exponent
                    <input id="activity-exponent-memory" type="number" min="1" max="5" step="0.1" value="2.2">
                  </label>
                  <label>Memory alpha
                    <input id="memory-alpha" type="number" min="0" max="5" step="0.1" value="1">
                  </label>
                </div>
              </div>
              <div class="sidebar-grid two-col">
                <label>Node mode
                  <select id="node-mode" onchange="updateGeneratorState()">
                    <option value="fixed">Fixed nodes</option>
                    <option value="dynamic">Nodes appear/disappear</option>
                  </select>
                </label>
                <label>Node churn
                  <input id="node-churn" type="number" min="0" max="1" step="0.05" value="0.25">
                </label>
              </div>
              <div class="sidebar-grid two-col">
                <label>Number of nodes
                  <input id="num-nodes" type="number" min="2" value="12">
                </label>
                <label>Snapshots
                  <input id="snapshots" type="number" min="1" value="3">
                </label>
              </div>
              <label>Seed
                <input id="seed" type="number" value="42">
              </label>
              <div class="toolbar">
                <button onclick="generateGraph()">Generate</button>
                <button class="secondary" onclick="document.getElementById('generator-panel').open = !document.getElementById('generator-panel').open">Toggle</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <div class="control-strip glass-panel" style="display: flex; flex-direction: column; gap: 12px; align-items: stretch; padding: 12px 16px;">
        <div class="playback-block" style="display: flex; align-items: center; gap: 16px; width: 100%; flex-wrap: nowrap;">
          <button class="play-button" onclick="togglePlayback()" style="width: 36px; height: 36px; border-radius: 50%; padding: 0; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.22);">
            <span id="playback-label">▶</span>
          </button>
          <div style="display: flex; align-items: center; gap: 10px; flex-grow: 1; min-width: 0;">
            <input id="playback-slider" type="range" min="0" max="0" value="0" step="1" oninput="seekPlayback(Number(this.value))" style="flex-grow: 1; min-width: 80px;">
            <span id="playback-step" class="metric-value" style="font-size: 14px; font-weight: 700; min-width: 28px; text-align: center; color: var(--ink);">0</span>
          </div>
          <div class="layout-shell" style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
            <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted);">Layout</span>
            <select id="layout-select" class="layout-select" style="width: auto; padding: 6px 12px; font-size: 13px; height: 34px;" onchange="setLayout(this.value)">
              <option value="preset">Preset spring</option>
              <option value="spring">Spring</option>
              <option value="circular">Circular</option>
            </select>
          </div>
          <button class="icon-button compact-icon-button" onclick="toggleAdvancedControls()" id="adv-toggle-btn" title="Advanced controls" aria-label="Advanced controls" style="flex-shrink: 0;">⌄</button>
        </div>
        
        <!-- Advanced Collapsible Area -->
        <div id="advanced-controls-panel" style="display: none; border-top: 1px solid var(--panel-border); padding-top: 10px; margin-top: 2px; flex-direction: column; gap: 12px;">
          <div class="floating-controls-grid" style="display: grid; gap: 10px; grid-template-columns: 1.15fr 1fr 1fr auto; align-items: end;">
            <label>Selected snapshot
              <select id="snapshot-select" onchange="selectSnapshot()"></select>
            </label>
            <label>Window start
              <select id="window-start-select"></select>
            </label>
            <label>Window end
              <select id="window-end-select"></select>
            </label>
            <div class="compact-row" style="display: flex; gap: 10px; align-items: center; margin-bottom: 2px;">
              <button class="secondary" onclick="stepSelection(-1, 'snapshot')" style="padding: 6px 12px; font-size: 13px; height: 34px;">Prev</button>
              <button class="secondary" onclick="stepSelection(1, 'snapshot')" style="padding: 6px 12px; font-size: 13px; height: 34px;">Next</button>
            </div>
          </div>
          <div class="compact-row" style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between; border-top: 1px solid var(--panel-border); padding-top: 10px; margin-top: 2px;">
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              <button class="icon-button compact-icon-button" onclick="applyWindow()" title="Apply window" aria-label="Apply window">↵</button>
              <button class="icon-button compact-icon-button" onclick="stepSelection(-1, 'window')" title="Shift window back" aria-label="Shift window back">◀</button>
              <button class="icon-button compact-icon-button" onclick="stepSelection(1, 'window')" title="Shift window forward" aria-label="Shift window forward">▶</button>
              <button class="icon-button compact-icon-button" onclick="clearSelection()" title="Show all snapshots" aria-label="Show all snapshots">◯</button>
              <button class="icon-button compact-icon-button" onclick="downloadState()" title="Download state" aria-label="Download state">⇩</button>
              <button class="icon-button compact-icon-button" onclick="downloadCsv()" title="Download CSV" aria-label="Download CSV">CSV</button>
            </div>
            <div class="summary" id="state-summary" style="margin-left: auto; font-size: 12px; color: var(--muted);">No graph loaded yet.</div>
          </div>
        </div>
      </div>

      <section class="metric-grid">
        <div class="metric">
          <div class="metric-label">Graph kind</div>
          <div class="metric-value" id="metric-graph-kind">-</div>
          <div class="metric-subvalue" id="metric-graph-kind-sub">No graph loaded yet.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Selection</div>
          <div class="metric-value" id="metric-selection-mode">-</div>
          <div class="metric-subvalue" id="metric-selection-sub">Snapshot and window controls available.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Nodes</div>
          <div class="metric-value" id="metric-total-nodes">0</div>
          <div class="metric-subvalue">Total nodes in the current session.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Interactions</div>
          <div class="metric-value" id="metric-total-interactions">0</div>
          <div class="metric-subvalue">Interactions visible across all snapshots.</div>
        </div>
      </section>

      <section class="workspace-grid">
        <div class="card network-card glass-panel" id="network-panel">
          <div class="card-row">
            <div>
              <div class="section-label">Network</div>
              <h2 id="network-title">Temporal network view</h2>
              <div class="network-meta" id="metric-density">Density: 0.000</div>
            </div>
            <div class="mini-actions">
              <button class="secondary mode-toggle compact-icon-button" id="network-mode-graph" onclick="setNetworkMode('graph')" title="Temporal graph" aria-label="Temporal graph">◫</button>
              <button class="secondary mode-toggle compact-icon-button" id="network-mode-stream" onclick="setNetworkMode('link-stream')" title="Link stream" aria-label="Link stream">≈</button>
              <button class="secondary fullscreen-toggle compact-icon-button" onclick="toggleFullscreen('network-panel', this)" title="Fullscreen" aria-label="Fullscreen">⛶</button>
            </div>
          </div>
          <div class="plot-shell network">
            <svg id="network-svg" viewBox="0 0 980 560" preserveAspectRatio="xMidYMid meet"></svg>
          </div>
        </div>

        <div class="card glass-panel plot-shell plot-card" id="timeline-panel">
          <div class="card-row">
            <div>
              <div class="section-label">Timeline</div>
              <h2>Interaction and node trends</h2>
            </div>
            <button class="secondary fullscreen-toggle compact-icon-button" onclick="toggleFullscreen('timeline-panel', this)" title="Fullscreen" aria-label="Fullscreen">⛶</button>
          </div>
          <div class="timeline-grid">
            <div class="timeline-chart">
              <svg id="timeline-interactions-svg" viewBox="0 0 980 460" preserveAspectRatio="xMidYMid meet"></svg>
            </div>
            <div class="timeline-chart">
              <svg id="timeline-nodes-svg" viewBox="0 0 980 460" preserveAspectRatio="xMidYMid meet"></svg>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
  <script>
    let currentDashboardState = null;
    let playbackTimer = null;
    let currentLayout = 'preset';
    let currentGraphSignature = null;
    const layoutPositionCache = new Map();
    let currentNetworkMode = 'graph';
    let currentNetworkModeUserSelected = false;
    let generatorSelectionMade = false;
    let sidebarCollapsed = false;

    async function getJson(url, opts={}) {
      const res = await fetch(url, opts);
      if (!res.ok) {
        throw new Error(await res.text());
      }
      return await res.json();
    }

    function createSvgEl(name, attrs) {
      const el = document.createElementNS('http://www.w3.org/2000/svg', name);
      Object.entries(attrs || {}).forEach(function(entry) {
        el.setAttribute(entry[0], entry[1]);
      });
      return el;
    }

    function clearSvg(svg) {
      while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
      }
    }

    function getTheme() {
      return document.body.dataset.theme || 'day';
    }

    function applyTheme(theme) {
      const nextTheme = theme === 'night' ? 'night' : 'day';
      document.body.dataset.theme = nextTheme;
      const themeSelect = document.getElementById('theme-select');
      if (themeSelect) {
        themeSelect.value = nextTheme;
      }
    }

    function toggleTheme() {
      applyTheme(getTheme() === 'night' ? 'day' : 'night');
    }

    function initTheme() {
      applyTheme('day');
    }

    function syncSidebarButton() {
      const button = document.getElementById('sidebar-toggle-btn');
      if (!button) {
        return;
      }
      setIconButtonState(button, sidebarCollapsed ? '▶' : '◀', sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar');
    }

    function toggleSidebar() {
      sidebarCollapsed = !sidebarCollapsed;
      document.body.classList.toggle('sidebar-collapsed', sidebarCollapsed);
      syncSidebarButton();
    }

    function toggleAdvancedControls() {
      const panel = document.getElementById('advanced-controls-panel');
      const btn = document.getElementById('adv-toggle-btn');
      if (!panel || !btn) return;
      if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'flex';
        setIconButtonState(btn, '⌃', 'Hide advanced controls');
      } else {
        panel.style.display = 'none';
        setIconButtonState(btn, '⌄', 'Show advanced controls');
      }
    }

    function initLayout() {
      currentLayout = 'preset';
      const select = document.getElementById('layout-select');
      if (select) {
        select.value = currentLayout;
      }
    }

    function setLayout(value) {
      currentLayout = value || 'preset';
      if (currentDashboardState) {
        refreshState().catch(function(err) {
          console.error(err);
        });
      }
    }

    function selectedNetworkModel() {
      const select = document.getElementById('network-model');
      return select ? select.value : 'erdos_renyi';
    }

    function isStreamOnlyModel(model) {
      return model === 'activity_driven'
        || model === 'activity_driven_memory'
        || model === 'event_shuffling'
        || model === 'timeline_shuffling'
        || model === 'link_shuffling'
        || model === 'inter_event_shuffling';
    }

    function isSnapshotOnlyModel(model) {
      return model === 'degree_constrained_link_shuffling';
    }

    function activityFieldId(base, model) {
      return model === 'activity_driven_memory' ? base + '-memory' : base;
    }

    function updateGeneratorState() {
      const model = selectedNetworkModel();
      const hint = document.getElementById('model-hint');
      const graphKind = document.getElementById('graph-kind');
      const nodeMode = document.getElementById('node-mode');
      const advanced = document.getElementById('generator-advanced-fields');
      document.querySelectorAll('.model-param').forEach(function(panel) {
        panel.classList.toggle('active', panel.dataset.model === model);
      });
      if (advanced) {
        advanced.style.display = generatorSelectionMade ? 'flex' : 'none';
      }
      if (graphKind) {
        const streamOption = graphKind.querySelector('option[value="stream"]');
        const snapshotOption = graphKind.querySelector('option[value="snapshot"]');
        if (streamOption) {
          streamOption.disabled = isSnapshotOnlyModel(model);
        }
        if (snapshotOption) {
          snapshotOption.disabled = isStreamOnlyModel(model);
        }
        if (isStreamOnlyModel(model)) {
          graphKind.value = 'stream';
        } else if (isSnapshotOnlyModel(model)) {
          graphKind.value = 'snapshot';
        }
      }
      if (hint) {
        const hints = {
          erdos_renyi: 'Random edges with probability p at each snapshot.',
          barabasi_albert: 'Preferential attachment with m links from each new node.',
          watts_strogatz: 'Small-world graph with local degree k and rewiring probability beta.',
          complete_graph: 'All nodes are connected at every snapshot.',
          stochastic_block_model: 'Block structure with separate intra- and inter-community probabilities.',
          activity_driven: 'Activity-driven stream graph with heterogeneous activation rates.',
          activity_driven_memory: 'Activity-driven stream graph with memory and social reinforcement.',
          event_shuffling: 'Stream graph null model with randomized event times.',
          timeline_shuffling: 'Stream graph null model that permutes full edge timelines.',
          link_shuffling: 'Stream graph null model that rewires timelines across links.',
          inter_event_shuffling: 'Stream graph null model that shuffles inter-event gaps on each link.',
          degree_constrained_link_shuffling: 'Snapshot null model that randomizes each snapshot while preserving degrees.'
        };
        hint.textContent = hints[model] || hints.erdos_renyi;
      }
      if (graphKind && graphKind.value === 'snapshot' && model === 'complete_graph' && nodeMode && nodeMode.value === 'dynamic') {
        nodeMode.value = 'fixed';
      }
      if (model === 'complete_graph') {
        const edgeProbability = document.getElementById('edge-probability');
        if (edgeProbability) {
          edgeProbability.value = '1';
        }
      }
    }

    function handleGeneratorSelectionChange() {
      generatorSelectionMade = true;
      const advanced = document.getElementById('generator-advanced-fields');
      if (advanced) {
        advanced.style.display = 'flex';
      }
      updateGeneratorState();
    }

    function getPlaybackMode() {
      if (currentDashboardState && currentDashboardState.selection_mode === 'window' && currentDashboardState.selected_window) {
        return 'window';
      }
      return 'snapshot';
    }

    function getPlaybackLabel() {
      return playbackTimer ? '⏸' : '▶';
    }

    function currentLayoutMode() {
      return currentLayout === 'preset' ? 'spring' : currentLayout;
    }

    function currentNetworkLabel() {
      return currentNetworkMode === 'link-stream' ? 'Link stream view' : 'Temporal network view';
    }

    function setNetworkMode(mode) {
      const nextMode = mode === 'link-stream' ? 'link-stream' : 'graph';
      currentNetworkMode = nextMode;
      currentNetworkModeUserSelected = true;
      if (currentDashboardState) {
        refreshState().catch(function(err) {
          console.error(err);
        });
      }
    }

    function syncNetworkModeButtons(eligible) {
      const graphButton = document.getElementById('network-mode-graph');
      const streamButton = document.getElementById('network-mode-stream');
      const title = document.getElementById('network-title');
      if (graphButton) {
        graphButton.classList.toggle('active', currentNetworkMode === 'graph');
        setIconButtonState(graphButton, '◫', 'Temporal graph');
      }
      if (streamButton) {
        streamButton.style.display = eligible ? 'inline-flex' : 'none';
        streamButton.classList.toggle('active', currentNetworkMode === 'link-stream');
        setIconButtonState(streamButton, '≈', 'Link stream');
      }
      if (title) {
        title.textContent = currentNetworkLabel();
      }
    }

    function currentDensityValue(state) {
      return Number(state && state.current_density != null ? state.current_density : 0);
    }

    function setIconButtonState(button, icon, title) {
      if (!button) {
        return;
      }
      button.innerHTML = '<span aria-hidden="true">' + icon + '</span>';
      if (title) {
        button.title = title;
        button.setAttribute('aria-label', title);
      }
    }

    function toggleFullscreen(panelId, button) {
      const target = document.getElementById(panelId);
      if (!target) {
        return;
      }
      const active = document.body.classList.contains('fullscreen-active') && target.classList.contains('fullscreen-panel-active');
      document.querySelectorAll('.fullscreen-panel-active').forEach(function(panel) {
        panel.classList.remove('fullscreen-panel-active');
      });
      if (active) {
        document.body.classList.remove('fullscreen-active');
        target.classList.remove('fullscreen-panel-active');
      } else {
        document.body.classList.add('fullscreen-active');
        target.classList.add('fullscreen-panel-active');
      }
      syncFullscreenButtons();
      window.scrollTo(0, 0);
    }

    function syncFullscreenButtons() {
      document.querySelectorAll('.fullscreen-toggle').forEach(function(button) {
        const panel = button.closest('.plot-card, .network-card');
        if (!panel) return;
        const active = document.body.classList.contains('fullscreen-active') && panel.classList.contains('fullscreen-panel-active');
        setIconButtonState(button, active ? '⤢' : '⛶', active ? 'Exit fullscreen' : 'Fullscreen');
      });
    }

    function syncPlaybackLabel() {
      const label = document.getElementById('playback-label');
      if (label) {
        label.textContent = getPlaybackLabel();
      }
    }

    function themePalette() {
      if (getTheme() === 'day') {
        return {
          axis: 'rgba(100, 116, 139, 0.55)',
          label: '#334155',
          muted: '#64748b',
          node: '#2563eb',
          nodeStroke: '#ffffff',
          edge: 'rgba(100, 116, 139, 0.55)',
          line: '#2563eb',
          marker: '#f97316',
          windowFill: 'rgba(37, 99, 235, 0.12)',
          empty: '#64748b'
        };
      }
      return {
        axis: 'rgba(226, 232, 240, 0.66)',
        label: '#f8fafc',
        muted: '#e2e8f0',
        node: '#e2e8f0',
        nodeStroke: '#0f172a',
        edge: 'rgba(226, 232, 240, 0.72)',
        line: '#93c5fd',
        marker: '#fbbf24',
        windowFill: 'rgba(96, 165, 250, 0.16)',
        empty: '#cbd5e1'
      };
    }

    function renderLinkStream(data) {
      const svg = document.getElementById('network-svg');
      clearSvg(svg);
      const width = 980;
      const height = 560;
      const palette = themePalette();
      const timePoints = Array.isArray(data.time_points) ? data.time_points : [];
      const nodes = Array.isArray(data.nodes) ? data.nodes : [];
      const links = Array.isArray(data.links) ? data.links : [];
      if (!timePoints.length || !nodes.length) {
        const empty = createSvgEl('text', {x: width / 2, y: height / 2, fill: palette.empty, 'font-size': 16, 'text-anchor': 'middle'});
        empty.textContent = 'No temporal data loaded';
        svg.appendChild(empty);
        return;
      }

      const padding = {top: 44, right: 28, bottom: 48, left: 92};
      const xMax = Math.max(1, timePoints.length);
      const yMax = Math.max(1, nodes.length - 1);
      const xAt = function(index) {
        return scale(index, 0, xMax, padding.left, width - padding.right);
      };
      const yAt = function(index) {
        return scale(index, 0, yMax, padding.top, height - padding.bottom);
      };
      const nodeById = {};
      nodes.forEach(function(node) {
        nodeById[node.id] = node;
      });

      const title = createSvgEl('text', {x: 20, y: 24, fill: palette.label, 'font-size': 13});
      title.textContent = 'Link stream representation';
      svg.appendChild(title);

      const axis = createSvgEl('g', {'stroke': palette.axis, 'stroke-width': 1});
      axis.appendChild(createSvgEl('line', {
        x1: padding.left,
        y1: height - padding.bottom,
        x2: width - padding.right,
        y2: height - padding.bottom
      }));
      axis.appendChild(createSvgEl('line', {
        x1: padding.left,
        y1: padding.top - 8,
        x2: padding.left,
        y2: height - padding.bottom
      }));
      svg.appendChild(axis);

      timePoints.forEach(function(timePoint, index) {
        const x = xAt(index);
        svg.appendChild(createSvgEl('line', {
          x1: x,
          y1: height - padding.bottom,
          x2: x,
          y2: height - padding.bottom + 6,
          stroke: palette.axis,
          'stroke-width': 1
        }));
        const label = createSvgEl('text', {
          x: x,
          y: height - padding.bottom + 22,
          fill: palette.label,
          'font-size': 11,
          'text-anchor': 'middle'
        });
        label.textContent = String(timePoint);
        svg.appendChild(label);
      });

      const edgeInk = getTheme() === 'day' ? 'rgba(17, 24, 39, 0.58)' : 'rgba(226, 232, 240, 0.72)';
      const highlightEdgeGroup = function(group, active) {
        if (!group) return;
        const edgeStroke = active ? '#dc2626' : edgeInk;
        const edgeFill = active ? '#dc2626' : edgeInk;
        group.querySelectorAll('[data-role="edge-duration"], [data-role="edge-curve"], [data-role="edge-node"]').forEach(function(el) {
          if (!el) return;
          if (el.dataset.originalStroke == null) {
            el.dataset.originalStroke = el.getAttribute('stroke') || '';
          }
          if (el.dataset.originalFill == null) {
            el.dataset.originalFill = el.getAttribute('fill') || '';
          }
          if (el.dataset.role === 'edge-duration' || el.dataset.role === 'edge-curve') {
            el.setAttribute('stroke', edgeStroke);
          }
          if (el.dataset.role === 'edge-node') {
            el.setAttribute('fill', edgeFill);
            el.setAttribute('stroke', edgeFill);
          }
        });
      };

      nodes.forEach(function(node) {
        const y = yAt(node.index);
        node.presence.forEach(function(span) {
          const x1 = xAt(span[0]);
          const x2 = xAt(span[1] + 1);
          const presence = createSvgEl('line', {
            x1: x1,
            y1: y,
            x2: x2,
            y2: y,
            stroke: palette.axis,
            'stroke-width': 1.5,
            'stroke-dasharray': '1 9',
            'stroke-linecap': 'round'
          });
          svg.appendChild(presence);
        });
        const label = createSvgEl('text', {
          x: 18,
          y: y + 4,
          fill: palette.label,
          'font-size': 12,
          'text-anchor': 'start'
        });
        label.textContent = String(node.id);
        svg.appendChild(label);
      });

      const edgeSpacing = function(sourceId, targetId, spanIndex) {
        const key = String(sourceId) + '|' + String(targetId) + '|' + String(spanIndex);
        const hash = hashString(key);
        const magnitude = 18 + (hash % 4) * 8;
        return magnitude;
      };

      const hoverLayer = createSvgEl('g', {
        'data-role': 'stream-hover-layer',
        'pointer-events': 'none'
      });
      const clearHoverLayer = function() {
        hoverLayer.textContent = '';
      };
      svg.addEventListener('pointerleave', clearHoverLayer);
      svg.addEventListener('pointermove', function(event) {
        const target = event.target && event.target.closest ? event.target.closest('g[data-link-source]') : null;
        if (!target) {
          clearHoverLayer();
        }
      });

      links.forEach(function(link) {
        const source = nodeById[link.source];
        const target = nodeById[link.target];
        if (!source || !target) {
          return;
        }
        const y1 = yAt(source.index);
        const y2 = yAt(target.index);
        const yMid = (y1 + y2) / 2;
        link.spans.forEach(function(span, spanIndex) {
          const x1 = xAt(span[0]);
          const x2 = xAt(span[1] + 1);
          const curveOffset = edgeSpacing(link.source, link.target, spanIndex);
          const controlX1 = x1 + curveOffset;
          const controlX2 = x1 - curveOffset;
          const durationX1 = x1 + (curveOffset / 2);
          const edgeGroup = createSvgEl('g', {
            'data-link-source': String(link.source),
            'data-link-target': String(link.target),
            'style': 'cursor:pointer'
          });
          const duration = createSvgEl('line', {
            x1: durationX1,
            y1: yMid,
            x2: x2,
            y2: yMid,
            stroke: edgeInk,
            'stroke-width': 2.8,
            'stroke-linecap': 'round',
            'data-role': 'edge-duration'
          });
          const curve = createSvgEl('path', {
            d: 'M ' + x1 + ' ' + y1 + ' C ' + controlX1 + ' ' + y1 + ', ' + controlX1 + ' ' + y2 + ', ' + x1 + ' ' + y2,
            fill: 'none',
            stroke: edgeInk,
            'stroke-width': 2.6,
            'stroke-linecap': 'round',
            'data-role': 'edge-curve'
          });
          const topNode = createSvgEl('circle', {cx: x1, cy: y1, r: 4.5, fill: edgeInk, stroke: edgeInk, 'data-role': 'edge-node'});
          const bottomNode = createSvgEl('circle', {cx: x1, cy: y2, r: 4.5, fill: edgeInk, stroke: edgeInk, 'data-role': 'edge-node'});
          edgeGroup.appendChild(duration);
          edgeGroup.appendChild(curve);
          edgeGroup.appendChild(topNode);
          edgeGroup.appendChild(bottomNode);
          edgeGroup.addEventListener('mouseenter', function() {
            clearHoverLayer();
            const hoverGroup = edgeGroup.cloneNode(true);
            highlightEdgeGroup(hoverGroup, true);
            hoverLayer.appendChild(hoverGroup);
          });
          edgeGroup.addEventListener('mouseleave', function() {
            clearHoverLayer();
          });
          svg.appendChild(edgeGroup);
        });
      });
      svg.appendChild(hoverLayer);
    }

    function hashString(input) {
      let hash = 2166136261;
      for (let i = 0; i < input.length; i += 1) {
        hash ^= input.charCodeAt(i);
        hash = Math.imul(hash, 16777619);
      }
      return hash >>> 0;
    }

    function seededRandom(seed) {
      let state = seed >>> 0;
      return function() {
        state = Math.imul(state, 1664525) + 1013904223;
        return ((state >>> 0) / 4294967296);
      };
    }

    function resolveLayoutName() {
      return currentLayoutMode();
    }

    function computeLayoutPositions(layoutData, layout, graphSignature) {
      const nodes = Array.isArray(layoutData && layoutData.nodes) ? layoutData.nodes : [];
      const links = Array.isArray(layoutData && layoutData.links) ? layoutData.links : [];
      const cacheKey = graphSignature + '|' + layout;
      if (layoutPositionCache.has(cacheKey)) {
        return layoutPositionCache.get(cacheKey);
      }
      const positions = {};
      if (!nodes.length) {
        layoutPositionCache.set(cacheKey, positions);
        return positions;
      }

      const nodeIds = nodes.map(function(node) {
        return String(node.id);
      }).sort();
      const width = 980;
      const height = 560;

      if (layout === 'circular') {
        const radius = Math.min(width, height) * 0.34;
        nodeIds.forEach(function(id, index) {
          const angle = (index / Math.max(1, nodeIds.length)) * Math.PI * 2;
          positions[id] = {
            x: width * 0.5 + Math.cos(angle) * radius,
            y: height * 0.5 + Math.sin(angle) * radius
          };
        });
        layoutPositionCache.set(cacheKey, positions);
        return positions;
      }

      const nodesState = nodeIds.map(function(id, index) {
        const rng = seededRandom(hashString(graphSignature + '|' + layout + '|' + id));
        const angle = rng() * Math.PI * 2;
        const radius = Math.min(width, height) * (0.18 + rng() * 0.22);
        return {
          id: id,
          x: width * 0.5 + Math.cos(angle) * radius,
          y: height * 0.5 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0
        };
      });
      const byId = {};
      nodesState.forEach(function(node) {
        byId[node.id] = node;
      });
      const edgePairs = links.map(function(link) {
        return {
          source: String(typeof link.source === 'object' ? link.source.id : link.source),
          target: String(typeof link.target === 'object' ? link.target.id : link.target)
        };
      }).filter(function(link) {
        return byId[link.source] && byId[link.target];
      });

      for (let tick = 0; tick < 140; tick += 1) {
        nodesState.forEach(function(a, i) {
          for (let j = i + 1; j < nodesState.length; j += 1) {
            const b = nodesState[j];
            let dx = a.x - b.x;
            let dy = a.y - b.y;
            const dist2 = Math.max(50, dx * dx + dy * dy);
            const force = 1200 / dist2;
            const dist = Math.sqrt(dist2);
            dx /= dist;
            dy /= dist;
            a.vx += dx * force;
            a.vy += dy * force;
            b.vx -= dx * force;
            b.vy -= dy * force;
          }
        });

        edgePairs.forEach(function(link) {
          const a = byId[link.source];
          const b = byId[link.target];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          const dist = Math.max(20, Math.sqrt(dx * dx + dy * dy));
          const force = (dist - 120) * 0.01;
          dx /= dist;
          dy /= dist;
          a.vx += dx * force;
          a.vy += dy * force;
          b.vx -= dx * force;
          b.vy -= dy * force;
        });

        nodesState.forEach(function(node) {
          const cx = width * 0.5;
          const cy = height * 0.5;
          node.vx += (cx - node.x) * 0.002;
          node.vy += (cy - node.y) * 0.002;
          node.vx *= 0.9;
          node.vy *= 0.9;
          node.x = Math.max(24, Math.min(width - 24, node.x + node.vx));
          node.y = Math.max(24, Math.min(height - 24, node.y + node.vy));
        });
      }

      nodesState.forEach(function(node) {
        positions[node.id] = {x: node.x, y: node.y};
      });
      layoutPositionCache.set(cacheKey, positions);
      return positions;
    }

    function seekPlayback(index) {
      const state = currentDashboardState;
      if (!state || !Array.isArray(state.snapshots) || !state.snapshots.length) {
        return;
      }
      const snapshots = state.snapshots;
      const clampedIndex = Math.max(0, Math.min(snapshots.length - 1, Number(index) || 0));
      const snapshot = snapshots[clampedIndex];
      getJson('/api/select', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({snapshot: Number(snapshot)})
      }).then(function() {
        return refreshState();
      }).catch(function(err) {
        console.error(err);
      });
    }

    function scale(value, fromMin, fromMax, toMin, toMax) {
      if (fromMax === fromMin) {
        return (toMin + toMax) / 2;
      }
      return toMin + ((value - fromMin) * (toMax - toMin)) / (fromMax - fromMin);
    }

    function simulateLayout(nodes, links, width, height) {
      const rand = (() => {
        let seed = nodes.length * 7919 + links.length * 104729 + 1;
        return () => {
          seed = (seed * 16807) % 2147483647;
          return (seed - 1) / 2147483646;
        };
      })();
      nodes.forEach(function(node, index) {
        node.x = width * 0.5 + Math.cos(index * 2 * Math.PI / Math.max(1, nodes.length)) * width * 0.25 + (rand() - 0.5) * 20;
        node.y = height * 0.5 + Math.sin(index * 2 * Math.PI / Math.max(1, nodes.length)) * height * 0.25 + (rand() - 0.5) * 20;
        node.vx = 0;
        node.vy = 0;
      });

      for (let tick = 0; tick < 180; tick += 1) {
        nodes.forEach(function(a, i) {
          for (let j = i + 1; j < nodes.length; j += 1) {
            const b = nodes[j];
            let dx = a.x - b.x;
            let dy = a.y - b.y;
            const dist2 = Math.max(50, dx * dx + dy * dy);
            const force = 1200 / dist2;
            const dist = Math.sqrt(dist2);
            dx /= dist;
            dy /= dist;
            a.vx += dx * force;
            a.vy += dy * force;
            b.vx -= dx * force;
            b.vy -= dy * force;
          }
        });

        links.forEach(function(link) {
          const a = link.source;
          const b = link.target;
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          const dist = Math.max(20, Math.sqrt(dx * dx + dy * dy));
          const force = (dist - 120) * 0.01;
          dx /= dist;
          dy /= dist;
          a.vx += dx * force;
          a.vy += dy * force;
          b.vx -= dx * force;
          b.vy -= dy * force;
        });

        nodes.forEach(function(node) {
          const cx = width * 0.5;
          const cy = height * 0.5;
          node.vx += (cx - node.x) * 0.002;
          node.vy += (cy - node.y) * 0.002;
          node.vx *= 0.9;
          node.vy *= 0.9;
          node.x = Math.max(24, Math.min(width - 24, node.x + node.vx));
          node.y = Math.max(24, Math.min(height - 24, node.y + node.vy));
        });
      }
      return nodes;
    }

    function drawAxes(svg, width, height, padding) {
      const palette = themePalette();
      const axis = createSvgEl('g', {'stroke': palette.axis, 'stroke-width': 1});
      axis.appendChild(createSvgEl('line', {
        x1: padding.left,
        y1: height - padding.bottom,
        x2: width - padding.right,
        y2: height - padding.bottom
      }));
      axis.appendChild(createSvgEl('line', {
        x1: padding.left,
        y1: padding.top,
        x2: padding.left,
        y2: height - padding.bottom
      }));
      svg.appendChild(axis);
    }

    function renderNetwork(data, state) {
      const svg = document.getElementById('network-svg');
      clearSvg(svg);
      const width = 980;
      const height = 560;
      const palette = themePalette();
      const nodes = (data.nodes || []).map(function(node, index) {
        return Object.assign({index: index}, node);
      });
      const byId = {};
      nodes.forEach(function(node) {
        byId[node.id] = node;
      });
      const links = (data.links || []).map(function(link) {
        return {
          source: byId[link.source],
          target: byId[link.target],
          t: link.t,
          e: link.e
        };
      }).filter(function(link) {
        return link.source && link.target;
      });
      if (!nodes.length) {
        const empty = createSvgEl('text', {x: width / 2, y: height / 2, fill: palette.empty, 'font-size': 16, 'text-anchor': 'middle'});
        empty.textContent = 'No temporal data loaded';
        svg.appendChild(empty);
        return;
      }
      const layoutName = resolveLayoutName();
      const layoutGraph = data.layout_graph || data;
      const graphSignature = data.graph_signature || currentGraphSignature || 'default';
      const positions = computeLayoutPositions(layoutGraph, layoutName, graphSignature);
      nodes.forEach(function(node) {
        const pos = positions[String(node.id)];
        if (pos) {
          node.x = pos.x;
          node.y = pos.y;
        }
      });

      const title = createSvgEl('text', {x: 20, y: 28, fill: palette.label, 'font-size': 13});
      title.textContent = state.selection_mode === 'window' && state.selected_window
        ? 'Window ' + state.selected_window[0] + ' - ' + state.selected_window[1]
        : (state.selected_snapshot !== null && state.selected_snapshot !== undefined
          ? 'Snapshot ' + state.selected_snapshot
          : 'All snapshots');
      svg.appendChild(title);

      const edgeLayer = createSvgEl('g', {'stroke': palette.edge, 'stroke-opacity': 0.95});
      links.forEach(function(link) {
        edgeLayer.appendChild(createSvgEl('line', {
          x1: link.source.x,
          y1: link.source.y,
          x2: link.target.x,
          y2: link.target.y,
          'stroke-width': 1.4,
          'stroke-linecap': 'round'
        }));
      });
      svg.appendChild(edgeLayer);

      const nodeLayer = createSvgEl('g');
      nodes.forEach(function(node) {
        const group = createSvgEl('g');
        const circle = createSvgEl('circle', {
          cx: node.x,
          cy: node.y,
          r: 14,
          fill: palette.node,
          stroke: palette.nodeStroke,
          'stroke-width': 2
        });
        const label = createSvgEl('text', {
          x: node.x,
          y: node.y - 18,
          fill: palette.label,
          'font-size': 11,
          'text-anchor': 'middle'
        });
        label.textContent = node.id;
        group.appendChild(circle);
        group.appendChild(label);
        nodeLayer.appendChild(group);
      });
      svg.appendChild(nodeLayer);
    }

    function renderLineChart(svgId, data, state, titleText) {
      const svg = document.getElementById(svgId);
      clearSvg(svg);
      const width = 980;
      const height = 460;
      const padding = {top: 18, right: 20, bottom: 42, left: 96};
      const palette = themePalette();
      const series = data.snapshots || [];
      const values = data.values || [];
      const maxValue = Math.max(1, ...values);
      const chartContainer = svg.closest('.timeline-chart');
      if (chartContainer) {
        const existingTooltip = chartContainer.querySelector('.plot-tooltip');
        if (existingTooltip) {
          existingTooltip.remove();
        }
      }
      if (!series.length || !values.length) {
        const empty = createSvgEl('text', {x: width / 2, y: height / 2, fill: palette.empty, 'font-size': 14, 'text-anchor': 'middle'});
        empty.textContent = 'No temporal data loaded';
        svg.appendChild(empty);
        return;
      }
      drawAxes(svg, width, height, padding);

      const isDensityChart = String(titleText || '').toLowerCase().indexOf('density') >= 0;
      const yAxisLabel = isDensityChart ? 'Density' : 'Interactions';
      const xAxisLabel = 'Snapshot';
      const formatValue = function(value) {
        return Math.abs(value - Math.round(value)) < 0.001 ? String(Math.round(value)) : value.toFixed(2);
      };

      const points = values.map(function(value, index) {
        const x = scale(series[index], series[0], series[series.length - 1], padding.left, width - padding.right);
        const y = scale(value, 0, maxValue, height - padding.bottom, padding.top);
        return [x, y];
      });
      const yTicks = [0, maxValue / 2, maxValue];
      yTicks.forEach(function(tickValue) {
        const y = scale(tickValue, 0, maxValue, height - padding.bottom, padding.top);
        svg.appendChild(createSvgEl('line', {
          x1: padding.left - 4,
          y1: y,
          x2: padding.left,
          y2: y,
          stroke: palette.axis,
          'stroke-width': 1,
          class: 'plot-axis plot-tick'
        }));
        const tickLabel = createSvgEl('text', {
          x: padding.left - 14,
          y: y + 4,
          fill: palette.muted,
          'font-size': 20,
          'font-weight': 700,
          'text-anchor': 'end',
          class: 'plot-label'
        });
        tickLabel.textContent = formatValue(tickValue);
        svg.appendChild(tickLabel);
      });
      const xStep = Math.max(1, Math.ceil(series.length / 5));
      series.forEach(function(snapshot, index) {
        if (index !== 0 && index !== series.length - 1 && index % xStep !== 0) {
          return;
        }
        const x = scale(snapshot, series[0], series[series.length - 1], padding.left, width - padding.right);
        svg.appendChild(createSvgEl('line', {
          x1: x,
          y1: height - padding.bottom,
          x2: x,
          y2: height - padding.bottom + 5,
          stroke: palette.axis,
          'stroke-width': 1,
          class: 'plot-axis plot-tick'
        }));
        const tickLabel = createSvgEl('text', {
          x: x,
          y: height - padding.bottom + 24,
          fill: palette.muted,
          'font-size': 20,
          'font-weight': 700,
          'text-anchor': 'middle',
          class: 'plot-label'
        });
        tickLabel.textContent = String(snapshot);
        svg.appendChild(tickLabel);
      });
      svg.appendChild(createSvgEl('text', {
        x: width / 2,
        y: height - 8,
        fill: palette.muted,
        'font-size': 20,
        'font-weight': 700,
        'text-anchor': 'middle',
        class: 'plot-label'
      })).textContent = xAxisLabel;
      const yAxis = createSvgEl('text', {
        x: 20,
        y: height / 2,
        fill: palette.muted,
        'font-size': 20,
        'font-weight': 700,
        'text-anchor': 'middle',
        transform: 'rotate(-90 20 ' + (height / 2) + ')',
        class: 'plot-label'
      });
      yAxis.textContent = yAxisLabel;
      svg.appendChild(yAxis);
      if (points.length >= 2) {
        const baseline = height - padding.bottom;
        const areaPoints = points.map(function(point) {
          return point[0] + ',' + point[1];
        });
        areaPoints.push(points[points.length - 1][0] + ',' + baseline);
        areaPoints.push(points[0][0] + ',' + baseline);
        svg.appendChild(createSvgEl('polygon', {
          fill: 'rgba(99, 102, 241, 0.14)',
          class: 'plot-fill',
          points: areaPoints.join(' ')
        }));
      }
      const polyline = createSvgEl('polyline', {
        fill: 'none',
        stroke: palette.line,
        'stroke-width': 2.8,
        class: 'plot-line',
        points: points.map(function(p) { return p[0] + ',' + p[1]; }).join(' ')
      });
      svg.appendChild(polyline);

      points.forEach(function(point, index) {
        const tooltipText = formatValue(values[index]) + ' at snapshot ' + String(series[index]);
        const markerGroup = createSvgEl('g', {
          class: 'plot-marker-group',
          style: 'cursor: help'
        });
        markerGroup.appendChild(createSvgEl('circle', {
          cx: point[0],
          cy: point[1],
          r: 11,
          fill: 'transparent',
          stroke: 'transparent',
          class: 'plot-marker-hit',
          'pointer-events': 'all'
        }));
        markerGroup.appendChild(createSvgEl('circle', {
          cx: point[0],
          cy: point[1],
          r: 4.5,
          fill: palette.marker,
          class: 'plot-marker'
        }));
        markerGroup.addEventListener('pointerenter', function(event) {
          if (!chartContainer) return;
          let tooltip = chartContainer.querySelector('.plot-tooltip');
          if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.className = 'plot-tooltip';
            chartContainer.appendChild(tooltip);
          }
          tooltip.textContent = tooltipText;
          tooltip.style.display = 'block';
          const rect = chartContainer.getBoundingClientRect();
          const offset = 14;
          const maxLeft = Math.max(0, rect.width - 228);
          const maxTop = Math.max(0, rect.height - 52);
          const left = Math.min(maxLeft, Math.max(0, event.clientX - rect.left + offset));
          const top = Math.min(maxTop, Math.max(0, event.clientY - rect.top - 34));
          tooltip.style.left = left + 'px';
          tooltip.style.top = top + 'px';
        });
        markerGroup.addEventListener('pointermove', function(event) {
          if (!chartContainer) return;
          const tooltip = chartContainer.querySelector('.plot-tooltip');
          if (!tooltip || tooltip.style.display !== 'block') return;
          const rect = chartContainer.getBoundingClientRect();
          const offset = 14;
          const maxLeft = Math.max(0, rect.width - 228);
          const maxTop = Math.max(0, rect.height - 52);
          const left = Math.min(maxLeft, Math.max(0, event.clientX - rect.left + offset));
          const top = Math.min(maxTop, Math.max(0, event.clientY - rect.top - 34));
          tooltip.style.left = left + 'px';
          tooltip.style.top = top + 'px';
        });
        markerGroup.addEventListener('pointerleave', function() {
          if (!chartContainer) return;
          const tooltip = chartContainer.querySelector('.plot-tooltip');
          if (tooltip) {
            tooltip.style.display = 'none';
          }
        });
        svg.appendChild(markerGroup);
      });

      if (state.selection_mode === 'snapshot' && state.selected_snapshot !== null && state.selected_snapshot !== undefined) {
        const idx = series.indexOf(state.selected_snapshot);
        if (idx >= 0) {
          const x = points[idx][0];
          svg.appendChild(createSvgEl('line', {
            x1: x,
            y1: padding.top,
            x2: x,
            y2: height - padding.bottom,
            stroke: palette.marker,
            'stroke-width': 1.5,
            'stroke-dasharray': '4 4',
            class: 'plot-axis'
          }));
        }
      }

      if (state.selection_mode === 'window' && state.selected_window) {
        const startIdx = series.indexOf(state.selected_window[0]);
        const endIdx = series.indexOf(state.selected_window[1]);
        if (startIdx >= 0 && endIdx >= 0) {
          const x1 = points[startIdx][0];
          const x2 = points[endIdx][0];
          svg.appendChild(createSvgEl('rect', {
            x: Math.min(x1, x2),
            y: padding.top,
            width: Math.max(1, Math.abs(x2 - x1)),
            height: height - padding.top - padding.bottom,
            fill: palette.windowFill,
            class: 'plot-fill'
          }));
        }
      }
    }

    function renderTimeline(data, state) {
      renderLineChart('timeline-interactions-svg', {
        snapshots: data.snapshots,
        values: data.interactions
      }, state, 'Interaction count over time');
      renderLineChart('timeline-nodes-svg', {
        snapshots: data.snapshots,
        values: data.active_nodes
      }, state, 'Active node count over time');
    }

    function renderSnapshots(options, selected) {
      const select = document.getElementById('snapshot-select');
      select.innerHTML = '';
      if (!options.length) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'No snapshots';
        select.appendChild(opt);
        select.disabled = true;
        return;
      }
      select.disabled = false;
      options.forEach(function(value) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = value;
        if (value === selected) {
          opt.selected = true;
        }
        select.appendChild(opt);
      });
    }

    function renderWindowOptions(options, selectedWindow) {
      const startSelect = document.getElementById('window-start-select');
      const endSelect = document.getElementById('window-end-select');
      startSelect.innerHTML = '';
      endSelect.innerHTML = '';
      if (!options.length) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'No snapshots';
        startSelect.appendChild(opt.cloneNode(true));
        endSelect.appendChild(opt);
        startSelect.disabled = true;
        endSelect.disabled = true;
        return;
      }
      startSelect.disabled = false;
      endSelect.disabled = false;
      options.forEach(function(value) {
        const startOpt = document.createElement('option');
        startOpt.value = value;
        startOpt.textContent = value;
        if (selectedWindow && value === selectedWindow[0]) {
          startOpt.selected = true;
        }
        startSelect.appendChild(startOpt);

        const endOpt = document.createElement('option');
        endOpt.value = value;
        endOpt.textContent = value;
        if (selectedWindow && value === selectedWindow[1]) {
          endOpt.selected = true;
        }
        endSelect.appendChild(endOpt);
      });
    }

    async function refreshState() {
      const state = await getJson('/api/state');
      const graph = await getJson('/api/current_graph');
      const chartData = await getJson('/api/chart_data');
      currentDashboardState = state;
      if (graph.graph_signature && graph.graph_signature !== currentGraphSignature) {
        layoutPositionCache.clear();
        currentGraphSignature = graph.graph_signature;
      }
      const streamEligible = Boolean(graph.stream_view && graph.stream_view.eligible);
      if (!streamEligible) {
        currentNetworkMode = 'graph';
      } else if (!currentNetworkModeUserSelected && currentNetworkMode !== 'link-stream') {
        currentNetworkMode = 'link-stream';
      }
      syncNetworkModeButtons(streamEligible);
      document.getElementById('state-summary').textContent =
        'Graph kind: ' + state.graph_kind + ' | Selection: ' + state.selection_mode + ' | Total nodes: ' + state.total_nodes + ' | Total interactions: ' + state.total_interactions;
      document.getElementById('metric-graph-kind').textContent = state.graph_kind;
      document.getElementById('metric-graph-kind-sub').textContent = state.snapshots.length
        ? 'Snapshots available: ' + state.snapshots.length
        : 'No snapshots loaded yet.';
      document.getElementById('metric-selection-mode').textContent = state.selection_mode;
      document.getElementById('metric-selection-sub').textContent = state.selection_mode === 'window' && state.selected_window
        ? 'Window ' + state.selected_window[0] + ' - ' + state.selected_window[1]
        : (state.selected_snapshot !== null && state.selected_snapshot !== undefined
          ? 'Snapshot ' + state.selected_snapshot
          : 'All snapshots visible');
      document.getElementById('metric-total-nodes').textContent = String(state.total_nodes);
      document.getElementById('metric-total-interactions').textContent = String(state.total_interactions);
      document.getElementById('metric-density').textContent = 'Density: ' + currentDensityValue(state).toFixed(3);
      const slider = document.getElementById('playback-slider');
      const playbackStep = document.getElementById('playback-step');
      if (slider && playbackStep) {
        if (state.snapshots && state.snapshots.length) {
          slider.disabled = false;
          slider.min = '0';
          slider.max = String(state.snapshots.length - 1);
          let index = 0;
          if (state.selection_mode === 'window' && state.selected_window) {
            index = state.snapshots.indexOf(state.selected_window[0]);
          } else if (state.selected_snapshot !== null && state.selected_snapshot !== undefined) {
            index = state.snapshots.indexOf(state.selected_snapshot);
          }
          if (index < 0) {
            index = 0;
          }
          slider.value = String(index);
          playbackStep.textContent = String(state.snapshots[index]);
        } else {
          slider.disabled = true;
          slider.min = '0';
          slider.max = '0';
          slider.value = '0';
          playbackStep.textContent = '0';
        }
      }
      syncPlaybackLabel();
      syncFullscreenButtons();
      syncSidebarButton();
      renderSnapshots(state.snapshots || [], state.selected_snapshot);
      renderWindowOptions(state.snapshots || [], state.selected_window);
      if (currentNetworkMode === 'link-stream' && streamEligible) {
        renderLinkStream(graph.stream_view);
      } else {
        renderNetwork(graph, state);
      }
      renderTimeline(chartData, state);
    }

    async function loadGraphFile() {
      const fileInput = document.getElementById('graph-file');
      if (!fileInput.files.length) {
        alert('Choose a JSON graph file first.');
        return;
      }
      const text = await fileInput.files[0].text();
      await getJson('/api/load_graph', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(JSON.parse(text))
      });
      await refreshState();
    }

    async function generateGraph() {
      try {
        const model = selectedNetworkModel();
        const payload = {
          kind: document.getElementById('graph-kind').value,
          num_nodes: Number(document.getElementById('num-nodes').value),
          snapshots: Number(document.getElementById('snapshots').value),
          edge_probability: Number(document.getElementById('edge-probability').value),
          seed: Number(document.getElementById('seed').value),
          network_model: model,
          dynamic_nodes: document.getElementById('node-mode').value === 'dynamic',
          node_churn: Number(document.getElementById('node-churn').value)
        };
        if (model === 'barabasi_albert') {
          payload.ba_m = Number(document.getElementById('ba-m').value);
        } else if (model === 'watts_strogatz') {
          payload.ws_k = Number(document.getElementById('ws-k').value);
          payload.ws_beta = Number(document.getElementById('ws-beta').value);
        } else if (model === 'stochastic_block_model') {
          payload.sbm_groups = Number(document.getElementById('sbm-groups').value);
          payload.sbm_p_in = Number(document.getElementById('sbm-p-in').value);
          payload.sbm_p_out = Number(document.getElementById('sbm-p-out').value);
        } else if (model === 'activity_driven' || model === 'activity_driven_memory') {
          const suffix = model === 'activity_driven_memory' ? '-memory' : '';
          payload.activity_m = Number(document.getElementById('activity-m' + suffix).value);
          payload.contact_duration = Number(document.getElementById('contact-duration' + suffix).value);
          payload.activity_min = Number(document.getElementById('activity-min' + suffix).value);
          payload.activity_max = Number(document.getElementById('activity-max' + suffix).value);
          payload.activity_exponent = Number(document.getElementById('activity-exponent' + suffix).value);
          if (model === 'activity_driven_memory') {
            payload.memory_alpha = Number(document.getElementById('memory-alpha').value);
          }
        }
        await getJson('/api/generate_graph', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        await refreshState();
      } catch (err) {
        console.error('Error generating graph:', err);
        alert('Failed to generate graph: ' + err.message);
      }
    }

    async function selectSnapshot() {
      const select = document.getElementById('snapshot-select');
      if (!select.value) {
        return;
      }
      await getJson('/api/select', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({snapshot: Number(select.value)})
      });
      await refreshState();
    }

    async function applyWindow() {
      const startSelect = document.getElementById('window-start-select');
      const endSelect = document.getElementById('window-end-select');
      if (!startSelect.value || !endSelect.value) {
        return;
      }
      await getJson('/api/select', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({window: [Number(startSelect.value), Number(endSelect.value)]})
      });
      await refreshState();
    }

    async function stepSelection(delta, mode) {
      await getJson('/api/step_selection', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({delta: delta, mode: mode})
      });
      await refreshState();
    }

    async function clearSelection() {
      await getJson('/api/clear_selection', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
      });
      await refreshState();
    }

    async function advancePlayback() {
      const state = currentDashboardState || await getJson('/api/state');
      const snapshots = state.snapshots || [];
      if (!snapshots.length) {
        return;
      }
      const mode = getPlaybackMode();
      if (mode === 'window') {
        const current = state.selected_window || [snapshots[0], snapshots[Math.min(1, snapshots.length - 1)]];
        const width = Math.max(1, current[1] - current[0]);
        const startIndex = snapshots.indexOf(current[0]);
        const nextIndex = (startIndex >= 0 ? startIndex + 1 : 0) % snapshots.length;
        const nextStart = snapshots[nextIndex];
        const nextEnd = snapshots[Math.min(snapshots.length - 1, nextIndex + width)];
        await getJson('/api/select', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({window: [Number(nextStart), Number(nextEnd)]})
        });
      } else {
        const currentSnapshot = state.selected_snapshot !== null && state.selected_snapshot !== undefined
          ? state.selected_snapshot
          : snapshots[0];
        const currentIndex = snapshots.indexOf(currentSnapshot);
        const nextIndex = (currentIndex >= 0 ? currentIndex + 1 : 0) % snapshots.length;
        await getJson('/api/select', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({snapshot: Number(snapshots[nextIndex])})
        });
      }
      await refreshState();
    }

    function stopPlayback() {
      if (playbackTimer) {
        window.clearInterval(playbackTimer);
        playbackTimer = null;
      }
      syncPlaybackLabel();
    }

    function togglePlayback() {
      if (playbackTimer) {
        stopPlayback();
        return;
      }
      playbackTimer = window.setInterval(function() {
        advancePlayback().catch(function(err) {
          stopPlayback();
          console.error(err);
        });
      }, 1400);
      syncPlaybackLabel();
    }

    async function downloadState() {
      const res = await fetch('/api/export_state');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'dynetx_dashboard_state.json';
      a.click();
      URL.revokeObjectURL(url);
    }

    async function downloadCsv() {
      const chartData = await getJson('/api/chart_data');
      const rows = [['snapshot', 'active_nodes', 'interactions', 'density']];
      (chartData.snapshots || []).forEach(function(snapshot, index) {
        rows.push([
          snapshot,
          (chartData.active_nodes || [])[index],
          (chartData.interactions || [])[index],
          (chartData.density || [])[index]
        ]);
      });
      const csv = rows.map(function(row) {
        return row.map(function(value) {
          return '"' + String(value ?? '').replaceAll('"', '""') + '"';
        }).join(',');
      }).join('\\n');
      const blob = new Blob([csv], {type: 'text/csv;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'dynetx_dashboard_chart.csv';
      a.click();
      URL.revokeObjectURL(url);
    }

    initTheme();
    initLayout();
    syncSidebarButton();
    updateGeneratorState();
    refreshState().catch(function(err) {
      document.getElementById('state-summary').textContent = 'Dashboard not initialized: ' + err.message;
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
