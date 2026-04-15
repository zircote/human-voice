"""Tests for the lexical analysis stage."""

from __future__ import annotations

from spacy.tokens import Doc

from voice_nlp.stages.lexical import analyze_lexical


class TestMTLD:
    def test_mtld_positive(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_lexical(business_doc, business_text)
        assert result["mtld"] > 0, f"MTLD {result['mtld']} should be positive"


class TestMATTR:
    def test_mattr_range(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_lexical(business_doc, business_text)
        assert 0 < result["mattr"] <= 1, f"MATTR {result['mattr']} should be in (0, 1]"


class TestHapaxRatio:
    def test_hapax_ratio_range(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_lexical(business_doc, business_text)
        assert 0 <= result["hapax_legomena_ratio"] <= 1, (
            f"Hapax ratio {result['hapax_legomena_ratio']} should be in [0, 1]"
        )


class TestWordLength:
    def test_word_length_reasonable(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_lexical(business_doc, business_text)
        avg = result["avg_word_length_chars"]
        assert 3 <= avg <= 10, f"Avg word length {avg} should be between 3 and 10"

    def test_academic_higher_word_length(
        self,
        academic_doc: Doc,
        academic_text: str,
        creative_doc: Doc,
        creative_text: str,
    ) -> None:
        acad = analyze_lexical(academic_doc, academic_text)
        cre = analyze_lexical(creative_doc, creative_text)
        assert acad["avg_word_length_chars"] > cre["avg_word_length_chars"], (
            f"Academic avg word length ({acad['avg_word_length_chars']}) "
            f"should exceed creative ({cre['avg_word_length_chars']})"
        )


class TestVocabularySophistication:
    def test_vocabulary_sophistication_range(
        self, business_doc: Doc, business_text: str
    ) -> None:
        result = analyze_lexical(business_doc, business_text)
        vs = result["vocabulary_sophistication"]
        assert 0 <= vs <= 1, f"Vocabulary sophistication {vs} should be in [0, 1]"
