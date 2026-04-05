"""CLI entry point for the mivoca scoring engine.

Provides the ``score`` command which reads a completed session directory,
runs the full scoring pipeline, and writes results to scores/self-report.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mivoca_scoring.self_report import score_self_report
from mivoca_scoring.semantic_differential import normalize_semantic_differentials
from mivoca_scoring.quality_checks import run_quality_checks
from mivoca_scoring.calibration import calibrate
from mivoca_scoring.profile_builder import build_profile


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSON-Lines file into a list of dicts."""
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _load_json(path: Path) -> Any:
    """Load a JSON file."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _load_metadata(session_dir: Path) -> dict[str, Any]:
    """Load question-bank metadata files from the session directory or project root.

    Looks for:
      - dimension-item-mapping.json
      - scoring-weights.json
      - sd-dimension-mapping.json  (optional)
      - population-means.json      (optional)

    Search order: session_dir/metadata/, session_dir/, project-root/question-bank/.
    """
    candidates = [
        session_dir / "metadata",
        session_dir,
    ]
    # Try to locate the project-level question-bank directory.
    project_root = session_dir
    for _ in range(5):
        project_root = project_root.parent
        qb = project_root / "question-bank"
        if qb.is_dir():
            candidates.append(qb)
            # Scoring config lives under question-bank/scoring/
            qb_scoring = qb / "scoring"
            if qb_scoring.is_dir():
                candidates.append(qb_scoring)
            break

    required = ["dimension-item-mapping.json", "scoring-weights.json"]
    optional = ["sd-dimension-mapping.json", "population-means.json"]

    meta: dict[str, Any] = {}
    for name in required + optional:
        for base in candidates:
            fpath = base / name
            if fpath.exists():
                meta[name] = _load_json(fpath)
                break
        else:
            if name in required:
                print(f"ERROR: required metadata file '{name}' not found.", file=sys.stderr)
                sys.exit(1)

    return meta


def _aggregate_nlp_analyses(session_dir: Path) -> dict[str, Any] | None:
    """Aggregate NLP analysis files from writing-samples/ into observed metrics.

    Reads all *.analysis.json files, averages composite scores, and returns
    a dict keyed by the metric names calibration expects.
    """
    ws_dir = session_dir / "writing-samples"
    if not ws_dir.is_dir():
        return None

    analysis_files = sorted(ws_dir.glob("*.analysis.json"))
    if not analysis_files:
        return None

    composites: list[dict[str, Any]] = []
    for af in analysis_files:
        data = _load_json(af)
        comp = data.get("composite", {})
        if comp:
            composites.append(comp)

    if not composites:
        return None

    def _avg(key: str) -> float:
        vals = [c[key] for c in composites if key in c]
        return sum(vals) / len(vals) if vals else 0.0

    observed = {
        "formality_f_score": _avg("formality_f_score"),
        "flesch_kincaid_grade": _avg("flesch_kincaid_grade"),
        "liwc_clout": _avg("clout"),
        "liwc_analytical": _avg("analytical_thinking"),
        "liwc_emotional_tone": _avg("emotional_tone"),
    }

    # Write aggregated observed.json for future use
    scores_dir = session_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    obs_path = scores_dir / "observed.json"
    with open(obs_path, "w", encoding="utf-8") as f:
        json.dump(observed, f, indent=2)

    return observed


def _flatten_dimension_mapping(raw: dict[str, Any]) -> dict[str, list[str]]:
    """Flatten nested dimension-item-mapping.json into {dim: [question_ids]}."""
    flat: dict[str, list[str]] = {}
    for section in ("gold_standard_dimensions", "gap_dimensions"):
        for dim, info in raw.get(section, {}).items():
            items: list[str] = []
            contributing = info.get("contributing_items", {})
            if isinstance(contributing, dict):
                for module_items in contributing.values():
                    if isinstance(module_items, list):
                        items.extend(module_items)
            flat[dim] = items
    return flat


def _flatten_scoring_weights(raw: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Flatten nested scoring-weights.json into {dim: {question_id: weight}}."""
    flat: dict[str, dict[str, float]] = {}
    for dim, info in raw.get("dimension_weights", {}).items():
        if isinstance(info, dict):
            flat[dim] = info.get("items", {})
        else:
            flat[dim] = {}
    return flat


def cmd_score(args: argparse.Namespace) -> None:
    """Execute the full scoring pipeline for a session directory."""
    session_dir = Path(args.session_dir).resolve()
    responses_path = session_dir / "responses.jsonl"
    if not responses_path.exists():
        print(f"ERROR: {responses_path} not found.", file=sys.stderr)
        sys.exit(1)

    responses = _load_jsonl(responses_path)
    metadata = _load_metadata(session_dir)

    dim_mapping = _flatten_dimension_mapping(metadata["dimension-item-mapping.json"])
    weights = _flatten_scoring_weights(metadata["scoring-weights.json"])
    sd_mapping = metadata.get("sd-dimension-mapping.json")
    pop_means = metadata.get("population-means.json")

    # Load question bank if available (for question metadata / types).
    questions_path = session_dir / "questions.json"
    questions: list[dict[str, Any]] | None = None
    if questions_path.exists():
        questions = _load_json(questions_path)

    # Load observed computational scores.
    # First try pre-aggregated scores/observed.json; if absent, aggregate
    # from NLP analysis files in writing-samples/*.analysis.json.
    observed_path = session_dir / "scores" / "observed.json"
    observed: dict[str, Any] | None = None
    if observed_path.exists():
        observed = _load_json(observed_path)
    else:
        observed = _aggregate_nlp_analyses(session_dir)

    # 1. Quality checks
    quality = run_quality_checks(responses, questions)

    # 2. Semantic differentials
    sd_scores = normalize_semantic_differentials(responses, sd_mapping)

    # 3. Self-report dimension scoring
    sr_scores = score_self_report(
        responses=responses,
        dimension_mapping=dim_mapping,
        scoring_weights=weights,
        sd_scores=sd_scores,
    )

    # 4. Calibration (if observed scores available)
    calibration_report: dict[str, Any] | None = None
    if observed:
        calibration_report = calibrate(sr_scores, observed)

    # 5. Merged profile
    profile = build_profile(
        sr_scores=sr_scores,
        observed=observed,
        calibration=calibration_report,
        population_means=pop_means,
        responses=responses,
        dimension_mapping=dim_mapping,
    )

    # Assemble output
    output = {
        "version": "0.1.0",
        "session_dir": str(session_dir),
        "quality": quality,
        "semantic_differentials": sd_scores,
        "self_report_scores": sr_scores,
        "calibration": calibration_report,
        "profile": profile,
    }

    scores_dir = session_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    out_path = scores_dir / "self-report.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"Scores written to {out_path}")
    if quality.get("pass") is False:
        print("WARNING: quality checks did not pass. Review quality flags.", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    """CLI main entry point."""
    parser = argparse.ArgumentParser(
        prog="mivoca-scoring",
        description="Score mivoca self-report interview sessions.",
    )
    subparsers = parser.add_subparsers(dest="command")

    score_parser = subparsers.add_parser("score", help="Score a completed session.")
    score_parser.add_argument(
        "--session-dir",
        required=True,
        help="Path to the session directory containing responses.jsonl.",
    )

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "score":
        cmd_score(args)


if __name__ == "__main__":
    main()
