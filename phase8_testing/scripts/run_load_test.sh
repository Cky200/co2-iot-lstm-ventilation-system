#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="${1:-http://127.0.0.1:5007}"
USERS="${USERS:-20}"
SPAWN_RATE="${SPAWN_RATE:-5}"
RUN_TIME="${RUN_TIME:-1m}"

cd "$(dirname "$0")/.."
locust -f load_tests/locustfile.py --headless -u "$USERS" -r "$SPAWN_RATE" -t "$RUN_TIME" --host "$TARGET_HOST"
