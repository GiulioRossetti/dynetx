*********
Dashboard
*********

Stateful dashboard helpers for temporal graphs, communities, and diffusion runs.

.. automodule:: dynetx.dashboard
.. autosummary::
   :toctree: generated/

   TemporalDashboard
   build_dashboard

Command line usage
------------------

After installation, run ``dynetx_dashboard`` or ``python -m
dynetx.dashboard.server`` to launch the browser dashboard. The service opens a
local web interface where you can load a temporal graph from a JSON file or
generate a synthetic snapshot/stream/dynamic graph, then inspect its timeline
and statistics. The dashboard now uses an NDlib-inspired layout with a
collapsible synthetic generator, day/night theme selection, SVG-based network
and chart rendering, a floating playback bar at the bottom of the workspace,
and auto-play controls for snapshot/window browsing.

Run ``dynetx_dashboard --help`` to inspect the server options. The browser
dashboard also exposes the current session state as JSON for reproducibility.
