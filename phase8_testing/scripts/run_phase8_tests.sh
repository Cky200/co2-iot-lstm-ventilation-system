#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m pytest -c pytest.ini --cov-config=.coveragerc --cov --cov-report=term-missing --cov-report=html --cov-report=xml
