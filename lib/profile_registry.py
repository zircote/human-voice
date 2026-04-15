"""Multi-profile registry for the human-voice plugin.

Manages named voice profiles stored under ``$CLAUDE_PLUGIN_DATA/profiles/``.
Each profile is a directory containing ``profile.json`` and ``voice-prompt.txt``.
A ``registry.json`` file tracks all profiles, the active profile, and
directory-based overrides.

The top-level ``profile.json`` and ``voice-prompt.txt`` in the data directory
are kept as copies of the active profile for backward compatibility.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from lib.io import atomic_write_json, now_iso


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,46}[a-z0-9]$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _data_dir() -> Path:
    from lib.config import CONFIG_DIR
    return CONFIG_DIR


def _profiles_dir() -> Path:
    d = _data_dir() / "profiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _registry_path() -> Path:
    return _profiles_dir() / "registry.json"


# ---------------------------------------------------------------------------
# Slug validation
# ---------------------------------------------------------------------------


def validate_slug(slug: str) -> bool:
    """Return True if *slug* is a valid profile slug."""
    return bool(_SLUG_RE.match(slug))


def slugify(name: str) -> str:
    """Convert a display name to a valid slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if len(s) < 2:
        s = s + "-profile"
    if len(s) > 48:
        s = s[:48].rstrip("-")
    return s


# ---------------------------------------------------------------------------
# Registry CRUD
# ---------------------------------------------------------------------------


def _empty_registry() -> dict:
    return {"active": None, "directory_overrides": {}, "profiles": {}}


def load_registry() -> dict:
    """Load the registry, migrating from single-profile if needed."""
    path = _registry_path()
    if not path.exists():
        migrated = migrate_single_to_multi()
        if migrated:
            return json.loads(path.read_text())
        reg = _empty_registry()
        atomic_write_json(path, reg)
        return reg
    return json.loads(path.read_text())


def save_registry(registry: dict) -> Path:
    """Write the registry atomically."""
    path = _registry_path()
    atomic_write_json(path, registry)
    return path


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


def migrate_single_to_multi() -> str | None:
    """Migrate a single top-level profile into the multi-profile registry.

    Returns the slug of the migrated profile, or None if nothing to migrate.
    """
    data = _data_dir()
    profile_path = data / "profile.json"
    registry_path = _registry_path()

    if registry_path.exists() or not profile_path.exists():
        return None

    profile = json.loads(profile_path.read_text())

    # Derive slug from metadata or use "default"
    metadata = profile.get("metadata", {})
    session_id = metadata.get("session_id")
    writer_type = profile.get("voice_aspirations", {}).get(
        "most_distinctive_trait", ""
    )
    if writer_type:
        slug = slugify(writer_type.split(",")[0].strip())
    else:
        slug = "default"

    if not validate_slug(slug):
        slug = "default"

    # Create profile directory
    prof_dir = _profiles_dir() / slug
    prof_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(profile_path, prof_dir / "profile.json")

    # Copy voice-prompt.txt if it exists
    prompt_path = data / "voice-prompt.txt"
    if prompt_path.exists():
        shutil.copy2(prompt_path, prof_dir / "voice-prompt.txt")

    # Build registry
    now = now_iso()
    registry = {
        "active": slug,
        "directory_overrides": {},
        "profiles": {
            slug: {
                "slug": slug,
                "display_name": slug.replace("-", " ").title(),
                "origin": "interview",
                "session_id": session_id,
                "tags": ["default"],
                "created_at": metadata.get("timestamp", now),
                "updated_at": now,
            }
        },
    }
    atomic_write_json(registry_path, registry)
    return slug


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------


def list_profiles() -> list[dict]:
    """Return all profile entries from the registry."""
    reg = load_registry()
    active = reg.get("active")
    profiles = []
    for slug, entry in reg.get("profiles", {}).items():
        entry = dict(entry)
        entry["is_active"] = slug == active
        profiles.append(entry)
    return sorted(profiles, key=lambda p: p.get("created_at", ""))


def get_profile(slug: str) -> dict | None:
    """Load a profile.json by slug. Returns None if not found."""
    path = _profiles_dir() / slug / "profile.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def get_profile_prompt(slug: str) -> str | None:
    """Load a voice-prompt.txt by slug. Returns None if not found."""
    path = _profiles_dir() / slug / "voice-prompt.txt"
    if not path.exists():
        return None
    return path.read_text()


def get_profile_dir(slug: str) -> Path:
    """Return the directory path for a profile slug."""
    return _profiles_dir() / slug


def store_profile(
    slug: str,
    profile: dict,
    display_name: str,
    origin: str = "interview",
    session_id: str | None = None,
    tags: list[str] | None = None,
) -> Path:
    """Store a profile under the given slug.

    Creates the profile directory, writes profile.json and voice-prompt.txt,
    and adds an entry to the registry.

    Returns the profile directory path.
    """
    if not validate_slug(slug):
        raise ValueError(f"Invalid slug: {slug!r}")

    from lib.profile import format_profile_for_injection

    prof_dir = _profiles_dir() / slug
    prof_dir.mkdir(parents=True, exist_ok=True)

    atomic_write_json(prof_dir / "profile.json", profile)

    # Generate and write voice-prompt.txt
    injection = format_profile_for_injection(profile)
    prompt_path = prof_dir / "voice-prompt.txt"
    fd, tmp = tempfile.mkstemp(dir=prof_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(injection)
        os.replace(tmp, prompt_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    # Update registry
    reg = load_registry()
    now = now_iso()
    # Read existing entry BEFORE overwriting so we can preserve created_at
    existing = reg["profiles"].get(slug)
    reg["profiles"][slug] = {
        "slug": slug,
        "display_name": display_name,
        "origin": origin,
        "session_id": session_id,
        "tags": tags or [],
        "created_at": existing["created_at"] if existing and existing.get("created_at") else now,
        "updated_at": now,
    }

    save_registry(reg)
    return prof_dir


def delete_profile(slug: str) -> bool:
    """Delete a profile by slug. Returns True if deleted."""
    reg = load_registry()
    if slug not in reg.get("profiles", {}):
        return False

    if reg.get("active") == slug:
        raise ValueError(f"Cannot delete active profile: {slug!r}")

    del reg["profiles"][slug]

    # Remove from directory overrides
    reg["directory_overrides"] = {
        k: v for k, v in reg.get("directory_overrides", {}).items() if v != slug
    }

    save_registry(reg)

    # Remove directory
    prof_dir = _profiles_dir() / slug
    if prof_dir.exists():
        shutil.rmtree(prof_dir)

    return True


def rename_profile(old_slug: str, new_slug: str) -> bool:
    """Rename a profile. Returns True on success."""
    if not validate_slug(new_slug):
        raise ValueError(f"Invalid slug: {new_slug!r}")

    reg = load_registry()
    if old_slug not in reg.get("profiles", {}):
        return False
    if new_slug in reg.get("profiles", {}):
        raise ValueError(f"Profile already exists: {new_slug!r}")

    # Move directory
    old_dir = _profiles_dir() / old_slug
    new_dir = _profiles_dir() / new_slug
    if old_dir.exists():
        old_dir.rename(new_dir)

    # Update registry entry
    entry = reg["profiles"].pop(old_slug)
    entry["slug"] = new_slug
    entry["updated_at"] = now_iso()
    reg["profiles"][new_slug] = entry

    # Update active pointer
    if reg.get("active") == old_slug:
        reg["active"] = new_slug

    # Update directory overrides
    reg["directory_overrides"] = {
        k: (new_slug if v == old_slug else v)
        for k, v in reg.get("directory_overrides", {}).items()
    }

    save_registry(reg)

    # Re-activate if this was the active profile
    if reg.get("active") == new_slug:
        activate_profile(new_slug)

    return True


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------


def activate_profile(slug: str) -> Path:
    """Set *slug* as the active profile.

    Copies profile.json and voice-prompt.txt to the top-level data directory
    and updates the registry.

    Returns the path to the top-level profile.json.
    """
    reg = load_registry()
    if slug not in reg.get("profiles", {}):
        raise ValueError(f"Unknown profile: {slug!r}")

    prof_dir = _profiles_dir() / slug
    data = _data_dir()

    # Copy profile.json
    src_profile = prof_dir / "profile.json"
    if src_profile.exists():
        shutil.copy2(src_profile, data / "profile.json")

    # Copy voice-prompt.txt
    src_prompt = prof_dir / "voice-prompt.txt"
    if src_prompt.exists():
        shutil.copy2(src_prompt, data / "voice-prompt.txt")

    # Update registry
    reg["active"] = slug
    save_registry(reg)

    return data / "profile.json"


def get_active_slug() -> str | None:
    """Return the slug of the currently active profile."""
    reg = load_registry()
    return reg.get("active")


# ---------------------------------------------------------------------------
# Directory overrides
# ---------------------------------------------------------------------------


def resolve_directory_override(cwd: str) -> str | None:
    """Check if *cwd* matches any directory override pattern.

    Returns the matching profile slug, or None.
    """
    reg = load_registry()
    for pattern, slug in reg.get("directory_overrides", {}).items():
        if fnmatch.fnmatch(cwd, pattern):
            if slug in reg.get("profiles", {}):
                return slug
    return None


def resolve_active_profile(cwd: str | None = None) -> str | None:
    """Resolve which profile should be active for *cwd*.

    Checks directory overrides first, then falls back to the registry
    default. If the resolved profile differs from the current active,
    activates it.

    Returns the slug of the resolved profile.
    """
    if cwd:
        override = resolve_directory_override(cwd)
        if override:
            current = get_active_slug()
            if override != current:
                activate_profile(override)
            return override

    return get_active_slug()


def set_directory_override(pattern: str, slug: str) -> None:
    """Set a directory override: paths matching *pattern* use *slug*."""
    reg = load_registry()
    if slug not in reg.get("profiles", {}):
        raise ValueError(f"Unknown profile: {slug!r}")
    reg.setdefault("directory_overrides", {})[pattern] = slug
    save_registry(reg)


def remove_directory_override(pattern: str) -> None:
    """Remove a directory override."""
    reg = load_registry()
    reg.get("directory_overrides", {}).pop(pattern, None)
    save_registry(reg)


# ---------------------------------------------------------------------------
# Copilot export
# ---------------------------------------------------------------------------


def _render_profile_section(slug: str, profile: dict, display_name: str) -> str:
    """Render a single profile as a markdown section for copilot-instructions."""
    lines: list[str] = []
    lines.append(f"### {display_name} (`{slug}`)")
    lines.append("")

    identity = profile.get("identity_summary", "")
    if identity:
        lines.append(identity)
        lines.append("")

    dims = (profile.get("dimensions")
            or profile.get("gold_standard_dimensions")
            or profile.get("merged_dimensions") or {})
    if dims:
        lines.append("**Dimensions:**")
        for dim_name, dim_data in dims.items():
            if isinstance(dim_data, dict):
                score = dim_data.get("score", dim_data.get("composite", "?"))
                evidence = dim_data.get("evidence", "")
                label = dim_name.replace("_", " ").title()
                lines.append(f"- {label} ({score}): {evidence}")
            elif isinstance(dim_data, (int, float)):
                label = dim_name.replace("_", " ").title()
                lines.append(f"- {label}: {dim_data}")
        lines.append("")

    mechanics = profile.get("mechanics", {})
    if mechanics:
        lines.append("**Mechanics:**")
        for key, value in mechanics.items():
            label = key.replace("_", " ").title()
            lines.append(f"- {label}: {value}")
        lines.append("")

    features = profile.get("distinctive_features", [])
    if features:
        lines.append("**Distinctive Features:**")
        for feat in features:
            if isinstance(feat, dict):
                lines.append(f"- {feat.get('description', feat.get('feature', str(feat)))}")
            else:
                lines.append(f"- {feat}")
        lines.append("")

    aspirations = profile.get("voice_aspirations", {})
    rejected = aspirations.get("rejected_qualities", [])
    if rejected:
        lines.append("**Anti-Patterns (Never Do These):**")
        for r in rejected:
            lines.append(f"- No {r} language or tone")
        lines.append("")

    return "\n".join(lines)


def install_to_repo(
    slugs: list[str],
    repo_path: str,
    default_slug: str | None = None,
    labels: dict[str, str] | None = None,
) -> Path:
    """Install voice profiles into a repo as copilot-instructions.md.

    Generates a single ``.github/copilot-instructions.md`` containing all
    specified profiles with routing logic.  Copilot reads this file and
    applies the matching profile based on issue labels, PR labels, or an
    explicit ``voice: {slug}`` instruction in the prompt.

    Args:
        slugs: Profile slugs to install.
        repo_path: Path to the target repository root.
        default_slug: Which profile is the default. If None, uses the first slug.
        labels: Optional mapping of slug to routing label/description.
            Example: ``{"tech-authority": "design docs, RFCs, postmortems"}``

    Returns:
        Path to the written copilot-instructions.md.
    """
    if not slugs:
        raise ValueError("At least one profile slug is required")

    default = default_slug or slugs[0]
    if default not in slugs:
        raise ValueError(f"Default slug {default!r} not in slugs list")

    reg = load_registry()

    # Render header with routing logic
    lines: list[str] = []
    lines.append("# Voice Instructions")
    lines.append("")
    lines.append("These are the voice profiles for content generated in this repository.")
    lines.append("Apply the matching profile precisely. Follow its dimensions, mechanics,")
    lines.append("distinctive features, and anti-patterns throughout all content.")
    lines.append("")
    lines.append("## Profile Selection")
    lines.append("")
    lines.append(f"**Default profile: `{default}`** — use this unless a different profile is specified.")
    lines.append("")
    lines.append("To select a different profile:")
    lines.append("- Add a label `voice:{slug}` to the issue or PR")
    lines.append("- Include `voice: {slug}` in the issue body or PR description")
    lines.append("- Or instruct directly: \"use the {slug} voice profile\"")
    lines.append("")

    if len(slugs) > 1:
        lines.append("| Profile | When to Use |")
        lines.append("|---------|-------------|")
        for slug in slugs:
            entry = reg.get("profiles", {}).get(slug, {})
            display = entry.get("display_name", slug.replace("-", " ").title())
            label = (labels or {}).get(slug, ", ".join(entry.get("tags", [])))
            marker = " **(default)**" if slug == default else ""
            lines.append(f"| `{slug}` | {label}{marker} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Render each profile
    for slug in slugs:
        profile = get_profile(slug)
        if profile is None:
            raise FileNotFoundError(f"Profile not found: {slug!r}")
        entry = reg.get("profiles", {}).get(slug, {})
        display = entry.get("display_name", slug.replace("-", " ").title())
        lines.append(_render_profile_section(slug, profile, display))
        lines.append("---")
        lines.append("")

    github_dir = Path(repo_path) / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    target = github_dir / "copilot-instructions.md"
    voice_block = "\n".join(lines)

    _MARKER_START = "<!-- voice-profiles:start -->"
    _MARKER_END = "<!-- voice-profiles:end -->"

    if target.exists():
        existing = target.read_text()
        # Replace existing voice block if present, otherwise prepend
        if _MARKER_START in existing:
            before = existing[: existing.index(_MARKER_START)]
            after_marker = existing[existing.index(_MARKER_END) + len(_MARKER_END) :]
            target.write_text(
                before + _MARKER_START + "\n" + voice_block + "\n" + _MARKER_END + after_marker
            )
        else:
            # Prepend voice block before existing content
            target.write_text(
                _MARKER_START + "\n" + voice_block + "\n" + _MARKER_END + "\n\n" + existing
            )
    else:
        target.write_text(_MARKER_START + "\n" + voice_block + "\n" + _MARKER_END + "\n")

    # Clean up stale single-file export if present
    stale = github_dir / "voice-profile.md"
    if stale.exists():
        stale.unlink()

    # Clean up old voice-profiles directory if present
    old_dir = github_dir / "voice-profiles"
    if old_dir.exists():
        shutil.rmtree(old_dir)

    return target


# Backward-compatible alias
def export_for_copilot(slug: str, repo_path: str) -> Path:
    """Export a single profile. Delegates to install_to_repo."""
    return install_to_repo([slug], repo_path, default_slug=slug)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m lib.profile_registry",
        description="Voice profile registry management",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all profiles")

    act = sub.add_parser("activate", help="Activate a profile")
    act.add_argument("slug", help="Profile slug to activate")

    info = sub.add_parser("info", help="Show profile details")
    info.add_argument("slug", help="Profile slug")

    rm = sub.add_parser("delete", help="Delete a profile")
    rm.add_argument("slug", help="Profile slug to delete")

    exp = sub.add_parser("install", help="Install profiles to a repo as copilot-instructions.md")
    exp.add_argument("slugs", nargs="+", help="Profile slugs to install")
    exp.add_argument("--to-repo", required=True, help="Target repo path")
    exp.add_argument("--default", dest="default_slug", help="Default profile slug")

    # Keep old name as alias
    exp_alias = sub.add_parser("export", help="Install a profile to a repo (alias for install)")
    exp_alias.add_argument("slug", help="Profile slug")
    exp_alias.add_argument("--to-repo", required=True, help="Target repo path")

    ov = sub.add_parser("set-override", help="Set directory override")
    ov.add_argument("pattern", help="Glob pattern for directory")
    ov.add_argument("slug", help="Profile slug")

    rov = sub.add_parser("remove-override", help="Remove directory override")
    rov.add_argument("pattern", help="Glob pattern to remove")

    sub.add_parser("migrate", help="Migrate single profile to multi-profile")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            profiles = list_profiles()
            if not profiles:
                print("No profiles found.")
                return
            for p in profiles:
                marker = " *" if p.get("is_active") else "  "
                print(
                    f"{marker} {p['slug']:<30} {p.get('origin', '?'):<12} "
                    f"{', '.join(p.get('tags', []))}"
                )

        elif args.command == "activate":
            path = activate_profile(args.slug)
            print(f"Activated: {args.slug} -> {path}")

        elif args.command == "info":
            reg = load_registry()
            entry = reg.get("profiles", {}).get(args.slug)
            if not entry:
                print(f"Profile not found: {args.slug}", file=sys.stderr)
                sys.exit(1)
            json.dump(entry, sys.stdout, indent=2)
            print()

        elif args.command == "delete":
            delete_profile(args.slug)
            print(f"Deleted: {args.slug}")

        elif args.command == "install":
            path = install_to_repo(args.slugs, args.to_repo, default_slug=args.default_slug)
            print(f"Installed {len(args.slugs)} profile(s) to: {path}")

        elif args.command == "export":
            path = export_for_copilot(args.slug, args.to_repo)
            print(f"Installed to: {path}")

        elif args.command == "set-override":
            set_directory_override(args.pattern, args.slug)
            print(f"Override set: {args.pattern} -> {args.slug}")

        elif args.command == "remove-override":
            remove_directory_override(args.pattern)
            print(f"Override removed: {args.pattern}")

        elif args.command == "migrate":
            slug = migrate_single_to_multi()
            if slug:
                print(f"Migrated to: {slug}")
            else:
                print("Nothing to migrate.")

    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
