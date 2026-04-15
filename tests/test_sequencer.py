"""Tests for lib.sequencer — question sequencing logic."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from lib.sequencer import (
    get_active_modules,
    get_next_question,
    update_format_streak,
)


# ---- helpers -----------------------------------------------------------------


def _empty_state() -> dict[str, Any]:
    """Return a minimal session state with no writer type (screening phase)."""
    return {
        "session_id": "test-session",
        "state": "init",
        "writer_type": None,
        "branch_path": [],
        "current_module": None,
        "current_question_index": 0,
        "questions_answered": 0,
        "questions_remaining_estimate": 70,
        "elapsed_seconds": 0,
        "format_streak": {"current_type": None, "count": 0},
        "quality_flags": {
            "straightline_count": 0,
            "too_fast_count": 0,
            "attention_checks_passed": 0,
            "attention_checks_total": 0,
            "engagement_resets_triggered": 0,
        },
        "module_progress": {},
        "deep_dives_triggered": [],
        "deep_dive_return": None,
        "previous_state": None,
    }


def _state_with_branch(writer_type: str, current_module: str | None = None) -> dict[str, Any]:
    """Return a state dict with a branch already selected."""
    s = _empty_state()
    s["writer_type"] = writer_type
    s["state"] = "in_progress"
    s["current_module"] = current_module
    return s


def _responses_for_ids(question_ids: list[str]) -> list[dict[str, Any]]:
    """Build a list of stub response dicts for the given question IDs."""
    return [
        {"question_id": qid, "value": "stub", "duration_ms": 5000}
        for qid in question_ids
    ]


# ---- screening questions -----------------------------------------------------


def test_screening_first_question() -> None:
    """Empty state with no responses returns M01-Q01."""
    state = _empty_state()
    result = get_next_question(state, [])
    assert result["module_id"] == "M01"
    assert result["question"]["question_id"] == "M01-Q01"


def test_screening_with_responses() -> None:
    """With some M01 responses already answered, returns next unanswered."""
    state = _empty_state()
    responses = _responses_for_ids(["M01-Q01", "M01-Q02"])
    result = get_next_question(state, responses)
    assert result["module_id"] == "M01"
    assert result["question"]["question_id"] == "M01-Q03"


def test_screening_complete() -> None:
    """All M01 questions answered with no writer_type returns screening_complete."""
    state = _empty_state()
    all_m01 = [f"M01-Q{i:02d}" for i in range(1, 11)]
    responses = _responses_for_ids(all_m01)
    result = get_next_question(state, responses)
    assert result["action"] == "screening_complete"


# ---- module transitions ------------------------------------------------------


def test_module_transition() -> None:
    """After M01 complete with branch set, transitions to next active module."""
    state = _state_with_branch("business_professional", current_module="M01")
    all_m01 = [f"M01-Q{i:02d}" for i in range(1, 11)]
    responses = _responses_for_ids(all_m01)

    result = get_next_question(state, responses)

    # Should be presenting a question from the next module (M02 is core, always active)
    assert result["module_id"] == "M02"
    assert result["action"] == "module_transition"
    assert result["transition_message"] is not None


# ---- format streak -----------------------------------------------------------


def test_format_streak_tracking() -> None:
    """update_format_streak increments on same type, resets on different type."""
    state = _empty_state()

    streak = update_format_streak(state, "likert_scale")
    assert streak["current_type"] == "likert_scale"
    assert streak["count"] == 1

    streak = update_format_streak(state, "likert_scale")
    assert streak["count"] == 2

    streak = update_format_streak(state, "likert_scale")
    assert streak["count"] == 3

    # Type change resets
    streak = update_format_streak(state, "open_text")
    assert streak["current_type"] == "open_text"
    assert streak["count"] == 1


# ---- active modules ----------------------------------------------------------


def test_active_modules_business() -> None:
    """Business professional path has correct active modules."""
    modules = get_active_modules("business_professional")

    # Core modules always included
    for core in ("M01", "M02", "M03", "M04", "M09", "M12"):
        assert core in modules

    # Business-activated
    for bmod in ("M07", "M08", "M11"):
        assert bmod in modules

    # NOT activated for business
    for excluded in ("M05", "M06", "M10"):
        assert excluded not in modules


# ---- interview complete ------------------------------------------------------


def test_interview_complete() -> None:
    """When all active-module questions are answered, returns interview_complete."""
    state = _state_with_branch("personal_journalistic", current_module="M01")
    active = get_active_modules("personal_journalistic")

    # Build a fake responses list that covers every question in every active module.
    # We mock _load_module_questions to return a small deterministic set per module.
    fake_questions: dict[str, list[dict]] = {}
    for mod_id in active:
        fake_questions[mod_id] = [
            {
                "question_id": f"{mod_id}-Q01",
                "type": "likert_scale",
                "metadata": {"branching": {"required_branches": ["*"]}},
            }
        ]

    all_responses = _responses_for_ids([f"{m}-Q01" for m in active])

    with patch("lib.sequencer._load_module_questions", side_effect=lambda mid: fake_questions.get(mid, [])):
        with patch("lib.sequencer.check_deep_dive_triggers", return_value=None):
            result = get_next_question(state, all_responses)

    assert result["action"] == "interview_complete"
    assert result["question"] is None


# ---- progress ----------------------------------------------------------------


def test_progress_computation() -> None:
    """Progress percentages are between 0 and 100 and answered >= 0."""
    state = _empty_state()
    result = get_next_question(state, [])
    progress = result["progress"]

    assert progress["answered"] >= 0
    assert 0.0 <= progress["percent"] <= 100.0
    assert progress["estimated_remaining"] >= 0
