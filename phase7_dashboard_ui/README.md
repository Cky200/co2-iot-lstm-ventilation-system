# Phase 7: Dashboard UI

Real-time web dashboard for CO2 monitoring and ventilation status. The dashboard uses Flask for HTTP APIs, Flask-SocketIO for WebSocket-style live updates, and Chart.js for responsive CO2 visualization.

## Features

- Live CO2 chart with Chart.js
- WebSocket updates for telemetry, ventilation status, and alerts
- REST ingestion endpoints for firmware or pipeline integration
- Ventilation status display with mode, relay state, fan speed, and reason
- Alert system for elevated, high, and critical CO2 levels
- Responsive operational UI for desktop and mobile
- Unit tests for APIs, Socket.IO events, alert logic, and data normalization

## Install

```bash
cd phase7_dashboard_ui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 -m dashboard_ui.main
```

By default the app listens on `0.0.0.0:5007`.

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind host |
| `DASHBOARD_PORT` | `5007` | Bind port |
| `DASHBOARD_SECRET_KEY` | `dev-dashboard-secret` | Flask secret key |
| `DASHBOARD_HISTORY_LIMIT` | `300` | Max live chart points retained |
| `DASHBOARD_ELEVATED_PPM` | `900` | Elevated alert threshold |
| `DASHBOARD_HIGH_PPM` | `1200` | High alert threshold |
| `DASHBOARD_CRITICAL_PPM` | `1800` | Critical alert threshold |
| `DASHBOARD_CORS_ORIGINS` | `*` | Socket.IO CORS origins |

## REST API

Post telemetry:

```bash
curl -X POST http://localhost:5007/api/telemetry \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"rpi_sensor_01","co2_ppm":950,"voltage":1.74,"relay_state":true}'
```

Update ventilation status:

```bash
curl -X POST http://localhost:5007/api/ventilation \
  -H 'Content-Type: application/json' \
  -d '{"relay_on":true,"fan_speed_percent":55,"mode":"auto","reason":"pid_control"}'
```

Read current state:

```bash
curl http://localhost:5007/api/state
```

## Socket.IO Events

Client receives:

- `state_snapshot`
- `telemetry_update`
- `ventilation_status`
- `alert`

Client may emit:

- `telemetry`
- `ventilation_status`

## Tests

```bash
python3 -m pytest phase7_dashboard_ui/tests -q
```
