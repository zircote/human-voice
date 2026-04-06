"""Tests for voice_scoring.calibration module."""

from __future__ import annotations

import pytest

from voice_scoring.calibration import calibrate


def _make_sr_scores(dim: str, score: float) -> dict:
    """Build a minimal sr_scores dict for a single dimension."""
    return {"dimensions": {dim: {"score": score}}}


def _make_observed(metric_key: str, raw_value: float) -> dict:
    """Build a minimal observed dict."""
    return {metric_key: raw_value}


class TestCalibrateAwareness:
    """Tests for awareness classification thresholds."""

    def test_calibrate_high_awareness(self):
        """|delta| <= 10 should classify as 'high' awareness."""
        # formality: SR=55, observed formality_f_score=0.50 -> normalized 50.0
        # delta = 55 - 50 = 5, |delta| = 5 <= 10 -> "high"
        sr = _make_sr_scores("formality", 55.0)
        obs = _make_observed("formality_f_score", 50.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["awareness"] == "high"
        assert abs(dim["delta"]) <= 10.0

    def test_calibrate_moderate(self):
        """|delta| 11-25 should classify as 'moderate' awareness."""
        # formality: SR=70, observed formality_f_score=0.50 -> normalized 50.0
        # delta = 70 - 50 = 20, |delta| = 20, 10 < 20 <= 25 -> "moderate"
        sr = _make_sr_scores("formality", 70.0)
        obs = _make_observed("formality_f_score", 50.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["awareness"] == "moderate"
        assert 10 < abs(dim["delta"]) <= 25

    def test_calibrate_blind_spot(self):
        """|delta| > 25 should classify as 'blind_spot'."""
        # formality: SR=90, observed formality_f_score=0.30 -> normalized 30.0
        # delta = 90 - 30 = 60, |delta| = 60 > 25 -> "blind_spot"
        sr = _make_sr_scores("formality", 90.0)
        obs = _make_observed("formality_f_score", 30.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["awareness"] == "blind_spot"
        assert abs(dim["delta"]) > 25


class TestCalibrateDirection:
    """Tests for overestimate / underestimate direction."""

    def test_calibrate_overestimates(self):
        """self_report > observed by more than threshold -> 'overestimate'."""
        # SR=80, observed formality_f_score=0.40 -> normalized 40.0
        # delta = 80 - 40 = 40 > 10 -> direction = "overestimate"
        sr = _make_sr_scores("formality", 80.0)
        obs = _make_observed("formality_f_score", 40.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["direction"] == "overestimate"
        assert dim["delta"] > 0

    def test_calibrate_underestimates(self):
        """observed > self_report by more than threshold -> 'underestimate'."""
        # SR=20, observed formality_f_score=0.80 -> normalized 80.0
        # delta = 20 - 80 = -60 < -10 -> direction = "underestimate"
        sr = _make_sr_scores("formality", 20.0)
        obs = _make_observed("formality_f_score", 80.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["direction"] == "underestimate"
        assert dim["delta"] < 0


class TestCalibrateEdgeCases:
    """Edge cases for calibrate."""

    def test_missing_observed(self):
        """Missing observed value yields None awareness."""
        sr = _make_sr_scores("formality", 50.0)
        result = calibrate(sr, {})
        dim = result["dimensions"]["formality"]
        assert dim["awareness"] is None
        assert dim["delta"] is None

    def test_missing_sr_score(self):
        """Missing SR score yields None awareness."""
        sr = {"dimensions": {"formality": {"score": None}}}
        obs = _make_observed("formality_f_score", 50.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["formality"]
        assert dim["awareness"] is None

    def test_overall_self_awareness(self):
        """Overall awareness is the mean of per-dimension awareness scores."""
        sr = {
            "dimensions": {
                "formality": {"score": 55.0},       # delta ~5 -> high (100)
                "complexity": {"score": 70.0},       # flesch 10.0 -> norm 50.0, delta 20 -> moderate (60)
            }
        }
        obs = {"formality_f_score": 50.0, "flesch_kincaid_grade": 10.0}
        result = calibrate(sr, obs)
        # high=100, moderate=60 -> mean=80
        assert result["overall_self_awareness"] == pytest.approx(80.0, abs=0.1)

    def test_inverted_metric(self):
        """Narrativity uses inverted liwc_analytical metric."""
        # SR=70, observed liwc_analytical=80 -> normalized 80, inverted -> 20
        # delta = 70 - 20 = 50 > 25 -> blind_spot, overestimate
        sr = _make_sr_scores("narrativity", 70.0)
        obs = _make_observed("liwc_analytical", 80.0)
        result = calibrate(sr, obs)
        dim = result["dimensions"]["narrativity"]
        assert dim["awareness"] == "blind_spot"
        assert dim["direction"] == "overestimate"
