---
description: Auto-fix AI character patterns in content
argument-hint: "[path] [--dry-run] [--ignore=categories]"
allowed-tools: Read, Bash(node:*), Bash(test:*), Bash(ls:*), Bash(for:*), Skill
---

# Human Voice Fix

Auto-fix AI-telltale characters (em dashes, smart quotes, emojis, etc.) in content files.

## Options

- `--dry-run` - Preview changes without modifying files
- `--ignore=emojis,em-dash` - Skip specific pattern categories
  - Valid categories: `emojis`, `em-dash`, `en-dash`, `smart-quotes`, `ellipsis`, `bullet`, `arrow`
  - Example: `/human-voice:fix --dry-run --ignore=emojis docs/`

## Target

$IF($1,
  Target: `$1`

  Verify the path exists:
  !`test -e "$1" && echo "Path exists: $1" || echo "ERROR: Path '$1' does not exist"`
,
  No target specified. Auto-detecting content directories...
  !`ls -d _posts content _docs docs 2>/dev/null || echo "No standard content directories found"`
)

## Dry Run First

When --dry-run is specified or when unsure, show what would change without modifying files:

$IF($1,
  !`node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js" --dry-run $ARGS 2>&1 || true`
,
  !`for d in _posts content _docs docs; do test -d "$d" && echo "$d"; done | xargs -r node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js" --dry-run $ARGS 2>&1 || echo "No content directories found"`
)

## Apply Fixes

If user confirms or no --dry-run flag:

$IF($1,
  !`node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js" $ARGS 2>&1 || true`
,
  !`for d in _posts content _docs docs; do test -d "$d" && echo "$d"; done | xargs -r node "${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js" $ARGS 2>&1 || echo "No content directories found"`
)

## Post-Fix Actions

After fixing character issues:

1. **Report summary**: Files modified, total replacements by type
2. **Remaining issues**: Language patterns still require manual review
3. **Next steps**: Suggest running `/human-voice:review` for full analysis

## What Gets Fixed

| Character | Replacement |
|-----------|-------------|
| Em dash (--) | Period, comma, or colon |
| En dash (-) | Hyphen |
| Smart quotes (" ") | Straight quotes |
| Ellipsis (...) | Three periods |
| Bullet (•) | Markdown dash |
| Emojis | Removed |

## Memory Integration

**Before fixing:** Recall project-specific exceptions

```bash
# Search for voice exceptions and allowed patterns
rg -i "voice\|exception\|character.patterns" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*decisions*" --glob "*.memory.md"
```

**After fixing:** Capture summary of changes

```bash
/mnemonic:capture learnings "Human Voice Fix: {PATH} - {N} character issues fixed"
```

Include:
- Files modified
- Total replacements by type
- Any exceptions applied

## Note

This command only fixes Tier 1 (character-level) patterns. For language, structural, and voice patterns, manual review is required. Run `/human-voice:review` for comprehensive analysis.
