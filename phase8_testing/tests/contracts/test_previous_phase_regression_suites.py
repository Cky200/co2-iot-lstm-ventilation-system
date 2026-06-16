from __future__ import annotations

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "suite_path",
    [
        "tests",
        "phase5_iot_firmware/tests",
        "phase6_ventilation_control/tests",
        "phase7_dashboard_ui/tests",
    ],
)
def test_previous_phase_pytest_suite_passes(repo_root, suite_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(repo_root),
            str(repo_root / "phase5_iot_firmware"),
            str(repo_root / "phase6_ventilation_control"),
            str(repo_root / "phase7_dashboard_ui"),
            env.get("PYTHONPATH", ""),
        ]
    )

    result = subprocess.run(
        [sys.executable, "-m", "pytest", suite_path, "-q"],
        cwd=repo_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
