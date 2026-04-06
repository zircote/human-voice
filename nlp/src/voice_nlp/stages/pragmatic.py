"""Pragmatic analysis stage.

Detects stance markers and interactional features:
- Hedge marker count and density
- Booster marker count and density
- Hedge/boost ratio
- Self-mention frequency (I, me, my, we, our, us)
- Engagement markers (consider, note, you, your, etc.)
- Attitude markers
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from spacy.tokens import Doc

_LEXICON_DIR = Path(__file__).parent.parent / "lexicons"

# Cached lexicons — loaded on first use
_hedges: list[str] | None = None
_boosters: list[str] | None = None

# Self-mention pronouns
_SELF_MENTION = frozenset({"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"})

# Engagement markers (Hyland's interactional model)
_ENGAGEMENT = frozenset({
    "consider", "note", "remember", "imagine", "suppose", "assume",
    "you", "your", "yours", "yourself",
    "let", "must", "should", "need",
    "see", "notice", "observe",
})

# Attitude markers — express writer's affect
_ATTITUDE = frozenset({
    "agree", "disagree", "prefer", "unfortunately", "fortunately",
    "importantly", "interestingly", "surprisingly", "remarkably",
    "appropriate", "inappropriate", "essential", "necessary",
    "expected", "unexpected", "understandable", "admittedly",
    "hopefully", "ideally", "curiously", "notably", "regrettably",
    "striking", "dramatic", "compelling", "problematic",
})


def _load_lexicon(name: str) -> list[str]:
    """Load a JSON lexicon file from the lexicons directory."""
    path = _LEXICON_DIR / f"{name}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_hedges() -> list[str]:
    global _hedges
    if _hedges is None:
        _hedges = _load_lexicon("hedges")
    return _hedges


def _get_boosters() -> list[str]:
    global _boosters
    if _boosters is None:
        _boosters = _load_lexicon("boosters")
    return _boosters


def _count_marker_hits(doc: Doc, markers: list[str]) -> int:
    """Count how many tokens match any marker in the list.

    Supports both single-word and multi-word markers. Multi-word markers
    are matched against the lowercased text with simple substring search.
    """
    single_words = set()
    multi_word: list[str] = []

    for m in markers:
        if " " in m:
            multi_word.append(m.lower())
        else:
            single_words.add(m.lower())

    count = sum(1 for token in doc if token.text.lower() in single_words)

    if multi_word:
        text_lower = doc.text.lower()
        for phrase in multi_word:
            # Count non-overlapping occurrences
            start = 0
            while True:
                idx = text_lower.find(phrase, start)
                if idx == -1:
                    break
                count += 1
                start = idx + len(phrase)

    return count


def analyze_pragmatic(doc: Doc, text: str) -> dict[str, Any]:
    """Run pragmatic analysis on a spaCy Doc.

    Args:
        doc: A processed spaCy Doc.
        text: Raw text (used for multi-word marker matching).

    Returns:
        Dict of pragmatic features.
    """
    word_count = sum(1 for t in doc if t.is_alpha)
    if word_count == 0:
        return {
            "hedge_count": 0,
            "hedge_density": 0.0,
            "booster_count": 0,
            "booster_density": 0.0,
            "hedge_boost_ratio": 0.0,
            "self_mention_count": 0,
            "self_mention_density": 0.0,
            "engagement_marker_count": 0,
            "engagement_marker_density": 0.0,
            "attitude_marker_count": 0,
            "attitude_marker_density": 0.0,
        }

    hedges = _get_hedges()
    boosters = _get_boosters()

    hedge_count = _count_marker_hits(doc, hedges)
    booster_count = _count_marker_hits(doc, boosters)

    self_mention_count = sum(
        1 for token in doc if token.text.lower() in _SELF_MENTION
    )

    engagement_count = sum(
        1 for token in doc if token.text.lower() in _ENGAGEMENT
    )

    attitude_count = sum(
        1 for token in doc if token.text.lower() in _ATTITUDE
    )

    per_1k = 1000.0 / word_count

    return {
        "hedge_count": hedge_count,
        "hedge_density": round(hedge_count * per_1k, 3),
        "booster_count": booster_count,
        "booster_density": round(booster_count * per_1k, 3),
        "hedge_boost_ratio": round(
            hedge_count / booster_count if booster_count > 0 else float(hedge_count), 3
        ),
        "self_mention_count": self_mention_count,
        "self_mention_density": round(self_mention_count * per_1k, 3),
        "engagement_marker_count": engagement_count,
        "engagement_marker_density": round(engagement_count * per_1k, 3),
        "attitude_marker_count": attitude_count,
        "attitude_marker_density": round(attitude_count * per_1k, 3),
    }
