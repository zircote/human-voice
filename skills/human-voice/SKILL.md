---
name: human-voice
description: This skill should be used when the user asks to review for AI patterns, make this sound human, check for AI writing, ai slop detection, fix AI voice, improve writing voice, human voice check, remove AI patterns, humanize this content, or needs to detect and correct AI-generated writing patterns.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Human Voice Skill

Detect, prevent, and correct AI-generated writing patterns to ensure authentic, professional human voice in all content.

## Purpose

Ensure all published content reads as authentic human writing through:
1. Detecting AI-telltale characters and patterns
2. Identifying language-level AI indicators
3. Correcting structural and stylistic issues
4. Guiding content creation with human voice principles

## Multi-Tier Analysis Framework

### Tier 1: Character-Level Patterns (Automated)

Run automated character detection first. These patterns are strong AI indicators:
- Em dashes, en dashes, smart quotes
- Horizontal ellipsis, bullet characters
- Emojis and special Unicode characters

Execute validation:
```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js <directory>
```

Auto-fix detected issues:
```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js <directory>
```

For complete character patterns table, see `references/character-patterns.md`.

### Tier 2: Language-Level Patterns (Manual Review)

Search for AI buzzwords and hedging phrases:
```bash
grep -rn -i -E "delve|realm|pivotal|harness|revolutionize|seamlessly" <directory>
grep -rn -i -E "it's worth noting|generally speaking|at the end of the day" <directory>
```

Key categories to check:
- **Hedging phrases**: "It's worth noting", "Generally speaking", "Arguably"
- **AI buzzwords**: delve, realm, pivotal, harness, revolutionize, seamlessly
- **Filler phrases**: "In order to", "Due to the fact that", "At this point in time"
- **Excessive transitions**: Furthermore, Moreover, Additionally, Consequently

For complete language patterns tables, see `references/language-patterns.md`.

### Tier 3: Structural Patterns

Review content for these AI structural patterns:
- **List addiction**: AI formats everything as bullet lists when prose works better
- **Rule of three overuse**: AI over-applies rhetorical threes, making content predictable
- **"From X to Y" construction**: "From beginners to experts", "From setup to deployment"
- **Monotonous sentence structure**: Similar length and structure throughout
- **Over-balanced perspectives**: "On one hand... on the other hand" for everything

For detailed structural patterns with examples, see `references/structural-patterns.md`.

### Tier 4: Voice and Style

Check for voice issues:
- **Passive voice overuse**: "The feature was implemented" instead of "The team shipped"
- **Generic analogies**: "Like a Swiss Army knife for developers"
- **Meta-commentary**: "In this article, we will discuss..."
- **Perfect grammar with shallow insights**: Well-formed sentences that say nothing specific

For voice patterns and fixes, see `references/voice-patterns.md`.

## Review Workflow

### Step 1: Automated Character Check

```bash
# Run validation on content directories
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js _posts content _docs

# Auto-fix detected issues
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js _posts content _docs
```

### Step 2: Language Pattern Scan

```bash
# AI buzzword search
grep -rn -i -E \
  "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang" \
  _posts/ content/ _docs/

# Hedging and filler search
grep -rn -i \
  "it's worth noting\|generally speaking\|in order to\|due to the fact" \
  _posts/ content/ _docs/
```

### Step 3: Structural Review

Apply the structural review checklist:
- [ ] Content doesn't over-rely on bullet lists
- [ ] Sentence lengths vary naturally
- [ ] No "rule of three" in every paragraph
- [ ] Perspectives aren't artificially balanced
- [ ] No "From X to Y" constructions
- [ ] Paragraphs vary in length

### Step 4: Voice Review

Apply the voice review checklist:
- [ ] Opening hooks the reader (no meta-commentary)
- [ ] Specific examples replace generic claims
- [ ] Personal experience or perspective included
- [ ] Honest about tradeoffs and limitations
- [ ] Varied rhythm (short and long sentences)
- [ ] Active voice predominates
- [ ] Numbers and specifics over vague claims

## Writing Guidelines

### Human Voice Principles

1. **Start with specifics**: "I spent three weeks debugging this" not "Many developers face challenges"
2. **Use active voice**: "The team shipped" not "The feature was shipped"
3. **Vary sentence length**: Mix short punchy statements with longer explanatory ones
4. **Be opinionated**: "This tool is better" not "This tool may be considered preferable"
5. **Include personal perspective**: "In my experience" backed by actual experience
6. **Acknowledge tradeoffs**: Real tools have real limitations
7. **Use concrete numbers**: "50ms" not "extremely fast"
8. **Write naturally**: Read content aloud. Rewrite anything that sounds robotic
9. **Be direct**: Say what you mean without qualifiers
10. **Show, don't tell**: Examples over descriptions

### AI Anti-Patterns to Avoid

1. Don't hedge everything: Pick a position
2. Don't use buzzwords: Say what you mean plainly
3. Don't list everything: Prose often works better
4. Don't balance artificially: Not every point needs a counterpoint
5. Don't meta-comment: Don't say "In this article, we will discuss"
6. Don't overuse transitions: Let ideas flow naturally
7. Don't genericize: "The tool" should be "swagger-php"
8. Don't claim without evidence: Show the improvement with numbers
9. Don't over-explain: Trust your reader
10. Don't use em dashes: Use colons, commas, or periods

## Content Generation Constraints

When using AI for content creation, include these constraints in prompts:

```text
MANDATORY CONSTRAINTS:
- No em dashes (use colons or commas)
- No smart quotes (use straight ASCII quotes)
- No emojis
- No buzzwords: delve, realm, pivotal, harness, revolutionize, seamlessly,
  cutting-edge, game-changing, robust, leverage, utilize, facilitate,
  synergy, paradigm, holistic, ecosystem, innovative, transformative
- No hedging: "it's worth noting", "generally speaking", "arguably"
- No filler: "in order to", "due to the fact", "at the end of the day"
- No meta-commentary: "In this article", "Let's dive in", "As mentioned"
- Use active voice
- Include specific examples with numbers
- Vary sentence length
- Be direct and opinionated
- Start with the content, not context-setting
```

## Configuration

Create `.claude/human-voice.local.md` to configure file extensions:

```yaml
---
extensions:
  - .md
  - .mdx
content_directories:
  - _posts
  - content
  - _docs
  - docs
---
```

## Additional Resources

### Reference Files

For detailed patterns and examples:
- **`references/character-patterns.md`** - Complete character restriction table with Unicode codes
- **`references/language-patterns.md`** - Hedging phrases, buzzwords, filler, transitions
- **`references/structural-patterns.md`** - Structural patterns with code examples
- **`references/voice-patterns.md`** - Voice and style issues with fixes

### Example Files

- **`examples/before-after.md`** - Before/after transformation examples

### Scripts

- **`${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js`** - Detect character violations
- **`${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js`** - Auto-fix character issues

## Related Skills

- `documentation-review:documentation-standards` - Documentation quality standards
- `documentation-review:changelog` - Changelog maintenance
