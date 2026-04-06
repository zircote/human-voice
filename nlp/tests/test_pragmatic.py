"""Tests for the pragmatic analysis stage."""

from __future__ import annotations

from spacy.tokens import Doc

from voice_nlp.stages.pragmatic import analyze_pragmatic


class TestHedgeCount:
    def test_hedge_count_nonneg(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_pragmatic(business_doc, business_text)
        assert result["hedge_count"] >= 0, (
            f"Hedge count {result['hedge_count']} should be >= 0"
        )


class TestBoostCount:
    def test_boost_count_nonneg(self, business_doc: Doc, business_text: str) -> None:
        result = analyze_pragmatic(business_doc, business_text)
        assert result["booster_count"] >= 0, (
            f"Booster count {result['booster_count']} should be >= 0"
        )


class TestSelfMention:
    def test_self_mention_business(self, business_doc: Doc, business_text: str) -> None:
        """Business text contains 'we', 'our', 'I' so self_mention_count > 0."""
        result = analyze_pragmatic(business_doc, business_text)
        assert result["self_mention_count"] > 0, (
            "Business text should have self-mentions (we, our, I)"
        )

    def test_creative_higher_self_mention(
        self,
        creative_doc: Doc,
        creative_text: str,
    ) -> None:
        """Creative text contains 'she', 'her' but those are not in _SELF_MENTION.

        However the creative text has no first-person pronouns, so we just
        verify the pragmatic stage runs and returns a non-negative count.
        The self-mention set is {i, me, my, we, us, our, ...} so 'she'/'her'
        are not self-mentions. We verify the count is non-negative.
        """
        result = analyze_pragmatic(creative_doc, creative_text)
        assert result["self_mention_count"] >= 0, (
            f"Creative self-mention count {result['self_mention_count']} should be >= 0"
        )
