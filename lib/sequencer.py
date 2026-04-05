"""Question sequencer for the mivoca voice elicitation engine.

Given the current session state, question bank, and branching rules, determines
the next question to present. Handles module transitions, format alternation
(max 5 same-type streak), engagement reset injection, and deep-dive injection.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lib.branching import (
    get_module_sequence,
    check_deep_dive_triggers,
    get_engagement_reset_points,
)


def _find_project_root() -> Path:
    """Walk up from this file to find the project root containing question-bank/."""
    current = Path(__file__).resolve().parent
    for ancestor in [current, *current.parents]:
        if (ancestor / "question-bank").is_dir():
            return ancestor
    raise FileNotFoundError("Cannot find project root with question-bank/ directory")


_MODULE_CACHE: dict[str, list[dict[str, Any]]] = {}


def _load_module_questions(module_id: str) -> list[dict[str, Any]]:
    """Load questions for a module from the question bank."""
    if module_id in _MODULE_CACHE:
        return _MODULE_CACHE[module_id]

    root = _find_project_root()
    modules_dir = root / "question-bank" / "modules"

    # Find the file matching this module_id
    for path in sorted(modules_dir.glob("*.json")):
        if path.stem.startswith(module_id) or (module_id == "SD" and path.stem.startswith("SD")):
            with open(path, "r", encoding="utf-8") as f:
                questions = json.load(f)
            _MODULE_CACHE[module_id] = questions
            return questions

    return []


def _get_answered_question_ids(responses: list[dict[str, Any]]) -> set[str]:
    """Extract the set of question IDs that have been answered."""
    return {r["question_id"] for r in responses if "question_id" in r}


def get_active_modules(writer_type: str) -> list[str]:
    """Return ordered list of active module IDs for a writer type."""
    sequence = get_module_sequence(writer_type)
    return [entry["module_id"] for entry in sequence if entry["is_active"]]


def _should_engagement_reset(state: dict[str, Any], next_module_id: str) -> bool:
    """Check if an engagement reset should be injected before this module."""
    reset_points = get_engagement_reset_points()
    for point in reset_points:
        after = point.get("after_module", "")
        # The reset fires when we're transitioning past the 'after_module'
        current = state.get("current_module", "")
        if current == after and next_module_id != current:
            return True
    return False


def _check_format_streak(state: dict[str, Any], question: dict[str, Any]) -> bool:
    """Check if we need to skip this question due to format streak limit.

    Returns True if the streak would exceed 5 with this question's type.
    """
    streak = state.get("format_streak", {})
    current_type = streak.get("current_type")
    count = streak.get("count", 0)
    question_type = question.get("type", "")

    if current_type == question_type and count >= 5:
        return True
    return False


def _find_format_break_question(
    questions: list[dict[str, Any]],
    current_index: int,
    current_type: str,
    answered_ids: set[str],
) -> dict[str, Any] | None:
    """Find the next question with a different format type, looking ahead."""
    for i in range(current_index + 1, len(questions)):
        q = questions[i]
        if q["question_id"] not in answered_ids and q.get("type") != current_type:
            return q
    return None


def update_format_streak(state: dict[str, Any], question_type: str) -> dict[str, Any]:
    """Update the format streak tracker in state. Returns updated streak dict."""
    streak = state.get("format_streak", {"current_type": None, "count": 0})
    if streak.get("current_type") == question_type:
        streak["count"] = streak.get("count", 0) + 1
    else:
        streak["current_type"] = question_type
        streak["count"] = 1
    state["format_streak"] = streak
    return streak


def get_next_question(
    state: dict[str, Any],
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Determine the next question to present.

    Returns a dict with:
        - "question": the question object to present (or None if interview complete)
        - "action": "present_question" | "module_transition" | "engagement_reset" | "deep_dive" | "interview_complete"
        - "module_id": the module this question belongs to
        - "transition_message": optional message for module transitions
        - "progress": {"answered": int, "estimated_remaining": int, "percent": float}
    """
    writer_type = state.get("writer_type")
    if not writer_type:
        # Still in screening — serve screening questions from M01
        return _get_screening_question(state, responses)

    answered_ids = _get_answered_question_ids(responses)
    active_modules = get_active_modules(writer_type)

    # Check for deep-dive return
    if state.get("state") == "deep_dive" and state.get("deep_dive_return"):
        return _handle_deep_dive(state, responses, answered_ids)

    # Walk through active modules in order
    current_module = state.get("current_module")
    started_current = False

    for module_id in active_modules:
        if current_module and not started_current:
            if module_id == current_module:
                started_current = True
            else:
                continue

        questions = _load_module_questions(module_id)
        if not questions:
            continue

        # Check for engagement reset at module boundary
        if module_id != current_module and current_module is not None:
            if _should_engagement_reset(state, module_id):
                return {
                    "question": None,
                    "action": "engagement_reset",
                    "module_id": module_id,
                    "transition_message": _get_module_transition_message(module_id),
                    "progress": _compute_progress(state, answered_ids, active_modules),
                }

        # Find next unanswered question in this module
        for q in questions:
            qid = q["question_id"]
            if qid in answered_ids:
                continue

            # Check branching eligibility
            branches = q.get("metadata", {}).get("branching", {})
            required = branches.get("required_branches", ["*"])
            if required != ["*"] and writer_type not in required:
                continue

            # Check format streak
            if _check_format_streak(state, q):
                alt = _find_format_break_question(
                    questions,
                    questions.index(q),
                    state.get("format_streak", {}).get("current_type", ""),
                    answered_ids,
                )
                if alt:
                    q = alt

            # Check deep-dive triggers before presenting
            trigger = check_deep_dive_triggers(module_id, responses, state)
            if trigger and trigger["trigger_id"] not in state.get("deep_dives_triggered", []):
                return {
                    "question": None,
                    "action": "deep_dive",
                    "module_id": module_id,
                    "trigger": trigger,
                    "progress": _compute_progress(state, answered_ids, active_modules),
                }

            # Module transition message
            action = "present_question"
            transition = None
            if module_id != current_module:
                action = "module_transition"
                transition = _get_module_transition_message(module_id)

            return {
                "question": q,
                "action": action,
                "module_id": module_id,
                "transition_message": transition,
                "progress": _compute_progress(state, answered_ids, active_modules),
            }

    # All modules exhausted
    return {
        "question": None,
        "action": "interview_complete",
        "module_id": None,
        "transition_message": None,
        "progress": _compute_progress(state, answered_ids, active_modules),
    }


def _get_screening_question(
    state: dict[str, Any],
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Get the next screening question (M01 Q01-Q10, first 5 are screening)."""
    answered_ids = _get_answered_question_ids(responses)
    questions = _load_module_questions("M01")

    for q in questions:
        if q["question_id"] not in answered_ids:
            action = "present_question"
            if not state.get("current_module"):
                action = "module_transition"
            return {
                "question": q,
                "action": action,
                "module_id": "M01",
                "transition_message": _get_module_transition_message("M01") if action == "module_transition" else None,
                "progress": {
                    "answered": len(answered_ids),
                    "estimated_remaining": 70 - len(answered_ids),
                    "percent": round(len(answered_ids) / 70 * 100, 1),
                },
            }

    # All M01 questions answered — screening complete
    return {
        "question": None,
        "action": "screening_complete",
        "module_id": "M01",
        "transition_message": None,
        "progress": {
            "answered": len(answered_ids),
            "estimated_remaining": 70 - len(answered_ids),
            "percent": round(len(answered_ids) / 70 * 100, 1),
        },
    }


def _handle_deep_dive(
    state: dict[str, Any],
    responses: list[dict[str, Any]],
    answered_ids: set[str],
) -> dict[str, Any]:
    """Serve the next deep-dive question, or return to normal flow when exhausted."""
    dd_return = state.get("deep_dive_return", {})
    inject_questions = dd_return.get("inject_questions", [])
    return_module = dd_return.get("module", state.get("current_module", "M01"))
    active_modules = get_active_modules(state.get("writer_type", "personal_journalistic"))
    progress = _compute_progress(state, answered_ids, active_modules)

    # Find the next unanswered deep-dive question
    for qid in inject_questions:
        if qid in answered_ids:
            continue
        # Try to load the question from the module's question bank
        module_id = qid.split("-")[0]  # e.g., "M03" from "M03-DD01"
        questions = _load_module_questions(module_id)
        for q in questions:
            if q["question_id"] == qid:
                return {
                    "question": q,
                    "action": "deep_dive",
                    "module_id": module_id,
                    "transition_message": None,
                    "progress": progress,
                }
        # Question ID not found in bank — skip it
        continue

    # All deep-dive questions answered or not found — return to normal flow
    return {
        "question": None,
        "action": "deep_dive_complete",
        "module_id": return_module,
        "transition_message": f"Returning to {return_module}",
        "progress": progress,
    }


def _compute_progress(
    state: dict[str, Any],
    answered_ids: set[str],
    active_modules: list[str],
) -> dict[str, Any]:
    """Compute interview progress metrics."""
    answered = len(answered_ids)
    total_estimate = 0
    for mod_id in active_modules:
        questions = _load_module_questions(mod_id)
        total_estimate += len(questions)

    remaining = max(0, total_estimate - answered)
    percent = round(answered / total_estimate * 100, 1) if total_estimate > 0 else 0.0

    return {
        "answered": answered,
        "estimated_remaining": remaining,
        "percent": percent,
    }


# Module transition framing messages (motivational, per spec Section 4.4)
_TRANSITION_MESSAGES: dict[str, str] = {
    "M01": "Let's start by understanding your writing background and identity.",
    "M02": "Now let's explore the personality and values behind your voice.",
    "M03": "The next section looks at how formal or casual your writing tends to be.",
    "M04": "Let's talk about how you express emotion and tone in your writing.",
    "M05": "This section explores your narrative and cognitive style.",
    "M06": "Now we'll look at how you structure and organize your writing.",
    "SD": "Here's a quick section — rate where your voice falls on each of these scales.",
    "M07": "The next section explores how you adapt your voice for different readers.",
    "M08": "Let's look at how you build arguments and use rhetoric.",
    "M09": "This section covers the mechanics and small details of your writing style.",
    "M10": "Let's explore your writing process — how you draft and revise.",
    "M11": "Almost done — let's capture what you aspire to and what you reject in voice.",
    "M12": "Final section — a few short writing exercises to see your voice in action.",
}


def _get_module_transition_message(module_id: str) -> str:
    """Get a motivational framing message for a module transition."""
    return _TRANSITION_MESSAGES.get(module_id, f"Moving to the next section: {module_id}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mivoca question sequencer — determine the next question."
    )
    sub = parser.add_subparsers(dest="command")

    # next-question
    nq = sub.add_parser("next-question", help="Get the next question for a session.")
    nq.add_argument("--state", required=True, help="Path to session state.json")
    nq.add_argument("--responses", required=True, help="Path to responses.jsonl")

    # active-modules
    am = sub.add_parser("active-modules", help="List active modules for a writer type.")
    am.add_argument("--writer-type", required=True, help="Writer type branch name.")

    args = parser.parse_args()

    if args.command == "next-question":
        with open(args.state, "r", encoding="utf-8") as f:
            state = json.load(f)
        responses: list[dict[str, Any]] = []
        resp_path = Path(args.responses)
        if resp_path.exists():
            with open(resp_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        responses.append(json.loads(line))

        result = get_next_question(state, responses)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "active-modules":
        modules = get_active_modules(args.writer_type)
        print(json.dumps(modules, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
