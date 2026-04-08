# Copilot Instructions

You are working in the Human Voice plugin repository for Claude Code.

## Project Overview

This is a Claude Code plugin that detects and prevents AI-generated writing patterns to ensure authentic human voice in content.

## Key Components

- **Skills**: `skills/human-voice/SKILL.md` - Core detection patterns
- **Commands**: `commands/*.md` - User-invocable slash commands
- **Agents**: `agents/voice-reviewer.md` - Proactive content review agent

## Plugin Structure

```
.claude-plugin/plugin.json  # Plugin manifest
skills/human-voice/         # Skill with references, examples, scripts
commands/                   # Slash commands (review, fix, setup)
agents/                     # Subagents (voice-reviewer)
templates/                  # Configuration templates
```

## Voice Profiles

This plugin uses **code-enforced profile routing** instead of text-based instruction routing. Do not embed profile routing logic in this file. Instead, use the resolve-profile.js script to determine which voice profile applies to a given file.

### How It Works

Run the resolver to get profile settings as JSON:
```bash
node skills/human-voice/scripts/resolve-profile.js <file-or-dir>
```

The script resolves profiles by checking (in order):
1. `voice-profile: <name>` in the file's YAML frontmatter
2. Path glob matches in `.claude/human-voice.local.md` routing rules
3. Config default profile
4. Plugin default profile

Pass the resolved JSON to validation/fix scripts via `--profile=<json>`.

### Preset Profiles

default, strict, lenient, docs, blog, marketing, changelog, academic. See `profiles/` directory for details.

## Development Guidelines

1. Follow Claude Code plugin standards
2. Keep changes focused and reviewable
3. Update CHANGELOG.md for user-facing changes
4. Test commands and agent triggering locally

## Testing

```bash
claude --plugin-dir .
```

Then test:
- `/human-voice:review` command
- `/human-voice:fix` command
- `/human-voice:setup` command
- Agent triggering after content edits
- Profile resolution: `node skills/human-voice/scripts/resolve-profile.js <file>`
