"""Normalize and map semantic differential (SD) responses to dimensions.

Each SD item is a 1-7 bipolar scale. This module normalizes all 20 SD
responses to a 0-100 scale and maps each pair to its corresponding
voice-profile dimensions via the SD dimension mapping.
"""

from __future__ import annotations

from typing import Any


def _normalize_sd_value(value: float | int) -> float:
    """Normalize a 1-7 SD value to 0-100."""
    return ((value - 1) / 6) * 100.0


def normalize_semantic_differentials(
    responses: list[dict[str, Any]],
    sd_dimension_mapping: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Normalize SD responses and aggregate per dimension.

    Parameters
    ----------
    responses:
        Full list of response records.  SD items are identified by having
        a non-null ``semantic_differential_value``.
    sd_dimension_mapping:
        Optional mapping from SD question_ids to dimension names.
        Format: ``{"SD-Q01": ["formality"], "SD-Q02": ["emotional_tone", "personality"], ...}``
        If None, returns per-item normalized scores keyed by question_id.

    Returns
    -------
    Dict mapping dimension names (or question_ids) to normalized 0-100 scores.
    """
    # Collect SD responses.
    sd_responses: dict[str, float] = {}
    for r in responses:
        sd_val = r.get("semantic_differential_value")
        if sd_val is not None:
            qid = r.get("question_id", "")
            try:
                sd_responses[qid] = float(sd_val)
            except (TypeError, ValueError):
                continue

    if not sd_responses:
        return {}

    # Normalize each SD value.
    normalized_items: dict[str, float] = {}
    for qid, raw in sd_responses.items():
        normalized_items[qid] = _normalize_sd_value(raw)

    # If no mapping, return per-item scores.
    if sd_dimension_mapping is None:
        return normalized_items

    # Aggregate by dimension.
    dim_accum: dict[str, list[float]] = {}
    for qid, norm_val in normalized_items.items():
        dims = sd_dimension_mapping.get(qid, [])
        if isinstance(dims, str):
            dims = [dims]
        for dim in dims:
            dim_accum.setdefault(dim, []).append(norm_val)

    dim_scores: dict[str, float] = {}
    for dim, vals in dim_accum.items():
        dim_scores[dim] = round(sum(vals) / len(vals), 2)

    return dim_scores
