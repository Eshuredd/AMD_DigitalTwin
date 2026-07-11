from __future__ import annotations

import base64
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
