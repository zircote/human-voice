"""Lexical analysis stage.

Computes vocabulary diversity and sophistication metrics:
- MTLD (Measure of Textual Lexical Diversity)
- MATTR (Moving Average Type-Token Ratio, window=50)
- Hapax legomena ratio
- Average word length (characters and syllables)
- Latinate/Germanic ratio
- Vocabulary sophistication (frequency band analysis)
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from spacy.tokens import Doc

# Common Latinate suffixes (from Latin/French roots via Norman French)
_LATINATE_SUFFIXES = (
    "tion", "sion", "ment", "ence", "ance", "ity", "ious", "eous",
    "ible", "able", "ive", "ous", "al", "ual", "ical",
)

# High-frequency Germanic core vocabulary (top ~200 words)
_GERMANIC_CORE = frozenset({
    "the", "a", "an", "and", "but", "or", "if", "so", "yet", "for",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their",
    "this", "that", "these", "those", "who", "what", "which", "where", "when",
    "how", "why", "all", "each", "every", "both", "few", "many", "much",
    "some", "any", "no", "not", "more", "most", "other", "such",
    "up", "out", "in", "on", "off", "over", "under", "with", "from", "to",
    "at", "by", "of", "about", "into", "through", "after", "before",
    "go", "get", "make", "come", "take", "give", "say", "tell", "think",
    "know", "see", "look", "find", "want", "need", "feel", "put", "keep",
    "let", "begin", "seem", "help", "show", "hear", "play", "run", "move",
    "live", "believe", "hold", "bring", "happen", "write", "sit", "stand",
    "lose", "pay", "meet", "set", "learn", "lead", "understand", "watch",
    "follow", "stop", "speak", "read", "spend", "grow", "open", "walk",
    "win", "teach", "offer", "remember", "love", "pull", "reach", "stay",
    "wait", "send", "build", "fall", "cut", "hit", "fill",
    "man", "woman", "child", "world", "life", "hand", "time", "day", "way",
    "thing", "word", "work", "home", "house", "water", "food", "land",
    "good", "great", "big", "small", "old", "new", "long", "high", "little",
    "own", "right", "true", "best", "better", "last", "first",
})


def _count_syllables(word: str) -> int:
    """Estimate syllable count using vowel-group heuristic."""
    word = word.lower().strip()
    if not word:
        return 0
    # Remove trailing silent e
    if word.endswith("e") and len(word) > 2:
        word = word[:-1]
    vowel_groups = re.findall(r"[aeiouy]+", word)
    count = len(vowel_groups)
    return max(count, 1)


def _compute_mtld_one_direction(words: list[str]) -> float:
    """Compute MTLD in one direction (forward or backward).

    Walk through the token list, maintaining a running TTR. When TTR
    drops below 0.72, count one factor and reset. The final partial
    segment contributes a fractional factor.
    """
    threshold = 0.72
    factor_count = 0.0
    types: set[str] = set()
    token_count = 0

    for word in words:
        types.add(word)
        token_count += 1
        ttr = len(types) / token_count
        if ttr <= threshold:
            factor_count += 1.0
            types = set()
            token_count = 0

    # Add partial factor for remaining segment
    if token_count > 0:
        current_ttr = len(types) / token_count
        if current_ttr < 1.0:
            # Proportion of the way from 1.0 down to threshold
            factor_count += (1.0 - current_ttr) / (1.0 - threshold)

    return factor_count


def compute_mtld(words: list[str]) -> float:
    """Compute MTLD as the average of forward and backward passes.

    MTLD = word_count / factor_count, averaged over both directions.
    """
    if len(words) < 10:
        return 0.0

    forward_factors = _compute_mtld_one_direction(words)
    backward_factors = _compute_mtld_one_direction(list(reversed(words)))

    n = len(words)
    forward_mtld = n / forward_factors if forward_factors > 0 else n
    backward_mtld = n / backward_factors if backward_factors > 0 else n

    return (forward_mtld + backward_mtld) / 2.0


def compute_mattr(words: list[str], window: int = 50) -> float:
    """Compute Moving Average Type-Token Ratio.

    Slides a window of size `window` across the token list, computing
    TTR at each position, then returns the mean.
    """
    if len(words) < window:
        if len(words) == 0:
            return 0.0
        # Fall back to simple TTR for short texts
        return len(set(words)) / len(words)

    ttr_values: list[float] = []
    for i in range(len(words) - window + 1):
        segment = words[i : i + window]
        ttr_values.append(len(set(segment)) / window)

    return sum(ttr_values) / len(ttr_values)


def _is_latinate(word: str) -> bool:
    """Heuristic: classify a word as Latinate based on suffix patterns."""
    lower = word.lower()
    if len(lower) < 4:
        return False
    return any(lower.endswith(suffix) for suffix in _LATINATE_SUFFIXES)


def _is_germanic(word: str) -> bool:
    """Heuristic: classify a word as Germanic (core vocabulary)."""
    return word.lower() in _GERMANIC_CORE


def analyze_lexical(doc: Doc, _text: str) -> dict[str, Any]:
    """Run lexical analysis on a spaCy Doc.

    Args:
        doc: A processed spaCy Doc.
        _text: The raw text (unused here but kept for interface consistency).

    Returns:
        Dict of lexical features.
    """
    # Collect content words (exclude punctuation and whitespace)
    words = [token.text.lower() for token in doc if token.is_alpha]

    if not words:
        return {
            "mtld": 0.0,
            "mattr": 0.0,
            "hapax_legomena_ratio": 0.0,
            "avg_word_length_chars": 0.0,
            "avg_word_length_syllables": 0.0,
            "latinate_germanic_ratio": 0.0,
            "latinate_count": 0,
            "germanic_count": 0,
            "vocabulary_sophistication": 0.0,
            "type_token_ratio": 0.0,
        }

    word_count = len(words)
    freq = Counter(words)
    types = set(words)

    # Hapax legomena: words occurring exactly once
    hapax = sum(1 for _, c in freq.items() if c == 1)
    hapax_ratio = hapax / len(types) if types else 0.0

    # Average word length
    avg_chars = sum(len(w) for w in words) / word_count
    avg_syllables = sum(_count_syllables(w) for w in words) / word_count

    # Latinate / Germanic ratio
    latinate_count = sum(1 for w in types if _is_latinate(w))
    germanic_count = sum(1 for w in types if _is_germanic(w))
    lat_germ_ratio = (
        latinate_count / germanic_count if germanic_count > 0 else float(latinate_count)
    )

    # Vocabulary sophistication: proportion of types that are hapax AND
    # longer than average (proxy for low-frequency sophisticated words)
    hapax_words = {w for w, c in freq.items() if c == 1}
    sophisticated = sum(1 for w in hapax_words if len(w) > avg_chars)
    vocab_sophistication = sophisticated / len(types) if types else 0.0

    return {
        "mtld": round(compute_mtld(words), 3),
        "mattr": round(compute_mattr(words, window=50), 4),
        "hapax_legomena_ratio": round(hapax_ratio, 4),
        "avg_word_length_chars": round(avg_chars, 3),
        "avg_word_length_syllables": round(avg_syllables, 3),
        "latinate_germanic_ratio": round(lat_germ_ratio, 3),
        "latinate_count": latinate_count,
        "germanic_count": germanic_count,
        "vocabulary_sophistication": round(vocab_sophistication, 4),
        "type_token_ratio": round(len(types) / word_count, 4),
    }
