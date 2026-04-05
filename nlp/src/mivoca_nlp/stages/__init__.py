"""Analysis stages for the mivoca-nlp pipeline."""

from mivoca_nlp.stages.tokenizer import tokenize
from mivoca_nlp.stages.lexical import analyze_lexical
from mivoca_nlp.stages.syntactic import analyze_syntactic
from mivoca_nlp.stages.pragmatic import analyze_pragmatic
from mivoca_nlp.stages.discourse import analyze_discourse
from mivoca_nlp.stages.composite import analyze_composite

__all__ = [
    "tokenize",
    "analyze_lexical",
    "analyze_syntactic",
    "analyze_pragmatic",
    "analyze_discourse",
    "analyze_composite",
]
