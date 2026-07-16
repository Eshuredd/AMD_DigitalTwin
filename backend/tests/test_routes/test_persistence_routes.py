from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_state_store
from app.main import app
from app.schemas import (
    ActionEnum,
    CreateSessionRequest,
    CropType,
    Location,
    SoilTexture,
)
from app.state_store import InMemoryTwinStateStore


@pytest.fixture
def client_and_store() -> Iterator[tuple[TestClient, InMemoryTwinStateStore]]:
    store = InMemoryTwinStateStore()

    def override_get_state_store() -> InMemoryTwinStateStore:
        return store

    previous_override = app.dependency_overrides.get(get_state_store)
    app.dependency_overrides[get_state_store] = override_get_state_store

    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_state_store, None)
        else:
            app.dependency_overrides[get_state_store] = previous_override


def test_farm_plot_and_plot_crop_cycle_routes(
    client_and_store: tuple[TestClient, InMemoryTwinStateStore],
) -> None:
    client, store = client_and_store

    farm_response = client.post("/farms", json={"name": "Route Farm"})
    assert farm_response.status_code == 200
    farm = farm_response.json()

    assert client.get("/farms").json() == [farm]
    assert client.get(f"/farms/{farm['farm_id']}").json() == farm

    plot_payload = {
        "name": "Route Plot",
        "location": {
            "name": "Route Field",
            "latitude": 17.385,
            "longitude": 78.4867,
            "elevation_m": 542.0,
        },
        "soil_texture": "sandy_loam",
    }
    plot_response = client.post(
        f"/farms/{farm['farm_id']}/plots",
        json=plot_payload,
    )
    assert plot_response.status_code == 200
    plot = plot_response.json()

    assert client.get(f"/farms/{farm['farm_id']}/plots").json() == [plot]
    assert client.get(f"/plots/{plot['plot_id']}").json() == plot

    cycle_response = client.post(
        f"/plots/{plot['plot_id']}/crop-cycles",
        json={"crop_type": "tomato", "planting_date": "2026-06-01"},
    )
    assert cycle_response.status_code == 200
    cycle = cycle_response.json()

    assert cycle["state_id"]
    assert cycle["location"] == plot_payload["location"]
    assert store.get_record(cycle["state_id"]).plot_id == plot["plot_id"]


def test_actual_action_routes_record_physical_actions_only(
    client_and_store: tuple[TestClient, InMemoryTwinStateStore],
) -> None:
    client, store = client_and_store
    session = store.create_session(
        CreateSessionRequest(
            crop_type=CropType.TOMATO,
            planting_date=date(2026, 6, 1),
            location=Location(
                name="Action Farm",
                latitude=17.385,
                longitude=78.4867,
                elevation_m=542.0,
            ),
            soil_texture=SoilTexture.SANDY_LOAM,
        )
    )
    payload = {
        "action": ActionEnum.IRRIGATE_NOW.value,
        "performed_at": datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "amount_mm": 5.0,
        "notes": "Actual irrigation performed after field inspection.",
    }

    response = client.post(
        f"/sessions/{session.state_id}/actual-actions",
        json=payload,
    )
    assert response.status_code == 200
    action = response.json()

    assert action["state_id"] == session.state_id
    assert action["action"] == ActionEnum.IRRIGATE_NOW.value
    assert store.get_record(session.state_id).current_state is None

    list_response = client.get(
        f"/sessions/{session.state_id}/actual-actions",
        params={"limit": 50},
    )
    assert list_response.status_code == 200
    assert list_response.json() == [action]


def test_new_routes_preserve_not_found_envelope(
    client_and_store: tuple[TestClient, InMemoryTwinStateStore],
) -> None:
    client, _store = client_and_store

    response = client.get("/farms/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STATE_NOT_FOUND"

    action_response = client.get("/sessions/missing/actual-actions")
    assert action_response.status_code == 404
    assert action_response.json()["error"]["code"] == "STATE_NOT_FOUND"
