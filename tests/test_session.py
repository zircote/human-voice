"""Tests for lib.session — session lifecycle management."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lib import session


@pytest.fixture(autouse=True)
def _isolate_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect all session storage to a temp directory."""
    fake_root = tmp_path / ".human-voice" / "sessions"
    fake_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session, "_sessions_root", lambda: fake_root)


# ---- create / load round-trip ------------------------------------------------


def test_create_session(tmp_path: Path) -> None:
    """create_session produces state.json and responses.jsonl with correct fields."""
    state = session.create_session()

    sid = state["session_id"]
    sdir = session.get_session_dir(sid)

    # Files exist
    assert (sdir / "state.json").exists()
    assert (sdir / "responses.jsonl").exists()
    assert (sdir / "writing-samples").is_dir()
    assert (sdir / "scores").is_dir()

    # Initial state has the required fields
    assert state["state"] == "init"
    assert state["writer_type"] is None
    assert state["branch_path"] == []
    assert state["current_module"] is None
    assert state["current_question_index"] == 0
    assert state["questions_answered"] == 0
    assert state["questions_remaining_estimate"] == 70
    assert state["elapsed_seconds"] == 0
    assert state["format_streak"] == {"current_type": None, "count": 0}
    assert "quality_flags" in state
    assert state["quality_flags"]["straightline_count"] == 0
    assert state["quality_flags"]["too_fast_count"] == 0
    assert state["created_at"] is not None
    assert state["updated_at"] is not None


def test_load_session() -> None:
    """Creating then loading a session preserves all fields."""
    state = session.create_session()
    loaded = session.load_session(state["session_id"])

    assert loaded == state


def test_load_session_missing_raises() -> None:
    """Loading a nonexistent session raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        session.load_session("nonexistent-uuid")


# ---- save (atomic) -----------------------------------------------------------


def test_save_session_atomic() -> None:
    """save_session writes updated state and bumps updated_at."""
    state = session.create_session()
    sid = state["session_id"]
    original_updated = state["updated_at"]

    # Small sleep so timestamps differ
    time.sleep(0.05)

    state["state"] = "in_progress"
    session.save_session(sid, state)

    reloaded = session.load_session(sid)
    assert reloaded["state"] == "in_progress"
    assert reloaded["updated_at"] > original_updated


# ---- list_sessions -----------------------------------------------------------


def test_list_sessions() -> None:
    """Two created sessions both appear, sorted by updated_at descending."""
    s1 = session.create_session()
    time.sleep(0.05)
    s2 = session.create_session()

    listing = session.list_sessions()
    ids = [s["id"] for s in listing]

    assert s1["session_id"] in ids
    assert s2["session_id"] in ids

    # Most recently updated first
    assert listing[0]["id"] == s2["session_id"]
    assert listing[1]["id"] == s1["session_id"]


# ---- pause / resume ----------------------------------------------------------


def test_pause_resume() -> None:
    """Pausing stores previous state; resuming restores it."""
    state = session.create_session()
    sid = state["session_id"]

    # Move to in_progress
    session.update_state_field(sid, state="in_progress")

    # Pause
    paused = session.pause_session(sid)
    assert paused["state"] == "paused"
    assert paused["previous_state"] == "in_progress"

    # Resume
    resumed = session.resume_session(sid)
    assert resumed["state"] == "in_progress"
    assert resumed["previous_state"] is None


def test_pause_idempotent() -> None:
    """Pausing an already-paused session is a no-op."""
    state = session.create_session()
    sid = state["session_id"]
    session.update_state_field(sid, state="in_progress")
    session.pause_session(sid)
    paused_again = session.pause_session(sid)
    assert paused_again["state"] == "paused"


def test_resume_not_paused_raises() -> None:
    """Resuming a non-paused session raises ValueError."""
    state = session.create_session()
    with pytest.raises(ValueError, match="not paused"):
        session.resume_session(state["session_id"])


# ---- record_response / load_responses ----------------------------------------


def test_record_response() -> None:
    """record_response appends to responses.jsonl and increments counters."""
    state = session.create_session()
    sid = state["session_id"]

    response = {
        "question_id": "M01-Q01",
        "value": "professional",
        "duration_ms": 5000,
        "quality_flags": {},
    }
    session.record_response(sid, response)

    responses = session.load_responses(sid)
    assert len(responses) == 1
    assert responses[0]["question_id"] == "M01-Q01"

    updated = session.load_session(sid)
    assert updated["questions_answered"] == 1
    assert updated["questions_remaining_estimate"] == 69


def test_record_response_quality_flags() -> None:
    """record_response increments quality counters from response flags."""
    state = session.create_session()
    sid = state["session_id"]

    response = {
        "question_id": "M02-Q01",
        "value": 4,
        "duration_ms": 500,
        "quality_flags": {
            "too_fast": True,
            "straightline_sequence": 5,
        },
    }
    session.record_response(sid, response)

    updated = session.load_session(sid)
    assert updated["quality_flags"]["too_fast_count"] == 1
    assert updated["quality_flags"]["straightline_count"] == 1


def test_record_probe_response_does_not_increment_counter() -> None:
    """Probe responses (with probe_of set) should not increment questions_answered."""
    state = session.create_session()
    sid = state["session_id"]

    # Record a primary response first
    primary = {
        "question_id": "M01-Q01",
        "value": "I write professionally",
        "duration_ms": 5000,
        "quality_flags": {},
    }
    session.record_response(sid, primary)

    updated = session.load_session(sid)
    assert updated["questions_answered"] == 1
    assert updated["questions_remaining_estimate"] == 69

    # Record a probe response for the same question
    probe = {
        "question_id": "M01-Q01",
        "probe_of": "M01-Q01",
        "probe_prompt": "Could you say more about that?",
        "probe_index": 1,
        "value": "I write technical documentation and internal memos",
        "raw_text": "I write technical documentation and internal memos",
        "duration_ms": 8000,
        "quality_flags": {},
    }
    session.record_response(sid, probe)

    updated = session.load_session(sid)
    assert updated["questions_answered"] == 1, "Probe should not increment questions_answered"
    assert updated["questions_remaining_estimate"] == 69, "Probe should not decrement remaining"

    # Both responses should be in responses.jsonl
    responses = session.load_responses(sid)
    assert len(responses) == 2
    assert responses[1]["probe_of"] == "M01-Q01"


# ---- save_writing_sample -----------------------------------------------------


def test_save_writing_sample() -> None:
    """save_writing_sample creates the JSON file in writing-samples/."""
    state = session.create_session()
    sid = state["session_id"]

    sample_data = {
        "sample_id": "sample-001",
        "prompt": "Describe your morning",
        "text": "I wake up and make coffee.",
        "word_count": 7,
    }
    session.save_writing_sample(sid, "sample-001", sample_data)

    sample_path = session.get_session_dir(sid) / "writing-samples" / "sample-001.json"
    assert sample_path.exists()

    with open(sample_path) as f:
        loaded = json.load(f)
    assert loaded["text"] == "I wake up and make coffee."
