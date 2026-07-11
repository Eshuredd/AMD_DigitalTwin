from __future__ import annotations

import base64
from html import escape
from typing import Any


MAX_IMAGE_BYTES = 10 * 1024 * 1024

ACTION_OPTIONS = [
    "IRRIGATE_NOW",
    "IRRIGATE_IN_6H",
    "IRRIGATE_TOMORROW_AM",
    "NO_IRRIGATION_24H",
]

SOIL_TEXTURE_OPTIONS = [
    "sand",
    "sandy_loam",
    "loam",
    "silty_loam",
    "clay_loam",
    "clay",
]

DOWNSTREAM_KEYS_BY_STEP = {
    "session": (
        "disease_response",
        "water_response",
        "twin_response",
        "simulation_response",
        "recommendation_response",
        "narration_response",
        "session_state_response",
        "history_response",
    ),
    "disease": (
        "twin_response",
        "simulation_response",
        "recommendation_response",
        "narration_response",
        "session_state_response",
        "history_response",
    ),
    "water": (
        "twin_response",
        "simulation_response",
        "recommendation_response",
        "narration_response",
        "session_state_response",
        "history_response",
    ),
    "twin": (
        "simulation_response",
        "recommendation_response",
        "narration_response",
        "session_state_response",
        "history_response",
    ),
    "simulation": ("recommendation_response", "narration_response"),
    "recommendation": ("narration_response",),
}


def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    if not image_bytes:
        raise ValueError("Upload a non-empty image file.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Image upload is larger than 10 MB.")
    return base64.b64encode(image_bytes).decode("ascii")


def humanize_disease_label(label: str) -> str:
    cleaned = label.replace("Tomato___", "").replace("_", " ").strip()
    return " ".join(cleaned.split())


def format_percent(value: float | int | None, *, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def top_class_probabilities(
    class_probs: dict[str, float],
    *,
    limit: int = 3,
) -> list[tuple[str, float]]:
    return sorted(class_probs.items(), key=lambda item: item[1], reverse=True)[:limit]


def keys_to_clear_after(step: str) -> tuple[str, ...]:
    return DOWNSTREAM_KEYS_BY_STEP.get(step, ())


def sanitize_error_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key == "image_base64" else sanitize_error_details(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_error_details(item) for item in value]
    return value


def escape_html(value: object) -> str:
    return escape(str(value), quote=True)


def badge_tone_for_uncertainty(uncertainty_band: str | None) -> str:
    if uncertainty_band == "low":
        return "success"
    if uncertainty_band == "medium":
        return "warning"
    if uncertainty_band == "high":
        return "danger"
    return "neutral"


def badge_tone_for_stress(stress_band: str | None) -> str:
    if stress_band == "low":
        return "success"
    if stress_band == "medium":
        return "warning"
    if stress_band == "high":
        return "danger"
    return "neutral"


def badge_tone_for_moisture(moisture_state: str | None) -> str:
    if moisture_state == "adequate":
        return "success"
    if moisture_state == "moderate_deficit":
        return "warning"
    if moisture_state == "depleted":
        return "danger"
    return "neutral"


def workflow_progress_states(completed: dict[str, bool]) -> list[dict[str, str]]:
    labels = [
        ("session", "Session"),
        ("disease", "Disease evidence"),
        ("water", "Water state"),
        ("twin", "Twin state"),
        ("simulation", "Simulations"),
        ("recommendation", "Recommendation"),
        ("narration", "Narration"),
    ]
    active_assigned = False
    states: list[dict[str, str]] = []

    for key, label in labels:
        if completed.get(key, False):
            state = "completed"
            symbol = "check"
        elif not active_assigned:
            state = "active"
            symbol = "current"
            active_assigned = True
        else:
            state = "pending"
            symbol = "pending"
        states.append({"key": key, "label": label, "state": state, "symbol": symbol})

    return states


def format_action_label(action: str) -> str:
    return action.replace("_", " ").title()
