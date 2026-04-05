"""Tests for mivoca_scoring.profile_builder module."""

from __future__ import annotations

import pytest

from mivoca_scoring.profile_builder import (
    build_profile,
    compute_voice_stability,
    detect_distinctive_features,
)


# ---------- detect_distinctive_features ----------


class TestDetectDistinctiveFeatures:
    """Tests for detect_distinctive_features."""

    def test_normal_features_not_distinctive(self):
        """Features near population mean should return empty list."""
        observed = {
            "formality_f_score": 55.0,     # mean=55.0, sd=10.0 -> z=0.0
            "flesch_kincaid_grade": 10.0,   # mean=10.0, sd=3.0 -> z=0.0
            "type_token_ratio": 0.65,       # mean=0.65, sd=0.10 -> z=0.0
        }
        result = detect_distinctive_features(observed)
        assert result == []

    def test_outlier_detected(self):
        """Features > 1.5 SD from population mean should be detected."""
        observed = {
            "formality_f_score": 80.0,     # mean=55.0, sd=10.0 -> z=2.5 (above)
            "flesch_kincaid_grade": 2.0,    # mean=10.0, sd=3.0 -> z=-2.67 (below)
        }
        result = detect_distinctive_features(observed)
        assert len(result) == 2

        metrics = {d["metric"] for d in result}
        assert "formality_f_score" in metrics
        assert "flesch_kincaid_grade" in metrics

        for d in result:
            assert abs(d["z_score"]) >= 1.5
            assert d["direction"] in ("above", "below")

    def test_custom_population_means(self):
        """Custom population means override defaults."""
        observed = {"formality_f_score": 55.0}
        # With default pop mean=55.0, this is z=0 -> not distinctive
        result_default = detect_distinctive_features(observed)
        assert len(result_default) == 0

        # With custom pop mean=20.0, sd=10.0 -> z=3.5 -> distinctive
        custom_pop = {"formality_f_score": {"mean": 20.0, "sd": 10.0}}
        result_custom = detect_distinctive_features(observed, population_means=custom_pop)
        assert len(result_custom) == 1
        assert result_custom[0]["z_score"] >= 1.5

    def test_custom_population_means_tuple_format(self):
        """Custom population means as [mean, sd] tuples also work."""
        observed = {"formality_f_score": 0.90}
        custom_pop = {"formality_f_score": [0.55, 0.15]}
        result = detect_distinctive_features(observed, population_means=custom_pop)
        assert len(result) == 1

    def test_empty_observed(self):
        """No observed data returns empty list."""
        assert detect_distinctive_features(None) == []
        assert detect_distinctive_features({}) == []

    def test_sorted_by_z_score(self):
        """Results should be sorted by absolute z-score descending."""
        observed = {
            "formality_f_score": 0.90,     # z ~ 2.33
            "flesch_kincaid_grade": 1.0,    # z ~ -3.0
        }
        result = detect_distinctive_features(observed)
        assert len(result) == 2
        assert abs(result[0]["z_score"]) >= abs(result[1]["z_score"])


# ---------- compute_voice_stability ----------


class TestComputeVoiceStability:
    """Tests for compute_voice_stability."""

    def test_consistent_scores_stable(self):
        """Same dimension scores across modules should classify as stable."""
        # Two modules with identical Likert scores for "formality"
        responses = [
            {"question_id": "M01-Q01", "scale_value": 5},
            {"question_id": "M01-Q02", "scale_value": 5},
            {"question_id": "M02-Q01", "scale_value": 5},
            {"question_id": "M02-Q02", "scale_value": 5},
        ]
        dim_mapping = {
            "formality": ["M01-Q01", "M01-Q02", "M02-Q01", "M02-Q02"],
        }
        result = compute_voice_stability(responses, dim_mapping)
        assert "formality" in result
        assert result["formality"]["classification"] == "stable_across_contexts"
        assert result["formality"]["variance"] < 150.0

    def test_variable_scores_adapts(self):
        """Widely varying scores across modules should classify as adapts_by_context."""
        # M01 answers all 1 (norm 0), M02 answers all 7 (norm 100)
        responses = [
            {"question_id": "M01-Q01", "scale_value": 1},
            {"question_id": "M01-Q02", "scale_value": 1},
            {"question_id": "M02-Q01", "scale_value": 7},
            {"question_id": "M02-Q02", "scale_value": 7},
        ]
        dim_mapping = {
            "formality": ["M01-Q01", "M01-Q02", "M02-Q01", "M02-Q02"],
        }
        result = compute_voice_stability(responses, dim_mapping)
        assert "formality" in result
        assert result["formality"]["classification"] == "adapts_by_context"
        assert result["formality"]["variance"] >= 150.0

    def test_single_module_insufficient(self):
        """A single module cannot determine stability."""
        responses = [
            {"question_id": "M01-Q01", "scale_value": 5},
            {"question_id": "M01-Q02", "scale_value": 6},
        ]
        dim_mapping = {"formality": ["M01-Q01", "M01-Q02"]}
        result = compute_voice_stability(responses, dim_mapping)
        assert result["formality"]["classification"] == "insufficient_data"


# ---------- build_profile ----------


class TestBuildProfile:
    """Tests for build_profile integration."""

    def test_basic_profile(self, mock_responses, mock_dimension_mapping, mock_scoring_weights):
        """Build profile returns expected top-level keys."""
        from mivoca_scoring.self_report import score_self_report

        sr_scores = score_self_report(
            mock_responses, mock_dimension_mapping, mock_scoring_weights
        )
        profile = build_profile(sr_scores)
        assert "merged_dimensions" in profile
        assert "gap_dimensions" in profile
        assert "distinctive_features" in profile
        assert "voice_stability" in profile

    def test_profile_with_observed(self, mock_responses, mock_dimension_mapping, mock_scoring_weights):
        """Profile merges SR and observed scores using tier weights."""
        from mivoca_scoring.self_report import score_self_report

        sr_scores = score_self_report(
            mock_responses, mock_dimension_mapping, mock_scoring_weights
        )
        observed = {"formality_f_score": 0.60}
        profile = build_profile(sr_scores, observed=observed)

        formality = profile["merged_dimensions"].get("formality")
        assert formality is not None
        assert formality["merged_score"] is not None
        assert formality["observed_score"] is not None
        # Formality is tier 1 by default: 0.7*SR + 0.3*obs
        assert formality["weight_sr"] == 0.7
        assert formality["weight_obs"] == 0.3

    def test_profile_stability_included(self, mock_responses, mock_dimension_mapping, mock_scoring_weights):
        """Profile includes voice stability when responses and mapping provided."""
        from mivoca_scoring.self_report import score_self_report

        sr_scores = score_self_report(
            mock_responses, mock_dimension_mapping, mock_scoring_weights
        )
        profile = build_profile(
            sr_scores,
            responses=mock_responses,
            dimension_mapping=mock_dimension_mapping,
        )
        # emotional_tone spans M02 and M03, so stability should exist
        assert "emotional_tone" in profile["voice_stability"]
