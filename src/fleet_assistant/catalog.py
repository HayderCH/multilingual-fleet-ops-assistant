from __future__ import annotations

from typing import Any

VEHICLES: dict[int, dict[str, Any]] = {
    2: {
        "vehicle_id": 2,
        "label": "Demo Van 2",
        "city": "Tunis",
        "status": "moving",
        "speed_kmh": 38,
        "latitude": 36.8065,
        "longitude": 10.1815,
        "engine_minutes_today": 126,
        "distance_km_today": 74.2,
    },
    4: {
        "vehicle_id": 4,
        "label": "Demo Car 4",
        "city": "La Marsa",
        "status": "stopped",
        "speed_kmh": 0,
        "latitude": 36.8782,
        "longitude": 10.3247,
        "engine_minutes_today": 81,
        "distance_km_today": 43.7,
    },
}


def list_vehicles() -> list[dict[str, Any]]:
    return [
        {"vehicle_id": row["vehicle_id"], "label": row["label"], "status": row["status"]}
        for row in VEHICLES.values()
    ]


def vehicle(vehicle_id: int) -> dict[str, Any] | None:
    row = VEHICLES.get(vehicle_id)
    return dict(row) if row else None
