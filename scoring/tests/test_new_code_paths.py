"""Tests for new code paths added in the scoring pipeline fix.

Covers: envelope unwrapping, scoring_map resolution, scale range detection,
question type inference from question bank, and end-to-end categorical scoring.
"""

from __future__ import annotations

import pytest

from mivoca_scoring.self_report import (
    _build_response_lookup,
    _infer_question_type,
    _resolve_scoring_map_value,
    _scoring_map_range,
    score_self_report,
)


# ---------- _build_response_lookup ----------


class TestBuildResponseLookup:
    """Tests for response envelope unwrapping."""

    def test_schema_compliant_format(self):
        """Top-level value/scale_value fields pass through unchanged."""
        responses = [
            {"question_id": "Q01", "scale_value": 5, "value": 5},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["scale_value"] == 5
        assert lookup["Q01"]["value"] == 5

    def test_nested_answer_envelope(self):
        """Nested answer.value is promoted to top-level value."""
        responses = [
            {"question_id": "Q01", "answer": {"value": 3, "raw": "3"}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["value"] == 3
        assert lookup["Q01"]["raw"] == "3"

    def test_top_level_takes_precedence(self):
        """Existing top-level keys are not overwritten by answer keys."""
        responses = [
            {"question_id": "Q01", "value": 5, "answer": {"value": 3, "raw": "3"}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["value"] == 5

    def test_none_top_level_overwritten(self):
        """Top-level None values are overwritten by answer keys."""
        responses = [
            {"question_id": "Q01", "value": None, "answer": {"value": 3}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["value"] == 3

    def test_no_answer_key(self):
        """Responses without answer key pass through as-is."""
        responses = [
            {"question_id": "Q01", "value": 4},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["value"] == 4

    def test_promotes_scale_value_from_envelope(self):
        """scale_value in answer envelope is promoted to top level."""
        responses = [
            {"question_id": "Q01", "answer": {"scale_value": 5, "value": 5}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["scale_value"] == 5

    def test_missing_question_id_skipped(self):
        """Responses without question_id are not included."""
        responses = [
            {"value": 3},
            {"question_id": "Q01", "value": 5},
        ]
        lookup = _build_response_lookup(responses)
        assert len(lookup) == 1
        assert "Q01" in lookup


# ---------- _infer_question_type ----------


class TestInferQuestionType:
    """Tests for question type inference."""

    def test_from_question_def(self):
        """Question bank type takes precedence over response fields."""
        resp = {"scale_value": 5}
        qdef = {"type": "forced_choice"}
        assert _infer_question_type(resp, question_def=qdef) == "forced_choice"

    def test_fallback_scale_value(self):
        """scale_value field infers likert."""
        resp = {"scale_value": 3}
        assert _infer_question_type(resp) == "likert"

    def test_fallback_numeric_value(self):
        """Numeric value field infers likert."""
        resp = {"value": 4}
        assert _infer_question_type(resp) == "likert"

    def test_fallback_string_value(self):
        """Non-numeric value field returns unknown."""
        resp = {"value": "technical"}
        assert _infer_question_type(resp) == "unknown"

    def test_qdef_none_falls_through(self):
        """None question_def falls through to response inference."""
        resp = {"semantic_differential_value": 5}
        assert _infer_question_type(resp, question_def=None) == "semantic_differential"


# ---------- _resolve_scoring_map_value ----------


class TestResolveScoringMapValue:
    """Tests for categorical-to-numeric score resolution."""

    def test_exact_dimension_match(self):
        """Exact dimension key in scoring_map entry returns the value."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "keep": {"formality": 5, "tone_warmth": 2},
                }
            }
        }
        result = _resolve_scoring_map_value("keep", qdef, "formality")
        assert result == 5.0

    def test_prefix_match(self):
        """Dimension 'formality' matches key 'formality_baseline'."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "avoid": {"formality_baseline": 5, "conversational_markers": 1},
                }
            }
        }
        result = _resolve_scoring_map_value("avoid", qdef, "formality")
        assert result == 5.0

    def test_reverse_prefix_match(self):
        """Dimension 'formality_baseline' matches key 'formality'."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "keep": {"formality": 4},
                }
            }
        }
        result = _resolve_scoring_map_value("keep", qdef, "formality_baseline")
        assert result == 4.0

    def test_no_match_returns_none(self):
        """Unmatched dimension returns None, not a fabricated average."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "keep": {"unrelated_dim": 5, "another_dim": 3},
                }
            }
        }
        result = _resolve_scoring_map_value("keep", qdef, "formality")
        assert result is None

    def test_no_scoring_map_returns_none(self):
        """Missing scoring_map returns None."""
        qdef = {"scoring": {"dimensions": ["formality"]}}
        result = _resolve_scoring_map_value("keep", qdef, "formality")
        assert result is None

    def test_none_qdef_returns_none(self):
        """None question_def returns None."""
        result = _resolve_scoring_map_value("keep", None, "formality")
        assert result is None

    def test_numeric_key_lookup(self):
        """Numeric scoring_map keys (e.g., '1', '2') are found via str conversion."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "1": {"formality": 1},
                    "5": {"formality": 5},
                }
            }
        }
        result = _resolve_scoring_map_value(1, qdef, "formality")
        assert result == 1.0

    def test_false_prefix_prevented(self):
        """Dimension 'precision' does not match key 'pre' (requires separator)."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "avoid": {"pre": 5},
                }
            }
        }
        result = _resolve_scoring_map_value("avoid", qdef, "precision")
        assert result is None


# ---------- _scoring_map_range ----------


class TestScoringMapRange:
    """Tests for scale range detection from scoring_map entries."""

    def test_normal_range(self):
        """Detects 1-5 range from scoring_map."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "a": {"formality_baseline": 1},
                    "b": {"formality_baseline": 3},
                    "c": {"formality_baseline": 5},
                }
            }
        }
        lo, hi = _scoring_map_range(qdef, "formality")
        assert lo == 1
        assert hi == 5

    def test_single_value_range(self):
        """When all entries have the same score, min equals max."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "a": {"formality_baseline": 3},
                    "b": {"formality_baseline": 3},
                }
            }
        }
        lo, hi = _scoring_map_range(qdef, "formality")
        assert lo == 3
        assert hi == 3

    def test_no_matching_dimension(self):
        """Falls back to (1, 5) when no entries match the dimension."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "a": {"unrelated": 2},
                }
            }
        }
        lo, hi = _scoring_map_range(qdef, "formality")
        assert (lo, hi) == (1, 5)

    def test_none_qdef(self):
        """None question_def returns default (1, 5)."""
        assert _scoring_map_range(None, "formality") == (1, 5)

    def test_empty_scoring_map(self):
        """Empty scoring_map returns default (1, 5)."""
        qdef = {"scoring": {"scoring_map": {}}}
        assert _scoring_map_range(qdef, "formality") == (1, 5)

    def test_rounding_not_truncation(self):
        """Fractional values are rounded, not truncated."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "a": {"formality_baseline": 1.6},
                    "b": {"formality_baseline": 4.5},
                }
            }
        }
        lo, hi = _scoring_map_range(qdef, "formality")
        assert lo == 2  # round(1.6) = 2, not int(1.6) = 1
        assert hi == 4  # round(4.5) = 4 (banker's rounding)


# ---------- End-to-end: score_self_report with question_bank ----------


class TestScoreSelfReportWithQuestionBank:
    """Integration tests for scoring with question bank and categorical values."""

    def test_categorical_responses_scored(self):
        """Categorical string values are resolved via scoring_map."""
        responses = [
            {"question_id": "Q01", "answer": {"value": "avoid", "raw": "3"}},
            {"question_id": "Q02", "answer": {"value": "keep", "raw": "2"}},
        ]
        question_bank = {
            "Q01": {
                "type": "forced_choice",
                "options": [
                    {"value": "always_use", "label": "Always"},
                    {"value": "selective", "label": "Selective"},
                    {"value": "avoid", "label": "Avoid"},
                ],
                "scoring": {
                    "scoring_map": {
                        "always_use": {"formality_baseline": 1},
                        "selective": {"formality_baseline": 3},
                        "avoid": {"formality_baseline": 5},
                    }
                },
            },
            "Q02": {
                "type": "scenario",
                "options": [
                    {"value": "loosen", "label": "Loosen"},
                    {"value": "keep", "label": "Keep"},
                    {"value": "split", "label": "Split"},
                ],
                "scoring": {
                    "scoring_map": {
                        "loosen": {"formality_baseline": 2},
                        "keep": {"formality_baseline": 5},
                        "split": {"formality_baseline": 3},
                    }
                },
            },
        }
        dimension_mapping = {"formality": ["Q01", "Q02"]}
        scoring_weights = {"formality": {"Q01": 1.0, "Q02": 1.0}}

        result = score_self_report(
            responses,
            dimension_mapping,
            scoring_weights,
            question_bank=question_bank,
        )

        formality = result["dimensions"]["formality"]
        assert formality["item_count"] == 2
        assert formality["skipped_items"] == 0
        assert formality["score"] is not None
        # Both resolve to 5 on a 1-5 scale -> normalized to 100.0 each -> mean 100.0
        assert formality["score"] == pytest.approx(100.0, abs=0.1)

    def test_mixed_numeric_and_categorical(self):
        """Mix of numeric Likert and categorical forced_choice scores correctly."""
        responses = [
            {"question_id": "Q01", "scale_value": 3},  # schema format, numeric
            {"question_id": "Q02", "answer": {"value": "avoid", "raw": "avoid"}},  # conductor format, categorical
        ]
        question_bank = {
            "Q01": {
                "type": "likert",
                "options": [
                    {"value": 1, "label": "Low"},
                    {"value": 2, "label": "Mid-low"},
                    {"value": 3, "label": "Mid"},
                    {"value": 4, "label": "Mid-high"},
                    {"value": 5, "label": "High"},
                ],
            },
            "Q02": {
                "type": "forced_choice",
                "options": [
                    {"value": "use", "label": "Use"},
                    {"value": "selective", "label": "Selective"},
                    {"value": "avoid", "label": "Avoid"},
                ],
                "scoring": {
                    "scoring_map": {
                        "use": {"formality_baseline": 1},
                        "selective": {"formality_baseline": 3},
                        "avoid": {"formality_baseline": 5},
                    }
                },
            },
        }
        dimension_mapping = {"formality": ["Q01", "Q02"]}
        scoring_weights = {"formality": {"Q01": 1.0, "Q02": 1.0}}

        result = score_self_report(
            responses,
            dimension_mapping,
            scoring_weights,
            question_bank=question_bank,
        )

        formality = result["dimensions"]["formality"]
        assert formality["item_count"] == 2
        # Q01: 3 on 1-5 scale = 50.0. Q02: 5 on 1-5 scale = 100.0. Mean = 75.0
        assert formality["score"] == pytest.approx(75.0, abs=0.1)

    def test_unresolvable_categorical_skipped(self):
        """Categorical value without scoring_map is skipped and counted."""
        responses = [
            {"question_id": "Q01", "answer": {"value": "unknown_option"}},
        ]
        question_bank = {
            "Q01": {
                "type": "select",
                "scoring": {},  # no scoring_map
            },
        }
        dimension_mapping = {"formality": ["Q01"]}
        scoring_weights = {"formality": {"Q01": 1.0}}

        result = score_self_report(
            responses,
            dimension_mapping,
            scoring_weights,
            question_bank=question_bank,
        )

        formality = result["dimensions"]["formality"]
        assert formality["item_count"] == 0
        assert formality["skipped_items"] == 1
        assert formality["score"] is None

    def test_skipped_items_counted(self):
        """Items with no response and unresolvable items both count as skipped."""
        responses = [
            {"question_id": "Q02", "answer": {"value": "unresolvable"}},
        ]
        question_bank = {
            "Q02": {"type": "forced_choice", "scoring": {}},
        }
        dimension_mapping = {"formality": ["Q01", "Q02", "Q03"]}
        scoring_weights = {}

        result = score_self_report(
            responses,
            dimension_mapping,
            scoring_weights,
            question_bank=question_bank,
        )

        formality = result["dimensions"]["formality"]
        assert formality["skipped_items"] == 3  # Q01 missing, Q02 unresolvable, Q03 missing
        assert formality["item_count"] == 0
