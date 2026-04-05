"""Shared fixtures for mivoca scoring tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def mock_responses() -> list[dict]:
    """Simulate a completed interview with responses across multiple modules."""
    return [
        # Formality items (M01)
        {"question_id": "M01-Q01", "scale_value": 5, "timing": {"duration_ms": 4500}},
        {"question_id": "M01-Q02", "scale_value": 6, "timing": {"duration_ms": 3200}},
        {"question_id": "M01-Q03", "scale_value": 4, "timing": {"duration_ms": 5100}},
        {"question_id": "M01-Q04", "scale_value": 5, "timing": {"duration_ms": 4000}},
        {"question_id": "M01-Q05", "scale_value": 5, "timing": {"duration_ms": 3800}},
        # Emotional tone items (M02, M03)
        {"question_id": "M02-Q01", "scale_value": 3, "timing": {"duration_ms": 3500}},
        {"question_id": "M02-Q02", "scale_value": 4, "timing": {"duration_ms": 4200}},
        {"question_id": "M02-Q03", "scale_value": 3, "timing": {"duration_ms": 3900}},
        {"question_id": "M02-Q04", "scale_value": 2, "timing": {"duration_ms": 4100}},
        {"question_id": "M03-Q01", "scale_value": 4, "timing": {"duration_ms": 3700}},
        {"question_id": "M03-Q02", "scale_value": 3, "timing": {"duration_ms": 4500}},
        # Complexity items (M04)
        {"question_id": "M04-Q01", "scale_value": 6, "timing": {"duration_ms": 5000}},
        {"question_id": "M04-Q02", "scale_value": 5, "timing": {"duration_ms": 4800}},
        {"question_id": "M04-Q03", "scale_value": 7, "timing": {"duration_ms": 4300}},
        {"question_id": "M04-Q04", "scale_value": 6, "timing": {"duration_ms": 4600}},
        {"question_id": "M04-Q05", "scale_value": 5, "timing": {"duration_ms": 3900}},
    ]


@pytest.fixture
def mock_dimension_mapping() -> dict:
    """Simplified dimension-to-item mapping."""
    return {
        "formality": ["M01-Q01", "M01-Q02", "M01-Q03", "M01-Q04", "M01-Q05"],
        "emotional_tone": [
            "M02-Q01", "M02-Q02", "M02-Q03", "M02-Q04",
            "M03-Q01", "M03-Q02",
        ],
        "complexity": ["M04-Q01", "M04-Q02", "M04-Q03", "M04-Q04", "M04-Q05"],
    }


@pytest.fixture
def mock_scoring_weights() -> dict:
    """Simplified scoring weights (all equal at 1.0)."""
    return {
        "formality": {
            "M01-Q01": 1.0,
            "M01-Q02": 1.0,
            "M01-Q03": 1.0,
            "M01-Q04": 1.0,
            "M01-Q05": 1.0,
        },
        "emotional_tone": {
            "M02-Q01": 1.0,
            "M02-Q02": 1.0,
            "M02-Q03": 1.0,
            "M02-Q04": 1.0,
            "M03-Q01": 1.0,
            "M03-Q02": 1.0,
        },
        "complexity": {
            "M04-Q01": 1.0,
            "M04-Q02": 1.0,
            "M04-Q03": 1.0,
            "M04-Q04": 1.0,
            "M04-Q05": 1.0,
        },
    }
