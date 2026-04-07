"""Shared response envelope handling for the human-voice plugin.

Provides canonical functions for extracting values from interview responses
that may arrive in two formats:

1. Schema-compliant flat format: ``{"value": 3, "scale_value": 3, ...}``
2. Interview-conductor nested format: ``{"answer": {"value": 3, "raw": "3"}, ...}``

Used by both real-time quality monitoring (lib/quality.py) and post-hoc
scoring (scoring/) to avoid duplicating envelope unwrapping logic.
"""

from __future__ import annotations

from typing import Any


def extract_value(response: dict[str, Any]) -> Any:
    """Extract the primary response value, handling the answer envelope format.

    Checks top-level keys first (``scale_value``, ``semantic_differential_value``,
    ``value``), then unwraps the ``answer`` envelope if present.

    Returns the raw value (may be int, float, str, or None).
    """
    val = response.get("scale_value")
    if val is None:
        val = response.get("semantic_differential_value")
    if val is None:
        val = response.get("value")
    # If val is still None or is itself a dict, try the answer envelope.
    if val is None or isinstance(val, dict):
        answer = response.get("answer")
        if isinstance(answer, dict):
            val = answer.get("scale_value")
            if val is None:
                val = answer.get("semantic_differential_value")
            if val is None:
                val = answer.get("value")
    return val


def extract_scale_value(response: dict[str, Any]) -> int | None:
    """Extract numeric scale value from a response.

    Like :func:`extract_value` but coerces to ``int``, returning ``None``
    for non-numeric values.  Handles string-encoded numbers (e.g. ``"3"``).
    """
    val = extract_value(response)
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(float(val))
        except ValueError:
            pass
    return None


def flatten_response(response: dict[str, Any]) -> dict[str, Any]:
    """Flatten the answer envelope to top-level keys.

    If the response has an ``answer`` dict, promotes its keys to top level
    without overwriting existing top-level keys (schema fields take precedence).

    Returns the original dict unchanged if no ``answer`` envelope is present.
    """
    answer = response.get("answer")
    if not isinstance(answer, dict):
        return response
    flat: dict[str, Any] = {**response}
    for key in ("value", "raw", "scale_value", "selected_options",
                "semantic_differential_value", "raw_text"):
        if key not in flat or flat[key] is None:
            if key in answer:
                flat[key] = answer[key]
    return flat


def build_response_lookup(
    responses: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build a question_id -> flattened response mapping.

    Iterates over *responses*, flattens each via :func:`flatten_response`,
    and indexes by ``question_id``.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for r in responses:
        qid = r.get("question_id")
        if qid:
            lookup[qid] = flatten_response(r)
    return lookup
