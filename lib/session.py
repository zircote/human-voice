"""Session management for the Mivoca voice elicitation engine.

Handles the full lifecycle of an interview session including creation,
persistence, pause/resume, response recording, and writing sample storage.

Session storage layout:
    ~/.human-voice/sessions/{session_id}/
        state.json          -- current session state
        responses.jsonl     -- one JSON object per line, append-only
        writing-samples/    -- individual sample JSON files
        scores/             -- scoring artifacts
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sessions_root() -> Path:
    """Return the root directory for all sessions, creating it if needed."""
    root = Path.home() / ".human-voice" / "sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _now_iso() -> str:
    """Return the current time as an ISO-8601 string in UTC."""
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* atomically via temp-file + rename."""
    # Write to a temp file in the same directory so os.replace is atomic
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        # Clean up the temp file on any failure
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _initial_state(session_id: str) -> dict:
    """Return a fresh session-state dict conforming to session-state.schema.json."""
    now = _now_iso()
    return {
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "state": "init",
        "writer_type": None,
        "branch_path": [],
        "current_module": None,
        "current_question_index": 0,
        "questions_answered": 0,
        "questions_remaining_estimate": 70,
        "elapsed_seconds": 0,
        "format_streak": {"current_type": None, "count": 0},
        "quality_flags": {
            "straightline_count": 0,
            "too_fast_count": 0,
            "attention_checks_passed": 0,
            "attention_checks_total": 0,
            "engagement_resets_triggered": 0,
        },
        "module_progress": {},
        "deep_dives_triggered": [],
        "deep_dive_return": None,
        "previous_state": None,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_session_dir(session_id: str) -> Path:
    """Return the path to a session directory."""
    return _sessions_root() / session_id


def create_session() -> dict:
    """Create a new session.

    Generates a UUID, creates the on-disk directory structure, and
    initialises ``state.json`` and ``responses.jsonl``.

    Returns:
        The initial state dict.
    """
    session_id = str(uuid.uuid4())
    session_dir = get_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "writing-samples").mkdir(exist_ok=True)
    (session_dir / "scores").mkdir(exist_ok=True)

    state = _initial_state(session_id)
    _atomic_write_json(session_dir / "state.json", state)

    # Create an empty responses file
    (session_dir / "responses.jsonl").touch()

    return state


def load_session(session_id: str) -> dict:
    """Load session state from ``state.json``.

    Returns:
        The state dict.

    Raises:
        FileNotFoundError: If the session directory or state file does not exist.
    """
    state_path = get_session_dir(session_id) / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    with open(state_path) as f:
        return json.load(f)


def save_session(session_id: str, state: dict) -> None:
    """Atomically save *state* to the session's ``state.json``.

    The ``updated_at`` timestamp is refreshed automatically.
    """
    state["updated_at"] = _now_iso()
    _atomic_write_json(get_session_dir(session_id) / "state.json", state)


def list_sessions() -> list[dict]:
    """List all sessions with summary information.

    Returns a list of dicts containing:
        id, state, writer_type, questions_answered, created_at, updated_at

    Sorted by ``updated_at`` descending (most recently updated first).
    """
    root = _sessions_root()
    summaries: list[dict] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        state_path = entry / "state.json"
        if not state_path.exists():
            continue
        try:
            with open(state_path) as f:
                state = json.load(f)
            summaries.append(
                {
                    "id": state.get("session_id", entry.name),
                    "state": state.get("state"),
                    "writer_type": state.get("writer_type"),
                    "questions_answered": state.get("questions_answered", 0),
                    "created_at": state.get("created_at"),
                    "updated_at": state.get("updated_at"),
                }
            )
        except (json.JSONDecodeError, OSError):
            # Skip corrupted sessions
            continue

    summaries.sort(key=lambda s: s.get("updated_at") or "", reverse=True)
    return summaries


def pause_session(session_id: str) -> dict:
    """Pause a session.

    Stores the current state value in ``previous_state`` so that
    :func:`resume_session` can restore it, then sets ``state`` to
    ``"paused"``.

    Returns:
        The updated state dict.
    """
    state = load_session(session_id)
    if state["state"] == "paused":
        return state  # already paused, idempotent
    state["previous_state"] = state["state"]
    state["state"] = "paused"
    save_session(session_id, state)
    return state


def resume_session(session_id: str) -> dict:
    """Resume a paused session.

    Restores ``state`` from ``previous_state`` (set during
    :func:`pause_session`).

    Returns:
        The updated state dict.

    Raises:
        ValueError: If the session is not currently paused.
    """
    state = load_session(session_id)
    if state["state"] != "paused":
        raise ValueError(
            f"Session {session_id} is not paused (current state: {state['state']})"
        )
    previous = state.get("previous_state")
    if previous is None:
        previous = "init"
    state["state"] = previous
    state["previous_state"] = None
    save_session(session_id, state)
    return state


def record_response(session_id: str, response: dict) -> None:
    """Append a response to the session's ``responses.jsonl``.

    Each line in the file is a complete JSON object conforming to
    ``response.schema.json``.  Quality flags in the session state are
    updated based on the response's ``quality_flags`` and ``timing``.
    """
    session_dir = get_session_dir(session_id)
    responses_path = session_dir / "responses.jsonl"

    # Append the response (one JSON object per line)
    with open(responses_path, "a") as f:
        f.write(json.dumps(response))
        f.write("\n")

    # Update session quality flags from the response
    state = load_session(session_id)
    qf = state["quality_flags"]

    resp_qf = response.get("quality_flags", {})
    if resp_qf.get("too_fast"):
        qf["too_fast_count"] += 1
    # Support both flag formats: quality checker's "straightlining" (bool)
    # and schema's "straightline_sequence" (int count)
    if resp_qf.get("straightlining"):
        qf["straightline_count"] += 1
    elif resp_qf.get("straightline_sequence", 0) >= 3:
        qf["straightline_count"] += 1

    state["questions_answered"] = state.get("questions_answered", 0) + 1
    if state["questions_remaining_estimate"] > 0:
        state["questions_remaining_estimate"] -= 1

    save_session(session_id, state)


def load_responses(session_id: str) -> list[dict]:
    """Load all responses from the session's ``responses.jsonl``.

    Returns:
        A list of response dicts, one per recorded response.
    """
    responses_path = get_session_dir(session_id) / "responses.jsonl"
    if not responses_path.exists():
        return []
    responses: list[dict] = []
    with open(responses_path) as f:
        for line in f:
            line = line.strip()
            if line:
                responses.append(json.loads(line))
    return responses


def save_writing_sample(
    session_id: str, sample_id: str, sample_data: dict
) -> None:
    """Save a writing sample to ``writing-samples/{sample_id}.json``."""
    samples_dir = get_session_dir(session_id) / "writing-samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(samples_dir / f"{sample_id}.json", sample_data)


def update_state_field(session_id: str, **kwargs: Any) -> dict:
    """Load state, update the specified fields, save atomically, and return
    the updated state.

    Example::

        update_state_field(sid, state="in_progress", current_module="mod-01")
    """
    state = load_session(session_id)
    state.update(kwargs)
    save_session(session_id, state)
    return state


# ---------------------------------------------------------------------------
# CLI entry point — python -m lib.session <command> [args]
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m lib.session",
        description="Mivoca session management CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("create", help="Create a new session")

    load_p = sub.add_parser("load", help="Load a session by ID")
    load_p.add_argument("session_id", help="UUID of the session")

    sub.add_parser("list", help="List all sessions")

    pause_p = sub.add_parser("pause", help="Pause a session")
    pause_p.add_argument("session_id", help="UUID of the session")

    resume_p = sub.add_parser("resume", help="Resume a paused session")
    resume_p.add_argument("session_id", help="UUID of the session")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            result = create_session()
        elif args.command == "load":
            result = load_session(args.session_id)
        elif args.command == "list":
            result = list_sessions()
        elif args.command == "pause":
            result = pause_session(args.session_id)
        elif args.command == "resume":
            result = resume_session(args.session_id)
        else:
            parser.print_help()
            sys.exit(1)
    except FileNotFoundError as exc:
        json.dump({"error": str(exc)}, sys.stdout, indent=2)
        print()
        sys.exit(1)
    except ValueError as exc:
        json.dump({"error": str(exc)}, sys.stdout, indent=2)
        print()
        sys.exit(1)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
