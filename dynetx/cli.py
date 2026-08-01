"""Command line entry points for DyNetx helpers."""

from __future__ import annotations

from dynetx.dashboard.server import main


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
