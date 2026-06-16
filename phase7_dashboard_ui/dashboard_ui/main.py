"""CLI entrypoint for the dashboard."""

from __future__ import annotations

import os

from .app import create_app, socketio
from .config import DashboardConfig


def main() -> None:
    app = create_app(DashboardConfig())
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "5007"))
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
