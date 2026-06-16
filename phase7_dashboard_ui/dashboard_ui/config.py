"""Configuration for the dashboard UI."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DashboardConfig:
    secret_key: str = os.getenv("DASHBOARD_SECRET_KEY", "dev-dashboard-secret")
    history_limit: int = int(os.getenv("DASHBOARD_HISTORY_LIMIT", "300"))
    elevated_ppm: float = float(os.getenv("DASHBOARD_ELEVATED_PPM", "900"))
    high_ppm: float = float(os.getenv("DASHBOARD_HIGH_PPM", "1200"))
    critical_ppm: float = float(os.getenv("DASHBOARD_CRITICAL_PPM", "1800"))
    cors_allowed_origins: str = os.getenv("DASHBOARD_CORS_ORIGINS", "*")
    debug: bool = _bool_env("DASHBOARD_DEBUG", False)
