"""Shared pytest fixtures for mivoca NLP pipeline tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import spacy
from spacy.tokens import Doc, Span

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def nlp_model() -> spacy.language.Language:
    """Load the en_core_web_sm spaCy model once per session."""
    return spacy.load("en_core_web_sm")


@pytest.fixture(scope="session")
def business_text() -> str:
    """Load the sample business text fixture."""
    return (_FIXTURES_DIR / "sample_business.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def creative_text() -> str:
    """Load the sample creative text fixture."""
    return (_FIXTURES_DIR / "sample_creative.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def academic_text() -> str:
    """Load the sample academic text fixture."""
    return (_FIXTURES_DIR / "sample_academic.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def business_doc(nlp_model: spacy.language.Language, business_text: str) -> Doc:
    """Pre-processed spaCy Doc for business text."""
    return nlp_model(business_text)


@pytest.fixture(scope="session")
def creative_doc(nlp_model: spacy.language.Language, creative_text: str) -> Doc:
    """Pre-processed spaCy Doc for creative text."""
    return nlp_model(creative_text)


@pytest.fixture(scope="session")
def academic_doc(nlp_model: spacy.language.Language, academic_text: str) -> Doc:
    """Pre-processed spaCy Doc for academic text."""
    return nlp_model(academic_text)
