"""Quality monitoring module for the voice elicitation engine.

Detects satisficing behavior in real-time during the interview by checking
for straightlining, speed flags, alternation patterns, and covert attention
check consistency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _find_project_root() -> Path:
    """Walk up from this file to find the project root containing question-bank/."""
    current = Path(__file__).resolve().parent
    for ancestor in [current, *current.parents]:
        if (ancestor / "question-bank").is_dir():
            return ancestor
    raise FileNotFoundError(
        "Cannot locate project root: no ancestor directory contains question-bank/"
    )


def load_quality_config() -> dict:
    """Load satisficing-rules.json and attention-checks.json.

    Returns:
        dict with keys: 'satisficing_rules', 'attention_checks'.
    """
    root = _find_project_root()
    scoring_dir = root / "question-bank" / "scoring"

    satisficing_path = scoring_dir / "satisficing-rules.json"
    attention_path = scoring_dir / "attention-checks.json"

    if not satisficing_path.exists():
        raise FileNotFoundError(f"Missing config: {satisficing_path}")
    if not attention_path.exists():
        raise FileNotFoundError(f"Missing config: {attention_path}")

    with open(satisficing_path, "r", encoding="utf-8") as f:
        satisficing_rules = json.load(f)
    with open(attention_path, "r", encoding="utf-8") as f:
        attention_checks = json.load(f)

    return {
        "satisficing_rules": satisficing_rules,
        "attention_checks": attention_checks,
    }


def _is_scale_response(response: dict, question: dict | None = None) -> bool:
    """Check if a response is from a scale-type question.

    Checks the question definition type first (authoritative), then falls
    back to response-level question_type, then infers from value type.
    """
    # Authoritative: question bank definition.
    if question is not None:
        q_type = question.get("type", "")
        return q_type in ("likert", "semantic_differential", "calibration")

    # Response-level (supports both naming conventions).
    q_type = response.get("question_type", "")
    if q_type in ("likert", "likert_scale", "semantic_differential", "calibration"):
        return True
    # Explicitly non-scale types.
    if q_type in ("open_text", "open_ended", "writing_sample", "process_narration",
                  "select", "select_multiple", "forced_choice", "scenario",
                  "projective", "behavioral"):
        return False

    # No type information at all: infer from value.
    if not q_type:
        val = _get_scale_value(response)
        return val is not None

    return False


def _quality_config() -> dict:
    """Load quality-specific config values with defaults."""
    try:
        from lib.config import get
        return {
            "straightlining_threshold": get("interview.quality.straightlining_threshold", 5),
            "speed_threshold_ms": get("interview.quality.speed_threshold_ms", 2000),
            "speed_exempt_below_seconds": get("interview.quality.speed_exempt_below_seconds", 5),
            "speed_applies_above_seconds": get("interview.quality.speed_applies_above_seconds", 10),
            "alternation_threshold": get("interview.quality.alternation_threshold", 4),
            "alternation_extreme_values": get("interview.quality.alternation_extreme_values", [1, 7]),
            "engagement_reset_min_flags": get("interview.quality.engagement_reset_min_flags", 2),
            "engagement_reset_max_per_session": get("interview.quality.engagement_reset_max_per_session", 3),
            "session_invalid_threshold": get("interview.quality.session_invalid_threshold", 8),
            "confidence_penalty_per_flag": get("interview.quality.confidence_penalty_per_flag", 0.05),
        }
    except ImportError:
        return {
            "straightlining_threshold": 5,
            "speed_threshold_ms": 2000,
            "speed_exempt_below_seconds": 5,
            "speed_applies_above_seconds": 10,
            "alternation_threshold": 4,
            "alternation_extreme_values": [1, 7],
            "engagement_reset_min_flags": 2,
            "engagement_reset_max_per_session": 3,
            "session_invalid_threshold": 8,
            "confidence_penalty_per_flag": 0.05,
        }


def _get_scale_value(response: dict) -> int | None:
    """Extract numeric scale value from a response, handling the answer envelope.

    Supports both schema-compliant format (top-level value/scale_value) and
    interview-conductor format (nested answer.value).
    """
    # Try top-level scale_value first.
    val = response.get("scale_value")
    if val is None:
        val = response.get("semantic_differential_value")
    if val is None:
        val = response.get("value")
    # Unwrap answer envelope if present.
    if val is None or isinstance(val, dict):
        answer = response.get("answer")
        if isinstance(answer, dict):
            val = answer.get("scale_value")
            if val is None:
                val = answer.get("value")
    if isinstance(val, (int, float)):
        return int(val)
    # Try numeric string conversion.
    if isinstance(val, str):
        try:
            return int(float(val))
        except ValueError:
            pass
    return None


def detect_straightlining(recent_responses: list[dict], threshold: int = 5) -> bool:
    """Check if the last `threshold` scale responses have identical values.

    Only applies to likert and semantic_differential responses.

    Args:
        recent_responses: Recent responses ordered oldest to newest.
        threshold: Minimum consecutive identical scale values to flag.

    Returns:
        True if straightlining detected.
    """
    scale_values: list[int] = []
    for resp in recent_responses:
        if _is_scale_response(resp):
            val = _get_scale_value(resp)
            if val is not None:
                scale_values.append(val)

    if len(scale_values) < threshold:
        return False

    tail = scale_values[-threshold:]
    return len(set(tail)) == 1


# Keep the old signature working but also support question-aware calls.


def detect_speed_flag(response: dict, question: dict) -> bool:
    """Check if response was too fast.

    Threshold: duration_ms < 2000 for questions with estimated_seconds > 10.
    Simple questions (estimated_seconds <= 5) are exempt.

    Args:
        response: The response dict with a 'duration_ms' field.
        question: The question definition with 'estimated_seconds'.

    Returns:
        True if speed flag should be raised.
    """
    qc = _quality_config()
    # estimated_seconds is nested under metadata in question bank definitions.
    estimated = question.get("estimated_seconds")
    if estimated is None:
        metadata = question.get("metadata", {})
        if isinstance(metadata, dict):
            estimated = metadata.get("estimated_seconds")
    if estimated is None or estimated <= qc["speed_exempt_below_seconds"]:
        return False

    if estimated <= qc["speed_applies_above_seconds"]:
        return False

    # Support both nested (schema-compliant) and flat formats
    timing = response.get("timing", {})
    duration_ms = timing.get("duration_ms") if isinstance(timing, dict) else None
    if duration_ms is None:
        duration_ms = response.get("duration_ms")
    if duration_ms is None:
        return False

    return duration_ms < qc["speed_threshold_ms"]


def detect_alternation(recent_responses: list[dict], threshold: int = 4) -> bool:
    """Check for alternating extreme values (1,7,1,7...) on scale items.

    Looks at the last `threshold` scale responses.

    Args:
        recent_responses: Recent responses ordered oldest to newest.
        threshold: Minimum consecutive alternating extremes to flag.

    Returns:
        True if alternation pattern detected.
    """
    scale_values: list[int] = []
    for resp in recent_responses:
        if _is_scale_response(resp):
            val = _get_scale_value(resp)
            if val is not None:
                scale_values.append(val)

    if len(scale_values) < threshold:
        return False

    tail = scale_values[-threshold:]
    extremes = {1, 7}

    # All values must be extreme
    if not all(v in extremes for v in tail):
        return False

    # Check alternation: each consecutive pair must differ
    for i in range(len(tail) - 1):
        if tail[i] == tail[i + 1]:
            return False

    return True


def check_response_quality(
    response: dict,
    recent_responses: list[dict],
    question: dict,
) -> dict:
    """Check a single response for quality issues.

    Args:
        response: The current response with timing data.
        recent_responses: Last 5-10 responses for pattern detection.
        question: The question definition (for estimated_seconds, type).

    Returns:
        Dict with flags, flag_count, needs_engagement_reset, and details.
    """
    # Build the full window including the current response for pattern checks
    full_window = recent_responses + [response]

    too_fast = detect_speed_flag(response, question)
    straightlining = detect_straightlining(full_window)
    alternation = detect_alternation(full_window)

    flags = {
        "too_fast": too_fast,
        "straightlining": straightlining,
        "alternation": alternation,
    }
    flag_count = sum(1 for v in flags.values() if v)

    # Engagement reset triggers when 2+ cumulative flags are present
    needs_engagement_reset = flag_count >= 2

    details_parts: list[str] = []
    if too_fast:
        duration = response.get("duration_ms", "?")
        details_parts.append(
            f"Response too fast ({duration}ms) for complex item "
            f"(estimated {question.get('estimated_seconds', '?')}s)"
        )
    if straightlining:
        details_parts.append("Straightlining detected: identical consecutive scale values")
    if alternation:
        details_parts.append("Alternation pattern detected: extreme value oscillation")

    return {
        "flags": flags,
        "flag_count": flag_count,
        "needs_engagement_reset": needs_engagement_reset,
        "details": "; ".join(details_parts) if details_parts else None,
    }


def evaluate_attention_checks(responses: list[dict]) -> dict:
    """Post-interview evaluation of the 3 covert consistency checks.

    Check 1: M03-Q06 vs M07-Q02 -- within +/-2 points (numeric tolerance).
    Check 2: M04-Q09 vs M11-Q01 -- semantic consistency (flag for review).
    Check 3: M02-Q10 vs M09-Q09 -- precision/Germanic correlation.

    Args:
        responses: All session responses, each with a 'question_id' field.

    Returns:
        Dict with checks list, passed count, total, and overall_pass.
    """
    # Index responses by question_id for fast lookup
    by_id: dict[str, dict] = {}
    for resp in responses:
        qid = resp.get("question_id")
        if qid:
            by_id[qid] = resp

    config = load_quality_config()
    checks_config = config["attention_checks"]["consistency_checks"]

    results: list[dict[str, Any]] = []
    passed_count = 0

    for check_def in checks_config:
        check_id = check_def["check_id"]
        pair = check_def["item_pair"]
        method = check_def["validation_method"]

        resp_a = by_id.get(pair[0])
        resp_b = by_id.get(pair[1])

        # If either response is missing, mark as not passed
        if resp_a is None or resp_b is None:
            results.append({
                "id": check_id,
                "pair": pair,
                "passed": False,
                "delta": None,
                "note": "Missing response for one or both items",
            })
            continue

        val_a = _get_scale_value(resp_a)
        val_b = _get_scale_value(resp_b)

        if method == "numeric_tolerance":
            tolerance = check_def.get("tolerance", 2)
            if val_a is not None and val_b is not None:
                delta = abs(val_a - val_b)
                check_passed = delta <= tolerance
            else:
                delta = None
                check_passed = False

            results.append({
                "id": check_id,
                "pair": pair,
                "passed": check_passed,
                "delta": delta,
            })

        elif method == "semantic_similarity":
            # Semantic consistency cannot be fully automated without NLP.
            # Flag for review: pass if both responses exist (manual review needed).
            results.append({
                "id": check_id,
                "pair": pair,
                "passed": True,
                "delta": None,
                "note": "Semantic consistency check -- flagged for manual review",
            })

        elif method == "correlation_check":
            # Positive correlation: both should trend in the same direction.
            # Simple heuristic: if both are above midpoint (4) or both below,
            # or both equal to midpoint, consider it passed.
            if val_a is not None and val_b is not None:
                midpoint = 4
                same_side = (
                    (val_a >= midpoint and val_b >= midpoint)
                    or (val_a < midpoint and val_b < midpoint)
                )
                delta = abs(val_a - val_b)
                results.append({
                    "id": check_id,
                    "pair": pair,
                    "passed": same_side,
                    "delta": delta,
                })
            else:
                results.append({
                    "id": check_id,
                    "pair": pair,
                    "passed": False,
                    "delta": None,
                })

        else:
            results.append({
                "id": check_id,
                "pair": pair,
                "passed": False,
                "delta": None,
                "note": f"Unknown validation method: {method}",
            })

        if results[-1]["passed"]:
            passed_count += 1

    total = len(results)
    min_pass = config["attention_checks"]["global_settings"].get("min_checks_passed", 2)

    return {
        "checks": results,
        "passed": passed_count,
        "total": total,
        "overall_pass": passed_count >= min_pass,
    }


def compute_session_quality_report(
    responses: list[dict], questions: dict
) -> dict:
    """Generate a complete quality report for a finished session.

    Args:
        responses: All session responses in order, each with question_id,
                   duration_ms, value/answer, and question_type fields.
        questions: Dict mapping question_id to question definitions.

    Returns:
        Full quality report dict.
    """
    total_flags = 0
    straightline_sequences = 0
    too_fast_count = 0
    alternation_count = 0
    engagement_resets_triggered = 0
    flagged_responses: list[str] = []

    # Track cumulative flags for engagement reset logic
    cumulative_flags = 0
    next_reset_at = 2  # First reset triggers at 2 cumulative flags

    config = load_quality_config()
    reset_cfg = config["satisficing_rules"]["engagement_reset_threshold"]
    min_flags_for_reset = reset_cfg.get("min_flags", 2)
    max_resets = reset_cfg.get("max_resets_per_session", 3)

    # Slide a window over responses
    for i, resp in enumerate(responses):
        qid = resp.get("question_id", "")
        question = questions.get(qid, {})

        # Build the recent window (up to 10 previous responses)
        start = max(0, i - 10)
        recent = responses[start:i]

        result = check_response_quality(resp, recent, question)

        if result["flag_count"] > 0:
            total_flags += result["flag_count"]
            cumulative_flags += result["flag_count"]
            flagged_responses.append(qid or f"response_{i}")

        if result["flags"]["too_fast"]:
            too_fast_count += 1
        if result["flags"]["straightlining"]:
            straightline_sequences += 1
        if result["flags"]["alternation"]:
            alternation_count += 1

        # Trigger engagement reset when cumulative flags cross the next threshold
        if (
            cumulative_flags >= next_reset_at
            and engagement_resets_triggered < max_resets
        ):
            engagement_resets_triggered += 1
            next_reset_at += min_flags_for_reset  # Next reset after another N flags

    attention_results = evaluate_attention_checks(responses)

    # Determine overall quality
    max_invalid = config["satisficing_rules"]["session_validity"].get(
        "max_flags_before_invalid", 8
    )
    if total_flags == 0 and attention_results["overall_pass"]:
        overall_quality = "good"
    elif total_flags < max_invalid and attention_results["overall_pass"]:
        overall_quality = "acceptable"
    else:
        overall_quality = "questionable"

    return {
        "total_responses": len(responses),
        "total_flags": total_flags,
        "straightline_sequences": straightline_sequences,
        "too_fast_count": too_fast_count,
        "alternation_count": alternation_count,
        "attention_check_results": attention_results,
        "engagement_resets_triggered": engagement_resets_triggered,
        "overall_quality": overall_quality,
        "flagged_responses": flagged_responses,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_check_response(args: argparse.Namespace) -> None:
    """Handle the check-response subcommand."""
    response = json.loads(args.response)
    recent = json.loads(args.recent)
    question = json.loads(args.question)
    result = check_response_quality(response, recent, question)
    print(json.dumps(result, indent=2))


def _cli_check_session(args: argparse.Namespace) -> None:
    """Handle the check-session subcommand."""
    session_dir = Path(args.session_dir).expanduser().resolve()

    # Load responses (JSONL format — one JSON object per line)
    responses_path = session_dir / "responses.jsonl"
    if not responses_path.exists():
        print(
            json.dumps({"error": f"responses.jsonl not found in {session_dir}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    responses: list[dict[str, Any]] = []
    with open(responses_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                responses.append(json.loads(line))

    # Load questions -- try questions.json in session dir, then fall back to
    # building a map from the responses themselves.
    questions_path = session_dir / "questions.json"
    if questions_path.exists():
        with open(questions_path, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        # Normalize: if it's a list, convert to dict keyed by question_id
        if isinstance(questions_data, list):
            questions = {q["question_id"]: q for q in questions_data if "question_id" in q}
        else:
            questions = questions_data
    else:
        # Build a minimal map from response metadata if available
        questions = {}
        for resp in responses:
            qid = resp.get("question_id")
            if qid and qid not in questions:
                questions[qid] = {
                    "question_id": qid,
                    "estimated_seconds": resp.get("estimated_seconds"),
                    "type": resp.get("question_type"),
                }

    report = compute_session_quality_report(responses, questions)
    print(json.dumps(report, indent=2))


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="quality",
        description="Voice quality monitoring — detect satisficing behavior",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check-response
    cr = subparsers.add_parser(
        "check-response",
        help="Check a single response for quality issues",
    )
    cr.add_argument("--response", required=True, help="JSON string of the current response")
    cr.add_argument("--recent", required=True, help="JSON array of recent responses")
    cr.add_argument("--question", required=True, help="JSON string of the question definition")
    cr.set_defaults(func=_cli_check_response)

    # check-session
    cs = subparsers.add_parser(
        "check-session",
        help="Generate quality report for a complete session",
    )
    cs.add_argument(
        "--session-dir",
        required=True,
        help="Path to session directory (e.g. ~/.human-voice/sessions/{id}/)",
    )
    cs.set_defaults(func=_cli_check_session)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
