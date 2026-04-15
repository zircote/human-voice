"""Discourse analysis stage.

Computes cohesion and coherence metrics:
- Connective density by type (causal, additive, adversative, temporal)
- Referential cohesion (noun overlap between adjacent sentences)
- Propositional idea density
"""

from __future__ import annotations

from typing import Any

from spacy.tokens import Doc, Span

# Discourse connectives categorized by relation type
_CONNECTIVES: dict[str, frozenset[str]] = {
    "causal": frozenset({
        "because", "since", "therefore", "thus", "hence", "consequently",
        "accordingly", "so", "as a result", "due to", "owing to",
        "for this reason", "that is why", "it follows that",
    }),
    "additive": frozenset({
        "and", "also", "moreover", "furthermore", "in addition",
        "additionally", "besides", "likewise", "similarly", "equally",
        "too", "as well", "not only", "what is more",
    }),
    "adversative": frozenset({
        "but", "however", "yet", "nevertheless", "nonetheless",
        "although", "though", "whereas", "while", "despite",
        "in contrast", "on the other hand", "conversely", "instead",
        "rather", "on the contrary", "still", "even so",
    }),
    "temporal": frozenset({
        "then", "next", "first", "second", "finally", "meanwhile",
        "subsequently", "previously", "afterwards", "before",
        "after", "during", "when", "while", "until", "since",
        "at the same time", "in the meantime", "eventually",
    }),
}

# Flatten single-word connectives for fast token lookup
_SINGLE_WORD_CONNECTIVES: dict[str, set[str]] = {}
_MULTI_WORD_CONNECTIVES: dict[str, list[str]] = {}

for _cat, _words in _CONNECTIVES.items():
    _SINGLE_WORD_CONNECTIVES[_cat] = set()
    _MULTI_WORD_CONNECTIVES[_cat] = []
    for w in _words:
        if " " in w:
            _MULTI_WORD_CONNECTIVES[_cat].append(w.lower())
        else:
            _SINGLE_WORD_CONNECTIVES[_cat].add(w.lower())


def _count_connectives(doc: Doc) -> dict[str, int]:
    """Count connectives by category."""
    counts: dict[str, int] = {cat: 0 for cat in _CONNECTIVES}
    text_lower = doc.text.lower()

    for cat in _CONNECTIVES:
        # Single-word matches
        for token in doc:
            if token.text.lower() in _SINGLE_WORD_CONNECTIVES[cat]:
                counts[cat] += 1

        # Multi-word matches
        for phrase in _MULTI_WORD_CONNECTIVES[cat]:
            start = 0
            while True:
                idx = text_lower.find(phrase, start)
                if idx == -1:
                    break
                counts[cat] += 1
                start = idx + len(phrase)

    return counts


def _noun_overlap(sent_a: Span, sent_b: Span) -> float:
    """Compute noun lemma overlap between two adjacent sentences.

    Returns the Jaccard coefficient of noun lemma sets.
    """
    nouns_a = {t.lemma_.lower() for t in sent_a if t.pos_ in ("NOUN", "PROPN")}
    nouns_b = {t.lemma_.lower() for t in sent_b if t.pos_ in ("NOUN", "PROPN")}

    if not nouns_a and not nouns_b:
        return 0.0

    intersection = nouns_a & nouns_b
    union = nouns_a | nouns_b
    return len(intersection) / len(union) if union else 0.0


def _referential_cohesion(sentences: list[Span]) -> float:
    """Mean noun overlap between all adjacent sentence pairs."""
    if len(sentences) < 2:
        return 0.0

    overlaps = [
        _noun_overlap(sentences[i], sentences[i + 1])
        for i in range(len(sentences) - 1)
    ]
    return sum(overlaps) / len(overlaps)


def _idea_density(doc: Doc) -> float:
    """Approximate propositional idea density.

    Idea density = number of propositions / number of words.
    Propositions are approximated by counting verbs, adjectives,
    adverbs, prepositions, and conjunctions (content-bearing relations).
    This follows the approach from Chand et al. (2012).
    """
    proposition_pos = {"VERB", "ADJ", "ADV", "ADP", "SCONJ", "CCONJ"}
    word_count = sum(1 for t in doc if t.is_alpha)
    prop_count = sum(1 for t in doc if t.pos_ in proposition_pos)
    return prop_count / word_count if word_count > 0 else 0.0


def analyze_discourse(doc: Doc, sentences: list[Span]) -> dict[str, Any]:
    """Run discourse analysis on a spaCy Doc.

    Args:
        doc: A processed spaCy Doc.
        sentences: List of sentence Spans from the tokenizer stage.

    Returns:
        Dict of discourse features.
    """
    word_count = sum(1 for t in doc if t.is_alpha)
    if word_count == 0:
        return {
            "connective_density_total": 0.0,
            "connective_density_causal": 0.0,
            "connective_density_additive": 0.0,
            "connective_density_adversative": 0.0,
            "connective_density_temporal": 0.0,
            "referential_cohesion": 0.0,
            "idea_density": 0.0,
        }

    conn_counts = _count_connectives(doc)
    total_conn = sum(conn_counts.values())
    per_1k = 1000.0 / word_count

    return {
        "connective_density_total": round(total_conn * per_1k, 3),
        "connective_density_causal": round(conn_counts["causal"] * per_1k, 3),
        "connective_density_additive": round(conn_counts["additive"] * per_1k, 3),
        "connective_density_adversative": round(conn_counts["adversative"] * per_1k, 3),
        "connective_density_temporal": round(conn_counts["temporal"] * per_1k, 3),
        "referential_cohesion": round(_referential_cohesion(sentences), 4),
        "idea_density": round(_idea_density(doc), 4),
    }
