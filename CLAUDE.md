# Human Voice Plugin

A Claude Code plugin for detecting and preventing AI-generated writing patterns.

## Project Context

This plugin provides:
- **Skill**: `human-voice` - Core detection patterns and writing guidelines
- **Commands**: `/human-voice:setup`, `/human-voice:review`, `/human-voice:fix`
- **Agent**: `voice-reviewer` - Proactive content review after edits

## Development Guidelines

- Follow Claude Code plugin standards
- Test commands locally with `claude --plugin-dir .`
- Update CHANGELOG.md for user-facing changes
- Keep backward compatibility (all features work without optional dependencies)

## File Structure

```
skills/human-voice/SKILL.md     # Core skill with detection patterns
commands/*.md                   # Slash commands
agents/voice-reviewer.md        # Proactive review agent
scripts/                        # Node.js validation/fix scripts
references/                     # Pattern documentation
```

## Subcog Memory Integration (Optional)

If Subcog MCP server is available, this plugin can leverage persistent memory for:
- Recalling project-specific voice decisions
- Storing learned patterns and exceptions
- Tracking configuration preferences across sessions

### Relevant Namespaces
- `decisions`: Voice style choices (e.g., "project allows emojis in README")
- `patterns`: Recurring voice fixes (e.g., "replace em dashes with colons")
- `learnings`: Project-specific gotchas discovered during review
- `config`: Per-project voice configuration settings

### Memory-Aware Workflow (When Available)

**Before analysis:**
```
subcog_recall: query="voice patterns OR voice decisions", filter="ns:decisions ns:patterns"
```

**After significant findings:**
```
subcog_capture: namespace=learnings, content="[finding]", tags=[human-voice, voice-pattern]
```

### Graceful Degradation

All plugin functionality works without Subcog:
- Commands execute normally without memory context
- Agent performs full analysis without recall
- Configuration via `.claude/human-voice.local.md` always works

Memory integration is additive - it enhances but never blocks core functionality.
