# Changelog

All notable changes to the Human Voice plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.1] - 2026-04-22

### Fixed

- `voice-copilot-install` defaulted `--target=.` to the plugin root because the
  bash wrapper did `cd "$PLUGIN_ROOT"` before exec. Removed the chdir; PYTHONPATH
  already lets Python import `lib.*` from anywhere, and `.` now correctly
  resolves to the user's cwd.

## [0.8.0] - 2026-04-22

### Added

- **`/human-voice:voice-copilot-install` command** (CLI: `bin/voice-copilot-install`)
  — installs one or more voice profiles into a target project's GitHub Copilot
  configuration. Writes the full surface so Copilot (code review, coding agent,
  Chat) applies the voice automatically:
  - `.github/copilot-instructions.md` (repo-wide, marker-idempotent)
  - `AGENTS.md` at repo root (coding-agent focus, marker-idempotent)
  - `.github/instructions/human-voice-<slug>.instructions.md` with `applyTo`
    globs (one per profile; path-scoped routing)
  - `.github/prompts/voice-{review,fix,draft}.prompt.md` (Copilot Chat slash
    commands)
  - `.github/agents/human-voice-<slug>.agent.md` (Copilot custom agents)
  - `.github/human-voice/<slug>/profile.json` (redacted) +
    `voice-prompt.txt`
  - `.github/human-voice/scripts/*.js` (bundled character-restriction
    validators)
  - `.github/workflows/voice-review.yml` (PR workflow that runs the validator
    and posts findings as a PR comment; triggers on `docs/**`, `README*`,
    `CHANGELOG*`, `CONTRIBUTING*`, `**/*.{md,mdx}`)
- Multi-profile install with `--profiles a,b --route 'GLOB=SLUG;...'` routing.
- Idempotent merge semantics via `<!-- human-voice:start -->` /
  `<!-- human-voice:end -->` markers — re-running never clobbers user content.
- Profile redaction by default (drops `metadata`, `known_gaps`, trims
  `calibration` to summary) so public repos don't leak session notes. Pass
  `--no-redact` to opt out.
- Overwrite policies: `merge` (default), `force`, `error`.
- `--dry-run` mode that prints intended writes without touching the filesystem.
- 21 new tests under `tests/test_copilot_install.py` covering redaction,
  routing, single/multi-profile install, overwrite policies, idempotency, and
  dry-run.

### Changed

- Expanded `docs/guides/copilot-integration.md` to document the new installer
  alongside the existing minimal-export flow.

## [0.7.0] - 2026-04-22

### Changed

- **Single canonical data directory.** All plugin data (profiles, sessions,
  config, voice-prompt.txt, observer-protocol.md) now lives in
  `~/.human-voice/` unconditionally. `CLAUDE_PLUGIN_DATA` and any other env
  var are ignored by the resolver. Rationale: users with multiple Claude
  accounts and differing `~/.claude*` directories want exactly one place for
  voice data. Skills, commands, agents, hooks, and setup script all point at
  `~/.human-voice/` directly.
- `lib.config.migrate_legacy_data` is now a no-op shim retained only for
  backward-compatible callers.

### Removed

- Env-var based data-directory resolution. The short-lived `HUMAN_VOICE_DATA_DIR`
  override (introduced in 0.6.0 but never released) is also removed — there is
  no escape hatch by design.
- `.human-voice-plugin` marker / stamping (no longer needed with a single
  fixed location).

## [0.5.0] - 2026-04-15

### Fixed

- **Auto-load config and profile**: `voice-review`, `voice-fix`, and `voice-reviewer` agent now read `~/.human-voice/config.json` and `~/.human-voice/profile.json` automatically. No longer need to specify content directories manually every invocation.

## [0.4.0] - 2026-04-04

### Added

- **Voice Elicitation Engine**: Adaptive interview system for building multi-dimensional voice profiles
  - 130 questions across 12 thematic modules + 20 semantic differential pairs
  - 4 writer-type branches (Creative, Business, Academic, Personal)
  - Dual-output architecture: self-reported preferences + computational observation
  - NLP pipeline (spaCy): lexical diversity, syntactic complexity, pragmatic markers, discourse cohesion, LIWC-equivalent metrics
  - Scoring engine: per-dimension subscale scoring, Cronbach's alpha, tier-weighted merging
  - Calibration report: self-perception gap analysis, blind spots, aspirational gaps
  - Session management with pause/resume across Claude Code sessions
  - Active profile published to `~/.human-voice/profile.json` for cross-session use
- **New Commands**: `interview`, `resume`, `status`, `profile`, `sessions`
- **New Agents**: `interview-conductor`, `profile-synthesizer`
- **New Skill**: `voice` for voice elicitation
- **Documentation**: Diátaxis-structured docs (tutorial, how-to, reference, explanation)
- **Tests**: 118 pytest tests covering session, branching, sequencing, quality, NLP, scoring, integration
- **CLI Tools**: 7 bin/ executables for session, branching, sequencer, quality, NLP, scoring, profiles

## [0.3.0] - 2026-01-23

### Added

- **Ignore Categories**: New `--ignore=categories` argument for both review and fix commands
  - Skip specific pattern categories during detection/fixing
  - Available categories: `emojis`, `em-dash`, `en-dash`, `smart-quotes`, `ellipsis`, `bullet`, `arrow`
  - Example: `/human-voice:voice-fix --ignore=emojis,em-dash docs/`
- **Validation Warnings**: Unknown category names now show a warning with valid options

### Changed

- **Commands**: Updated `review.md` and `fix.md` with `--ignore` option documentation
- **Scripts**: Both validation and fix scripts now support category filtering

## [0.2.0] - 2026-01-17

### Added

- **CLAUDE.md**: Project-level instructions with development guidelines
- **Subcog Memory Integration**: Optional memory support across all components
  - Recall existing voice decisions before analysis
  - Capture findings for future sessions
  - Graceful degradation when Subcog unavailable

### Changed

- **Skill**: Added optional memory workflow section to `SKILL.md`
- **Agent**: `voice-reviewer` now supports optional memory context
- **Commands**: All commands (`fix`, `review`, `setup`) enhanced with optional memory integration

## [0.1.0] - 2025-01-16

### Added

- Initial release as standalone Claude Code plugin
- **Skill**: `human-voice` - Core detection patterns and writing guidelines
  - Character patterns detection (em dashes, smart quotes, emojis)
  - Language patterns detection (buzzwords, hedging, filler phrases)
  - Structural patterns detection (list addiction, rule of three)
  - Voice patterns detection (passive voice, generic analogies)
- **Commands**:
  - `/human-voice:voice-setup` - Interactive configuration wizard
  - `/human-voice:voice-review [path]` - Analyze content for AI patterns
  - `/human-voice:voice-fix [path]` - Auto-fix character-level issues
- **Agent**: `voice-reviewer` - Proactive content review after Write/Edit operations
- **Scripts**:
  - `validate-character-restrictions.js` - Validation script for character patterns
  - `fix-character-restrictions.js` - Auto-fix script for character patterns
- **References**:
  - `character-patterns.md` - Detailed character pattern documentation
  - `language-patterns.md` - Language pattern detection guide
  - `structural-patterns.md` - Structural pattern analysis
  - `voice-patterns.md` - Voice and tone pattern guide
- **Examples**:
  - `before-after.md` - Real-world transformation examples
- **Templates**:
- Configuration support via `config.json` (`$CLAUDE_PLUGIN_DATA/config.json`)

### Research Sources

Pattern detection based on:
- [Measuring AI "Slop" in Text](https://arxiv.org/html/2509.19163v1)
- [The Field Guide to AI Slop](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)
- [Common AI Words - Grammarly](https://www.grammarly.com/blog/ai/common-ai-words/)

[0.8.1]: https://github.com/zircote/human-voice/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/zircote/human-voice/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/zircote/human-voice/compare/v0.5.0...v0.7.0
[0.5.0]: https://github.com/zircote/human-voice/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/zircote/human-voice/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/zircote/human-voice/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/zircote/human-voice/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zircote/human-voice/releases/tag/v0.1.0
