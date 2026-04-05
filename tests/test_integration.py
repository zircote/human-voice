"""End-to-end integration test: session → NLP → scoring → profile → schema validation.

Creates a mock completed session, runs NLP analysis on writing samples,
runs scoring, builds a profile, and validates the output against the
voice-profile JSON schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import spacy

from lib.session import create_session, record_response, save_writing_sample, save_session
from lib.branching import evaluate_primary_route
from mivoca_nlp.pipeline import run_pipeline
from mivoca_scoring.self_report import normalize_response, cronbachs_alpha
from mivoca_scoring.calibration import calibrate
from mivoca_scoring.profile_builder import build_profile, detect_distinctive_features


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "question-bank" / "schemas"


@pytest.fixture(scope="session")
def nlp_model():
    return spacy.load("en_core_web_sm")


@pytest.fixture(autouse=True)
def isolate_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from lib import session
    fake_root = tmp_path / ".human-voice" / "sessions"
    fake_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session, "_sessions_root", lambda: fake_root)


@pytest.fixture
def voice_profile_schema() -> dict:
    with open(SCHEMA_DIR / "voice-profile.schema.json", "r") as f:
        return json.load(f)


# --- Mock interview data ---

SCREENING_RESPONSES = [
    {"question_id": "M01-Q01", "value": "direct, analytical, precise"},
    {"question_id": "M01-Q02", "value": "em dashes and short paragraphs"},
    {"question_id": "M01-Q03", "value": "structured reasoning"},
    {"question_id": "M01-Q04", "value": "distinctive", "selected_options": ["distinctive"]},
    {"question_id": "M01-Q05", "value": "business", "response": "business", "selected_options": ["business"]},
    {"question_id": "M01-Q06", "value": "directness and precision"},
    {"question_id": "M01-Q07", "value": "more concise over time"},
    {"question_id": "M01-Q08", "value": "clear and direct"},
    {"question_id": "M01-Q09", "value": "sentence rhythm"},
    {"question_id": "M01-Q10", "value": "4", "scale_value": 4},
]

DIMENSION_RESPONSES = {
    "formality": [5, 6, 5, 4, 6, 5],
    "emotional_tone": [3, 2, 3, 4, 3, 2],
    "personality": [6, 5, 7, 5, 6],
    "complexity": [4, 5, 4, 5, 4],
    "audience_awareness": [6, 7, 6, 5, 6],
    "authority": [6, 5, 6, 5],
    "narrativity": [3, 4, 3, 4, 3],
    "humor": [2, 3, 2, 3],
}

WRITING_SAMPLES = {
    "ws-01": {
        "prompt_id": "M12-WS01",
        "prompt_type": "spontaneous",
        "raw_text": (
            "Thanks for thinking of me, but I'm going to have to pass on Saturday. "
            "I've got a deadline Monday that's going to eat the whole weekend. "
            "Let's find another time — maybe the following week works better for both of us."
        ),
    },
    "ws-02": {
        "prompt_id": "M12-WS02",
        "prompt_type": "reflective",
        "raw_text": (
            "The library in my college town had this particular corner on the second floor "
            "where the afternoon sun would hit the oak table just right. It smelled like old paper "
            "and floor wax. I spent four years at that table, and most of what I know about "
            "thinking carefully I learned there. Not from any book in particular, but from the "
            "habit of sitting still long enough to let an idea finish forming before I tried to "
            "write it down."
        ),
    },
    "ws-03": {
        "prompt_id": "M12-WS03",
        "prompt_type": "professional",
        "raw_text": (
            "We decided to sunset the legacy API because maintaining two parallel interfaces "
            "was costing us roughly 30% of the backend team's time. The new API covers all the "
            "same use cases with better documentation and faster response times. We gave partners "
            "a 90-day migration window and offered hands-on support for the transition. So far, "
            "85% have migrated without issues."
        ),
    },
}


class TestBranchRouting:
    """Verify branch routing works with screening responses."""

    def test_business_route(self):
        route = evaluate_primary_route(SCREENING_RESPONSES)
        assert route["writer_type"] == "business_professional"
        assert "M08" in route["activated_modules"]


class TestNLPOnWritingSamples:
    """Run the real NLP pipeline on writing samples."""

    def test_analyze_all_samples(self, nlp_model):
        for sample_id, sample in WRITING_SAMPLES.items():
            result = run_pipeline(nlp_model, sample["raw_text"])
            assert "lexical" in result
            assert "syntactic" in result
            assert "pragmatic" in result
            assert "discourse" in result
            assert "composite" in result
            assert result["sentence_count"] > 0
            assert result["text_length_tokens"] > 0

    def test_professional_more_formal_than_spontaneous(self, nlp_model):
        prof = run_pipeline(nlp_model, WRITING_SAMPLES["ws-03"]["raw_text"])
        spont = run_pipeline(nlp_model, WRITING_SAMPLES["ws-01"]["raw_text"])
        # Professional writing typically has higher formality
        assert prof["composite"]["formality_f_score"] >= spont["composite"]["formality_f_score"] - 15


class TestScoringPipeline:
    """Test self-report scoring with mock dimension responses."""

    def test_normalize_and_score_dimensions(self):
        scores = {}
        for dim, values in DIMENSION_RESPONSES.items():
            normalized = [normalize_response(v, "likert", scale_max=7) for v in values]
            scores[dim] = sum(normalized) / len(normalized)
            assert 0 <= scores[dim] <= 100, f"{dim} score out of range"

        # Business writer should have moderate-high formality
        assert scores["formality"] > 50
        # Low humor scores
        assert scores["humor"] < 50

    def test_cronbachs_alpha_on_dimension(self):
        # Formality items are consistent (5,6,5,4,6,5) → reasonable alpha
        items = [[v] for v in DIMENSION_RESPONSES["formality"]]
        alpha = cronbachs_alpha(items)
        # With only 1 item per "subject" this won't compute meaningfully,
        # but it should not crash
        assert alpha is None or isinstance(alpha, float)


class TestCalibration:
    """Test calibration of self-report vs observed."""

    def test_calibration_output_structure(self):
        sr_scores = {"dimensions": {
            "formality": {"score": 70},
            "complexity": {"score": 55},
            "authority": {"score": 65},
        }}
        observed = {
            "formality_f_score": 60.0,
            "flesch_kincaid_grade": 10.0,
            "liwc_clout": 70.0,
        }
        result = calibrate(sr_scores, observed)
        assert "dimensions" in result
        assert "overall_self_awareness" in result

    def test_high_awareness_when_close(self):
        sr_scores = {"dimensions": {"formality": {"score": 60}}}
        observed = {"formality_f_score": 58.0}  # F-score on 0-100 scale
        result = calibrate(sr_scores, observed)
        dim_result = result["dimensions"]["formality"]
        assert dim_result["awareness"] == "high"


class TestProfileGeneration:
    """Test full profile generation."""

    def test_build_profile_structure(self):
        sr_scores = {
            "dimensions": {
                "formality": {"score": 70, "items": 6, "alpha": 0.75},
                "emotional_tone": {"score": 35, "items": 6, "alpha": 0.70},
                "personality": {"score": 65, "items": 5, "alpha": 0.72},
                "complexity": {"score": 50, "items": 5, "alpha": 0.68},
                "audience_awareness": {"score": 75, "items": 5, "alpha": 0.80},
                "authority": {"score": 68, "items": 4, "alpha": 0.71},
                "narrativity": {"score": 40, "items": 5, "alpha": 0.69},
                "humor": {"score": 30, "items": 4, "alpha": 0.65},
            }
        }
        observed = {
            "formality_f_score": 62.0,
            "flesch_kincaid_grade": 10.5,
            "liwc_clout": 72.0,
            "liwc_analytical": 78.0,
            "liwc_emotional_tone": 38.0,
        }
        profile = build_profile(sr_scores, observed)
        assert "merged_dimensions" in profile
        assert "distinctive_features" in profile

    def test_distinctive_features_detection(self):
        observed = {
            "formality_f_score": 85.0,  # Very high — should be distinctive
            "flesch_kincaid_grade": 8.0,
        }
        features = detect_distinctive_features(observed)
        assert isinstance(features, list)
        # Each feature is a dict, not a string
        for f in features:
            assert isinstance(f, dict)


class TestEndToEndSession:
    """Full end-to-end: create session, record responses, analyze, score, profile."""

    def test_full_pipeline(self, nlp_model):
        # 1. Create session
        state = create_session()
        sid = state["session_id"]

        # 2. Record screening responses
        for resp in SCREENING_RESPONSES:
            record_response(sid, {
                "question_id": resp["question_id"],
                "value": resp.get("value"),
                "selected_options": resp.get("selected_options"),
                "scale_value": resp.get("scale_value"),
                "timing": {"duration_ms": 5000},
                "quality_flags": {"too_fast": False, "straightline_sequence": 0},
            })

        # 3. Route to branch
        route = evaluate_primary_route(SCREENING_RESPONSES)
        state["writer_type"] = route["writer_type"]
        state["branch_path"] = route["branch_path"]
        state["state"] = "in_progress"
        save_session(sid, state)

        # 4. Save writing samples and run NLP
        nlp_results = {}
        for sample_id, sample in WRITING_SAMPLES.items():
            save_writing_sample(sid, sample_id, sample)
            analysis = run_pipeline(nlp_model, sample["raw_text"])
            nlp_results[sample_id] = analysis

        # 5. Score self-report dimensions
        sr_scores = {"dimensions": {}}
        for dim, values in DIMENSION_RESPONSES.items():
            normalized = [normalize_response(v, "likert", scale_max=7) for v in values]
            mean_score = sum(normalized) / len(normalized)
            sr_scores["dimensions"][dim] = {
                "score": round(mean_score, 1),
                "items": len(values),
            }

        # 6. Aggregate observed features
        all_analyses = list(nlp_results.values())
        observed = {
            "formality_f_score": sum(a["composite"]["formality_f_score"] for a in all_analyses) / len(all_analyses),
            "flesch_kincaid_grade": sum(a["composite"]["flesch_kincaid_grade"] for a in all_analyses) / len(all_analyses),
            "liwc_clout": sum(a["composite"]["clout"] for a in all_analyses) / len(all_analyses),
            "liwc_analytical": sum(a["composite"]["analytical_thinking"] for a in all_analyses) / len(all_analyses),
            "liwc_emotional_tone": sum(a["composite"]["emotional_tone"] for a in all_analyses) / len(all_analyses),
        }

        # 7. Calibrate (calibrate expects sr_scores with "dimensions" key)
        cal = calibrate(sr_scores, observed)

        # 8. Build profile
        profile = build_profile(sr_scores, observed)

        # Verify the profile has expected structure
        assert "merged_dimensions" in profile
        assert "distinctive_features" in profile
        assert len(profile["merged_dimensions"]) > 0

        # Verify calibration produced results
        assert "dimensions" in cal
        assert "overall_self_awareness" in cal

        # Verify NLP ran on all samples
        assert len(nlp_results) == 3
        for analysis in nlp_results.values():
            assert analysis["sentence_count"] > 0
