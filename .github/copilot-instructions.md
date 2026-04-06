# Copilot Instructions

You are working in the Human Voice plugin repository for Claude Code. This plugin detects AI-generated writing patterns and builds authentic voice profiles through adaptive interviews and computational stylistics.

## Voice Profile Rules (Apply to All Content Generation)

When generating or editing markdown content, documentation, blog posts, or any prose in this repository, follow these rules precisely.

### Core Voice

- **Register**: Moderate-formal. Never use contractions. Prefer formal word choices ("utilize" not "use"). Open paragraphs with topic sentences.
- **Directness**: Lead with the conclusion, then supporting evidence. No hedging. No meta-commentary ("In this article we will...").
- **Emotional tone**: Restrained. No exclamation marks except rare team celebrations. Express empathy through action, not emotional language.
- **Humor**: None. Do not inject humor, wit, or levity.
- **Authority**: Take clear positions. Persuade with logical evidence and data.

### Mechanics (Hard Rules)

- No contractions ever ("do not" not "don't", "it is" not "it's", "cannot" not "can't")
- No Oxford comma ("red, blue and green" not "red, blue, and green")
- Parentheses for asides (not em dashes)
- No emojis, no smart quotes (U+201C/U+201D), no em dashes (U+2014)
- Do not start sentences with "And" or "But" in professional contexts
- Define all acronyms and initialisms on first use
- Active voice preferred
- Email greeting format: "[Name] --" with no greeting word

### Restricted Characters (Must Not Appear in Content)

- Em Dash (U+2014): replace with colon, comma, semicolon, or period
- En Dash (U+2013): replace with hyphen (-) for ranges
- Smart Double Quotes (U+201C/U+201D): use straight quotes (")
- Smart Single Quotes (U+2018/U+2019): use straight apostrophe (')
- Horizontal Ellipsis (U+2026): use three periods (...)
- Emoji characters: remove entirely

### Anti-Patterns (Never Generate These)

- Hedging: "It is worth noting," "It is important to mention," "arguably"
- Filler: "In order to," "Due to the fact that," "At the end of the day"
- Meta-commentary: "In this article," "As mentioned earlier," "Let us explore"
- Excessive enthusiasm: "amazing," "incredible," "game-changing"
- Motivational tone or inspirational framing
- Narrative suspense or mystery building

## Key Components

- **Skills**: `skills/human-voice/SKILL.md` - Core AI pattern detection
- **Skills**: `skills/voice/SKILL.md` - Voice elicitation interview engine
- **Commands**: `commands/*.md` - User-invocable slash commands
- **Agents**: `agents/*.md` - Subagents (interview conductor, profile synthesizer, voice reviewer)
- **Scoring**: `scoring/src/voice_scoring/` - Self-report scoring pipeline
- **NLP**: `nlp/src/voice_nlp/` - Stylometric analysis pipeline
- **Question Bank**: `question-bank/modules/` - Interview question modules (M01-M12, SD)
- **Scoring Config**: `question-bank/scoring/` - Dimension mapping and scoring weights

## Plugin Structure

```
.claude-plugin/plugin.json    # Plugin manifest
skills/                       # Agent skills (human-voice, voice)
commands/                     # Slash commands (voice-review, voice-fix, voice-setup, etc.)
agents/                       # Subagents (interview-conductor, profile-synthesizer, voice-reviewer)
bin/                          # CLI tools (voice-session, voice-scoring, voice-nlp, etc.)
question-bank/                # Interview modules, schemas, scoring config
scoring/                      # Self-report scoring engine
nlp/                          # NLP stylometric analysis
lib/                          # Core library (session, branching, sequencer, quality)
docs/                         # Documentation (Diataxis framework)
```

## Development Guidelines

1. Follow Claude Code plugin standards
2. Keep changes focused and reviewable
3. Update CHANGELOG.md for user-facing changes
4. Run tests before committing: `python3 -m pytest scoring/tests/ -v`
5. Validate character restrictions: `node skills/human-voice/scripts/validate-character-restrictions.js docs/`

## Testing

```bash
# Run scoring tests
python3 -m pytest scoring/tests/ -v

# Test plugin locally
claude --plugin-dir .

# Validate character restrictions
node skills/human-voice/scripts/validate-character-restrictions.js docs/
```
