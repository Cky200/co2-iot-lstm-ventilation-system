from __future__ import annotations

import random
import time

from locust import HttpUser, between, task


class DashboardUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(4)
    def post_telemetry(self) -> None:
        ppm = random.randint(650, 2100)
        self.client.post(
            "/api/telemetry",
            json={
                "device_id": f"load-sensor-{random.randint(1, 8)}",
                "ts": int(time.time()),
                "co2_ppm": ppm,
                "voltage": round(random.uniform(1.1, 2.6), 2),
                "relay_state": ppm >= 900,
                "fan_speed_percent": 100 if ppm >= 1800 else random.randint(0, 80),
            },
            name="/api/telemetry",
        )

    @task(2)
    def read_state(self) -> None:
        self.client.get("/api/state", name="/api/state")

    @task(1)
    def read_history(self) -> None:
        self.client.get("/api/history?limit=120", name="/api/history")

    @task(1)
    def update_ventilation(self) -> None:
        self.client.post(
            "/api/ventilation",
            json={
                "relay_on": True,
                "fan_speed_percent": random.randint(20, 100),
                "mode": "auto",
                "reason": "load_test",
            },
            name="/api/ventilation",
        )
