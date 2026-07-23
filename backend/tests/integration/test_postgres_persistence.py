from __future__ import annotations

from datetime import date, datetime, timezone
import os
import uuid

import pytest

from app.growth_stage.resolver import resolve_growth_stage
from app.persistence.sqlalchemy_store import SQLAlchemyTwinStateStore
from app.schemas import (
    CreateSessionRequest,
    CropType,
    DiseaseCategory,
    DiseasePredictionResponse,
    Location,
    SoilTexture,
    UncertaintyBand,
    WeatherInput,
)
from app.state_store import MissingCachedOutputError
from app.water.update_identity import (
    compute_water_update_fingerprint,
    derive_water_update_id,
)
from app.water.water_balance import compute_water_state


POSTGRES_URL = os.getenv("CROPTWIN_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires CROPTWIN_TEST_POSTGRES_URL",
)


def test_postgres_migrated_store_persists_canonical_water_and_snapshot_retry() -> None:
    assert POSTGRES_URL is not None
    state_id = f"state-postgres-{uuid.uuid4().hex}"
    store = SQLAlchemyTwinStateStore(
        database_url=POSTGRES_URL,
        auto_create=False,
    )
    session = store.create_session(_session_request(), state_id=state_id)
    disease = _disease(state_id)
    store.cache_disease_state(state_id, disease)

    record = store.get_record(state_id)
    growth = resolve_growth_stage(
        state_id=state_id,
        crop_type=record.crop_type,
        planting_date=record.planting_date,
        current_date=date(2026, 7, 10),
    )
    weather = _weather()
    water = compute_water_state(
        state_id=state_id,
        crop_type=record.crop_type,
        growth_stage=growth.growth_stage,
        soil_texture=record.soil_texture,
        current_date=growth.current_date,
        weather=weather,
        latitude_deg=record.location.latitude,
        elevation_m=record.location.elevation_m or 0.0,
        observed_at=datetime(2026, 7, 10, 7, 0, tzinfo=timezone.utc),
    )
    water_update_id = derive_water_update_id(
        state_id=state_id,
        observed_at=water.observed_at,
        observation_time_basis=water.observation_time_basis,
    )
    request_fingerprint = compute_water_update_fingerprint(
        state_id=state_id,
        water_update_id=water_update_id,
        current_date=growth.current_date,
        observed_at=water.observed_at,
        observation_time_basis=water.observation_time_basis,
        weather=weather,
        last_irrigation_event=None,
    )

    cached_water = store.cache_water_update(
        state_id,
        growth,
        water,
        water_update_id=water_update_id,
        request_fingerprint=request_fingerprint,
        weather_payload=weather.model_dump(mode="json"),
        computed_at=water.computed_at,
    )
    first_snapshot = store.update_current_state(state_id)
    retried_snapshot = store.update_current_state(state_id)

    assert session.state_id == state_id
    assert cached_water.water_sequence == 1
    assert first_snapshot.snapshot_created is True
    assert retried_snapshot.snapshot_created is False
    assert retried_snapshot.snapshot_id == first_snapshot.snapshot_id
    assert retried_snapshot.state_history_count == first_snapshot.state_history_count
    with pytest.raises(MissingCachedOutputError):
        store.get_latest_simulation(state_id)

    second_store = SQLAlchemyTwinStateStore(
        database_url=POSTGRES_URL,
        auto_create=False,
    )
    persisted_current = second_store.get_current_state(state_id)
    persisted_baseline = second_store.get_canonical_water_baseline(state_id)

    assert persisted_current == first_snapshot.current_state
    assert persisted_baseline is not None
    assert persisted_baseline.water_sequence == 1
    assert persisted_baseline.water_update_id == water_update_id
    assert persisted_baseline.water_observation_id == cached_water.water_observation_id


def _session_request() -> CreateSessionRequest:
    return CreateSessionRequest(
        crop_type=CropType.TOMATO,
        planting_date=date(2026, 6, 1),
        location=Location(
            name="PostgreSQL CI Farm",
            latitude=17.385,
            longitude=78.4867,
            elevation_m=542.0,
        ),
        soil_texture=SoilTexture.SANDY_LOAM,
    )


def _weather() -> WeatherInput:
    return WeatherInput(
        tmin_c=22.0,
        tmax_c=31.0,
        humidity_pct=62.0,
        wind_speed_mps=2.1,
        shortwave_radiation_sum_mj_m2=18.5,
        rainfall_mm=0.5,
        eto_reference_feed=4.9,
    )


def _disease(state_id: str) -> DiseasePredictionResponse:
    return DiseasePredictionResponse(
        state_id=state_id,
        crop_type=CropType.TOMATO,
        predicted_label="Tomato___healthy",
        disease_category=DiseaseCategory.NONE,
        class_probs={"Tomato___healthy": 0.94, "Tomato___Late_blight": 0.06},
        confidence_calibrated=0.94,
        uncertainty_score=0.06,
        uncertainty_band=UncertaintyBand.LOW,
        predicted_at=datetime(2026, 7, 10, 6, 0, tzinfo=timezone.utc),
    )
