"""CLI entry point for the voice scoring engine.

Provides the ``score`` command which reads a completed session directory,
runs the full scoring pipeline, and writes results to scores/self-report.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from voice_scoring.self_report import score_self_report
from voice_scoring.semantic_differential import normalize_semantic_differentials
from voice_scoring.quality_checks import run_quality_checks
from voice_scoring.calibration import calibrate
from voice_scoring.profile_builder import build_profile


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


def _find_question_bank_dirs(session_dir: Path, metadata_dir: Path | None = None) -> list[Path]:
    """Build the list of candidate directories for question-bank discovery.

    Used by both ``_load_metadata`` (for scoring config files) and
    ``_load_question_bank`` (for question module JSON files).

    Search order:
      1. Explicit metadata_dir (from --metadata-dir flag)
      2. VOICE_QUESTION_BANK environment variable (or legacy MIVOCA_QUESTION_BANK)
      3. Walk up from session_dir looking for question-bank/
      4. Well-known fallback: $CLAUDE_PLUGIN_DATA/question-bank/
    """
    import os

    candidates: list[Path] = []

    if metadata_dir is not None:
        candidates.append(Path(metadata_dir).resolve())

    env_qb = os.environ.get("VOICE_QUESTION_BANK") or os.environ.get("MIVOCA_QUESTION_BANK")
    if env_qb:
        candidates.append(Path(env_qb).resolve())

    # Walk up from session_dir looking for question-bank/.
    project_root = session_dir
    for _ in range(5):
        project_root = project_root.parent
        qb = project_root / "question-bank"
        if qb.is_dir():
            candidates.append(qb)
            break

    # Well-known fallback.
    home_qb = Path.home() / ".human-voice" / "question-bank"
    if home_qb.is_dir():
        candidates.append(home_qb)

    return candidates


def _load_metadata(session_dir: Path, metadata_dir: Path | None = None) -> dict[str, Any]:
    """Load question-bank metadata files from the session directory or project root.

    Looks for:
      - dimension-item-mapping.json
      - scoring-weights.json
      - sd-dimension-mapping.json  (optional)
      - population-means.json      (optional)

    Uses ``_find_question_bank_dirs`` for discovery, plus session-local
    directories and ``scoring/`` subdirectories of each candidate.
    """
    # Build search candidates: session-local first, then shared discovery.
    candidates = [
        session_dir / "metadata",
        session_dir,
    ]
    qb_dirs = _find_question_bank_dirs(session_dir, metadata_dir=metadata_dir)
    for qb in qb_dirs:
        candidates.append(qb)
        qb_scoring = qb / "scoring"
        if qb_scoring.is_dir():
            candidates.append(qb_scoring)

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
                searched = [str(c) for c in candidates]
                print(
                    f"ERROR: required metadata file '{name}' not found.\n"
                    f"Searched: {searched}\n"
                    f"Hint: set VOICE_QUESTION_BANK=/path/to/question-bank "
                    f"or use --metadata-dir.",
                    file=sys.stderr,
                )
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


def _load_question_bank(candidates: list[Path]) -> dict[str, dict[str, Any]]:
    """Load question bank modules and build a {question_id: question_def} lookup.

    Searches candidate directories for a ``modules/`` subdirectory containing
    JSON question bank files (M01-*.json, M02-*.json, etc.).

    Returns a mapping from question_id to the full question definition dict,
    which includes ``type``, ``options``, and ``scoring_map``.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for base in candidates:
        modules_dir = base / "modules"
        if not modules_dir.is_dir():
            # Also check if base itself contains module files.
            modules_dir = base
        for fpath in sorted(list(modules_dir.glob("M*.json")) + list(modules_dir.glob("SD*.json"))):
            try:
                questions = _load_json(fpath)
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(questions, list):
                for q in questions:
                    qid = q.get("question_id")
                    if qid and qid not in lookup:
                        lookup[qid] = q
    return lookup


def cmd_score(args: argparse.Namespace) -> None:
    """Execute the full scoring pipeline for a session directory."""
    session_dir = Path(args.session_dir).resolve()
    metadata_dir = getattr(args, "metadata_dir", None)
    if metadata_dir is not None:
        metadata_dir = Path(metadata_dir).resolve()

    responses_path = session_dir / "responses.jsonl"
    if not responses_path.exists():
        print(f"ERROR: {responses_path} not found.", file=sys.stderr)
        sys.exit(1)

    responses = _load_jsonl(responses_path)
    metadata = _load_metadata(session_dir, metadata_dir=metadata_dir)

    dim_mapping = _flatten_dimension_mapping(metadata["dimension-item-mapping.json"])
    weights = _flatten_scoring_weights(metadata["scoring-weights.json"])
    sd_mapping_raw = metadata.get("sd-dimension-mapping.json")
    sd_mapping = sd_mapping_raw.get("mapping", sd_mapping_raw) if isinstance(sd_mapping_raw, dict) else sd_mapping_raw
    pop_means = metadata.get("population-means.json")

    # Load question bank for question metadata (type, options, scoring_map).
    # First try session-local questions.json, then load from question-bank modules.
    questions_path = session_dir / "questions.json"
    questions: list[dict[str, Any]] | None = None
    question_lookup: dict[str, dict[str, Any]] = {}
    if questions_path.exists():
        questions = _load_json(questions_path)
        if isinstance(questions, list):
            for q in questions:
                qid = q.get("question_id")
                if qid:
                    question_lookup[qid] = q
    if not question_lookup:
        qb_dirs = _find_question_bank_dirs(session_dir, metadata_dir=metadata_dir)
        question_lookup = _load_question_bank(qb_dirs)

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
        question_bank=question_lookup,
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
        prog="voice-scoring",
        description="Score voice self-report interview sessions.",
    )
    subparsers = parser.add_subparsers(dest="command")

    score_parser = subparsers.add_parser("score", help="Score a completed session.")
    score_parser.add_argument(
        "--session-dir",
        required=True,
        help="Path to the session directory containing responses.jsonl.",
    )
    score_parser.add_argument(
        "--metadata-dir",
        default=None,
        help="Path to question-bank directory containing scoring metadata. "
        "Overrides automatic discovery. Can also be set via "
        "VOICE_QUESTION_BANK environment variable.",
    )

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "score":
        cmd_score(args)


if __name__ == "__main__":
    main()
