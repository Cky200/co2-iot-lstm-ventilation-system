"""Dashboard data models and normalization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TelemetryPoint:
    device_id: str
    timestamp: datetime
    co2_ppm: float
    voltage: float | None = None
    relay_state: bool | None = None
    fan_speed_percent: float | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TelemetryPoint":
        ppm = payload.get("co2_ppm", payload.get("ppm"))
        if ppm is None:
            raise ValueError("Telemetry payload requires co2_ppm or ppm")

        timestamp = payload.get("timestamp", payload.get("time", payload.get("ts")))
        parsed_timestamp = _parse_timestamp(timestamp)

        return cls(
            device_id=str(payload.get("device_id", "unknown")),
            timestamp=parsed_timestamp,
            co2_ppm=float(ppm),
            voltage=_optional_float(payload.get("voltage")),
            relay_state=_optional_bool(payload.get("relay_state")),
            fan_speed_percent=_optional_float(payload.get("fan_speed_percent")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass(frozen=True)
class VentilationStatus:
    relay_state: bool = False
    fan_speed_percent: float = 0.0
    mode: str = "auto"
    reason: str = "waiting_for_data"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VentilationStatus":
        fan_speed = payload.get("fan_speed_percent")
        if fan_speed is None:
            fan_speed = 100.0 if payload.get("relay_state", payload.get("relay_on", False)) else 0.0
        return cls(
            relay_state=bool(payload.get("relay_state", payload.get("relay_on", False))),
            fan_speed_percent=float(fan_speed),
            mode=str(payload.get("mode", "auto")),
            reason=str(payload.get("reason", "telemetry_update")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Alert:
    level: str
    message: str
    co2_ppm: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "co2_ppm": self.co2_ppm,
            "timestamp": self.timestamp.isoformat(),
        }


def _parse_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    raise ValueError(f"Unsupported timestamp value: {value!r}")


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
