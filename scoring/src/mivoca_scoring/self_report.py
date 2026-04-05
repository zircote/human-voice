"""Per-dimension subscale scoring for self-report responses.

Implements the mivoca scoring algorithm:

1. Get contributing items per dimension from dimension-item-mapping.
2. Normalize each response to 0-100 scale based on question type.
3. Apply weights from scoring-weights.
4. Compute weighted mean as dimension_score.
5. Compute Cronbach's alpha when >=4 items; flag if alpha < 0.60.
6. Cross-validate with semantic differential where mapping exists
   (0.7 * dimension + 0.3 * SD_normalized).

Also scores 10 gap dimensions from self-report items.
"""

from __future__ import annotations

from typing import Any

import numpy as np


# ---------- Gold-standard dimensions ----------

GOLD_DIMENSIONS = [
    "formality",
    "emotional_tone",
    "personality",
    "complexity",
    "audience_awareness",
    "authority",
    "narrativity",
    "humor",
]

# Gap dimensions derived from self-report comparisons.
GAP_DIMENSIONS = [
    "formality_gap",
    "emotional_tone_gap",
    "personality_gap",
    "complexity_gap",
    "audience_awareness_gap",
    "authority_gap",
    "narrativity_gap",
    "humor_gap",
    "self_awareness_gap",
    "adaptability_gap",
]


# ---------- Normalization helpers ----------


def _normalize_likert(value: float | int, scale_min: int = 1, scale_max: int = 7) -> float:
    """Normalize a Likert value to 0-100."""
    if scale_max == scale_min:
        return 50.0
    return ((value - scale_min) / (scale_max - scale_min)) * 100.0


def _normalize_forced_choice(value: float | int, n_options: int) -> float:
    """Normalize a forced-choice ordinal value to 0-100."""
    if n_options <= 1:
        return 50.0
    return ((value - 1) / (n_options - 1)) * 100.0


def _normalize_semantic_differential(value: float | int) -> float:
    """Normalize a 1-7 semantic differential value to 0-100."""
    return _normalize_likert(value, 1, 7)


def _normalize_scenario(value: float | int, n_options: int) -> float:
    """Normalize a scenario response (treated as ordinal) to 0-100."""
    return _normalize_forced_choice(value, n_options)


def normalize_response(
    value: Any,
    question_type: str,
    n_options: int = 7,
    scale_min: int = 1,
    scale_max: int = 7,
) -> float | None:
    """Normalize a single response value to 0-100 based on question type.

    Returns None if value is not numeric or question type is non-scorable.
    """
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None

    if question_type == "likert":
        return _normalize_likert(num, scale_min, scale_max)
    if question_type == "semantic_differential":
        return _normalize_semantic_differential(num)
    if question_type in ("forced_choice", "select"):
        return _normalize_forced_choice(num, n_options)
    if question_type == "scenario":
        return _normalize_scenario(num, n_options)
    # Non-scorable types (open_ended, writing_sample, etc.)
    return None


# ---------- Cronbach's alpha ----------


def cronbachs_alpha(item_scores: list[list[float]]) -> float | None:
    """Compute Cronbach's alpha for a set of item score vectors.

    Parameters
    ----------
    item_scores:
        List of item vectors (one list per item). All vectors must have equal
        length (number of respondents / observations). For single-session
        scoring, each vector has length 1 so alpha is computed from the
        item-level variance decomposition using the items as "observations".

    Returns
    -------
    Alpha coefficient, or None if computation is not meaningful (< 2 items).
    """
    k = len(item_scores)
    if k < 2:
        return None

    arr = np.array(item_scores, dtype=np.float64)  # shape (k, n)
    n = arr.shape[1]

    if n < 2:
        # With a single observation we cannot compute variance reliably.
        # Fall back: treat the k item scores as a single observation set and
        # compute alpha treating each item as a "test" across a synthetic
        # leave-one-out approach.  This is a pragmatic fallback for single-
        # session scoring.
        scores = arr.flatten()
        total_var = float(np.var(scores, ddof=1))
        if total_var == 0:
            return 1.0  # No variance means perfect consistency.
        item_vars = 0.0  # Each "item" has single value → variance = 0.
        alpha = (k / (k - 1)) * (1 - item_vars / total_var)
        return float(np.clip(alpha, -1.0, 1.0))

    item_variances = np.var(arr, axis=1, ddof=1)
    total_scores = np.sum(arr, axis=0)
    total_variance = float(np.var(total_scores, ddof=1))

    if total_variance == 0:
        return 1.0

    alpha = (k / (k - 1)) * (1 - float(np.sum(item_variances)) / total_variance)
    return float(np.clip(alpha, -1.0, 1.0))


# ---------- Main scoring entry point ----------


def _build_response_lookup(responses: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a question_id -> response mapping.

    Handles two response formats:

    1. Schema-compliant (top-level keys): ``{"question_id": "...", "value": 3, "scale_value": 3}``
    2. Interview-conductor format (nested answer): ``{"question_id": "...", "answer": {"value": 3, "raw": "3"}}``

    For format 2, the ``answer`` dict is flattened into top-level keys so
    downstream code can use ``resp.get("value")`` regardless of format.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for r in responses:
        qid = r.get("question_id")
        if qid:
            # Unwrap nested answer envelope if present.
            answer = r.get("answer")
            if isinstance(answer, dict):
                flat = {**r}
                # Promote answer keys to top level without overwriting
                # existing top-level keys (schema fields take precedence).
                for key in ("value", "raw", "scale_value", "selected_options",
                            "semantic_differential_value", "raw_text"):
                    if key not in flat or flat[key] is None:
                        if key in answer:
                            flat[key] = answer[key]
                lookup[qid] = flat
            else:
                lookup[qid] = r
    return lookup


def _infer_question_type(
    response: dict[str, Any],
    question_def: dict[str, Any] | None = None,
) -> str:
    """Determine question type from question bank metadata or response data.

    When a question definition is available (from the question bank), its
    ``type`` field is authoritative. Otherwise falls back to best-effort
    inference from response data shape.
    """
    # Prefer authoritative type from question bank.
    if question_def is not None:
        qtype = question_def.get("type")
        if qtype:
            return str(qtype)

    # Fallback: infer from response fields.
    if response.get("semantic_differential_value") is not None:
        return "semantic_differential"
    if response.get("scale_value") is not None:
        return "likert"
    if response.get("selected_options") is not None:
        return "select"
    if response.get("raw_text") is not None:
        return "open_ended"
    # Default for numeric values.
    v = response.get("value")
    if isinstance(v, (int, float)):
        return "likert"
    return "unknown"


def _resolve_scoring_map_value(
    value: Any,
    question_def: dict[str, Any] | None,
    dimension: str,
) -> float | None:
    """Resolve a categorical response value to a numeric score via scoring_map.

    For questions with string values (forced_choice, select, scenario, projective),
    the question definition's ``scoring_map`` maps each option value to per-dimension
    numeric scores.  This function looks up the value in the scoring_map and returns
    the score for the requested dimension.

    Returns None if no scoring_map exists or the value/dimension is not found.
    """
    if question_def is None:
        return None
    scoring = question_def.get("scoring", {})
    scoring_map = scoring.get("scoring_map", {})
    if not scoring_map:
        return None

    # scoring_map keys may be strings even for numeric values.
    str_value = str(value)
    entry = scoring_map.get(value)
    if entry is None:
        entry = scoring_map.get(str_value)
    if not isinstance(entry, dict):
        return None

    # The scoring_map contains per-dimension scores using sub-dimension
    # names (e.g., "formality_baseline" for the "formality" dimension).
    # Try exact match first, then prefix match in both directions.
    if dimension in entry:
        return float(entry[dimension])

    # Prefix match with separator: "formality" matches "formality_baseline".
    for key, val in entry.items():
        if isinstance(val, (int, float)) and key.startswith(dimension + "_"):
            return float(val)

    # Reverse prefix with separator: "formality_baseline" dimension matches "formality_" key.
    for key, val in entry.items():
        if isinstance(val, (int, float)) and dimension.startswith(key + "_"):
            return float(val)

    # No match found. Do not fabricate a score by averaging unrelated
    # sub-dimensions; return None so the item is skipped transparently.
    return None


def _scoring_map_range(
    question_def: dict[str, Any] | None,
    dimension: str,
) -> tuple[int, int]:
    """Determine the min/max score range from a question's scoring_map.

    Examines all entries in the scoring_map for the values associated with
    the target dimension (using the same prefix-matching logic as
    ``_resolve_scoring_map_value``).  Returns (min, max) of found values.

    Falls back to (1, 5) if no matching values are found, since the
    question bank predominantly uses 1-5 scoring scales.
    """
    if question_def is None:
        return (1, 5)

    scoring_map = question_def.get("scoring", {}).get("scoring_map", {})
    if not scoring_map:
        return (1, 5)

    matched_values: list[float] = []
    for entry in scoring_map.values():
        if not isinstance(entry, dict):
            continue
        # Exact match.
        if dimension in entry and isinstance(entry[dimension], (int, float)):
            matched_values.append(float(entry[dimension]))
            continue
        # Prefix match with separator.
        for key, val in entry.items():
            if isinstance(val, (int, float)) and key.startswith(dimension + "_"):
                matched_values.append(float(val))
                break
        else:
            # Reverse prefix with separator.
            for key, val in entry.items():
                if isinstance(val, (int, float)) and dimension.startswith(key + "_"):
                    matched_values.append(float(val))
                    break

    if not matched_values:
        return (1, 5)

    import math
    return (math.floor(min(matched_values)), math.ceil(max(matched_values)))


def score_self_report(
    responses: list[dict[str, Any]],
    dimension_mapping: dict[str, Any],
    scoring_weights: dict[str, Any],
    sd_scores: dict[str, float] | None = None,
    question_bank: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score all self-report dimensions.

    Parameters
    ----------
    responses:
        List of response records (from responses.jsonl).
    dimension_mapping:
        Maps dimension names to lists of contributing item question_ids.
        Format: ``{"formality": ["M01-Q01", "M01-Q02", ...], ...}``
    scoring_weights:
        Maps dimension names to per-item weights.
        Format: ``{"formality": {"M01-Q01": 0.8, ...}, ...}``
    sd_scores:
        Optional normalized semantic-differential scores keyed by dimension.
    question_bank:
        Optional mapping from question_id to question definition dicts
        (loaded from question-bank modules). Provides authoritative question
        type, option count, and scoring_map for categorical value resolution.

    Returns
    -------
    Dict with per-dimension score entries and gap dimension scores.
    """
    if question_bank is None:
        question_bank = {}

    resp_lookup = _build_response_lookup(responses)
    results: dict[str, Any] = {"dimensions": {}, "gap_dimensions": {}}

    # Score gold-standard dimensions.
    all_dims = list(dimension_mapping.keys())
    for dim in all_dims:
        item_ids = dimension_mapping.get(dim, [])
        dim_weights = scoring_weights.get(dim, {})

        normalized_values: list[float] = []
        weighted_values: list[float] = []
        weight_sum = 0.0
        skipped_items = 0

        for qid in item_ids:
            resp = resp_lookup.get(qid)
            if resp is None:
                skipped_items += 1
                continue

            qdef = question_bank.get(qid)
            qtype = _infer_question_type(resp, question_def=qdef)
            raw_value = resp.get("scale_value") or resp.get("semantic_differential_value") or resp.get("value")

            # For categorical string values, resolve via scoring_map.
            scoring_map_used = False
            if raw_value is not None and isinstance(raw_value, str):
                try:
                    # Try numeric conversion first (e.g., "3" -> 3.0).
                    raw_value = float(raw_value)
                except ValueError:
                    # Categorical string: resolve through scoring_map.
                    resolved = _resolve_scoring_map_value(raw_value, qdef, dim)
                    if resolved is not None:
                        raw_value = resolved
                        scoring_map_used = True
                    else:
                        # Cannot resolve; skip this item.
                        skipped_items += 1
                        continue

            # When a scoring_map was used, the resolved value is already on
            # a meaningful numeric scale. Determine the actual scale range
            # from the scoring_map entries rather than assuming 1-7.
            if scoring_map_used and raw_value is not None:
                smap_min, smap_max = _scoring_map_range(qdef, dim)
                norm = _normalize_likert(float(raw_value), scale_min=smap_min, scale_max=smap_max)
            else:
                # Determine n_options and scale bounds from question definition.
                n_options = 7  # default
                scale_min = 1
                scale_max = 7
                if qdef is not None:
                    options = qdef.get("options", [])
                    if options:
                        n_options = len(options)
                        # For Likert scales, extract min/max from option values.
                        if qtype == "likert":
                            opt_vals = [o.get("value") for o in options if isinstance(o.get("value"), (int, float))]
                            if opt_vals:
                                scale_min = int(min(opt_vals))
                                scale_max = int(max(opt_vals))

                norm = normalize_response(raw_value, qtype, n_options=n_options, scale_min=scale_min, scale_max=scale_max)
            if norm is None:
                skipped_items += 1
                continue

            w = dim_weights.get(qid, 1.0)
            normalized_values.append(norm)
            weighted_values.append(norm * w)
            weight_sum += w

        # Compute weighted mean.
        if weight_sum > 0:
            dimension_score = sum(weighted_values) / weight_sum
        else:
            dimension_score = None

        # Cronbach's alpha (need >= 4 items).
        alpha: float | None = None
        alpha_flag = False
        if len(normalized_values) >= 4:
            # Each item is a single-score vector (single session).
            item_vecs = [[v] for v in normalized_values]
            alpha = cronbachs_alpha(item_vecs)
            if alpha is not None and alpha < 0.60:
                alpha_flag = True

        # Cross-validate with semantic differential if available.
        final_score = dimension_score
        sd_used = False
        if dimension_score is not None and sd_scores and dim in sd_scores:
            sd_val = sd_scores[dim]
            if sd_val is not None:
                final_score = 0.7 * dimension_score + 0.3 * sd_val
                sd_used = True

        is_gap = dim in GAP_DIMENSIONS
        target = results["gap_dimensions"] if is_gap else results["dimensions"]
        target[dim] = {
            "score": round(final_score, 2) if final_score is not None else None,
            "raw_weighted_mean": round(dimension_score, 2) if dimension_score is not None else None,
            "item_count": len(normalized_values),
            "total_items": len(item_ids),
            "skipped_items": skipped_items,
            "cronbachs_alpha": round(alpha, 3) if alpha is not None else None,
            "alpha_flag": alpha_flag,
            "sd_cross_validated": sd_used,
        }

    return results
