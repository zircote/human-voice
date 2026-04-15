---
name: voice-review
description: Review content for AI writing patterns
argument-hint: "[path] [--ignore=categories]"
allowed-tools: Read, Glob, Grep, Bash(node:*), Bash(test:*), Bash(ls:*), Bash(grep:*), Bash(cat:*), Skill
---

# Human Voice Review

Analyze content for AI-generated writing patterns using a multi-tier approach.

## Options

- `--ignore=emojis,em-dash` - Skip specific pattern categories during character detection
  - Valid categories: `emojis`, `em-dash`, `en-dash`, `smart-quotes`, `ellipsis`, `bullet`, `arrow`
  - Example: `/human-voice:voice-review --ignore=emojis,arrow docs/`

## Step 0: Load Configuration and Voice Profile

ALWAYS run this before any analysis. Not optional.

!`cat "$HOME/.human-voice/config.json" 2>/dev/null || echo "NO_CONFIG"`
!`cat "$HOME/.human-voice/profile.json" 2>/dev/null || echo "NO_PROFILE"`

Use `detection.content_directories` to resolve targets when no path is given. Use `detection.extensions` to filter file types. Use `detection.ignore` to skip directories. If a voice profile loaded, use it to calibrate Tier 3/4 against the user's actual voice.

## Step 1: Resolve Target

$IF($1,
  Review target: `$1`

  Verify the path exists:
  !`test -e "$1" && echo "Path exists: $1" || echo "ERROR: Path '$1' does not exist"`
,
  No target specified. Resolving from config...
  !`python3 -c "import json,os,sys; p=os.path.expanduser('~/.human-voice'+'/config.json'); c=json.load(open(p)); dirs=[d for d in c.get('detection',{}).get('content_directories',[]) if os.path.isdir(d)]; print(' '.join(dirs)) if dirs else sys.exit(1)" 2>/dev/null && echo "(from config.json)" || ls -d _posts content _docs docs 2>/dev/null || echo "No content directories found"`
)

## Step 2: Character-Level Detection

Run automated character validation:

$IF($1,
  !`node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js" $ARGS 2>&1 || true`
,
  !`dirs=$(python3 -c "import json,os,sys; p=os.path.expanduser('~/.human-voice'+'/config.json'); c=json.load(open(p)); dirs=[d for d in c.get('detection',{}).get('content_directories',[]) if os.path.isdir(d)]; print(' '.join(dirs)) if dirs else sys.exit(1)" 2>/dev/null || { for d in _posts content _docs docs; do test -d "$d" && printf '%s ' "$d"; done; }); test -n "$dirs" && node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js" $dirs $ARGS 2>&1 || echo "No content directories found to validate"`
)

Report any em dashes, smart quotes, emojis, or other AI-telltale characters found.

## Step 3: Language Pattern Scan

$IF($1,
  Search for AI buzzwords:
  !`grep -rn -i -E "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang" "$1" 2>/dev/null | head -20 || echo "No AI buzzwords found"`

  Search for hedging phrases:
  !`grep -rn -i -E "it's worth noting|generally speaking|in order to|due to the fact|at the end of the day" "$1" 2>/dev/null | head -20 || echo "No hedging phrases found"`

  Search for meta-commentary:
  !`grep -rn -i -E "in this article|let's dive|let's explore|as mentioned earlier" "$1" 2>/dev/null | head -20 || echo "No meta-commentary found"`
,
  !`dirs=$(python3 -c "import json,os,sys; p=os.path.expanduser('~/.human-voice'+'/config.json'); c=json.load(open(p)); dirs=[d for d in c.get('detection',{}).get('content_directories',[]) if os.path.isdir(d)]; print(' '.join(dirs)) if dirs else sys.exit(1)" 2>/dev/null || { for d in _posts content _docs docs; do test -d "$d" && printf '%s ' "$d"; done; }); if test -n "$dirs"; then echo "Scanning: $dirs"; grep -rn -i -E "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang" $dirs 2>/dev/null | head -20 || echo "No AI buzzwords found"; grep -rn -i -E "it's worth noting|generally speaking|in order to|due to the fact|at the end of the day" $dirs 2>/dev/null | head -20 || echo "No hedging phrases found"; grep -rn -i -E "in this article|let's dive|let's explore|as mentioned earlier" $dirs 2>/dev/null | head -20 || echo "No meta-commentary found"; else echo "No content directories found for language scan"; fi`
)

## Step 4: Manual Review

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

Run `/human-voice:voice-fix [path]` to auto-fix character issues.
```

Load the human-voice skill for detailed pattern reference if needed.

