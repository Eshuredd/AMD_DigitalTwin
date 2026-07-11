"""Health and system metadata routes for the tomato digital twin API.

The system-info route exposes deterministic MVP assumptions without running
domain computations or mutating state.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.growth_stage.resolver import (
    DEFAULT_STAGE_CONFIG_SOURCE,
    DEFAULT_TOMATO_STAGE_DAYS,
)
from app.narration.narrator import (
    MAX_LLM_RATIONALE_CHARS,
    MAX_LLM_RATIONALE_CHARS_BASIS,
)
from app.recommendation.engine import (
    FUNGAL_CONFIDENCE_THRESHOLD,
    FUNGAL_CONFIDENCE_THRESHOLD_BASIS,
)
from app.routes.disease import (
    DEFAULT_DISEASE_MODEL_BASIS,
    DEFAULT_DISEASE_MODEL_NAME,
    DEFAULT_DISEASE_MODEL_VERSION,
    DISEASE_CLASSES,
    INSUFFICIENT_SIGNAL_UNCERTAINTY_SCORE,
    MEDIUM_MOCK_UNCERTAINTY_SCORE,
    STRONG_MOCK_UNCERTAINTY_SCORE,
)
from app.schemas import (
    CautionReason,
    CropType,
    EtoMethod,
    HealthResponse,
)
from app.water.crop_coefficients import (
    DEFAULT_KC_CONFIG_SOURCE,
    get_kc_config_snapshot,
)
from app.water.water_balance import (
    DEFAULT_P_ALLOWABLE,
    DEFAULT_ROOT_DEPTH_BASIS,
    DEFAULT_SOIL_PARAMETER_BASIS,
)


router = APIRouter(tags=["meta"])


PROJECT_NAME = "tomato_irrigation_disease_digital_twin"
API_STAGE = "mvp"
API_SERVICE = "tomato_irrigation_disease_digital_twin_api"
API_VERSION = "mvp"
DECISION_BOUNDARY = "deterministic_engine_decides_narrator_explains"
E_TO_FALLBACK_TRIGGER = "shortwave_radiation_sum_mj_m2_missing"
E_TO_REFERENCE_FEED = "optional_weather_eto_reference_feed_for_delta_only"
DISEASE_DATASET = DEFAULT_DISEASE_MODEL_BASIS
DISEASE_CALIBRATION_METHOD = "deterministic_mock_confidence_assumptions"
DISEASE_UNCERTAINTY_METHOD = "deterministic_mock_signal_length_bands"
DISEASE_ECE_VALIDATION_SCORE = 0.0


def _stage_days_snapshot() -> dict[str, int]:
    return {
        growth_stage.value: days
        for growth_stage, days in DEFAULT_TOMATO_STAGE_DAYS.items()
    }


def _disease_classes_snapshot() -> list[dict[str, str]]:
    return [
        {
            "label": label,
            "category": category.value,
        }
        for label, category in DISEASE_CLASSES
    ]


@router.get("/health", response_model=HealthResponse)
def health_route() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=API_SERVICE,
        version=API_VERSION,
    )


@router.get("/system-info")
def system_info_route() -> dict[str, object]:
    return {
        "project_name": PROJECT_NAME,
        "api_stage": API_STAGE,
        "decision_boundary": DECISION_BOUNDARY,
        "crop_type": CropType.TOMATO.value,
        "disease_model": {
            "model_name": DEFAULT_DISEASE_MODEL_NAME,
            "model_version": DEFAULT_DISEASE_MODEL_VERSION,
            "dataset": DISEASE_DATASET,
            "calibration_method": DISEASE_CALIBRATION_METHOD,
            "uncertainty_method": DISEASE_UNCERTAINTY_METHOD,
            "uncertainty_thresholds": {
                "low_lt": STRONG_MOCK_UNCERTAINTY_SCORE,
                "medium_lt": MEDIUM_MOCK_UNCERTAINTY_SCORE,
                "high_gte": INSUFFICIENT_SIGNAL_UNCERTAINTY_SCORE,
            },
            "classes": _disease_classes_snapshot(),
            "ece_validation_score": DISEASE_ECE_VALIDATION_SCORE,
        },
        "growth_stage_config": {
            "source": DEFAULT_STAGE_CONFIG_SOURCE,
            "stages_days": _stage_days_snapshot(),
        },
        "water_model_config": {
            "primary_eto_method": EtoMethod.PENMAN_MONTEITH.value,
            "fallback_eto_method": EtoMethod.HARGREAVES_SAMANI.value,
            "fallback_trigger": E_TO_FALLBACK_TRIGGER,
            "reference_feed": E_TO_REFERENCE_FEED,
            "soil_parameter_basis": DEFAULT_SOIL_PARAMETER_BASIS,
            "root_depth_basis": DEFAULT_ROOT_DEPTH_BASIS,
            "p_allowable": DEFAULT_P_ALLOWABLE,
            "kc_config_source": DEFAULT_KC_CONFIG_SOURCE,
            "kc_by_stage": get_kc_config_snapshot(),
        },
        "recommendation_policy": {
            "fungal_confidence_threshold": FUNGAL_CONFIDENCE_THRESHOLD,
            "fungal_confidence_threshold_basis": (
                FUNGAL_CONFIDENCE_THRESHOLD_BASIS
            ),
        },
        "narrator_policy": {
            "caution_triggers": [
                CautionReason.HIGH_UNCERTAINTY.value,
                CautionReason.FUNGAL_DISEASE_RISK.value,
            ],
            "max_llm_rationale_chars": MAX_LLM_RATIONALE_CHARS,
            "max_llm_rationale_chars_basis": MAX_LLM_RATIONALE_CHARS_BASIS,
            "default_mode": "deterministic_fallback_no_llm_client",
        },
    }
