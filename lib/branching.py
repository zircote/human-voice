"""Branching evaluator for the voice elicitation engine.

Determines interview routing based on screening question responses,
manages module sequencing by writer type, and evaluates deep-dive
trigger conditions during the elicitation session.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lib.paths import find_project_root


def load_branching_config() -> dict[str, Any]:
    """Load all branching config files from question-bank/branching/.

    Returns a dict with keys:
        'primary_routes'     - branch conditions and activated modules
        'deep_dive_triggers' - trigger rules for injecting deep-dive questions
        'module_sequence'    - phase ordering, core/branch module lists, resets
    """
    root = find_project_root()
    branching_dir = root / "question-bank" / "branching"

    config: dict[str, Any] = {}
    for key, filename in [
        ("primary_routes", "primary-routes.json"),
        ("deep_dive_triggers", "deep-dive-triggers.json"),
        ("module_sequence", "module-sequence.json"),
    ]:
        path = branching_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing branching config: {path}")
        with open(path, encoding="utf-8") as f:
            config[key] = json.load(f)

    return config


def evaluate_primary_route(screening_responses: list[dict[str, Any]]) -> dict[str, Any]:
    """Determine the writer-type branch from screening question responses.

    Args:
        screening_responses: List of dicts, each with at least
            ``{"question_id": "M01-Q05", "response": "business"}`` shape.
            The ``response`` value for M01-Q05 supplies the writer_context.
            Responses to M01-Q10 / M01-Q04 may supply experience_level
            (numeric 1-7).

    Returns:
        Dict with keys: writer_type, branch_path, activated_modules, description.
        Falls back to the default branch when no conditions match.
    """
    config = load_branching_config()
    routes = config["primary_routes"]

    # Index responses by question_id for quick lookup.
    by_id: dict[str, Any] = {}
    for resp in screening_responses:
        qid = resp.get("question_id")
        if qid:
            by_id[qid] = resp

    # Extract writer_context from M01-Q05.
    writer_context_raw = ""
    if "M01-Q05" in by_id:
        writer_context_raw = str(by_id["M01-Q05"].get("response", "")).strip().lower()

    # Extract experience_level from M01-Q10 (primary) or M01-Q04 (fallback).
    experience_level: float | None = None
    for qid in ("M01-Q10", "M01-Q04"):
        if qid in by_id:
            try:
                experience_level = float(by_id[qid].get("response", 0))
            except (TypeError, ValueError):
                pass
            if experience_level is not None:
                break

    # Walk evaluation_order; first match wins.
    branches = routes["branches"]
    eval_order: list[str] = routes.get("evaluation_order", list(branches.keys()))

    for branch_name in eval_order:
        branch = branches[branch_name]
        conditions = branch["conditions"]

        # Check writer_context match.
        allowed_contexts: list[str] = conditions.get("writer_context", [])
        if writer_context_raw not in allowed_contexts:
            continue

        # Check experience_level_min if specified.
        min_exp = conditions.get("experience_level_min")
        if min_exp is not None:
            if experience_level is None or experience_level < min_exp:
                continue

        return {
            "writer_type": branch_name,
            "branch_path": ["core", branch_name],
            "activated_modules": branch["activated_modules"],
            "description": branch["description"],
        }

    # No match — fall back to default branch.
    default_name: str = routes.get("default_branch", "personal_journalistic")
    default_branch = branches[default_name]
    return {
        "writer_type": default_name,
        "branch_path": ["core", default_name],
        "activated_modules": default_branch["activated_modules"],
        "description": default_branch["description"],
    }


def get_module_sequence(writer_type: str) -> list[dict[str, Any]]:
    """Return the ordered list of modules to administer for a writer type.

    Each entry:
        {"module_id": "M01", "phase": 1, "is_core": True, "is_active": True}

    Core modules are always active.  Branch-activated modules are active only
    when they appear in the branch's ``activated_modules`` list.
    """
    config = load_branching_config()
    routes = config["primary_routes"]
    seq = config["module_sequence"]

    core_modules: set[str] = set(seq.get("core_modules", []))

    # Determine which branch-activated modules are active for this writer type.
    branch = routes["branches"].get(writer_type)
    activated: set[str] = set(branch["activated_modules"]) if branch else set()

    result: list[dict[str, Any]] = []
    for phase_info in seq["phases"]:
        phase_num = phase_info["phase"]
        for mod_id in phase_info["modules"]:
            is_core = mod_id in core_modules
            is_active = is_core or mod_id in activated
            result.append({
                "module_id": mod_id,
                "phase": phase_num,
                "is_core": is_core,
                "is_active": is_active,
            })

    return result


def check_deep_dive_triggers(
    current_module: str,
    _responses: list[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, Any] | None:
    """Check whether any deep-dive trigger fires for the current module.

    Args:
        current_module: Module ID currently being administered (e.g. "M03").
        _responses: List of response dicts collected so far (reserved for future triggers).
        state: Session state dict that may contain computed metrics such as:
            - ``semantic_differential.formal_casual`` (float)
            - ``narrativity_score`` (float, 0-100)
            - ``self_report_score`` (float)
            - ``projective_score`` (float)
            - ``consecutive_too_fast_responses`` (int)

    Returns:
        None if no trigger fires; otherwise a dict with keys:
            trigger_id, inject_questions, purpose.

    Triggers are evaluated in priority order:
        low_engagement_detector > self_perception_divergence >
        extreme_formality > high_narrative_tendency
    """
    config = load_branching_config()
    triggers = config["deep_dive_triggers"]["triggers"]

    # Priority order from config notes.
    priority_order = [
        "low_engagement_detector",
        "self_perception_divergence",
        "extreme_formality",
        "high_narrative_tendency",
    ]

    for trigger_id in priority_order:
        trigger = triggers.get(trigger_id)
        if trigger is None:
            continue

        source = trigger["source_module"]
        # "any" means it can fire on any module; otherwise must match current.
        if source != "any" and source != current_module:
            continue

        if _evaluate_trigger_condition(trigger, state):
            return {
                "trigger_id": trigger_id,
                "inject_questions": trigger["injected_items"],
                "purpose": trigger["description"],
            }

    return None


def _evaluate_trigger_condition(
    trigger: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    """Evaluate a single trigger's condition against the session state."""
    cond = trigger["condition"]
    metric = cond["metric"]
    operator = cond["operator"]
    threshold = cond["threshold"]

    value: float | None = None

    if metric == "semantic_differential":
        sd_pair = cond.get("sd_pair", "")
        sd_data = state.get("semantic_differential", {})
        raw = sd_data.get(sd_pair)
        if raw is not None:
            try:
                value = float(raw)
            except (TypeError, ValueError):
                pass

    elif metric == "narrativity_score":
        raw = state.get("narrativity_score")
        if raw is not None:
            try:
                value = float(raw)
            except (TypeError, ValueError):
                pass

    elif metric == "self_report_projective_delta":
        self_raw = state.get("self_report_score")
        proj_raw = state.get("projective_score")
        if self_raw is not None and proj_raw is not None:
            try:
                value = abs(float(self_raw) - float(proj_raw))
            except (TypeError, ValueError):
                pass

    elif metric == "consecutive_too_fast_responses":
        raw = state.get("consecutive_too_fast_responses")
        if raw is not None:
            try:
                value = float(raw)
            except (TypeError, ValueError):
                pass

    if value is None:
        return False

    return _compare(value, operator, threshold)


def _compare(value: float, operator: str, threshold: float) -> bool:
    """Apply a comparison operator."""
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    if operator == "==":
        return value == threshold
    if operator == "!=":
        return value != threshold
    raise ValueError(f"Unknown operator: {operator!r}")


def is_module_active(module_id: str, writer_type: str) -> bool:
    """Check if a module should be administered for the given writer type."""
    sequence = get_module_sequence(writer_type)
    for entry in sequence:
        if entry["module_id"] == module_id:
            return entry["is_active"]
    # Module not found in any phase — not active.
    return False


def get_engagement_reset_points() -> list[dict[str, Any]]:
    """Return the scheduled engagement reset points from module-sequence.json.

    Each entry: {"after_module": "M03", "type": "engagement_reset", ...}
    """
    config = load_branching_config()
    seq = config["module_sequence"]

    results: list[dict[str, Any]] = []
    for phase_info in seq["phases"]:
        for reset in phase_info.get("engagement_reset_points", []):
            # Normalise to a stable shape with after_module derived from position.
            position = reset.get("position", "")
            # Positions look like "between_M03_M04" or "after_M06".
            after_module = _extract_after_module(position, phase_info["modules"])
            results.append({
                "after_module": after_module,
                "type": reset.get("type", "engagement_reset"),
                "description": reset.get("description", ""),
                "position": position,
            })

    return results


def _extract_after_module(position: str, phase_modules: list[str]) -> str:
    """Parse the position string to determine which module the reset follows.

    Examples:
        "between_M03_M04" -> "M03"
        "after_M06"       -> "M06"
    """
    if position.startswith("after_"):
        return position.removeprefix("after_")
    if position.startswith("between_"):
        parts = position.removeprefix("between_").split("_")
        # First module in the pair is the one after which the reset occurs.
        if parts:
            return parts[0]
    # Fallback: last module in the phase.
    return phase_modules[-1] if phase_modules else ""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m lib.branching",
        description="Branching evaluator for the voice elicitation engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # evaluate-route
    er = sub.add_parser(
        "evaluate-route",
        help="Determine the writer-type branch from screening responses.",
    )
    er.add_argument(
        "--responses",
        required=True,
        help=(
            "JSON object mapping question IDs to response values, "
            'e.g. \'{"M01-Q05": "business", "M01-Q10": 5}\''
        ),
    )

    # module-sequence
    ms = sub.add_parser(
        "module-sequence",
        help="Print the module sequence for a writer type.",
    )
    ms.add_argument("--writer-type", required=True)

    # check-triggers
    ct = sub.add_parser(
        "check-triggers",
        help="Check deep-dive triggers for a module.",
    )
    ct.add_argument("--module", required=True, help="Current module ID (e.g. M03).")
    ct.add_argument(
        "--state",
        required=True,
        help="Path to a JSON file with session state metrics.",
    )
    ct.add_argument(
        "--responses",
        required=True,
        help="Path to a JSONL file with response records (one JSON object per line).",
    )

    return parser


def _cli_evaluate_route(args: argparse.Namespace) -> None:
    raw = json.loads(args.responses)
    # Convert flat {"M01-Q05": "business", ...} to list-of-dicts.
    if isinstance(raw, dict):
        responses = [
            {"question_id": qid, "response": val} for qid, val in raw.items()
        ]
    elif isinstance(raw, list):
        responses = raw
    else:
        print(json.dumps({"error": "responses must be a JSON object or array"}), file=sys.stderr)
        sys.exit(1)

    result = evaluate_primary_route(responses)
    print(json.dumps(result, indent=2))


def _cli_module_sequence(args: argparse.Namespace) -> None:
    result = get_module_sequence(args.writer_type)
    print(json.dumps(result, indent=2))


def _cli_check_triggers(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    if not state_path.exists():
        print(json.dumps({"error": f"State file not found: {state_path}"}), file=sys.stderr)
        sys.exit(1)
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    responses: list[dict[str, Any]] = []
    resp_path = Path(args.responses)
    if not resp_path.exists():
        print(json.dumps({"error": f"Responses file not found: {resp_path}"}), file=sys.stderr)
        sys.exit(1)
    with open(resp_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                responses.append(json.loads(line))

    result = check_deep_dive_triggers(args.module, responses, state)
    if result is None:
        print(json.dumps({"triggered": False}))
    else:
        result["triggered"] = True
        print(json.dumps(result, indent=2))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "evaluate-route": _cli_evaluate_route,
        "module-sequence": _cli_module_sequence,
        "check-triggers": _cli_check_triggers,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
