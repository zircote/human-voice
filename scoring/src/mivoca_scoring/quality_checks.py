"""Satisficing detection and attention-check validation.

Detects low-quality responding patterns:
- Straightlining: 5+ consecutive identical scale responses.
- Speed: response time < 2 seconds for non-trivial questions.
- Pattern: alternating extremes (1,7,1,7...) over 4+ questions.

Validates attention-check items:
- Check 1: M03-Q06 vs M07-Q02 — within +/-2 points.
- Check 2: M04-Q09 vs M11-Q01 — semantic consistency (flag for manual review).
- Check 3: M02-Q10 vs M09-Q09 — precision-Germanic correlation.
"""

from __future__ import annotations

from typing import Any


def _extract_value(r: dict[str, Any]) -> Any:
    """Extract the primary response value, handling the answer envelope format."""
    val = r.get("scale_value")
    if val is None:
        val = r.get("semantic_differential_value")
    if val is None:
        val = r.get("value")
    if val is None:
        answer = r.get("answer")
        if isinstance(answer, dict):
            val = answer.get("scale_value")
            if val is None:
                val = answer.get("semantic_differential_value")
            if val is None:
                val = answer.get("value")
    return val


# Non-trivial question types where speed check applies.
_NONTRIVIAL_TYPES = {
    "likert",
    "forced_choice",
    "scenario",
    "semantic_differential",
    "select",
    "select_multiple",
    "behavioral",
}

# Minimum response time (ms) below which a response is flagged.
_MIN_DURATION_MS = 2000


# ---------- Satisficing detectors ----------


def detect_straightlining(
    responses: list[dict[str, Any]],
    threshold: int = 5,
) -> list[dict[str, Any]]:
    """Detect runs of >= *threshold* consecutive identical scale values.

    Returns a list of flag dicts, each with ``start_index``, ``end_index``,
    ``value``, and ``count``.
    """
    flags: list[dict[str, Any]] = []
    run_value: Any = None
    run_start = 0
    run_count = 0

    for i, r in enumerate(responses):
        val = _extract_value(r)
        if val is not None and val == run_value:
            run_count += 1
        else:
            if run_count >= threshold:
                flags.append({
                    "type": "straightlining",
                    "start_index": run_start,
                    "end_index": i - 1,
                    "value": run_value,
                    "count": run_count,
                })
            run_value = val
            run_start = i
            run_count = 1

    # Flush trailing run.
    if run_count >= threshold:
        flags.append({
            "type": "straightlining",
            "start_index": run_start,
            "end_index": len(responses) - 1,
            "value": run_value,
            "count": run_count,
        })

    return flags


def detect_speed_flags(
    responses: list[dict[str, Any]],
    questions: list[dict[str, Any]] | None = None,
    min_duration_ms: int = _MIN_DURATION_MS,
) -> list[dict[str, Any]]:
    """Detect responses faster than *min_duration_ms* for non-trivial questions.

    Returns list of flag dicts with ``question_id`` and ``duration_ms``.
    """
    # Build a set of non-trivial question ids if question metadata available.
    nontrivial_ids: set[str] | None = None
    if questions:
        nontrivial_ids = set()
        for q in questions:
            if q.get("type") in _NONTRIVIAL_TYPES:
                nontrivial_ids.add(q["question_id"])

    flags: list[dict[str, Any]] = []
    for r in responses:
        qid = r.get("question_id", "")
        timing = r.get("timing", {})
        duration = timing.get("duration_ms")
        if duration is None:
            continue

        # If we have question metadata, only flag non-trivial types.
        if nontrivial_ids is not None and qid not in nontrivial_ids:
            continue
        # Without metadata, flag all responses with numeric value (assumed non-trivial).
        if nontrivial_ids is None:
            val = _extract_value(r)
            if not isinstance(val, (int, float)):
                continue

        if duration < min_duration_ms:
            flags.append({
                "type": "speed",
                "question_id": qid,
                "duration_ms": duration,
            })

    return flags


def detect_alternating_extremes(
    responses: list[dict[str, Any]],
    min_run: int = 4,
    extremes: tuple[float, float] = (1.0, 7.0),
) -> list[dict[str, Any]]:
    """Detect alternating extreme responses (e.g. 1,7,1,7) over *min_run*+ items.

    Returns flag dicts with ``start_index``, ``end_index``, ``count``.
    """
    flags: list[dict[str, Any]] = []
    low, high = extremes

    run_start: int | None = None
    run_count = 0
    expected_next: float | None = None

    for i, r in enumerate(responses):
        val = _extract_value(r)
        if not isinstance(val, (int, float)):
            # Break in scale values resets the run.
            if run_count >= min_run and run_start is not None:
                flags.append({
                    "type": "alternating_extremes",
                    "start_index": run_start,
                    "end_index": i - 1,
                    "count": run_count,
                })
            run_start = None
            run_count = 0
            expected_next = None
            continue

        fval = float(val)
        if fval not in (low, high):
            if run_count >= min_run and run_start is not None:
                flags.append({
                    "type": "alternating_extremes",
                    "start_index": run_start,
                    "end_index": i - 1,
                    "count": run_count,
                })
            run_start = None
            run_count = 0
            expected_next = None
            continue

        if expected_next is None:
            # Starting a potential run.
            run_start = i
            run_count = 1
            expected_next = high if fval == low else low
        elif fval == expected_next:
            run_count += 1
            expected_next = high if fval == low else low
        else:
            # Same extreme repeated, not alternating.
            if run_count >= min_run and run_start is not None:
                flags.append({
                    "type": "alternating_extremes",
                    "start_index": run_start,
                    "end_index": i - 1,
                    "count": run_count,
                })
            run_start = i
            run_count = 1
            expected_next = high if fval == low else low

    # Flush trailing run.
    if run_count >= min_run and run_start is not None:
        flags.append({
            "type": "alternating_extremes",
            "start_index": run_start,
            "end_index": len(responses) - 1,
            "count": run_count,
        })

    return flags


# ---------- Attention checks ----------


def _get_scale_value(response: dict[str, Any] | None) -> float | None:
    """Extract the primary numeric scale value from a response."""
    if response is None:
        return None
    for key in ("scale_value", "semantic_differential_value", "value"):
        v = response.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def validate_attention_checks(
    responses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate the three attention-check pairs.

    Returns a list of check result dicts, each with ``check_id``, ``passed``,
    ``details``, and optionally ``manual_review``.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for r in responses:
        qid = r.get("question_id")
        if qid:
            lookup[qid] = r

    checks: list[dict[str, Any]] = []

    # Check 1: M03-Q06 vs M07-Q02 — within +/-2 points.
    v1a = _get_scale_value(lookup.get("M03-Q06"))
    v1b = _get_scale_value(lookup.get("M07-Q02"))
    if v1a is not None and v1b is not None:
        delta = abs(v1a - v1b)
        checks.append({
            "check_id": 1,
            "pair": ["M03-Q06", "M07-Q02"],
            "values": [v1a, v1b],
            "delta": delta,
            "passed": delta <= 2.0,
            "rule": "within +/-2 points",
        })
    else:
        checks.append({
            "check_id": 1,
            "pair": ["M03-Q06", "M07-Q02"],
            "values": [v1a, v1b],
            "delta": None,
            "passed": None,
            "rule": "within +/-2 points (items missing)",
        })

    # Check 2: M04-Q09 vs M11-Q01 — semantic consistency, flag for manual review.
    v2a = _get_scale_value(lookup.get("M04-Q09"))
    v2b = _get_scale_value(lookup.get("M11-Q01"))
    if v2a is not None and v2b is not None:
        delta = abs(v2a - v2b)
        # Flag if delta > 3 (lenient threshold; still requires manual review).
        checks.append({
            "check_id": 2,
            "pair": ["M04-Q09", "M11-Q01"],
            "values": [v2a, v2b],
            "delta": delta,
            "passed": delta <= 3.0,
            "manual_review": True,
            "rule": "semantic consistency (manual review)",
        })
    else:
        checks.append({
            "check_id": 2,
            "pair": ["M04-Q09", "M11-Q01"],
            "values": [v2a, v2b],
            "delta": None,
            "passed": None,
            "manual_review": True,
            "rule": "semantic consistency (items missing)",
        })

    # Check 3: M02-Q10 vs M09-Q09 — precision/Germanic correlation.
    v3a = _get_scale_value(lookup.get("M02-Q10"))
    v3b = _get_scale_value(lookup.get("M09-Q09"))
    if v3a is not None and v3b is not None:
        delta = abs(v3a - v3b)
        checks.append({
            "check_id": 3,
            "pair": ["M02-Q10", "M09-Q09"],
            "values": [v3a, v3b],
            "delta": delta,
            "passed": delta <= 2.0,
            "rule": "precision-Germanic correlation (within +/-2)",
        })
    else:
        checks.append({
            "check_id": 3,
            "pair": ["M02-Q10", "M09-Q09"],
            "values": [v3a, v3b],
            "delta": None,
            "passed": None,
            "rule": "precision-Germanic correlation (items missing)",
        })

    return checks


# ---------- Aggregate quality report ----------


def run_quality_checks(
    responses: list[dict[str, Any]],
    questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run all quality checks and return a consolidated report.

    Returns dict with:
      - ``satisficing_flags``: list of all satisficing detections
      - ``attention_checks``: list of attention check results
      - ``pass``: overall pass/fail (bool)
      - ``summary``: human-readable summary string
    """
    straightline_flags = detect_straightlining(responses)
    speed_flags = detect_speed_flags(responses, questions)
    pattern_flags = detect_alternating_extremes(responses)

    all_satisficing = straightline_flags + speed_flags + pattern_flags

    attention_checks = validate_attention_checks(responses)

    # Determine overall pass.
    # Fail conditions: any attention check explicitly failed, or severe satisficing.
    attention_failed = any(
        c.get("passed") is False and not c.get("manual_review")
        for c in attention_checks
    )
    severe_satisficing = len(straightline_flags) > 0 or len(pattern_flags) > 0
    speed_count = len(speed_flags)

    overall_pass = not attention_failed and not severe_satisficing and speed_count < 5

    summary_parts: list[str] = []
    if straightline_flags:
        summary_parts.append(f"{len(straightline_flags)} straightlining run(s)")
    if speed_flags:
        summary_parts.append(f"{speed_count} fast response(s)")
    if pattern_flags:
        summary_parts.append(f"{len(pattern_flags)} alternating-extreme pattern(s)")
    if attention_failed:
        summary_parts.append("attention check(s) failed")

    summary = "Quality: PASS" if overall_pass else "Quality: FAIL"
    if summary_parts:
        summary += " — " + "; ".join(summary_parts)

    return {
        "pass": overall_pass,
        "satisficing_flags": all_satisficing,
        "attention_checks": attention_checks,
        "summary": summary,
    }
