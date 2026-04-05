"""Tests for lib.branching — branching evaluator."""

from __future__ import annotations

import pytest

from lib.branching import (
    evaluate_primary_route,
    get_engagement_reset_points,
    get_module_sequence,
    is_module_active,
)


# ---- helpers -----------------------------------------------------------------


def _screening(context: str, experience: float | None = None) -> list[dict]:
    """Build a minimal screening-response list."""
    responses: list[dict] = [{"question_id": "M01-Q05", "response": context}]
    if experience is not None:
        responses.append({"question_id": "M01-Q10", "response": experience})
    return responses


# ---- evaluate_primary_route --------------------------------------------------


def test_evaluate_route_business() -> None:
    """writer_context='business' routes to business_professional."""
    result = evaluate_primary_route(_screening("business"))
    assert result["writer_type"] == "business_professional"
    assert "M08" in result["activated_modules"]


def test_evaluate_route_creative() -> None:
    """writer_context='fiction' + experience>=3 routes to creative_literary."""
    result = evaluate_primary_route(_screening("fiction", experience=5))
    assert result["writer_type"] == "creative_literary"
    assert "M05" in result["activated_modules"]


def test_evaluate_route_creative_low_experience() -> None:
    """fiction + experience < 3 does NOT match creative_literary; falls to default."""
    result = evaluate_primary_route(_screening("fiction", experience=2))
    # creative_literary requires experience_level_min=3, so this falls through
    assert result["writer_type"] == "personal_journalistic"


def test_evaluate_route_academic() -> None:
    """writer_context='academic' routes to academic_technical."""
    result = evaluate_primary_route(_screening("academic"))
    assert result["writer_type"] == "academic_technical"
    assert "M06" in result["activated_modules"]


def test_evaluate_route_default() -> None:
    """Unknown writer context falls to the default branch (personal_journalistic)."""
    result = evaluate_primary_route(_screening("underwater_basket_weaving"))
    assert result["writer_type"] == "personal_journalistic"


# ---- module sequence ---------------------------------------------------------


def test_get_module_sequence_business() -> None:
    """Business path activates M07, M08, M11 plus all core modules."""
    seq = get_module_sequence("business_professional")
    active_ids = [e["module_id"] for e in seq if e["is_active"]]

    # Core modules always present
    for core in ("M01", "M02", "M03", "M04", "M09", "M12"):
        assert core in active_ids, f"Core module {core} should be active"

    # Branch-activated for business
    for branch_mod in ("M07", "M08", "M11"):
        assert branch_mod in active_ids, f"Branch module {branch_mod} should be active"

    # Modules NOT activated for business
    for inactive in ("M05", "M06", "M10"):
        assert inactive not in active_ids, f"{inactive} should NOT be active for business"


def test_is_module_active_business_m08() -> None:
    """M08 is active for business_professional."""
    assert is_module_active("M08", "business_professional") is True


def test_is_module_active_personal_m08() -> None:
    """M08 is NOT active for personal_journalistic (not in its activated_modules)."""
    assert is_module_active("M08", "personal_journalistic") is False


# ---- engagement reset points -------------------------------------------------


def test_get_engagement_reset_points() -> None:
    """At least one engagement reset point exists, and each has expected keys."""
    points = get_engagement_reset_points()
    assert len(points) >= 1

    for point in points:
        assert "after_module" in point
        assert "type" in point
        assert "position" in point

    # Verify known reset between M03/M04
    after_modules = [p["after_module"] for p in points]
    assert "M03" in after_modules, "Expected reset point after M03"
