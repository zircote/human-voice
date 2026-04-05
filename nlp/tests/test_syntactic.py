"""Tests for the syntactic analysis stage."""

from __future__ import annotations

import spacy
from spacy.tokens import Doc

from mivoca_nlp.stages.tokenizer import tokenize
from mivoca_nlp.stages.syntactic import analyze_syntactic


class TestMeanSentenceLength:
    def test_mean_sentence_length_positive(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        doc, sentences = tokenize(nlp_model, business_text)
        result = analyze_syntactic(doc, sentences)
        assert result["mean_sentence_length"] > 0, (
            f"Mean sentence length {result['mean_sentence_length']} should be positive"
        )


class TestSentenceLengthSD:
    def test_sentence_length_sd_nonnegative(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        doc, sentences = tokenize(nlp_model, business_text)
        result = analyze_syntactic(doc, sentences)
        assert result["sentence_length_sd"] >= 0, (
            f"Sentence length SD {result['sentence_length_sd']} should be >= 0"
        )


class TestClausesPerSentence:
    def test_clauses_per_sentence(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        doc, sentences = tokenize(nlp_model, business_text)
        result = analyze_syntactic(doc, sentences)
        assert result["clauses_per_sentence"] >= 1.0, (
            f"Clauses per sentence {result['clauses_per_sentence']} should be >= 1.0"
        )


class TestPassiveVoiceRatio:
    def test_passive_voice_ratio_range(
        self, nlp_model: spacy.language.Language, business_text: str
    ) -> None:
        doc, sentences = tokenize(nlp_model, business_text)
        result = analyze_syntactic(doc, sentences)
        assert 0 <= result["passive_voice_ratio"] <= 1, (
            f"Passive voice ratio {result['passive_voice_ratio']} should be in [0, 1]"
        )


class TestAcademicLongerSentences:
    def test_academic_longer_sentences(
        self,
        nlp_model: spacy.language.Language,
        academic_text: str,
        creative_text: str,
    ) -> None:
        acad_doc, acad_sents = tokenize(nlp_model, academic_text)
        cre_doc, cre_sents = tokenize(nlp_model, creative_text)

        acad_result = analyze_syntactic(acad_doc, acad_sents)
        cre_result = analyze_syntactic(cre_doc, cre_sents)

        assert acad_result["mean_sentence_length"] > cre_result["mean_sentence_length"], (
            f"Academic mean sentence length ({acad_result['mean_sentence_length']}) "
            f"should exceed creative ({cre_result['mean_sentence_length']})"
        )
