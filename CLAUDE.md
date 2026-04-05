# Human Voice Plugin

A Claude Code plugin for detecting AI-generated writing patterns and building authentic voice profiles through adaptive interviews and computational stylistics.

## Project Context

This plugin provides two complementary capabilities:

**AI Pattern Detection:**
- **Skill**: `human-voice` — Core detection patterns and writing guidelines
- **Commands**: `/human-voice:voice-setup`, `/human-voice:voice-review`, `/human-voice:voice-fix`
- **Agent**: `voice-reviewer` — Proactive content review after edits

**Voice Elicitation (Mivoca):**
- **Skill**: `mivoca` — Adaptive interview engine for voice profiling
- **Commands**: `/human-voice:voice-interview`, `/human-voice:voice-resume`, `/human-voice:voice-status`, `/human-voice:voice-profile`, `/human-voice:voice-sessions`
- **Agents**: `interview-conductor` — Conversational interview, `profile-synthesizer` — Profile generation
- **NLP Pipeline**: spaCy-based writing sample analysis (lexical, syntactic, pragmatic, discourse, composite)
- **Scoring Engine**: Self-report dimension scoring with calibration

## Development Guidelines

- Follow Claude Code plugin standards
- Test commands locally with `claude --plugin-dir .`
- Update CHANGELOG.md for user-facing changes
- Keep backward compatibility (all features work without optional dependencies)

## File Structure

```
# AI Pattern Detection
skills/human-voice/SKILL.md     # Core skill with detection patterns
commands/voice-*.md              # voice-setup, voice-review, voice-fix
agents/voice-reviewer.md         # Proactive review agent
skills/human-voice/scripts/      # Node.js validation/fix scripts
skills/human-voice/references/   # Pattern documentation

# Voice Elicitation (Mivoca)
skills/mivoca/SKILL.md           # Interview engine skill
commands/{interview,resume,status,profile,sessions}.md
agents/{interview-conductor,profile-synthesizer}.md
question-bank/                   # 130 questions, 13 modules, branching rules, schemas
lib/                             # Python: session, branching, sequencer, quality, profile
nlp/                             # Python NLP pipeline (spaCy)
scoring/                         # Python scoring engine
bin/                             # CLI executables
tests/                           # pytest suite (118 tests)
docs/                            # Diátaxis documentation
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
