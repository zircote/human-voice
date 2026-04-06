"""Composite scores stage.

Computes aggregate stylometric indices:
- Heylighen-Dewaele Formality F-score
- Flesch-Kincaid Grade Level
- Flesch Reading Ease
- Gunning Fog Index
- LIWC-equivalent summary variables (Analytical Thinking, Clout,
  Authenticity, Emotional Tone)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from spacy.tokens import Doc

_LEXICON_DIR = Path(__file__).parent.parent / "lexicons"

_liwc_categories: dict[str, list[str]] | None = None


def _load_liwc_categories() -> dict[str, list[str]]:
    global _liwc_categories
    if _liwc_categories is None:
        path = _LEXICON_DIR / "liwc_categories.json"
        with open(path, "r", encoding="utf-8") as f:
            _liwc_categories = json.load(f)
    assert _liwc_categories is not None
    return _liwc_categories


def _count_syllables(word: str) -> int:
    """Estimate syllable count using vowel-group heuristic."""
    word = word.lower().strip()
    if not word:
        return 0
    if word.endswith("e") and len(word) > 2:
        word = word[:-1]
    vowel_groups = re.findall(r"[aeiouy]+", word)
    count = len(vowel_groups)
    return max(count, 1)


def _formality_score(doc: Doc) -> float:
    """Compute Heylighen-Dewaele Formality F-score.

    F = (noun + adjective + preposition + article
         - pronoun - verb - adverb - interjection + 100) / 2

    POS mapping to Universal POS tags:
        noun = NOUN + PROPN
        adjective = ADJ
        preposition = ADP
        article = DET (filtered to articles)
        pronoun = PRON
        verb = VERB + AUX
        adverb = ADV
        interjection = INTJ
    """
    pos_counts: dict[str, int] = {
        "noun": 0,
        "adj": 0,
        "adp": 0,
        "det": 0,
        "pron": 0,
        "verb": 0,
        "adv": 0,
        "intj": 0,
    }

    articles = {"a", "an", "the"}

    for token in doc:
        if not token.is_alpha:
            continue
        pos = token.pos_
        if pos in ("NOUN", "PROPN"):
            pos_counts["noun"] += 1
        elif pos == "ADJ":
            pos_counts["adj"] += 1
        elif pos == "ADP":
            pos_counts["adp"] += 1
        elif pos == "DET" and token.text.lower() in articles:
            pos_counts["det"] += 1
        elif pos == "PRON":
            pos_counts["pron"] += 1
        elif pos in ("VERB", "AUX"):
            pos_counts["verb"] += 1
        elif pos == "ADV":
            pos_counts["adv"] += 1
        elif pos == "INTJ":
            pos_counts["intj"] += 1

    f_score = (
        pos_counts["noun"]
        + pos_counts["adj"]
        + pos_counts["adp"]
        + pos_counts["det"]
        - pos_counts["pron"]
        - pos_counts["verb"]
        - pos_counts["adv"]
        - pos_counts["intj"]
        + 100
    ) / 2

    return f_score


def _readability_metrics(doc: Doc) -> dict[str, float]:
    """Compute Flesch-Kincaid, Flesch Reading Ease, and Gunning Fog.

    Uses the spaCy Doc for tokenization rather than external libraries,
    so we have consistent token counts across the pipeline.
    """
    words = [t for t in doc if t.is_alpha]
    sentences = list(doc.sents)

    word_count = len(words)
    sent_count = len(sentences)
    if word_count == 0 or sent_count == 0:
        return {
            "flesch_kincaid_grade": 0.0,
            "flesch_reading_ease": 0.0,
            "gunning_fog_index": 0.0,
        }

    syllable_count = sum(_count_syllables(t.text) for t in words)
    avg_sent_len = word_count / sent_count
    avg_syl_per_word = syllable_count / word_count

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * avg_sent_len + 11.8 * avg_syl_per_word - 15.59

    # Flesch Reading Ease
    fre = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syl_per_word

    # Gunning Fog Index: complex words = 3+ syllables
    complex_words = sum(1 for t in words if _count_syllables(t.text) >= 3)
    fog = 0.4 * (avg_sent_len + 100 * (complex_words / word_count))

    return {
        "flesch_kincaid_grade": round(fk_grade, 2),
        "flesch_reading_ease": round(fre, 2),
        "gunning_fog_index": round(fog, 2),
    }


def _category_frequency(doc: Doc, word_list: list[str]) -> float:
    """Compute the frequency of category words per total word tokens."""
    word_set = frozenset(w.lower() for w in word_list)
    words = [t for t in doc if t.is_alpha]
    if not words:
        return 0.0
    hits = sum(1 for t in words if t.text.lower() in word_set)
    return hits / len(words)


def _liwc_equivalents(doc: Doc) -> dict[str, float]:
    """Compute LIWC-equivalent summary variables from word category frequencies.

    These are open approximations:
    - Analytical Thinking: high articles + prepositions, low pronouns/aux verbs
    - Clout: high first-person plural, second-person; low hedging, first-person singular
    - Authenticity: high first-person singular, past tense, exclusive words; low negations
    - Emotional Tone: positive emotion words minus negative emotion words
    """
    cats = _load_liwc_categories()

    words = [t for t in doc if t.is_alpha]
    word_count = len(words)
    if word_count == 0:
        return {
            "analytical_thinking": 0.0,
            "clout": 0.0,
            "authenticity": 0.0,
            "emotional_tone": 0.0,
        }

    def freq(category: str) -> float:
        if category not in cats:
            return 0.0
        return _category_frequency(doc, cats[category])

    # Analytical Thinking: articles + prepositions signal formal, analytical style
    articles_f = freq("articles")
    prepositions_f = freq("prepositions")
    fpsing_f = freq("first_person_singular")
    fpplur_f = freq("first_person_plural")
    second_f = freq("second_person")
    pos_emo_f = freq("positive_emotion")
    neg_emo_f = freq("negative_emotion")
    cognitive_f = freq("cognitive_process")
    social_f = freq("social_process")

    # Analytical Thinking (0-100 scale): driven by article/preposition use
    # Higher = more formal/analytical; lower = more narrative/personal
    analytical = min(100.0, (articles_f + prepositions_f) * 500)

    # Clout (0-100 scale): social confidence and leadership
    # High we-references, you-references; low I-references
    clout_raw = (fpplur_f + second_f + social_f) - fpsing_f
    clout = min(100.0, max(0.0, 50 + clout_raw * 500))

    # Authenticity (0-100 scale): personal, honest disclosure
    # High first-person singular, cognitive process words
    auth_raw = fpsing_f + cognitive_f - (articles_f * 0.5)
    authenticity = min(100.0, max(0.0, 50 + auth_raw * 500))

    # Emotional Tone (0-100 scale): positive minus negative emotion
    tone_raw = pos_emo_f - neg_emo_f
    emotional_tone = min(100.0, max(0.0, 50 + tone_raw * 1000))

    return {
        "analytical_thinking": round(analytical, 2),
        "clout": round(clout, 2),
        "authenticity": round(authenticity, 2),
        "emotional_tone": round(emotional_tone, 2),
    }


def analyze_composite(doc: Doc, _text: str) -> dict[str, Any]:
    """Run composite analysis on a spaCy Doc.

    Args:
        doc: A processed spaCy Doc.
        _text: Raw text (unused, kept for interface consistency).

    Returns:
        Dict of composite features.
    """
    f_score = _formality_score(doc)
    readability = _readability_metrics(doc)
    liwc = _liwc_equivalents(doc)

    return {
        "formality_f_score": round(f_score, 2),
        **readability,
        **liwc,
    }
