---
description: Review content for AI writing patterns
argument-hint: "[path] [--ignore=categories]"
allowed-tools: Read, Glob, Grep, Bash(node:*), Bash(test:*), Bash(ls:*), Bash(grep:*)
---

# Human Voice Review

Analyze content for AI-generated writing patterns using a multi-tier approach.

## Options

- `--ignore=emojis,em-dash` - Skip specific pattern categories during character detection
  - Valid categories: `emojis`, `em-dash`, `en-dash`, `smart-quotes`, `ellipsis`, `bullet`, `arrow`
  - Example: `/human-voice:review --ignore=emojis,arrow docs/`

## Target

$IF($1,
  Review target: `$1`

  First, verify the path exists:
  !`test -e "$1" && echo "Path exists: $1" || echo "ERROR: Path '$1' does not exist"`
,
  No target specified. Auto-detecting content directories...
  !`ls -d _posts content _docs docs 2>/dev/null || echo "No standard content directories found"`
)

## Step 1: Character-Level Detection

Run automated character validation:

$IF($1,
  !`node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js" $ARGS 2>&1 || true`
,
  !`for d in _posts content _docs docs; do test -d "$d" && echo "$d"; done | xargs -r node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js" $ARGS 2>&1 || echo "No content directories found to validate"`
)

Report any em dashes, smart quotes, emojis, or other AI-telltale characters found.

## Step 2: Language Pattern Scan

$IF($1,
  Search for AI buzzwords:
  !`grep -rn -i -E "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang" "$1" 2>/dev/null | head -20 || echo "No AI buzzwords found"`

  Search for hedging phrases:
  !`grep -rn -i -E "it's worth noting|generally speaking|in order to|due to the fact|at the end of the day" "$1" 2>/dev/null | head -20 || echo "No hedging phrases found"`

  Search for meta-commentary:
  !`grep -rn -i -E "in this article|let's dive|let's explore|as mentioned earlier" "$1" 2>/dev/null | head -20 || echo "No meta-commentary found"`
,
  Skipping language scan - no target specified. Run with a directory argument.
)

## Step 3: Manual Review

For each file with issues, provide:

1. **Summary**: Total violations by category
2. **Specific issues**: Line-by-line findings with context
3. **Recommendations**: How to fix each issue
4. **Priority**: Which issues to fix first

## Output Format

```
=== Human Voice Review: [path] ===

Tier 1 - Character Issues: [count]
  - [file:line] [character] -> [replacement]

Tier 2 - Language Issues: [count]
  - [file:line] "[phrase]" -> [suggestion]

Tier 3 - Structural Issues: [assessment]
  - [observation]

Tier 4 - Voice Issues: [assessment]
  - [observation]

Recommendations:
1. [Priority fix]
2. [Secondary fix]
...

Run `/human-voice:fix [path]` to auto-fix character issues.
```

Load the human-voice skill for detailed pattern reference if needed.

## Memory Integration (Optional)

If Subcog MCP tools are available, enhance the review with persistent context:

**Before reviewing:** Recall existing voice decisions and patterns for this project.

**After reviewing:** If significant findings are identified, suggest capturing them for future sessions.

This integration is optional. Core review functionality works without Subcog.
