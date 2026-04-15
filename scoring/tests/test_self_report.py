"""Tests for voice_scoring.self_report module."""

from __future__ import annotations

import random

import numpy as np
import pytest

from voice_scoring.self_report import cronbachs_alpha, normalize_response, score_self_report


# ---------- normalize_response ----------


class TestNormalizeResponse:
    """Tests for normalize_response."""

    def test_normalize_likert_midpoint(self):
        """4 on a 1-7 Likert scale should normalize to ~50.0."""
        result = normalize_response(4, "likert", scale_min=1, scale_max=7)
        assert result == pytest.approx(50.0, abs=0.1)

    def test_normalize_likert_extremes(self):
        """1/7 -> 0.0, 7/7 -> 100.0 on default 1-7 scale."""
        low = normalize_response(1, "likert", scale_min=1, scale_max=7)
        high = normalize_response(7, "likert", scale_min=1, scale_max=7)
        assert low == pytest.approx(0.0)
        assert high == pytest.approx(100.0)

    def test_normalize_forced_choice(self):
        """Forced choice normalizes ordinal position to 0-100."""
        # Option 1 of 4 -> 0.0, option 4 of 4 -> 100.0, option 2 of 4 -> 33.33
        result_first = normalize_response(1, "forced_choice", n_options=4)
        result_last = normalize_response(4, "forced_choice", n_options=4)
        result_mid = normalize_response(2, "forced_choice", n_options=4)
        assert result_first == pytest.approx(0.0)
        assert result_last == pytest.approx(100.0)
        assert result_mid == pytest.approx(33.33, abs=0.1)

    def test_normalize_semantic_differential(self):
        """Semantic differential uses 1-7 Likert normalization."""
        result = normalize_response(4, "semantic_differential")
        assert result == pytest.approx(50.0, abs=0.1)

    def test_normalize_scenario(self):
        """Scenario responses are treated as ordinal."""
        result = normalize_response(3, "scenario", n_options=5)
        assert result == pytest.approx(50.0)

    def test_normalize_none_value(self):
        """None input returns None."""
        assert normalize_response(None, "likert") is None

    def test_normalize_non_numeric_value(self):
        """Non-numeric string returns None."""
        assert normalize_response("not a number", "likert") is None

    def test_normalize_open_ended_returns_none(self):
        """Non-scorable question types return None."""
        assert normalize_response(5, "open_ended") is None
        assert normalize_response(5, "writing_sample") is None


# ---------- cronbachs_alpha ----------


class TestCronbachsAlpha:
    """Tests for cronbachs_alpha."""

    def test_perfect_consistency(self):
        """Identical items across respondents should yield alpha = 1.0 (or very high).

        Using multiple respondents with perfectly correlated items.
        """
        # 5 items, 10 respondents — all items identical per respondent
        np.random.seed(42)
        base = np.random.randint(1, 8, size=10).tolist()
        item_scores = [base[:] for _ in range(5)]
        alpha = cronbachs_alpha(item_scores)
        assert alpha is not None
        assert alpha == pytest.approx(1.0, abs=0.01)

    def test_random_items_low_alpha(self):
        """Truly random (uncorrelated) items should produce low alpha."""
        np.random.seed(99)
        # 6 items, 30 respondents — independent random
        item_scores = [np.random.uniform(0, 100, size=30).tolist() for _ in range(6)]
        alpha = cronbachs_alpha(item_scores)
        assert alpha is not None
        assert alpha < 0.3

    def test_few_items(self):
        """Alpha should still compute with only 2 items."""
        # 2 correlated items, 20 respondents
        np.random.seed(7)
        base = np.random.uniform(0, 100, size=20)
        item_a = base.tolist()
        item_b = (base + np.random.normal(0, 5, size=20)).tolist()
        alpha = cronbachs_alpha([item_a, item_b])
        assert alpha is not None
        # With high correlation, should be positive
        assert alpha > 0.5

    def test_single_item_returns_none(self):
        """A single item cannot produce a meaningful alpha."""
        alpha = cronbachs_alpha([[50.0, 60.0, 70.0]])
        assert alpha is None

    def test_empty_returns_none(self):
        """No items returns None."""
        alpha = cronbachs_alpha([])
        assert alpha is None

    def test_single_observation_returns_none(self):
        """Single-session scoring (n=1) returns None -- alpha is not meaningful."""
        # 4 items, each with 1 observation -- cannot compute reliability
        item_scores = [[30.0], [50.0], [70.0], [90.0]]
        alpha = cronbachs_alpha(item_scores)
        assert alpha is None


# ---------- score_self_report ----------


class TestScoreSelfReport:
    """Tests for score_self_report integration."""

    def test_basic_scoring(self, mock_responses, mock_dimension_mapping, mock_scoring_weights):
        """Score self report returns expected structure with dimension scores."""
        result = score_self_report(
            mock_responses,
            mock_dimension_mapping,
            mock_scoring_weights,
        )
        assert "dimensions" in result
        assert "gap_dimensions" in result

        # Formality dimension should have a score
        formality = result["dimensions"].get("formality")
        assert formality is not None
        assert formality["score"] is not None
        assert formality["item_count"] == 5
        # 5 items with values 5,6,4,5,5 -> normalized: 66.67,83.33,50.0,66.67,66.67
        # Mean ~66.67
        assert formality["score"] == pytest.approx(66.67, abs=1.0)

    def test_sd_cross_validation(self, mock_responses, mock_dimension_mapping, mock_scoring_weights):
        """When sd_scores are provided, final score blends 0.7*SR + 0.3*SD."""
        sd_scores = {"formality": 80.0}
        result = score_self_report(
            mock_responses,
            mock_dimension_mapping,
            mock_scoring_weights,
            sd_scores=sd_scores,
        )
        formality = result["dimensions"]["formality"]
        assert formality["sd_cross_validated"] is True
        # raw_weighted_mean ~66.67, final = 0.7*66.67 + 0.3*80 = 46.67 + 24 = 70.67
        assert formality["score"] == pytest.approx(70.67, abs=1.0)

    def test_missing_responses(self, mock_dimension_mapping, mock_scoring_weights):
        """Empty responses should yield None scores."""
        result = score_self_report([], mock_dimension_mapping, mock_scoring_weights)
        for dim_data in result["dimensions"].values():
            assert dim_data["score"] is None
            assert dim_data["item_count"] == 0
