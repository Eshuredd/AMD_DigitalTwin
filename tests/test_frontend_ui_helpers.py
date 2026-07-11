from __future__ import annotations

import base64

import pytest

from frontend.ui_helpers import (
    MAX_IMAGE_BYTES,
    encode_image_bytes_to_base64,
    format_percent,
    humanize_disease_label,
    keys_to_clear_after,
    sanitize_error_details,
    top_class_probabilities,
)


def test_encode_image_bytes_to_base64_round_trips() -> None:
    encoded = encode_image_bytes_to_base64(b"image-bytes")

    assert base64.b64decode(encoded) == b"image-bytes"


def test_encode_image_bytes_rejects_empty_and_oversized_payloads() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        encode_image_bytes_to_base64(b"")

    with pytest.raises(ValueError, match="10 MB"):
        encode_image_bytes_to_base64(b"x" * (MAX_IMAGE_BYTES + 1))


def test_humanize_disease_label() -> None:
    assert (
        humanize_disease_label("Tomato___Tomato_Yellow_Leaf_Curl_Virus")
        == "Tomato Yellow Leaf Curl Virus"
    )


def test_format_percent() -> None:
    assert format_percent(0.81234) == "81.2%"
    assert format_percent(None) == "n/a"


def test_top_class_probabilities_are_sorted_and_limited() -> None:
    assert top_class_probabilities({"b": 0.2, "a": 0.8, "c": 0.1}, limit=2) == [
        ("a", 0.8),
        ("b", 0.2),
    ]


def test_keys_to_clear_after_returns_downstream_keys() -> None:
    assert "recommendation_response" in keys_to_clear_after("simulation")
    assert "disease_response" not in keys_to_clear_after("simulation")
    assert keys_to_clear_after("unknown") == ()


def test_sanitize_error_details_redacts_nested_base64() -> None:
    sanitized = sanitize_error_details(
        {"outer": [{"image_base64": "secret", "other": "visible"}]}
    )

    assert sanitized == {"outer": [{"image_base64": "[redacted]", "other": "visible"}]}
