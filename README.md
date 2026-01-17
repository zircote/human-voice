# Human Voice Plugin

A Claude Code plugin that detects and prevents AI-generated writing patterns to ensure authentic, professional human voice in all content.

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
| Command | `/human-voice:setup` | Interactive configuration wizard |
| Command | `/human-voice:review [path]` | Analyze content for AI patterns |
| Command | `/human-voice:fix [path]` | Auto-fix character-level issues |
| Agent | voice-reviewer | Proactive content review after edits |

## Usage

### Quick Start

```bash
# Set up configuration for your project
/human-voice:setup

# Review content for AI patterns
/human-voice:review docs

# Auto-fix character issues
/human-voice:fix docs --dry-run
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
/human-voice:setup
```

Detects project structure, content directories, and creates `.claude/human-voice.local.md` with your preferences.

**Review content for AI patterns:**
```
/human-voice:review docs           # review specific directory
/human-voice:review content/blog   # review specific path
/human-voice:review                # auto-detects content directories
```

**Auto-fix character issues:**
```
/human-voice:fix docs              # apply fixes to directory
/human-voice:fix --dry-run docs    # preview changes first
/human-voice:fix                   # auto-detect and fix
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

Run `/human-voice:setup` for interactive configuration, or create `.claude/human-voice.local.md` manually.

See `templates/human-voice.local.md.example` for a complete example.

### Basic Configuration

```yaml
---
extensions:
  - .md
  - .mdx
  - .txt
content_directories:
  - _posts
  - content
  - docs
---
```

### Full Configuration Options

```yaml
---
extensions:
  - .md
  - .mdx
  - .txt

content_directories:
  - _posts
  - content
  - docs

ignore:
  - "**/node_modules/**"
  - "**/vendor/**"
  - "CHANGELOG.md"

detection:
  character_patterns:
    enabled: true
    em_dash: true
    smart_quotes: true
    emojis: true
  language_patterns:
    enabled: true
  structural_patterns:
    enabled: true
  voice_patterns:
    enabled: true

fix:
  dry_run_by_default: true
  report_format: detailed

output:
  verbosity: normal
  format: markdown
---

# Project Voice Notes

Add project-specific voice guidelines here.
```

## File Structure

```
human-voice/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── voice-reviewer.md
├── commands/
│   ├── fix.md
│   ├── review.md
│   └── setup.md
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
│   └── human-voice.local.md.example
├── LICENSE
├── CHANGELOG.md
└── README.md
```

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
