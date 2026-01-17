# Changelog

All notable changes to the Human Voice plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  - `/human-voice:setup` - Interactive configuration wizard
  - `/human-voice:review [path]` - Analyze content for AI patterns
  - `/human-voice:fix [path]` - Auto-fix character-level issues
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
  - `human-voice.local.md.example` - Configuration template
- Configuration support via `.claude/human-voice.local.md`

### Research Sources

Pattern detection based on:
- [Measuring AI "Slop" in Text](https://arxiv.org/html/2509.19163v1)
- [The Field Guide to AI Slop](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)
- [Common AI Words - Grammarly](https://www.grammarly.com/blog/ai/common-ai-words/)

[0.1.0]: https://github.com/zircote/human-voice/releases/tag/v0.1.0
