from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_PATHS = [
    REPO_ROOT,
    REPO_ROOT / "phase5_iot_firmware",
    REPO_ROOT / "phase6_ventilation_control",
    REPO_ROOT / "phase7_dashboard_ui",
]

for path in PHASE_PATHS:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def fixed_timestamp() -> int:
    return 1781548200
