"""Unified configuration loader for the human-voice plugin.

Manages $CLAUDE_PLUGIN_DATA/config.json — a single JSON file covering both
AI pattern detection and voice interview settings.

Usage as a module::

    from lib.config import load_config, get, save_config

    cfg = load_config()
    threshold = get("interview.quality.speed_threshold_ms")

CLI::

    python -m lib.config show          # print effective config
    python -m lib.config get KEY_PATH  # get specific value
    python -m lib.config reset         # write defaults
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from lib.io import atomic_write_json

_LEGACY_DIR = Path.home() / ".human-voice"


def _resolve_data_dir() -> Path:
    """Resolve the plugin data directory.

    Prefers ``CLAUDE_PLUGIN_DATA`` (set by Claude Code / Cowork runtime),
    falls back to ``~/.human-voice`` for standalone / development use.
    """
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env:
        return Path(env)
    return _LEGACY_DIR


def migrate_legacy_data() -> bool:
    """Copy data from ~/.human-voice to CLAUDE_PLUGIN_DATA if needed.

    Runs once: if the plugin data dir is not the legacy dir and the legacy
    dir has data that the plugin data dir lacks, copy it over.

    Returns True if migration occurred.
    """
    data_dir = _resolve_data_dir()
    if data_dir == _LEGACY_DIR:
        return False
    if not _LEGACY_DIR.is_dir():
        return False

    data_dir.mkdir(parents=True, exist_ok=True)
    migrated = False

    import shutil
    for item in _LEGACY_DIR.iterdir():
        target = data_dir / item.name
        if target.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
        migrated = True

    return migrated


def _config_dir() -> Path:
    """Return the plugin data directory, resolving lazily and caching in globals.

    Previously computed at import time. Lazy resolution allows tests to set
    ``CLAUDE_PLUGIN_DATA`` before first access.
    """
    d = globals().get("_CONFIG_DIR_CACHED")
    if d is None:
        d = _resolve_data_dir()
        globals()["_CONFIG_DIR_CACHED"] = d
    return d


def _config_path() -> Path:
    """Return the config.json path, resolving lazily."""
    return _config_dir() / "config.json"


def __getattr__(name: str):
    """Lazy resolution of CONFIG_DIR and CONFIG_PATH for external consumers.

    Supports ``from lib.config import CONFIG_DIR`` without import-time side effects.
    """
    if name == "CONFIG_DIR":
        return _config_dir()
    if name == "CONFIG_PATH":
        return _config_path()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_default_config() -> dict:
    """Return the full default configuration dict."""
    return {
        "detection": {
            "extensions": [".md", ".mdx", ".txt"],
            "content_directories": [],
            "ignore": [],
            "character_patterns": {
                "em_dash": True,
                "en_dash": True,
                "smart_quotes": True,
                "ellipsis": True,
                "emojis": True,
            },
            "language_patterns": {
                "buzzwords": True,
                "hedging": True,
                "filler": True,
                "meta_commentary": True,
            },
            "structural_patterns": {
                "list_addiction": True,
                "rule_of_three": True,
                "from_x_to_y": True,
            },
            "voice_patterns": {
                "passive_voice": True,
                "generic_analogies": True,
                "perfect_grammar": True,
            },
            "fix": {
                "dry_run_by_default": True,
                "backup_files": False,
                "report_format": "normal",
            },
            "output": {
                "verbosity": "normal",
                "format": "markdown",
                "show_line_numbers": True,
                "max_results_per_tier": 50,
            },
        },
        "interview": {
            "session_storage": str(_config_dir() / "sessions"),
            "total_estimated_minutes": 35,
            "estimated_questions": 70,
            "format_streak_limit": 5,
            "default_branch": "personal_journalistic",
            "quality": {
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
            },
            "attention_checks": {
                "min_checks_passed": 2,
                "confidence_penalty_per_failure": 0.1,
            },
            "scoring": {
                "dimension_sd_weight": 0.7,
                "sd_normalized_weight": 0.3,
                "min_cronbach_alpha": 0.60,
                "reliability_tiers": {
                    "tier_1": [
                        "formality",
                        "directness",
                        "conciseness",
                        "enthusiasm",
                        "technical_density",
                    ],
                    "tier_2": [
                        "humor",
                        "warmth",
                        "hedging",
                        "figurative_language",
                        "sentence_complexity",
                    ],
                },
            },
            "elicitation": {
                "enabled": True,
                "max_probes_per_question": 2,
                "eligible_types": [
                    "open_ended",
                    "writing_sample",
                    "process_narration",
                    "scenario",
                    "projective",
                ],
                "min_words_open_ended": 15,
                "min_words_writing_sample": 40,
                "min_words_scenario": 20,
                "vagueness_indicators": [
                    "I don't know",
                    "not sure",
                    "it depends",
                    "maybe",
                    "I guess",
                    "hard to say",
                    "no preference",
                ],
            },
            "deep_dives": {
                "max_per_session": 5,
                "time_budget_minutes": 3,
            },
            "profile": {
                "publish_to": str(_config_dir() / "profile.json"),
                "injection_to": str(_config_dir() / "voice-prompt.txt"),
                "profiles_dir": str(_config_dir() / "profiles"),
                "population_means": {
                    "formality_f_score": {"mean": 55.0, "sd": 10.0},
                    "flesch_kincaid_grade": {"mean": 10.0, "sd": 3.0},
                    "liwc_clout": {"mean": 55.0, "sd": 18.0},
                    "liwc_analytical": {"mean": 50.0, "sd": 20.0},
                    "liwc_emotional_tone": {"mean": 50.0, "sd": 20.0},
                    "avg_sentence_length": {"mean": 18.0, "sd": 5.0},
                    "type_token_ratio": {"mean": 0.65, "sd": 0.10},
                    "hedge_word_rate": {"mean": 0.02, "sd": 0.01},
                    "passive_voice_rate": {"mean": 0.08, "sd": 0.05},
                    "contraction_rate": {"mean": 0.04, "sd": 0.03},
                },
            },
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*.  Override values win.

    Returns a new dict — neither input is mutated.
    """
    merged = dict(base)
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = _deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged


def load_config() -> dict:
    """Load config from $CLAUDE_PLUGIN_DATA/config.json, deep-merging with defaults.

    If config.json doesn't exist, returns defaults.
    If config.json exists but is partial, fills missing keys from defaults.
    Uses deep merge — nested dicts merge recursively, not overwrite.
    """
    defaults = get_default_config()
    if not _config_path().is_file():
        return defaults
    with _config_path().open("r", encoding="utf-8") as fh:
        user_cfg = json.load(fh)
    return _deep_merge(defaults, user_cfg)


def save_config(config: dict) -> Path:
    """Write *config* to $CLAUDE_PLUGIN_DATA/config.json atomically.

    Returns the path written.
    """
    _config_dir().mkdir(parents=True, exist_ok=True)
    atomic_write_json(_config_path(), config)
    return _config_path()


def get(key_path: str, default: Any = None) -> Any:
    """Get a config value by dot-separated path.

    Example::

        get("interview.quality.speed_threshold_ms")  # -> 2000
    """
    cfg = load_config()
    parts = key_path.split(".")
    current: Any = cfg
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m lib.config",
        description="Human-voice configuration utility",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Print current effective config as JSON")

    get_parser = sub.add_parser("get", help="Get a specific config value")
    get_parser.add_argument(
        "key_path",
        help="Dot-separated key path (e.g. interview.quality.speed_threshold_ms)",
    )

    sub.add_parser("reset", help="Write defaults to config.json")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for ``python -m lib.config``."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "show":
        cfg = load_config()
        json.dump(cfg, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")

    elif args.command == "get":
        value = get(args.key_path)
        if value is None:
            print(f"Key not found: {args.key_path}", file=sys.stderr)
            sys.exit(1)
        if isinstance(value, (dict, list)):
            json.dump(value, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            print(value)

    elif args.command == "reset":
        path = save_config(get_default_config())
        print(f"Defaults written to {path}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
