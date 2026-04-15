"""Pipeline orchestrator — runs all analysis stages in sequence.

Takes raw text, returns a complete analysis dict matching the
writing-analysis schema.
"""

from __future__ import annotations

from typing import Any

import spacy

from voice_nlp.stages.tokenizer import tokenize
from voice_nlp.stages.lexical import analyze_lexical
from voice_nlp.stages.syntactic import analyze_syntactic
from voice_nlp.stages.pragmatic import analyze_pragmatic
from voice_nlp.stages.discourse import analyze_discourse
from voice_nlp.stages.composite import analyze_composite


def run_pipeline(nlp: spacy.language.Language, text: str) -> dict[str, Any]:
    """Run the full stylometric analysis pipeline.

    Stages executed in order:
        1. tokenizer  — spaCy tokenization, POS tagging, sentence splitting
        2. lexical    — vocabulary diversity and sophistication metrics
        3. syntactic  — sentence structure and complexity metrics
        4. pragmatic  — stance markers, self-mention, engagement
        5. discourse  — cohesion, connectives, idea density
        6. composite  — formality, readability, LIWC-equivalent scores

    Args:
        nlp: A loaded spaCy Language model.
        text: The raw writing sample text.

    Returns:
        A dict with keys for each stage plus top-level metadata.
    """
    doc, sentences = tokenize(nlp, text)

    lexical = analyze_lexical(doc, text)
    syntactic = analyze_syntactic(doc, sentences)
    pragmatic = analyze_pragmatic(doc, text)
    discourse = analyze_discourse(doc, sentences)
    composite = analyze_composite(doc, text)

    return {
        "text_length_chars": len(text),
        "text_length_tokens": len(doc),
        "sentence_count": len(sentences),
        "lexical": lexical,
        "syntactic": syntactic,
        "pragmatic": pragmatic,
        "discourse": discourse,
        "composite": composite,
    }
