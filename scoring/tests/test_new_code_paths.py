"""Tests for new code paths added in the scoring pipeline fix.

Covers: envelope unwrapping, scoring_map resolution, scale range detection,
question type inference from question bank, and end-to-end categorical scoring.
"""

from __future__ import annotations

import pytest

import json
from pathlib import Path

from voice_scoring.cli import _flatten_dimension_mapping, _flatten_scoring_weights, _load_question_bank
from voice_scoring.profile_builder import assemble_voice_profile, compute_voice_stability
from voice_scoring.self_report import (
    _build_response_lookup,
    _infer_question_type,
    _resolve_scoring_map_value,
    _scoring_map_range,
    normalize_response,
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

    def test_promotes_selected_options_from_envelope(self):
        """selected_options in answer envelope is promoted to top level."""
        responses = [
            {"question_id": "Q01", "answer": {"selected_options": ["a", "b"], "value": "a,b"}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["selected_options"] == ["a", "b"]

    def test_promotes_raw_text_from_envelope(self):
        """raw_text in answer envelope is promoted to top level."""
        responses = [
            {"question_id": "Q01", "answer": {"raw_text": "some free text", "value": "some free text"}},
        ]
        lookup = _build_response_lookup(responses)
        assert lookup["Q01"]["raw_text"] == "some free text"

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

    def test_fractional_values_use_enclosing_range(self):
        """Fractional values use floor/ceil to produce enclosing bounds."""
        qdef = {
            "scoring": {
                "scoring_map": {
                    "a": {"formality_baseline": 1.6},
                    "b": {"formality_baseline": 4.5},
                }
            }
        }
        lo, hi = _scoring_map_range(qdef, "formality")
        assert lo == 1  # floor(1.6) = 1
        assert hi == 5  # ceil(4.5) = 5


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


# ---------- _load_question_bank ----------


class TestLoadQuestionBank:
    """Tests for question bank module loading from filesystem."""

    def test_loads_modules_from_directory(self, tmp_path):
        """Loads question definitions from M*.json files in modules/ subdir."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        module_data = [
            {"question_id": "M01-Q01", "type": "likert", "text": "Test question"},
            {"question_id": "M01-Q02", "type": "forced_choice", "text": "Another"},
        ]
        (modules_dir / "M01-test.json").write_text(json.dumps(module_data))

        lookup = _load_question_bank([tmp_path])
        assert "M01-Q01" in lookup
        assert "M01-Q02" in lookup
        assert lookup["M01-Q01"]["type"] == "likert"

    def test_first_writer_wins(self, tmp_path):
        """Higher-priority candidate directory wins on duplicate question_ids."""
        high_priority = tmp_path / "high"
        low_priority = tmp_path / "low"
        for d in (high_priority, low_priority):
            modules = d / "modules"
            modules.mkdir(parents=True)

        high_data = [{"question_id": "Q01", "type": "likert", "source": "high"}]
        low_data = [{"question_id": "Q01", "type": "forced_choice", "source": "low"}]
        (high_priority / "modules" / "M01.json").write_text(json.dumps(high_data))
        (low_priority / "modules" / "M01.json").write_text(json.dumps(low_data))

        lookup = _load_question_bank([high_priority, low_priority])
        assert lookup["Q01"]["source"] == "high"

    def test_skips_invalid_json(self, tmp_path):
        """Malformed JSON files are skipped without crashing."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        (modules_dir / "M01-bad.json").write_text("not valid json{{{")
        good_data = [{"question_id": "Q01", "type": "likert"}]
        (modules_dir / "M02-good.json").write_text(json.dumps(good_data))

        lookup = _load_question_bank([tmp_path])
        assert "Q01" in lookup

    def test_empty_candidates(self):
        """Empty candidate list returns empty lookup."""
        lookup = _load_question_bank([])
        assert lookup == {}

    def test_nonexistent_directory(self, tmp_path):
        """Non-existent directory is handled gracefully."""
        fake = tmp_path / "does_not_exist"
        lookup = _load_question_bank([fake])
        assert lookup == {}


# ---------- Gap dimension routing ----------


class TestGapDimensionRouting:
    """Tests that gap dimensions route to results['gap_dimensions']."""

    def test_gap_dimension_routed_correctly(self):
        """Dimensions in GAP_DIMENSIONS list appear in gap_dimensions, not dimensions."""
        responses = [
            {"question_id": "Q01", "scale_value": 3},
        ]
        dimension_mapping = {"precision": ["Q01"]}
        scoring_weights = {"precision": {"Q01": 1.0}}

        result = score_self_report(responses, dimension_mapping, scoring_weights)

        assert "precision" in result["gap_dimensions"]
        assert "precision" not in result["dimensions"]
        assert result["gap_dimensions"]["precision"]["score"] is not None

    def test_gold_dimension_not_in_gap(self):
        """Gold standard dimensions appear in dimensions, not gap_dimensions."""
        responses = [
            {"question_id": "Q01", "scale_value": 5},
        ]
        dimension_mapping = {"formality": ["Q01"]}
        scoring_weights = {"formality": {"Q01": 1.0}}

        result = score_self_report(responses, dimension_mapping, scoring_weights)

        assert "formality" in result["dimensions"]
        assert "formality" not in result["gap_dimensions"]

    def test_multiple_gap_dimensions(self):
        """Multiple gap dimensions all route correctly."""
        responses = [
            {"question_id": "Q01", "scale_value": 4},
            {"question_id": "Q02", "scale_value": 2},
        ]
        dimension_mapping = {
            "precision": ["Q01"],
            "risk_tolerance": ["Q02"],
        }
        scoring_weights = {}

        result = score_self_report(responses, dimension_mapping, scoring_weights)

        assert "precision" in result["gap_dimensions"]
        assert "risk_tolerance" in result["gap_dimensions"]
        assert result["gap_dimensions"]["precision"]["score"] is not None
        assert result["gap_dimensions"]["risk_tolerance"]["score"] is not None


# ---------- _flatten_dimension_mapping and _flatten_scoring_weights ----------


class TestFlattenDimensionMapping:
    """Tests for dimension mapping flattening."""

    def test_flattens_gold_and_gap(self):
        """Extracts question IDs from both gold_standard and gap sections."""
        raw = {
            "gold_standard_dimensions": {
                "formality": {
                    "contributing_items": {
                        "M03": ["M03-Q01", "M03-Q02"],
                        "SD": ["formal_casual"],
                    }
                }
            },
            "gap_dimensions": {
                "precision": {
                    "contributing_items": {
                        "M09": ["M09-Q01", "M09-Q03"],
                    }
                }
            },
        }
        flat = _flatten_dimension_mapping(raw)
        assert flat["formality"] == ["M03-Q01", "M03-Q02", "formal_casual"]
        assert flat["precision"] == ["M09-Q01", "M09-Q03"]

    def test_empty_mapping(self):
        """Empty input returns empty dict."""
        assert _flatten_dimension_mapping({}) == {}

    def test_skips_non_list_items(self):
        """Non-list contributing_items values are skipped."""
        raw = {
            "gold_standard_dimensions": {
                "formality": {
                    "contributing_items": {
                        "M03": "not_a_list",
                    }
                }
            }
        }
        flat = _flatten_dimension_mapping(raw)
        assert flat["formality"] == []


class TestFlattenScoringWeights:
    """Tests for scoring weights flattening."""

    def test_flattens_weights(self):
        """Extracts per-item weights from nested structure."""
        raw = {
            "dimension_weights": {
                "formality": {
                    "items": {"M03-Q01": 1.0, "M03-Q02": 0.8},
                    "sd_pairs": {"formal_casual": 1.0},
                }
            }
        }
        flat = _flatten_scoring_weights(raw)
        assert flat["formality"] == {"M03-Q01": 1.0, "M03-Q02": 0.8}

    def test_empty_weights(self):
        """Empty input returns empty dict."""
        assert _flatten_scoring_weights({}) == {}

    def test_missing_items_key(self):
        """Dimension without items key returns empty dict for that dimension."""
        raw = {
            "dimension_weights": {
                "formality": {"sd_pairs": {"formal_casual": 1.0}}
            }
        }
        flat = _flatten_scoring_weights(raw)
        assert flat["formality"] == {}


# ---------- normalize_response for calibration/projective types ----------


class TestNormalizeCalibrationProjective:
    """Tests for calibration and projective type normalization."""

    def test_calibration_type_normalizes(self):
        """Calibration type normalizes as forced_choice."""
        result = normalize_response(3, "calibration", n_options=7)
        assert result is not None
        assert result == pytest.approx(33.33, abs=0.1)

    def test_projective_type_normalizes(self):
        """Projective type normalizes as forced_choice."""
        result = normalize_response(2, "projective", n_options=5)
        assert result is not None
        assert result == pytest.approx(25.0, abs=0.1)

    def test_calibration_extremes(self):
        """Calibration type at endpoints: 1/7 -> 0.0, 7/7 -> 100.0."""
        low = normalize_response(1, "calibration", n_options=7)
        high = normalize_response(7, "calibration", n_options=7)
        assert low == pytest.approx(0.0)
        assert high == pytest.approx(100.0)


# ---------- assemble_voice_profile ----------


class TestAssembleVoiceProfile:
    """Tests for the profile assembly function."""

    def _make_result(self, **overrides):
        """Build a minimal build_result dict with overrides."""
        base = {
            "merged_dimensions": {},
            "gap_dimensions": {},
            "distinctive_features": [],
            "voice_stability": {},
        }
        base.update(overrides)
        return base

    def _assemble(self, build_result):
        """Call assemble_voice_profile with required args."""
        return assemble_voice_profile(
            build_result,
            session_id="test-session",
            writer_type="personal_journalistic",
            identity_summary="Test voice.",
        )

    def test_gold_dimensions_use_correct_keys(self):
        """Gold standard dimensions extract merged_score, self_report_score, observed_score."""
        build_result = self._make_result(
            merged_dimensions={
                "formality": {
                    "merged_score": 65.0,
                    "self_report_score": 60.0,
                    "observed_score": 75.0,
                    "tier": 1,
                    "weight_sr": 0.7,
                    "weight_obs": 0.3,
                }
            },
        )
        result = self._assemble(build_result)
        gold = result["gold_standard_dimensions"]
        assert "formality" in gold
        assert gold["formality"]["score"] == 65.0
        assert gold["formality"]["self_report"] == 60.0
        assert gold["formality"]["observed"] == 75.0
        assert gold["formality"]["tier"] == 1

    def test_stability_map_classifies_dimensions(self):
        """Voice stability map correctly classifies dimensions."""
        build_result = self._make_result(
            voice_stability={
                "formality": {
                    "classification": "stable_across_contexts",
                    "module_count": 2,
                    "variance": 5.0,
                },
                "authority": {
                    "classification": "adapts_by_context",
                    "module_count": 3,
                    "variance": 250.0,
                },
            },
        )
        result = self._assemble(build_result)
        vsm = result["voice_stability_map"]
        assert "formality" in vsm["stable_across_contexts"]
        assert "authority" in vsm["adapts_by_context"]
        assert "formality" not in vsm["adapts_by_context"]
        assert vsm["per_dimension"]["formality"]["classification"] == "stable_across_contexts"

    def test_distinctive_features_to_strings(self):
        """Distinctive features convert dict entries to description strings."""
        build_result = self._make_result(
            distinctive_features=[
                {"description": "High vocabulary richness"},
                {"metric": "hedge_density", "value": 2.1, "z_score": -2.5},
            ],
        )
        result = self._assemble(build_result)
        feats = result["distinctive_features"]
        assert feats[0] == "High vocabulary richness"
        assert "hedge_density" in feats[1]


# ---------- compute_voice_stability ----------


class TestComputeVoiceStabilityWithEnvelope:
    """Tests for voice stability with answer envelope format."""

    def test_envelope_responses_processed(self):
        """Responses in answer envelope format are unwrapped for stability computation."""
        responses = [
            {"question_id": "M03-Q01", "answer": {"value": 3}},
            {"question_id": "M06-Q01", "answer": {"value": 4}},
        ]
        dimension_mapping = {"formality": ["M03-Q01", "M06-Q01"]}
        result = compute_voice_stability(responses, dimension_mapping)
        # Both items are in different modules (M03, M06) -> 2 modules
        assert "formality" in result
        assert result["formality"]["module_count"] == 2
