"""Tests for lib.quality — satisficing detection and quality monitoring."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from lib.quality import (
    check_response_quality,
    compute_session_quality_report,
    detect_alternation,
    detect_speed_flag,
    detect_straightlining,
)


# ---- helpers -----------------------------------------------------------------


def _scale_response(value: int, question_type: str = "likert_scale") -> dict[str, Any]:
    """Build a minimal scale response dict."""
    return {"value": value, "question_type": question_type, "duration_ms": 5000}


def _timed_response(
    value: int = 4,
    duration_ms: int = 5000,
    question_type: str = "likert_scale",
    question_id: str = "M02-Q01",
) -> dict[str, Any]:
    """Build a response dict with timing info."""
    return {
        "question_id": question_id,
        "value": value,
        "duration_ms": duration_ms,
        "question_type": question_type,
    }


def _question(estimated_seconds: int = 15) -> dict[str, Any]:
    """Build a minimal question definition."""
    return {"question_id": "M02-Q01", "estimated_seconds": estimated_seconds}


# ---- straightlining ----------------------------------------------------------


def test_detect_straightlining_positive() -> None:
    """5 identical scale values triggers straightlining."""
    responses = [_scale_response(4) for _ in range(5)]
    assert detect_straightlining(responses, threshold=5) is True


def test_detect_straightlining_negative() -> None:
    """Varied scale values do not trigger straightlining."""
    responses = [_scale_response(v) for v in [1, 3, 5, 2, 7]]
    assert detect_straightlining(responses, threshold=5) is False


def test_detect_straightlining_below_threshold() -> None:
    """Fewer than threshold responses returns False even if identical."""
    responses = [_scale_response(4) for _ in range(3)]
    assert detect_straightlining(responses, threshold=5) is False


def test_detect_straightlining_ignores_non_scale() -> None:
    """Non-scale responses are filtered out; only scale values are checked."""
    responses = [
        {"value": 4, "question_type": "open_text", "duration_ms": 5000},
        *[_scale_response(4) for _ in range(4)],
    ]
    # Only 4 scale values (open_text filtered), below threshold of 5
    assert detect_straightlining(responses, threshold=5) is False


# ---- speed flags -------------------------------------------------------------


def test_detect_speed_flag() -> None:
    """1000ms on a complex question (estimated>10s) flags too-fast."""
    resp = _timed_response(duration_ms=1000)
    q = _question(estimated_seconds=15)
    assert detect_speed_flag(resp, q) is True


def test_detect_speed_exempt_simple() -> None:
    """Fast response on a simple question (estimated<=5s) is exempt."""
    resp = _timed_response(duration_ms=500)
    q = _question(estimated_seconds=5)
    assert detect_speed_flag(resp, q) is False


def test_detect_speed_exempt_moderate() -> None:
    """Questions with estimated_seconds between 5 and 10 are also exempt."""
    resp = _timed_response(duration_ms=1000)
    q = _question(estimated_seconds=8)
    assert detect_speed_flag(resp, q) is False


def test_detect_speed_flag_no_duration() -> None:
    """Missing duration_ms returns False."""
    resp = {"value": 4, "question_type": "likert_scale"}
    q = _question(estimated_seconds=15)
    assert detect_speed_flag(resp, q) is False


# ---- alternation -------------------------------------------------------------


def test_detect_alternation() -> None:
    """1,7,1,7 pattern triggers alternation detection."""
    responses = [_scale_response(v) for v in [1, 7, 1, 7]]
    assert detect_alternation(responses, threshold=4) is True


def test_detect_alternation_negative() -> None:
    """Non-alternating values do not trigger."""
    responses = [_scale_response(v) for v in [3, 5, 2, 6]]
    assert detect_alternation(responses, threshold=4) is False


def test_detect_alternation_repeated_extremes() -> None:
    """Repeated extremes (1,1,7,7) are NOT alternation."""
    responses = [_scale_response(v) for v in [1, 1, 7, 7]]
    assert detect_alternation(responses, threshold=4) is False


def test_detect_alternation_non_extreme() -> None:
    """Alternating non-extreme values (2,6,2,6) are not flagged."""
    responses = [_scale_response(v) for v in [2, 6, 2, 6]]
    assert detect_alternation(responses, threshold=4) is False


# ---- check_response_quality --------------------------------------------------


def test_check_response_quality_clean() -> None:
    """A normal response with no issues produces no flags."""
    resp = _timed_response(value=4, duration_ms=8000)
    recent = [_scale_response(v) for v in [2, 5, 3, 6]]
    q = _question(estimated_seconds=15)

    result = check_response_quality(resp, recent, q)
    assert result["flag_count"] == 0
    assert result["needs_engagement_reset"] is False
    assert result["details"] is None


def test_check_response_quality_flagged() -> None:
    """Fast + straightlining together produces 2 flags and triggers reset."""
    # 4 identical recent + current = 5 identical => straightlining
    recent = [_scale_response(4) for _ in range(4)]
    resp = _timed_response(value=4, duration_ms=1000, question_type="likert_scale")
    q = _question(estimated_seconds=15)

    result = check_response_quality(resp, recent, q)
    assert result["flags"]["too_fast"] is True
    assert result["flags"]["straightlining"] is True
    assert result["flag_count"] >= 2
    assert result["needs_engagement_reset"] is True


# ---- needs_engagement_reset --------------------------------------------------


def test_needs_engagement_reset_threshold() -> None:
    """2+ cumulative flags in a single check triggers engagement reset."""
    # Construct a scenario with too_fast + straightlining
    recent = [_scale_response(4) for _ in range(4)]
    resp = _timed_response(value=4, duration_ms=1000, question_type="likert_scale")
    q = _question(estimated_seconds=15)

    result = check_response_quality(resp, recent, q)
    assert result["needs_engagement_reset"] is True


def test_needs_engagement_reset_single_flag() -> None:
    """A single flag does not trigger engagement reset."""
    recent = [_scale_response(4) for _ in range(4)]
    # duration is fine, but straightlining triggers (5 identical)
    resp = _timed_response(value=4, duration_ms=8000, question_type="likert_scale")
    q = _question(estimated_seconds=15)

    result = check_response_quality(resp, recent, q)
    assert result["flags"]["straightlining"] is True
    assert result["flags"]["too_fast"] is False
    assert result["flag_count"] == 1
    assert result["needs_engagement_reset"] is False


# ---- session quality report --------------------------------------------------


def _mock_quality_config() -> dict:
    """Return a minimal quality config for testing compute_session_quality_report."""
    return {
        "satisficing_rules": {
            "engagement_reset_threshold": {
                "min_flags": 2,
                "max_resets_per_session": 3,
            },
            "session_validity": {
                "max_flags_before_invalid": 8,
            },
        },
        "attention_checks": {
            "consistency_checks": [],
            "global_settings": {
                "min_checks_passed": 2,
            },
        },
    }


def test_session_quality_report() -> None:
    """A complete session report contains all expected fields."""
    responses = [
        _timed_response(value=v, duration_ms=8000, question_id=f"M02-Q{i:02d}")
        for i, v in enumerate([3, 5, 2, 6, 4, 1, 7, 3, 5, 2], start=1)
    ]
    questions = {
        f"M02-Q{i:02d}": _question(estimated_seconds=15)
        for i in range(1, 11)
    }

    with patch("lib.quality.load_quality_config", return_value=_mock_quality_config()):
        report = compute_session_quality_report(responses, questions)

    assert "total_responses" in report
    assert report["total_responses"] == 10
    assert "total_flags" in report
    assert "straightline_sequences" in report
    assert "too_fast_count" in report
    assert "alternation_count" in report
    assert "attention_check_results" in report
    assert "engagement_resets_triggered" in report
    assert "overall_quality" in report
    assert "flagged_responses" in report
    assert report["overall_quality"] in ("good", "acceptable", "questionable")
