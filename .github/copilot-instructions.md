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
