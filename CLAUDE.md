# Human Voice Plugin

A Claude Code plugin for detecting AI-generated writing patterns and building voice profiles through adaptive interviews and computational stylistics.

## Branching Strategy

- **main**: Stable release branch. Only merge from develop when the code is tested and reviewed. Do not commit directly to main.
- **develop**: Active development branch. All new work goes here. Feature branches merge into develop. When develop is stable and ready for release, merge into main.

## Project Context

This plugin provides:
- **Skills**: `human-voice` (AI pattern detection), `voice` (voice elicitation interview)
- **Commands**: `/human-voice:voice-setup`, `/human-voice:voice-review`, `/human-voice:voice-fix`, `/human-voice:voice-interview`, `/human-voice:voice-profile`, `/human-voice:voice-resume`, `/human-voice:voice-drift`, `/human-voice:voice-sessions`, `/human-voice:voice-status`
- **Agents**: `interview-conductor`, `profile-synthesizer`, `voice-reviewer`
- **Scoring**: Self-report scoring pipeline with SD cross-validation
- **NLP**: Stylometric analysis pipeline (spacy-based)
- **Observer**: Passive voice observation protocol via SessionStart hook

## Development Guidelines

- All development on the `develop` branch
- Test commands locally with `claude --plugin-dir .`
- Run scoring tests: `python3 -m pytest scoring/tests/ -v`
- Validate character restrictions: `node skills/human-voice/scripts/validate-character-restrictions.js docs/`
- Update CHANGELOG.md for user-facing changes
- Keep backward compatibility (all features work without optional dependencies)

## File Structure

```
.claude-plugin/plugin.json        # Plugin manifest (hooks registered here)
skills/human-voice/SKILL.md       # Core skill with detection patterns
skills/voice/SKILL.md            # Voice elicitation interview skill
commands/*.md                     # Slash commands
agents/*.md                       # Subagents (interview, synthesizer, reviewer)
hooks/hooks.json                  # SessionStart hook for observer protocol
templates/observer-protocol.md    # Observer protocol template
bin/                              # CLI tools (voice-session, voice-scoring, etc.)
question-bank/                    # Interview modules, schemas, scoring config
scoring/src/voice_scoring/       # Self-report scoring engine
nlp/src/voice_nlp/               # NLP stylometric analysis pipeline
lib/                              # Core library (session, branching, quality, etc.)
docs/                             # Documentation (Diataxis framework)
.github/agents/                   # GitHub Copilot custom agents
.github/workflows/                # CI workflows (validation, voice checks)
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
- `voice-observations`: Passive voice drift observations from observer protocol

### Graceful Degradation

All plugin functionality works without Subcog:
- Commands execute normally without memory context
- Agent performs full analysis without recall
- Configuration via `.claude/human-voice.local.md` always works

Memory integration is additive - it enhances but never blocks core functionality.
