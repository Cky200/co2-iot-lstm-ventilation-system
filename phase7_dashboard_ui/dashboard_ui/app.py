"""Flask application factory with Socket.IO support."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from .alerts import AlertManager, AlertThresholds
from .config import DashboardConfig
from .models import TelemetryPoint, VentilationStatus
from .store import DashboardStore

socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")


def create_app(config: DashboardConfig | None = None, store: DashboardStore | None = None) -> Flask:
    dashboard_config = config or DashboardConfig()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=dashboard_config.secret_key,
        DASHBOARD_CONFIG=dashboard_config,
    )

    dashboard_store = store or DashboardStore(
        max_points=dashboard_config.history_limit,
        alert_manager=AlertManager(
            AlertThresholds(
                elevated_ppm=dashboard_config.elevated_ppm,
                high_ppm=dashboard_config.high_ppm,
                critical_ppm=dashboard_config.critical_ppm,
            )
        ),
    )
    app.extensions["dashboard_store"] = dashboard_store

    socketio.init_app(app, cors_allowed_origins=dashboard_config.cors_allowed_origins)

    @app.errorhandler(ValueError)
    def handle_bad_request(error):
        return jsonify({"error": str(error)}), 400

    @app.get("/")
    def index():
        return render_template("dashboard.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/state")
    def state():
        return jsonify(dashboard_store.snapshot())

    @app.get("/api/history")
    def history():
        limit = request.args.get("limit", type=int)
        return jsonify({"data": dashboard_store.history(limit=limit)})

    @app.get("/api/alerts")
    def alerts():
        return jsonify({"data": dashboard_store.alerts()})

    @app.post("/api/telemetry")
    def ingest_telemetry():
        point, alert = dashboard_store.add_telemetry(TelemetryPoint.from_payload(request.get_json(force=True)))
        _broadcast_telemetry(point, alert)
        return jsonify({"status": "accepted", "telemetry": point.to_dict(), "alert": alert.to_dict() if alert else None}), 202

    @app.post("/api/ventilation")
    def update_ventilation():
        status = dashboard_store.update_ventilation(VentilationStatus.from_payload(request.get_json(force=True)))
        socketio.emit("ventilation_status", status.to_dict())
        return jsonify({"status": "accepted", "ventilation": status.to_dict()}), 202

    @socketio.on("connect")
    def on_connect():
        emit("state_snapshot", dashboard_store.snapshot())

    @socketio.on("telemetry")
    def on_socket_telemetry(payload):
        point, alert = dashboard_store.add_telemetry(TelemetryPoint.from_payload(payload))
        _broadcast_telemetry(point, alert)
        return {"status": "accepted"}

    @socketio.on("ventilation_status")
    def on_socket_ventilation(payload):
        status = dashboard_store.update_ventilation(VentilationStatus.from_payload(payload))
        socketio.emit("ventilation_status", status.to_dict())
        return {"status": "accepted"}

    return app


def _broadcast_telemetry(point: TelemetryPoint, alert) -> None:
    socketio.emit("telemetry_update", point.to_dict())
    if point.relay_state is not None or point.fan_speed_percent is not None:
        socketio.emit(
            "ventilation_status",
            VentilationStatus.from_payload(point.to_dict()).to_dict(),
        )
    if alert:
        socketio.emit("alert", alert.to_dict())
