"""Install voice profiles into a project's GitHub Copilot configuration.

Writes the full `.github/` surface that Copilot (code review, coding agent,
chat) reads:

- ``.github/copilot-instructions.md``     — repo-wide entry
- ``AGENTS.md``                           — root-level coding-agent instructions
- ``.github/instructions/*.instructions.md`` — path-scoped (applyTo globs)
- ``.github/prompts/*.prompt.md``         — reusable slash commands
- ``.github/agents/*.agent.md``           — custom-agent personas
- ``.github/human-voice/<slug>/``         — redacted profile artefacts
- ``.github/workflows/voice-review.yml``  — PR review workflow

Idempotent: re-runs replace content between
``<!-- human-voice:start -->`` / ``<!-- human-voice:end -->`` markers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lib.profile_registry import get_profile, get_profile_prompt, load_registry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MARKER_START = "<!-- human-voice:start -->"
MARKER_END = "<!-- human-voice:end -->"

OVERWRITE_ERROR = "error"
OVERWRITE_MERGE = "merge"
OVERWRITE_FORCE = "force"
_OVERWRITE_POLICIES = {OVERWRITE_ERROR, OVERWRITE_MERGE, OVERWRITE_FORCE}

# Default workflow path globs (answered 'PR only, narrow paths').
_WORKFLOW_PATHS = [
    "docs/**",
    "README*",
    "CHANGELOG*",
    "CONTRIBUTING*",
    "**/*.{md,mdx}",
]

# Fields to drop from profile.json when redacting for public-repo embedding.
_REDACT_DROP_TOP = {"metadata", "known_gaps"}
_REDACT_DROP_CALIBRATION = {"formality", "emotional_tone", "authority"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class InstallOptions:
    target: Path
    slugs: list[str]
    default_slug: str
    routing: list[tuple[str, str]] = field(default_factory=list)
    with_workflow: bool = True
    with_prompts: bool = True
    with_agent: bool = True
    with_agents_md: bool = True
    overwrite: str = OVERWRITE_MERGE
    dry_run: bool = False
    redact: bool = True

    def __post_init__(self) -> None:
        if self.overwrite not in _OVERWRITE_POLICIES:
            raise ValueError(
                f"overwrite must be one of {sorted(_OVERWRITE_POLICIES)}, got {self.overwrite!r}"
            )
        if not self.slugs:
            raise ValueError("At least one profile slug is required")
        if self.default_slug not in self.slugs:
            raise ValueError(f"default_slug {self.default_slug!r} not in slugs")
        for _glob, slug in self.routing:
            if slug not in self.slugs:
                raise ValueError(f"routing target {slug!r} not in installed slugs")


@dataclass
class InstallResult:
    written: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)
    would_write: dict[Path, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def parse_route(spec: str) -> list[tuple[str, str]]:
    """Parse a routing spec like 'docs/**=tech-authority;**/*.md=robert-allen'.

    Returns a list of (glob, slug) tuples preserving order.
    """
    if not spec:
        return []
    out: list[tuple[str, str]] = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"Invalid routing entry {chunk!r} (expected 'GLOB=SLUG')")
        glob, slug = chunk.split("=", 1)
        glob, slug = glob.strip(), slug.strip()
        if not glob or not slug:
            raise ValueError(f"Invalid routing entry {chunk!r}")
        out.append((glob, slug))
    return out


def _apply_to_for(slug: str, options: InstallOptions) -> str:
    """Resolve the applyTo glob(s) for a given profile slug."""
    matches = [glob for (glob, s) in options.routing if s == slug]
    if not matches:
        if slug == options.default_slug:
            return "**/*.{md,mdx,txt}"
        return f"**/.human-voice-unrouted-{slug}/**"
    if len(matches) == 1:
        return matches[0]
    return "{" + ",".join(matches) + "}"


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def redact_profile(profile: dict) -> dict:
    """Return a repo-safe copy of the profile JSON.

    Drops metadata (session_id, notes) and known_gaps. Trims calibration to
    its ``summary`` field only, dropping per-dimension self-vs-observed deltas.
    Keeps dimensions, mechanics, distinctive_features, voice_aspirations,
    identity_summary — the signals Copilot actually needs to emulate the voice.
    """
    out: dict = {}
    for key, value in profile.items():
        if key in _REDACT_DROP_TOP:
            continue
        if key == "calibration" and isinstance(value, dict):
            out[key] = {k: v for k, v in value.items() if k not in _REDACT_DROP_CALIBRATION}
            continue
        out[key] = value
    return out


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _marker_wrap(body: str) -> str:
    return f"{MARKER_START}\n{body.rstrip()}\n{MARKER_END}\n"


def _merge_marker_block(existing: str, new_body: str) -> str:
    """Replace the marker block in *existing* with *new_body*, or append."""
    if MARKER_START in existing and MARKER_END in existing:
        before = existing[: existing.index(MARKER_START)]
        after = existing[existing.index(MARKER_END) + len(MARKER_END) :]
        return before.rstrip() + "\n\n" + _marker_wrap(new_body) + after.lstrip()
    sep = "\n\n" if existing.strip() else ""
    return existing.rstrip() + sep + _marker_wrap(new_body)


def render_copilot_instructions(options: InstallOptions, prompts: dict[str, str]) -> str:
    """Render the repo-wide .github/copilot-instructions.md body."""
    lines: list[str] = []
    lines.append("# Human-Voice Instructions for GitHub Copilot")
    lines.append("")
    lines.append(
        "This repository uses the [human-voice](https://github.com/zircote/human-voice) "
        "plugin to enforce authentic writing-voice rules. Copilot code review, the "
        "Copilot coding agent, and Copilot Chat should apply these rules whenever they "
        "generate prose, documentation, PR descriptions, commit messages, or issue content."
    )
    lines.append("")
    lines.append("## Active profiles")
    lines.append("")

    reg = load_registry()
    if len(options.slugs) == 1:
        slug = options.slugs[0]
        entry = reg.get("profiles", {}).get(slug, {})
        display = entry.get("display_name", slug.replace("-", " ").title())
        lines.append(f"Single profile: **{display}** (`{slug}`). Apply it to all generated prose.")
    else:
        lines.append("| Profile | Slug | Applies to | Default |")
        lines.append("|---|---|---|---|")
        for slug in options.slugs:
            entry = reg.get("profiles", {}).get(slug, {})
            display = entry.get("display_name", slug.replace("-", " ").title())
            apply_to = _apply_to_for(slug, options)
            mark = "Yes" if slug == options.default_slug else ""
            lines.append(f"| {display} | `{slug}` | `{apply_to}` | {mark} |")
    lines.append("")
    lines.append("Path-scoped composition on the GitHub cloud is driven by the `applyTo` frontmatter "
                 "in `.github/instructions/*.instructions.md`. For IDE users, enable the VS Code "
                 "setting `chat.includeReferencedInstructions` to also resolve the markdown links below.")
    lines.append("")

    lines.append("## Embedded voice rules")
    lines.append("")
    lines.append("The compact voice rules are inlined here so the rules reach the model even when "
                 "path-scoped composition or markdown-link following is not available.")
    lines.append("")
    for slug in options.slugs:
        entry = reg.get("profiles", {}).get(slug, {})
        display = entry.get("display_name", slug.replace("-", " ").title())
        body = prompts.get(slug, "").strip()
        if not body:
            continue
        lines.append(f"### {display} (`{slug}`)")
        lines.append("")
        lines.append("```")
        lines.append(body)
        lines.append("```")
        lines.append("")

    lines.append("## Companion files")
    lines.append("")
    lines.append("- Path-scoped rules:")
    for slug in options.slugs:
        lines.append(f"  - [`instructions/human-voice-{slug}.instructions.md`](instructions/human-voice-{slug}.instructions.md)")
    if options.with_prompts:
        lines.append("- Reusable prompts (slash commands in Copilot Chat):")
        lines.append("  - [`prompts/voice-review.prompt.md`](prompts/voice-review.prompt.md)")
        lines.append("  - [`prompts/voice-fix.prompt.md`](prompts/voice-fix.prompt.md)")
        lines.append("  - [`prompts/voice-draft.prompt.md`](prompts/voice-draft.prompt.md)")
    if options.with_agent:
        lines.append("- Custom agents:")
        for slug in options.slugs:
            lines.append(f"  - [`agents/human-voice-{slug}.agent.md`](agents/human-voice-{slug}.agent.md)")
    lines.append("- Redacted profile artefacts (machine-readable):")
    for slug in options.slugs:
        lines.append(f"  - [`human-voice/{slug}/profile.json`](human-voice/{slug}/profile.json)")
        lines.append(f"  - [`human-voice/{slug}/voice-prompt.txt`](human-voice/{slug}/voice-prompt.txt)")
    if options.with_workflow:
        lines.append("- PR review workflow: [`workflows/voice-review.yml`](workflows/voice-review.yml)")
    lines.append("")
    lines.append("## Core principles (apply to all profiles)")
    lines.append("")
    lines.append("- Avoid AI-giveaway patterns: em dashes (—), smart quotes, Unicode ellipsis, "
                 "buzzwords (delve, leverage, tapestry, testament), excessive hedging, rule-of-three "
                 "cadence, from-X-to-Y constructions, list-addiction when prose fits.")
    lines.append("- Match the active profile's formality, directness, conciseness, warmth, humour, "
                 "and technical density dimensions.")
    lines.append("- Honour the profile's mechanics (contractions, Oxford comma, punctuation style).")
    lines.append("- Never introduce generic analogies, meta-commentary, or self-referential filler.")
    lines.append("")

    return "\n".join(lines)


def render_agents_md(options: InstallOptions, prompts: dict[str, str]) -> str:
    """Render the root-level AGENTS.md (coding-agent focus)."""
    lines = [
        "# AGENTS.md",
        "",
        "Instructions for AI coding agents (including GitHub Copilot coding agent) operating in this repo.",
        "",
        "## Voice rules",
        "",
        "This repository enforces human-voice writing rules. When you generate prose "
        "(PR descriptions, commit messages, documentation, comments, issue bodies), apply "
        "the voice profile matching the file or the default profile. The full Copilot-specific "
        "guidance lives in [`.github/copilot-instructions.md`](.github/copilot-instructions.md).",
        "",
    ]
    if len(options.slugs) == 1:
        lines.append(f"Default profile: **`{options.default_slug}`**.")
    else:
        lines.append(f"Default profile: **`{options.default_slug}`**. Path-scoped routing:")
        lines.append("")
        for glob, slug in options.routing:
            lines.append(f"- `{glob}` → `{slug}`")
    lines.append("")
    lines.append("Compact rules (embedded so agents without filesystem access still see them):")
    lines.append("")
    for slug in options.slugs:
        body = prompts.get(slug, "").strip()
        if not body:
            continue
        lines.append(f"### `{slug}`")
        lines.append("")
        lines.append("```")
        lines.append(body)
        lines.append("```")
        lines.append("")
    lines.append("## General rules")
    lines.append("")
    lines.append("- Run repo tests before declaring work complete.")
    lines.append("- Prefer surgical edits; do not refactor adjacent unrelated code.")
    lines.append("- Keep commit messages in conventional-commit format; honour the active voice profile in the body.")
    return "\n".join(lines)


def render_instructions_file(
    slug: str, display: str, apply_to: str, prompt_body: str, exclude_agent: str | None = None
) -> str:
    """Render a path-scoped .github/instructions/human-voice-<slug>.instructions.md."""
    fm_lines = [f'applyTo: "{apply_to}"', f'description: "Human-voice rules for the {display} profile"']
    if exclude_agent:
        fm_lines.append(f'excludeAgent: "{exclude_agent}"')
    fm = "---\n" + "\n".join(fm_lines) + "\n---\n"
    body = [
        f"# Voice rules: {display} (`{slug}`)",
        "",
        "When generating or editing prose matching the path glob above, apply the rules below. "
        "These rules derive from a completed voice interview and stylometric analysis; do not "
        "substitute generic \"write clearly\" advice for them.",
        "",
        "```",
        prompt_body.strip(),
        "```",
        "",
        "## Anti-patterns to avoid",
        "",
        "- Em dashes (—), en dashes (– unless numeric range), smart quotes, Unicode ellipsis (…).",
        "- Emoji in prose (unless the profile explicitly allows).",
        "- Hedging filler: \"it's worth noting that\", \"navigating the landscape\", \"in today's fast-paced\".",
        "- Rule-of-three cadence (\"fast, reliable, and scalable\") and from-X-to-Y constructions.",
        "- Generic analogies (\"like a symphony\", \"like a well-oiled machine\").",
        "- Meta-commentary (\"This response will explore...\").",
        "- Reaching for lists when prose fits.",
        "",
        "## Companion artefacts",
        "",
        f"- Full profile (machine-readable): [`../human-voice/{slug}/profile.json`](../human-voice/{slug}/profile.json)",
        f"- Voice prompt (compact): [`../human-voice/{slug}/voice-prompt.txt`](../human-voice/{slug}/voice-prompt.txt)",
    ]
    return fm + "\n".join(body) + "\n"


def render_prompt_review(slugs: list[str]) -> str:
    fm = (
        "---\n"
        'description: "Review the current selection or file for AI-giveaway patterns and voice drift"\n'
        'mode: "ask"\n'
        "---\n"
    )
    body = [
        "# /voice-review",
        "",
        "Review the referenced content for AI-generated writing patterns and drift from the "
        "active human-voice profile. Use the companion artefacts under `.github/human-voice/<slug>/`.",
        "",
        "## Steps",
        "",
        "1. Identify which profile applies (default: `" + slugs[0] + "`; check `.github/copilot-instructions.md` for routing).",
        "2. Read the profile's `voice-prompt.txt` and `profile.json`.",
        "3. Scan for character restrictions: em dashes, smart quotes, Unicode ellipsis, emoji in prose.",
        "4. Scan for language patterns: AI-favoured buzzwords, hedging, filler, meta-commentary.",
        "5. Scan for structural patterns: list addiction, rule of three, from-X-to-Y, generic analogies.",
        "6. Compare dimension scores in the profile against the content's tone (formality, directness, conciseness, warmth, technical density).",
        "7. Return a prioritised findings list: High/Medium/Low severity with exact line citations and proposed rewrites.",
    ]
    return fm + "\n".join(body) + "\n"


def render_prompt_fix(slugs: list[str]) -> str:
    fm = (
        "---\n"
        'description: "Rewrite the selection to match the active human-voice profile"\n'
        'mode: "edit"\n'
        "---\n"
    )
    body = [
        "# /voice-fix",
        "",
        "Rewrite the referenced content to comply with the active human-voice profile. Preserve meaning; "
        "change voice, cadence, vocabulary, and mechanics. Do not introduce new facts.",
        "",
        "## Steps",
        "",
        "1. Identify the applicable profile (default: `" + slugs[0] + "`).",
        "2. Read `.github/human-voice/<slug>/voice-prompt.txt` and `profile.json`.",
        "3. Replace AI characters (em dashes → colon or period; smart quotes → straight; Unicode ellipsis → three periods).",
        "4. Remove AI buzzwords, hedging, filler; collapse rule-of-three cadence.",
        "5. Adjust formality, directness, conciseness to match the profile's dimension scores.",
        "6. Honour mechanics: contractions on/off, Oxford comma on/off, punctuation style.",
        "7. Return the rewritten text inline. Do not add a summary of changes unless asked.",
    ]
    return fm + "\n".join(body) + "\n"


def render_prompt_draft(slugs: list[str]) -> str:
    fm = (
        "---\n"
        'description: "Draft new content in the active human-voice profile"\n'
        'mode: "agent"\n'
        "---\n"
    )
    body = [
        "# /voice-draft",
        "",
        "Draft new content in the active human-voice profile. Do not use generic \"professional writing\" defaults.",
        "",
        "## Inputs",
        "",
        "- Topic or outline (from the user or referenced files).",
        "- Target profile (default: `" + slugs[0] + "`).",
        "- Output format (prose, PR description, commit body, issue, doc section).",
        "",
        "## Steps",
        "",
        "1. Load `.github/human-voice/<slug>/voice-prompt.txt` and `profile.json`.",
        "2. Draft in the profile's voice from the first sentence. Do not \"warm up\" with generic prose.",
        "3. Run an internal check before returning: any em dashes, smart quotes, Unicode ellipsis, buzzwords, rule-of-three, from-X-to-Y, meta-commentary? Rewrite if yes.",
        "4. Return only the drafted content. No preamble, no trailing summary.",
    ]
    return fm + "\n".join(body) + "\n"


def render_agent_file(slug: str, display: str, prompt_body: str) -> str:
    fm = (
        "---\n"
        f'description: "Write in the {display} human-voice profile"\n'
        'tools: []\n'
        "---\n"
    )
    body = [
        f"# {display} human-voice agent (`{slug}`)",
        "",
        "You are a writing assistant constrained to the " + display + " voice profile. "
        "Every response (prose, documentation, PR text, commit body, issue content) must comply with the rules below.",
        "",
        "## Voice rules (verbatim from the profile)",
        "",
        "```",
        prompt_body.strip(),
        "```",
        "",
        "## Operating mode",
        "",
        "- Default to prose, not lists, unless the user asks for a list.",
        "- No em dashes, smart quotes, Unicode ellipsis, or emoji in prose output.",
        "- No hedging filler, rule-of-three cadence, or generic analogies.",
        "- Match the profile's formality, directness, conciseness, warmth, humour, and technical-density scores.",
        "- If the user's request conflicts with the profile, follow the request but flag the conflict.",
    ]
    return fm + "\n".join(body) + "\n"


def render_workflow_yaml(options: InstallOptions) -> str:
    paths_yaml = "\n".join(f"      - '{p}'" for p in _WORKFLOW_PATHS)
    slug_list = ", ".join(options.slugs)
    return f"""# Generated by human-voice voice-copilot-install for profile(s): {slug_list}.
# Edit the marker block in .github/copilot-instructions.md to change voice rules;
# re-run voice-copilot-install to regenerate this file.
name: Human-voice review

"on":
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
{paths_yaml}

permissions:
  contents: read
  pull-requests: write

jobs:
  voice-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Identify changed prose files
        id: changed
        shell: bash
        run: |
          git fetch origin "${{{{ github.base_ref }}}}" --depth=1
          files=$(git diff --name-only \\
            "origin/${{{{ github.base_ref }}}}...HEAD" \\
            -- '*.md' '*.mdx' '*.txt' | tr '\\n' ' ')
          echo "files=$files" >> "$GITHUB_OUTPUT"
      - name: Run character-restriction validator
        if: steps.changed.outputs.files != ''
        shell: bash
        run: |
          node .github/human-voice/scripts/validate-character-restrictions.js \\
            ${{{{ steps.changed.outputs.files }}}} | tee voice-review.txt
      - name: Post PR comment
        if: steps.changed.outputs.files != '' && always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            if (!fs.existsSync('voice-review.txt')) return;
            const body = fs.readFileSync('voice-review.txt', 'utf8').trim();
            if (!body) return;
            await github.rest.issues.createComment({{
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: '<!-- human-voice:review -->\\n## Human-voice review\\n\\n```\\n' + body + '\\n```',
            }});
"""


# ---------------------------------------------------------------------------
# Filesystem write helpers
# ---------------------------------------------------------------------------


def _write_text(path: Path, content: str, options: InstallOptions, result: InstallResult,
                merge_markers: bool) -> None:
    """Write *content* to *path*, honouring the overwrite policy and dry-run."""
    if options.dry_run:
        result.would_write[path] = content
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        result.written.append(path)
        return

    if options.overwrite == OVERWRITE_ERROR:
        result.skipped.append((path, "already exists (overwrite=error)"))
        return

    if options.overwrite == OVERWRITE_FORCE:
        path.write_text(content, encoding="utf-8")
        result.written.append(path)
        return

    # merge
    if merge_markers:
        existing = path.read_text(encoding="utf-8")
        # Treat the generated file as one marker block.
        body = content
        if body.startswith(MARKER_START) and body.rstrip().endswith(MARKER_END):
            new_block = body.rstrip() + "\n"
            if MARKER_START in existing and MARKER_END in existing:
                before = existing[: existing.index(MARKER_START)].rstrip()
                after = existing[existing.index(MARKER_END) + len(MARKER_END) :].lstrip()
                before_sep = before + "\n\n" if before else ""
                after_sep = "\n" + after if after else ""
                merged = before_sep + new_block.rstrip() + "\n" + after_sep
            else:
                prefix = existing.rstrip()
                sep = "\n\n" if prefix else ""
                merged = prefix + sep + new_block
            if not merged.endswith("\n"):
                merged += "\n"
            path.write_text(merged, encoding="utf-8")
            result.written.append(path)
            return
        # Body is not already marker-wrapped; wrap then merge.
        merged = _merge_marker_block(existing, content)
        path.write_text(merged, encoding="utf-8")
        result.written.append(path)
        return

    # Non-mergeable file with overwrite=merge: preserve user's copy.
    result.skipped.append((path, "already exists; overwrite=merge only applies to markered files"))


def _write_marker_text(path: Path, body: str, options: InstallOptions,
                       result: InstallResult) -> None:
    _write_text(path, _marker_wrap(body), options, result, merge_markers=True)


# ---------------------------------------------------------------------------
# Installer
# ---------------------------------------------------------------------------


def install(options: InstallOptions) -> InstallResult:
    """Install voice profiles into ``options.target``."""
    result = InstallResult()

    # Pre-flight: load every profile + its prompt.
    profiles: dict[str, dict] = {}
    prompts: dict[str, str] = {}
    for slug in options.slugs:
        profile = get_profile(slug)
        if profile is None:
            raise FileNotFoundError(f"Profile not found: {slug!r}")
        profiles[slug] = profile
        prompts[slug] = get_profile_prompt(slug) or ""

    reg = load_registry()
    gh = options.target / ".github"

    # 1. Repo-wide instructions (markered).
    body = render_copilot_instructions(options, prompts)
    _write_marker_text(gh / "copilot-instructions.md", body, options, result)

    # 2. AGENTS.md at repo root (markered).
    if options.with_agents_md:
        body = render_agents_md(options, prompts)
        _write_marker_text(options.target / "AGENTS.md", body, options, result)

    # 3. Path-scoped instruction files (full overwrite — file is ours).
    for slug in options.slugs:
        entry = reg.get("profiles", {}).get(slug, {})
        display = entry.get("display_name", slug.replace("-", " ").title())
        apply_to = _apply_to_for(slug, options)
        content = render_instructions_file(slug, display, apply_to, prompts[slug])
        path = gh / "instructions" / f"human-voice-{slug}.instructions.md"
        _write_text(path, content, options, result, merge_markers=False)

    # 4. Prompts.
    if options.with_prompts:
        for name, fn in (
            ("voice-review.prompt.md", render_prompt_review),
            ("voice-fix.prompt.md", render_prompt_fix),
            ("voice-draft.prompt.md", render_prompt_draft),
        ):
            _write_text(gh / "prompts" / name, fn(options.slugs), options, result, merge_markers=False)

    # 5. Agents (one per profile).
    if options.with_agent:
        for slug in options.slugs:
            entry = reg.get("profiles", {}).get(slug, {})
            display = entry.get("display_name", slug.replace("-", " ").title())
            content = render_agent_file(slug, display, prompts[slug])
            _write_text(gh / "agents" / f"human-voice-{slug}.agent.md", content, options, result,
                        merge_markers=False)

    # 6. Embedded profile artefacts.
    for slug in options.slugs:
        data = redact_profile(profiles[slug]) if options.redact else profiles[slug]
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        _write_text(gh / "human-voice" / slug / "profile.json", payload, options, result,
                    merge_markers=False)
        _write_text(gh / "human-voice" / slug / "voice-prompt.txt", prompts[slug] + "\n", options,
                    result, merge_markers=False)

    # 7. Bundled validator scripts (copy from plugin repo).
    if options.with_workflow:
        plugin_root = Path(__file__).resolve().parent.parent
        scripts_src = plugin_root / "skills" / "human-voice" / "scripts"
        for name in ("validate-character-restrictions.js", "fix-character-restrictions.js"):
            src = scripts_src / name
            if src.is_file():
                content = src.read_text(encoding="utf-8")
                _write_text(gh / "human-voice" / "scripts" / name, content, options, result,
                            merge_markers=False)

        # 8. PR workflow.
        _write_text(gh / "workflows" / "voice-review.yml", render_workflow_yaml(options), options,
                    result, merge_markers=False)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_default_slug(slugs: list[str]) -> str:
    reg = load_registry()
    active = reg.get("active")
    if active and active in slugs:
        return active
    return slugs[0]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="voice-copilot-install",
        description="Install human-voice profiles into a repo's GitHub Copilot config.",
    )
    p.add_argument("--target", default=".", help="Target repo root (default: .)")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--profile", help="Single profile slug (default: active profile)")
    grp.add_argument("--profiles", help="Comma-separated profile slugs for multi-profile install")
    p.add_argument("--default", dest="default_slug",
                   help="Which installed slug is the default (only for --profiles)")
    p.add_argument("--route", default="",
                   help="Routing spec 'GLOB=SLUG;GLOB=SLUG' for multi-profile installs")
    p.add_argument("--no-workflow", dest="with_workflow", action="store_false")
    p.add_argument("--no-prompts", dest="with_prompts", action="store_false")
    p.add_argument("--no-agent", dest="with_agent", action="store_false")
    p.add_argument("--no-agents-md", dest="with_agents_md", action="store_false")
    p.add_argument("--no-redact", dest="redact", action="store_false",
                   help="Write the full profile.json including metadata and calibration details")
    p.add_argument("--overwrite", choices=sorted(_OVERWRITE_POLICIES), default=OVERWRITE_MERGE)
    p.add_argument("--dry-run", action="store_true")
    return p


def _resolve_slugs(args: argparse.Namespace) -> tuple[list[str], str]:
    if args.profiles:
        slugs = [s.strip() for s in args.profiles.split(",") if s.strip()]
    elif args.profile:
        slugs = [args.profile]
    else:
        reg = load_registry()
        active = reg.get("active")
        if not active:
            raise SystemExit("No --profile given and no active profile found")
        slugs = [active]
    default = args.default_slug or _resolve_default_slug(slugs)
    if default not in slugs:
        raise SystemExit(f"--default {default!r} is not in the installed slugs")
    return slugs, default


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    slugs, default = _resolve_slugs(args)
    options = InstallOptions(
        target=Path(args.target).resolve(),
        slugs=slugs,
        default_slug=default,
        routing=parse_route(args.route),
        with_workflow=args.with_workflow,
        with_prompts=args.with_prompts,
        with_agent=args.with_agent,
        with_agents_md=args.with_agents_md,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        redact=args.redact,
    )
    result = install(options)

    if options.dry_run:
        print("DRY RUN — would write:")
        for path in sorted(result.would_write):
            print(f"  {path}  ({len(result.would_write[path])} bytes)")
        return 0

    for path in result.written:
        print(f"wrote    {path}")
    for path, reason in result.skipped:
        print(f"skipped  {path}  ({reason})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
