"""Tests for the composite analysis stage."""

from __future__ import annotations

import spacy
from spacy.tokens import Doc

from mivoca_nlp.stages.composite import analyze_composite
from mivoca_nlp.pipeline import run_pipeline


class TestFormalityFScore:
    def test_formality_f_score_range(
        self, business_doc: Doc, business_text: str
    ) -> None:
        result = analyze_composite(business_doc, business_text)
        f_score = result["formality_f_score"]
        assert 0 <= f_score <= 100, (
            f"Formality F-score {f_score} should be in [0, 100]"
        )


class TestFleschKincaid:
    def test_flesch_kincaid_positive(
        self, business_doc: Doc, business_text: str
    ) -> None:
        result = analyze_composite(business_doc, business_text)
        assert result["flesch_kincaid_grade"] > 0, (
            f"Flesch-Kincaid grade {result['flesch_kincaid_grade']} should be positive"
        )


class TestGunningFog:
    def test_gunning_fog_positive(
        self, business_doc: Doc, business_text: str
    ) -> None:
        result = analyze_composite(business_doc, business_text)
        assert result["gunning_fog_index"] > 0, (
            f"Gunning Fog index {result['gunning_fog_index']} should be positive"
        )


class TestLIWCAnalytical:
    def test_liwc_analytical_range(
        self, business_doc: Doc, business_text: str
    ) -> None:
        result = analyze_composite(business_doc, business_text)
        at = result["analytical_thinking"]
        assert 0 <= at <= 100, (
            f"Analytical thinking {at} should be in [0, 100]"
        )


class TestFormalityComparisons:
    def test_academic_higher_formality(
        self,
        nlp_model: spacy.language.Language,
        academic_text: str,
        creative_text: str,
    ) -> None:
        acad = run_pipeline(nlp_model, academic_text)
        cre = run_pipeline(nlp_model, creative_text)
        assert acad["composite"]["formality_f_score"] > cre["composite"]["formality_f_score"], (
            f"Academic formality ({acad['composite']['formality_f_score']}) "
            f"should exceed creative ({cre['composite']['formality_f_score']})"
        )

    def test_business_moderate_formality(
        self,
        nlp_model: spacy.language.Language,
        business_text: str,
        academic_text: str,
        creative_text: str,
    ) -> None:
        biz = run_pipeline(nlp_model, business_text)
        acad = run_pipeline(nlp_model, academic_text)
        cre = run_pipeline(nlp_model, creative_text)

        biz_f = biz["composite"]["formality_f_score"]
        acad_f = acad["composite"]["formality_f_score"]
        cre_f = cre["composite"]["formality_f_score"]

        assert cre_f < biz_f <= acad_f, (
            f"Expected creative ({cre_f}) < business ({biz_f}) <= academic ({acad_f})"
        )
