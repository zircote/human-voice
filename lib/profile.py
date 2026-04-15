"""Voice profile persistence and formatting.

Manages the active voice profile at $CLAUDE_PLUGIN_DATA/profile.json and provides
formatting utilities for system prompt injection.

The active profile is the well-known location that hooks, agents, and other
tools read to get the user's current voice profile without needing a session
ID lookup.

Files written:
    $CLAUDE_PLUGIN_DATA/profile.json     — full voice profile JSON
    $CLAUDE_PLUGIN_DATA/voice-prompt.txt — compact injection text for LLM prompts
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _resolve_paths() -> tuple[Path, Path, Path]:
    """Resolve profile publish paths from config."""
    try:
        from lib.config import get, CONFIG_DIR
        pub = Path(get("interview.profile.publish_to", str(CONFIG_DIR / "profile.json"))).expanduser()
        inj = Path(get("interview.profile.injection_to", str(CONFIG_DIR / "voice-prompt.txt"))).expanduser()
    except ImportError:
        from lib.config import CONFIG_DIR
        pub = CONFIG_DIR / "profile.json"
        inj = CONFIG_DIR / "voice-prompt.txt"
    return pub.parent, pub, inj


_ACTIVE_PATHS_CACHED: tuple[Path, Path, Path] | None = None


def _active_paths() -> tuple[Path, Path, Path]:
    """Lazily resolve and cache active profile paths.

    Previously computed at import time via ``_resolve_paths()``.
    Lazy resolution avoids import-time side effects and improves testability.
    """
    global _ACTIVE_PATHS_CACHED
    if _ACTIVE_PATHS_CACHED is None:
        _ACTIVE_PATHS_CACHED = _resolve_paths()
    return _ACTIVE_PATHS_CACHED


def __getattr__(name: str):
    """Lazy resolution of ACTIVE_PROFILE_DIR/PATH/INJECTION_PATH for external consumers."""
    mapping = {
        "ACTIVE_PROFILE_DIR": 0,
        "ACTIVE_PROFILE_PATH": 1,
        "ACTIVE_INJECTION_PATH": 2,
    }
    if name in mapping:
        return _active_paths()[mapping[name]]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def publish_active_profile(
    profile: dict[str, Any],
    slug: str | None = None,
    display_name: str | None = None,
    origin: str = "interview",
    tags: list[str] | None = None,
) -> Path:
    """Write the voice profile to $CLAUDE_PLUGIN_DATA/profile.json.

    If *slug* is provided, the profile is also stored in the multi-profile
    registry under that name and activated.  If *slug* is None, the profile
    is written directly to the top-level path (backward-compatible behavior).

    Atomically writes the full profile and a compact voice-prompt.txt
    for direct system prompt injection.  Also marks the originating
    session as ``complete`` so that session-based lookups find it.

    Args:
        profile: Complete voice profile dict.
        slug: Optional profile slug for named storage.
        display_name: Human-readable name (defaults to slug titlecased).
        origin: How the profile was created (interview, designed, template, imported).
        tags: Optional tags for the profile.

    Returns:
        Path to the written profile.json.
    """
    session_id = (profile.get("metadata") or {}).get("session_id")

    # Named profile path: store in registry and activate
    if slug:
        from lib.profile_registry import store_profile, activate_profile
        name = display_name or slug.replace("-", " ").title()
        store_profile(slug, profile, name, origin, session_id, tags)
        activate_profile(slug)
        # Mark session complete
        if session_id:
            try:
                from lib.session import update_state_field
                update_state_field(session_id, state="complete")
            except (FileNotFoundError, ImportError):
                pass
        return _active_paths()[1]

    # Legacy path: write directly to top-level
    profile_dir, profile_path, injection_path = _active_paths()
    profile_dir.mkdir(parents=True, exist_ok=True)

    # Atomic write for profile.json
    fd, tmp = tempfile.mkstemp(dir=profile_dir, suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        os.replace(tmp, profile_path)
    except BaseException:
        os.unlink(tmp)
        raise

    # Also write the compact injection text
    injection = format_profile_for_injection(profile)
    fd2, tmp2 = tempfile.mkstemp(dir=profile_dir, suffix=".txt")
    try:
        with os.fdopen(fd2, "w", encoding="utf-8") as f:
            f.write(injection)
        os.replace(tmp2, injection_path)
    except BaseException:
        os.unlink(tmp2)
        raise

    # Mark session complete
    if session_id:
        try:
            from lib.session import update_state_field
            update_state_field(session_id, state="complete")
        except (FileNotFoundError, ImportError):
            pass

    return profile_path


def load_active_profile() -> dict[str, Any] | None:
    """Load the active voice profile from $CLAUDE_PLUGIN_DATA/profile.json.

    Returns None if no profile exists yet.
    """
    profile_path = _active_paths()[1]
    if profile_path.exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_active_injection() -> str | None:
    """Load the compact voice prompt from $CLAUDE_PLUGIN_DATA/voice-prompt.txt.

    Returns None if no profile has been published yet.
    """
    injection_path = _active_paths()[2]
    if injection_path.exists():
        return injection_path.read_text(encoding="utf-8")
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

    calibration = profile.get("calibration") or {}
    blind_spots = calibration.get("blind_spots", [])
    if blind_spots:
        parts.append(f"Blind spots (writer underestimates): {', '.join(blind_spots[:3])}")

    text = "\n".join(parts)

    # Rough token estimate (4 chars per token)
    if len(text) > token_budget * 4:
        text = text[: token_budget * 4] + "..."

    return text
