"""CLI entry point for voice-nlp pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import spacy

from voice_nlp.pipeline import run_pipeline


def _load_model(model_name: str = "en_core_web_sm") -> spacy.language.Language:
    """Load a spaCy language model, with a clear error if missing."""
    try:
        return spacy.load(model_name)
    except OSError:
        print(
            f"spaCy model '{model_name}' not found. Install it with:\n"
            f"  python -m spacy download {model_name}",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze a single writing sample JSON file."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        sample = json.load(f)

    text = sample.get("raw_text", sample.get("text", sample.get("content", "")))
    if not text:
        print("No 'raw_text', 'text', or 'content' field found in input JSON.", file=sys.stderr)
        sys.exit(1)

    nlp = _load_model(args.model)
    result = run_pipeline(nlp, text)

    # Preserve metadata from input
    result["metadata"] = {
        "source_file": str(input_path),
        "prompt_id": sample.get("prompt_id"),
        "session_id": sample.get("session_id"),
    }

    output_path = Path(args.output) if args.output else input_path.with_suffix(".analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Analysis written to {output_path}")


def cmd_analyze_session(args: argparse.Namespace) -> None:
    """Analyze all writing sample JSON files in a session directory."""
    session_dir = Path(args.session_dir)
    if not session_dir.is_dir():
        print(f"Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    # Writing samples are stored in the writing-samples/ subdirectory
    ws_dir = session_dir / "writing-samples"
    if not ws_dir.is_dir():
        # Fall back to scanning session_dir directly
        ws_dir = session_dir
    sample_files = sorted(ws_dir.glob("*.json"))
    if not sample_files:
        print(f"No writing sample JSON files found in {ws_dir}", file=sys.stderr)
        sys.exit(1)

    nlp = _load_model(args.model)

    for sample_file in sample_files:
        # Skip files that are already analysis outputs
        if sample_file.name.endswith(".analysis.json"):
            continue

        with open(sample_file, "r", encoding="utf-8") as f:
            sample = json.load(f)

        text = sample.get("raw_text", sample.get("text", sample.get("content", "")))
        if not text:
            print(f"Skipping {sample_file.name}: no raw_text/text field", file=sys.stderr)
            continue

        result = run_pipeline(nlp, text)
        result["metadata"] = {
            "source_file": str(sample_file),
            "prompt_id": sample.get("prompt_id"),
            "session_id": sample.get("session_id"),
        }

        output_path = sample_file.with_suffix(".analysis.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"  {sample_file.name} -> {output_path.name}")

    print("Session analysis complete.")


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="voice-nlp",
        description="Stylometric analysis pipeline for writing samples.",
    )
    parser.add_argument(
        "--model",
        default="en_core_web_sm",
        help="spaCy model to use (default: en_core_web_sm)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze subcommand
    p_analyze = subparsers.add_parser("analyze", help="Analyze a single writing sample")
    p_analyze.add_argument("--input", "-i", required=True, help="Path to input JSON file")
    p_analyze.add_argument("--output", "-o", default=None, help="Path to output JSON file")
    p_analyze.set_defaults(func=cmd_analyze)

    # analyze-session subcommand
    p_session = subparsers.add_parser(
        "analyze-session", help="Analyze all samples in a session directory"
    )
    p_session.add_argument(
        "--session-dir", "-d", required=True, help="Path to session directory"
    )
    p_session.set_defaults(func=cmd_analyze_session)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
