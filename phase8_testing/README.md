# Phase 8: Testing

Comprehensive testing package covering the CO2 IoT project across previous phases.

## What This Covers

- Contract checks for previous phase artifacts and payload compatibility
- Integration test for Phase 5 sensor telemetry, Phase 6 ventilation control, and Phase 7 dashboard state
- API tests for dashboard health, telemetry ingestion, history, alerts, and validation errors
- End-to-end Socket.IO test for real-time dashboard updates
- Lightweight load/capacity test for dashboard ingestion storage
- Locust load-test scenario for a running dashboard service
- Coverage reports across `src`, Phase 5, Phase 6, and Phase 7 Python packages

## Install

```bash
cd phase8_testing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The tests import prior phase packages directly from the repository, so no package build step is required.

## Run Tests

From the repository root:

```bash
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests -q
```

Or from this folder:

```bash
python3 -m pytest -c pytest.ini
```

Phase 8 also verifies prior pytest suites by invoking each suite separately. This avoids pytest module-name collisions between phase folders that both contain files like `test_app.py`.

```bash
cd phase8_testing
./scripts/run_previous_phase_suites.sh
```

## Coverage Reports

```bash
cd phase8_testing
./scripts/run_phase8_tests.sh
```

Reports are written to:

- Terminal summary
- `phase8_testing/reports/htmlcov/index.html`
- `phase8_testing/reports/coverage.xml`

## Load Testing

Start the Phase 7 dashboard:

```bash
cd ../phase7_dashboard_ui
python3 -m dashboard_ui.main
```

Run the Locust load test:

```bash
cd ../phase8_testing
./scripts/run_load_test.sh http://127.0.0.1:5007
```

Optional controls:

```bash
USERS=50 SPAWN_RATE=10 RUN_TIME=3m ./scripts/run_load_test.sh http://127.0.0.1:5007
```

## Test Categories

```bash
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests/contracts
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests/integration
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests/api
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests/e2e
python3 -m pytest -c phase8_testing/pytest.ini phase8_testing/tests/load
```
