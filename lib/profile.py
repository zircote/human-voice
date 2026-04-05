"""Voice profile persistence and formatting.

Manages the active voice profile at ~/.human-voice/profile.json and provides
formatting utilities for system prompt injection.

The active profile is the well-known location that hooks, agents, and other
tools read to get the user's current voice profile without needing a session
ID lookup.

Files written:
    ~/.human-voice/profile.json     — full voice profile JSON
    ~/.human-voice/voice-prompt.txt — compact injection text for LLM prompts
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


ACTIVE_PROFILE_DIR = Path.home() / ".human-voice"
ACTIVE_PROFILE_PATH = ACTIVE_PROFILE_DIR / "profile.json"
ACTIVE_INJECTION_PATH = ACTIVE_PROFILE_DIR / "voice-prompt.txt"


def publish_active_profile(profile: dict[str, Any]) -> Path:
    """Write the voice profile to ~/.human-voice/profile.json.

    Atomically writes the full profile and a compact voice-prompt.txt
    for direct system prompt injection.

    Args:
        profile: Complete voice profile dict.

    Returns:
        Path to the written profile.json.
    """
    ACTIVE_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Atomic write for profile.json
    fd, tmp = tempfile.mkstemp(dir=ACTIVE_PROFILE_DIR, suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        os.replace(tmp, ACTIVE_PROFILE_PATH)
    except BaseException:
        os.unlink(tmp)
        raise

    # Also write the compact injection text
    injection = format_profile_for_injection(profile)
    fd2, tmp2 = tempfile.mkstemp(dir=ACTIVE_PROFILE_DIR, suffix=".txt")
    try:
        with os.fdopen(fd2, "w", encoding="utf-8") as f:
            f.write(injection)
        os.replace(tmp2, ACTIVE_INJECTION_PATH)
    except BaseException:
        os.unlink(tmp2)
        raise

    return ACTIVE_PROFILE_PATH


def load_active_profile() -> dict[str, Any] | None:
    """Load the active voice profile from ~/.human-voice/profile.json.

    Returns None if no profile exists yet.
    """
    if ACTIVE_PROFILE_PATH.exists():
        with open(ACTIVE_PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_active_injection() -> str | None:
    """Load the compact voice prompt from ~/.human-voice/voice-prompt.txt.

    Returns None if no profile has been published yet.
    """
    if ACTIVE_INJECTION_PATH.exists():
        return ACTIVE_INJECTION_PATH.read_text(encoding="utf-8")
    return None


def format_profile_for_injection(
    profile: dict[str, Any],
    token_budget: int = 500,
) -> str:
    """Format a voice profile as a compact system prompt injection.

    Produces a concise text block that an LLM can use to match this writer's
    voice when generating content.

    Args:
        profile: Complete voice profile dict.
        token_budget: Approximate token limit for the injection text.

    Returns:
        A string suitable for injection into an LLM system prompt.
    """
    parts = []

    identity = profile.get("identity_summary", "")
    if identity:
        parts.append(f"Voice: {identity}")

    dimensions = profile.get("gold_standard_dimensions", profile.get("merged_dimensions", {}))
    if dimensions:
        dim_strs = []
        for dim, data in dimensions.items():
            if isinstance(data, dict):
                score = data.get("score", data.get("composite"))
                if score is not None:
                    dim_strs.append(f"{dim}={score}")
            elif isinstance(data, (int, float)):
                dim_strs.append(f"{dim}={data}")
        if dim_strs:
            parts.append(f"Dimensions: {', '.join(dim_strs)}")

    sd = profile.get("semantic_differential", {})
    if sd:
        extremes = []
        for pair, value in sd.items():
            if isinstance(value, (int, float)):
                if value <= 2.5:
                    poles = pair.split("_")
                    extremes.append(f"strongly {poles[0]}")
                elif value >= 5.5:
                    poles = pair.split("_")
                    extremes.append(f"strongly {poles[-1]}" if len(poles) > 1 else f"high {pair}")
        if extremes:
            parts.append(f"Strong tendencies: {', '.join(extremes[:5])}")

    distinctive = profile.get("distinctive_features", [])
    if distinctive:
        feat_strs = []
        for feat in distinctive[:5]:
            if isinstance(feat, dict):
                feat_strs.append(feat.get("description", str(feat)))
            else:
                feat_strs.append(str(feat))
        parts.append(f"Distinctive: {'; '.join(feat_strs)}")

    calibration = profile.get("calibration", {})
    blind_spots = calibration.get("blind_spots", [])
    if blind_spots:
        parts.append(f"Blind spots (writer underestimates): {', '.join(blind_spots[:3])}")

    text = "\n".join(parts)

    # Rough token estimate (4 chars per token)
    if len(text) > token_budget * 4:
        text = text[: token_budget * 4] + "..."

    return text
