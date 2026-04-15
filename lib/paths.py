"""Shared path utilities for the human-voice plugin.

Provides project root discovery used by modules that need to locate the
question-bank directory.
"""

from __future__ import annotations

from pathlib import Path


def find_project_root() -> Path:
    """Walk up from the lib/ directory to find the project root containing question-bank/.

    Returns the first ancestor directory that contains a ``question-bank/``
    subdirectory.

    Raises:
        FileNotFoundError: If no ancestor contains ``question-bank/``.
    """
    current = Path(__file__).resolve().parent
    for ancestor in [current, *current.parents]:
        if (ancestor / "question-bank").is_dir():
            return ancestor
    raise FileNotFoundError(
        "Cannot locate project root: no ancestor directory contains question-bank/"
    )
