"""Syntactic analysis stage.

Computes sentence structure and complexity metrics:
- Mean sentence length (tokens)
- Sentence length standard deviation
- Mean clause length (approximated via dependency parsing)
- Clauses per sentence
- Dependent clause ratio
- Complex T-unit ratio
- Active/passive voice ratio
- Left-branching ratio
"""

from __future__ import annotations

import math
from typing import Any

from spacy.tokens import Doc, Span


def _count_clauses(sent: Span) -> tuple[int, int]:
    """Count total clauses and dependent clauses in a sentence.

    Approximation: each finite verb (with a subject dependency) signals
    a clause. Dependent clauses are identified by subordinate markers
    (mark, advcl, relcl, ccomp, xcomp, acl).

    Returns:
        (total_clauses, dependent_clauses)
    """
    dependent_deps = {"advcl", "relcl", "ccomp", "xcomp", "acl"}
    total = 0
    dependent = 0

    for token in sent:
        # A verb heading a clause (has a subject child or is root verb)
        if token.pos_ in ("VERB", "AUX") and token.dep_ in (
            "ROOT", "advcl", "relcl", "ccomp", "xcomp", "acl", "conj",
        ):
            total += 1
            if token.dep_ in dependent_deps:
                dependent += 1

    # Ensure at least one clause per sentence
    return max(total, 1), dependent


def _is_passive(sent: Span) -> bool:
    """Detect passive voice in a sentence.

    Looks for nsubjpass (spaCy v3 still uses this in some models) or
    the aux + past-participle pattern with a by-agent.
    """
    for token in sent:
        if token.dep_ in ("nsubjpass", "nsubj:pass"):
            return True
    # Fallback: look for be-verb + past participle pattern
    for token in sent:
        if token.dep_ == "auxpass":
            return True
    return False


def _left_branching_ratio(sent: Span) -> float:
    """Compute the ratio of pre-head dependents to total dependents.

    Left-branching measures how many modifiers come before their heads.
    """
    left = 0
    total = 0
    for token in sent:
        if token.dep_ == "ROOT" or token.is_punct:
            continue
        total += 1
        if token.i < token.head.i:
            left += 1
    return left / total if total > 0 else 0.0


def analyze_syntactic(doc: Doc, sentences: list[Span]) -> dict[str, Any]:
    """Run syntactic analysis on a spaCy Doc.

    Args:
        doc: A processed spaCy Doc.
        sentences: List of sentence Spans from the tokenizer stage.

    Returns:
        Dict of syntactic features.
    """
    if not sentences:
        return {
            "mean_sentence_length": 0.0,
            "sentence_length_sd": 0.0,
            "mean_clause_length": 0.0,
            "clauses_per_sentence": 0.0,
            "dependent_clause_ratio": 0.0,
            "complex_t_unit_ratio": 0.0,
            "passive_voice_ratio": 0.0,
            "left_branching_ratio": 0.0,
        }

    sent_lengths = [
        sum(1 for t in sent if not t.is_punct and not t.is_space)
        for sent in sentences
    ]
    n_sents = len(sentences)

    mean_len = sum(sent_lengths) / n_sents
    variance = sum((l - mean_len) ** 2 for l in sent_lengths) / n_sents
    sd_len = math.sqrt(variance)

    total_clauses = 0
    total_dep_clauses = 0
    complex_t_units = 0
    passive_count = 0
    lb_ratios: list[float] = []

    for sent in sentences:
        clauses, dep_clauses = _count_clauses(sent)
        total_clauses += clauses
        total_dep_clauses += dep_clauses

        # A complex T-unit has at least one dependent clause
        if dep_clauses > 0:
            complex_t_units += 1

        if _is_passive(sent):
            passive_count += 1

        lb_ratios.append(_left_branching_ratio(sent))

    # Total content tokens for clause length
    content_tokens = sum(1 for t in doc if not t.is_punct and not t.is_space)
    mean_clause_length = content_tokens / total_clauses if total_clauses > 0 else 0.0

    return {
        "mean_sentence_length": round(mean_len, 2),
        "sentence_length_sd": round(sd_len, 2),
        "mean_clause_length": round(mean_clause_length, 2),
        "clauses_per_sentence": round(total_clauses / n_sents, 3),
        "dependent_clause_ratio": round(
            total_dep_clauses / total_clauses if total_clauses > 0 else 0.0, 4
        ),
        "complex_t_unit_ratio": round(complex_t_units / n_sents, 4),
        "passive_voice_ratio": round(passive_count / n_sents, 4),
        "left_branching_ratio": round(
            sum(lb_ratios) / len(lb_ratios) if lb_ratios else 0.0, 4
        ),
    }
