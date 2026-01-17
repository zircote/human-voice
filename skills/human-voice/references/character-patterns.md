# Character-Level Patterns (Tier 1)

These characters are strong AI indicators and can be detected/fixed automatically.

## Restricted Characters Table

| Character | Name | Unicode | Replacement | Severity |
|-----------|------|---------|-------------|----------|
| `—` | Em Dash | U+2014 | Colon (:), comma (,), semicolon (;), or period (.) | Error |
| `–` | En Dash | U+2013 | Hyphen (-) | Error |
| `" "` | Smart Double Quotes | U+201C/U+201D | Straight quotes (") | Error |
| `' '` | Smart Single Quotes | U+2018/U+2019 | Straight apostrophe (') | Error |
| `…` | Horizontal Ellipsis | U+2026 | Three periods (...) | Error |
| Various | Emoji Characters | Various | Remove entirely | Error |
| • | Bullet Character | U+2022 | Markdown list (-) | Error |
| Various | Arrow Characters | Various | ASCII arrows (->) | Warning |

## Detection Regex Patterns

### Em Dash Detection
```regex
\u2014
```

### En Dash Detection
```regex
\u2013
```

### Smart Quotes Detection
```regex
[\u201C\u201D\u2018\u2019]
```

### Ellipsis Detection
```regex
\u2026
```

### Common Emoji Ranges
```regex
[\u{1F600}-\u{1F64F}]  # Emoticons
[\u{1F300}-\u{1F5FF}]  # Misc Symbols and Pictographs
[\u{1F680}-\u{1F6FF}]  # Transport and Map
[\u{2600}-\u{26FF}]    # Misc symbols
[\u{2700}-\u{27BF}]    # Dingbats
```

## Replacement Logic

### Em Dash Replacement

Context-dependent replacement:
- Before a list or explanation: Use colon (:)
- Between clauses: Use comma (,) or semicolon (;)
- For parenthetical content: Use commas or parentheses
- When separating thoughts: Use period (.)

**Example transformations:**
```
AI pattern:  The tool is powerful—it handles everything.
Human fix:   The tool is powerful. It handles everything.

AI pattern:  Three features—speed, reliability, ease—matter most.
Human fix:   Three features matter most: speed, reliability, and ease.
```

### Smart Quote Replacement

Replace directly with ASCII equivalents:
- `"` (U+201C) → `"` (U+0022)
- `"` (U+201D) → `"` (U+0022)
- `'` (U+2018) → `'` (U+0027)
- `'` (U+2019) → `'` (U+0027)

### Ellipsis Replacement

Replace horizontal ellipsis (U+2026) with three periods:
- `…` → `...`

## Automated Commands

```bash
# Detect character violations in specific directories
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js _posts
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js content
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js _docs

# Auto-fix violations (dry run first recommended)
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js --dry-run _posts
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js _posts

# Process multiple directories
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/fix-character-restrictions.js _posts content _docs
```

## Why These Characters Matter

### Em Dashes

Em dashes are heavily overused in AI-generated text. Research shows AI models use em dashes at 3-5x the rate of human writers. They create a distinctive "AI rhythm" that readers recognize subconsciously.

### Smart Quotes

Smart quotes indicate content was likely processed through a word processor or AI system that auto-converts quotes. Raw human-typed content uses straight quotes.

### Emojis

Professional technical content rarely uses emojis. AI tends to add them for "friendliness" in contexts where they're inappropriate.

## Integration

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
node ${CLAUDE_PLUGIN_ROOT}/skills/human-voice/scripts/validate-character-restrictions.js _posts _docs content
if [ $? -ne 0 ]; then
    echo "AI writing patterns detected. Fix before committing."
    exit 1
fi
```

### CI/CD Pipeline

Add to GitHub Actions or similar:

```yaml
- name: Validate content for AI patterns
  run: node scripts/validate-character-restrictions.js _posts content _docs
```
