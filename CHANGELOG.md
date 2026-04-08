# Changelog

All notable changes to the Human Voice plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.3.0]: https://github.com/zircote/human-voice/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/zircote/human-voice/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zircote/human-voice/releases/tag/v0.1.0
