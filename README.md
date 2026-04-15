# Human Voice Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://github.com/anthropics/claude-code)
[![CI](https://github.com/zircote/human-voice/actions/workflows/ci.yml/badge.svg)](https://github.com/zircote/human-voice/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/zircote/human-voice/releases)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![GitHub Stars](https://img.shields.io/github/stars/zircote/human-voice?style=social)](https://github.com/zircote/human-voice)

A Claude Code plugin that detects AI-generated writing patterns and builds voice profiles through adaptive interviews and computational stylistics.

> **Experimental.** This project is a research prototype. The scoring pipeline, dimension mapping, and NLP analysis have not been validated against external benchmarks or peer-reviewed psychometric standards. The voice profiles it produces are plausible but unproven. Treat the output as a starting point for editorial guidance, not as a validated instrument. The question bank, scoring weights, and dimension definitions will change as the system matures. Use it, break it, report what does not work.

![Human Voice Plugin - 4-tier analysis flow](.github/infographic.jpg)

## Features

- **Multi-tier pattern detection**: Character, language, structural, and voice analysis
- **Automated character fixes**: Auto-fix em dashes, smart quotes, emojis
- **Proactive review**: Agent triggers after content creation/editing
- **Interactive setup**: Configuration wizard for project-specific settings
- **Configurable**: Customize file types, directories, and detection tiers

## Installation

### From GitHub

```bash
claude plugin install zircote/human-voice
```

### Manual Installation

Clone and add to Claude Code:

```bash
git clone https://github.com/zircote/human-voice.git
claude --plugin-dir /path/to/human-voice
```

Or copy to your project's `.claude-plugin/` directory.

## Prerequisites

- Claude Code CLI
- Node.js 18+ (for validation scripts)

## Components

| Component | Name | Purpose |
|-----------|------|---------|
| Skill | human-voice | Core detection patterns and writing guidelines |
| Command | `/human-voice:voice-setup` | Interactive configuration wizard |
| Command | `/human-voice:voice-review [path]` | Analyze content for AI patterns |
| Command | `/human-voice:voice-fix [path]` | Auto-fix character-level issues |
| Agent | voice-reviewer | Proactive content review after edits |

## Usage

### Quick Start

```bash
# Set up configuration for your project
/human-voice:voice-setup

# Review content for AI patterns
/human-voice:voice-review docs

# Auto-fix character issues
/human-voice:voice-fix docs --dry-run
```

### Skill Triggers

The skill loads automatically when you say:
- "review for AI patterns"
- "make this sound human"
- "check for AI writing"
- "ai slop detection"
- "fix AI voice"
- "improve writing voice"

### Commands

**Set up configuration:**
```
/human-voice:voice-setup
```

Detects project structure, content directories, and creates `config.json` with your preferences.

**Review content for AI patterns:**
```
/human-voice:voice-review docs           # review specific directory
/human-voice:voice-review content/blog   # review specific path
/human-voice:voice-review                # auto-detects content directories
```

**Auto-fix character issues:**
```
/human-voice:voice-fix docs              # apply fixes to directory
/human-voice:voice-fix --dry-run docs    # preview changes first
/human-voice:voice-fix                   # auto-detect and fix
```

### Agent

The `voice-reviewer` agent triggers:
- **Proactively**: After Write/Edit operations on .md/.mdx files
- **On request**: When you ask to review content voice

## Detection Tiers

### Tier 1: Character Patterns (Automated)

| Character | Unicode | Replacement |
|-----------|---------|-------------|
| Em dash (--) | U+2014 | Period, comma, colon |
| En dash (-) | U+2013 | Hyphen |
| Smart quotes | U+201C/D, U+2018/9 | Straight quotes |
| Ellipsis (...) | U+2026 | Three periods |
| Emojis | Various | Remove |

### Tier 2: Language Patterns (Manual)

- **Buzzwords**: delve, realm, pivotal, harness, revolutionize, seamlessly
- **Hedging**: "it's worth noting", "generally speaking", "arguably"
- **Filler**: "in order to", "due to the fact", "at this point in time"

### Tier 3: Structural Patterns

- List addiction (everything as bullets)
- Rule of three overuse
- "From X to Y" constructions
- Monotonous sentence structure

### Tier 4: Voice Patterns

- Passive voice overuse
- Generic analogies
- Meta-commentary ("In this article...")
- Perfect grammar with shallow insights

## Configuration

Run `/human-voice:voice-setup` for interactive configuration, or edit `config.json` directly.

Configuration is stored at `$CLAUDE_PLUGIN_DATA/config.json` (defaults to `~/.human-voice/config.json` in standalone mode). Use `python -m lib.config show` to view the effective config, or `python -m lib.config reset` to write defaults.

## Memory Integration (Optional)

When [Subcog](https://github.com/zircote/subcog) MCP server is available, the plugin can leverage persistent memory:

- **Recall** project-specific voice decisions before analysis
- **Capture** findings and patterns for future sessions
- **Track** configuration preferences across sessions

All features work without Subcog. Memory integration is additive and never blocks core functionality.

## File Structure

```
human-voice/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── voice-reviewer.md
├── commands/
│   ├── voice-fix.md
│   ├── voice-review.md
│   └── voice-setup.md
├── skills/
│   └── human-voice/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── fix-character-restrictions.js
│       │   └── validate-character-restrictions.js
│       ├── references/
│       │   ├── character-patterns.md
│       │   ├── language-patterns.md
│       │   ├── structural-patterns.md
│       │   └── voice-patterns.md
│       └── examples/
│           └── before-after.md
├── templates/
│   └── observer-protocol.md
├── LICENSE
├── CHANGELOG.md
└── README.md
```

## Voice Elicitation (Voice)

Voice is an experimental voice elicitation system that captures a writer's voice through a 67-question adaptive interview, computational NLP analysis of writing samples, and automated profile synthesis. It produces two independent profiles per writer: a self-reported profile (what the writer believes about their voice) and a computationally observed profile (what their writing exhibits). A calibration layer identifies where these profiles agree and where they diverge.

> **Status**: The scoring pipeline produces numeric dimension scores but these scores have not been validated against external psychometric instruments. The NLP analysis uses standard stylometric measures (type-token ratio, Flesch-Kincaid, hedge density, etc.) but the mapping from NLP metrics to voice dimensions is hand-authored and unvalidated. The question bank is based on published findings in voice elicitation research but the specific item-to-dimension mappings are untested for reliability (Cronbach alpha) across a population. This is a functional prototype, not a finished measurement tool.

### CLI Tools

| Tool | Purpose |
|------|---------|
| `voice-session` | Session lifecycle: create, load, list, pause, resume |
| `voice-scoring` | Score a completed session and produce dimension profiles |
| `voice-nlp` | Run the stylometric NLP analysis pipeline on writing samples |
| `voice-branching` | Evaluate interview routing and module sequencing |
| `voice-sequencer` | Determine the next question based on session state |
| `voice-quality` | Detect satisficing and response quality issues |

### Getting Started

See the [Getting Started tutorial](docs/tutorials/getting-started.md) for a complete walkthrough of running your first voice elicitation session.

See the [CLI Reference](docs/reference/cli.md) for detailed documentation of all commands, options and output formats.

## Research Sources

Pattern detection based on:
- [Measuring AI "Slop" in Text](https://arxiv.org/html/2509.19163v1)
- [The Field Guide to AI Slop](https://www.ignorance.ai/p/the-field-guide-to-ai-slop)
- [Common AI Words - Grammarly](https://www.grammarly.com/blog/ai/common-ai-words/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT
