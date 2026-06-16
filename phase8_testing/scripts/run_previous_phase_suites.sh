#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

python3 -m pytest tests -q
python3 -m pytest phase5_iot_firmware/tests -q
python3 -m pytest phase6_ventilation_control/tests -q
python3 -m pytest phase7_dashboard_ui/tests -q
