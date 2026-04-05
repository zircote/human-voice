"""Tokenization and POS tagging stage using spaCy.

Produces a spaCy Doc object with sentence boundaries for downstream stages.
"""

from __future__ import annotations

import spacy
from spacy.tokens import Doc, Span


def tokenize(nlp: spacy.language.Language, text: str) -> tuple[Doc, list[Span]]:
    """Tokenize text and extract sentence boundaries.

    Args:
        nlp: A loaded spaCy Language model (must include sentencizer or parser).
        text: Raw input text.

    Returns:
        A tuple of (doc, sentences) where sentences is a list of Span objects.
    """
    doc = nlp(text)
    sentences = list(doc.sents)
    return doc, sentences
