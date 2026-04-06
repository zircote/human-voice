"""Integration tests for the voice NLP pipeline."""

from __future__ import annotations

import spacy

from voice_nlp.pipeline import run_pipeline


class TestRunPipelineReturnsSections:
    """Verify the pipeline returns all expected top-level keys."""

    def test_run_pipeline_returns_all_sections(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        result = run_pipeline(nlp_model, business_text)

        expected_keys = {
            "text_length_chars",
            "text_length_tokens",
            "sentence_count",
            "lexical",
            "syntactic",
            "pragmatic",
            "discourse",
            "composite",
        }
        assert expected_keys == set(result.keys())

        # Each section should be a dict
        for section in ("lexical", "syntactic", "pragmatic", "discourse", "composite"):
            assert isinstance(result[section], dict), f"{section} should be a dict"


class TestRunPipelineBusiness:
    """Pipeline on business text should produce reasonable metrics."""

    def test_run_pipeline_business(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        result = run_pipeline(nlp_model, business_text)

        # Formality F-score should be > 45 for business writing
        f_score = result["composite"]["formality_f_score"]
        assert f_score > 45, f"Business F-score {f_score} should be > 45"

        # Flesch-Kincaid grade should be positive
        fk = result["composite"]["flesch_kincaid_grade"]
        assert fk > 0, f"Flesch-Kincaid grade {fk} should be positive"


class TestRunPipelineCreative:
    """Pipeline on creative text should show lower formality than business."""

    def test_run_pipeline_creative(
        self, nlp_model: spacy.language.Language, business_text: str, creative_text: str
    ) -> None:
        biz = run_pipeline(nlp_model, business_text)
        cre = run_pipeline(nlp_model, creative_text)

        assert cre["composite"]["formality_f_score"] < biz["composite"]["formality_f_score"], (
            f"Creative formality ({cre['composite']['formality_f_score']}) "
            f"should be lower than business ({biz['composite']['formality_f_score']})"
        )


class TestRunPipelineAcademic:
    """Pipeline on academic text should show higher grade level than creative."""

    def test_run_pipeline_academic(
        self, nlp_model: spacy.language.Language, academic_text: str, creative_text: str
    ) -> None:
        acad = run_pipeline(nlp_model, academic_text)
        cre = run_pipeline(nlp_model, creative_text)

        assert acad["composite"]["flesch_kincaid_grade"] > cre["composite"]["flesch_kincaid_grade"], (
            f"Academic FK grade ({acad['composite']['flesch_kincaid_grade']}) "
            f"should be higher than creative ({cre['composite']['flesch_kincaid_grade']})"
        )
