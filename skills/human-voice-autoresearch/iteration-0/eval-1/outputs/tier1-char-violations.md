# Tier 1: Character-Level Violations

**File**: `char-violations.md`
**Total violations**: 13 (11 errors, 2 warnings)

## Errors

| Line | Col | Pattern | Character | Fix |
|------|-----|---------|-----------|-----|
| 3 | 22 | Em Dash | U+2014 `—` | Replace with colon, comma, semicolon, or period |
| 5 | 1 | Left Double Quote | U+201C `"` | Replace with straight quote `"` |
| 5 | 30 | Right Double Quote | U+201D `"` | Replace with straight quote `"` |
| 5 | 52 | Left Single Quote | U+2018 `'` | Replace with straight apostrophe `'` |
| 5 | 70 | Right Single Quote | U+2019 `'` | Replace with straight apostrophe `'` |
| 7 | 29 | Horizontal Ellipsis | U+2026 `...` | Replace with three periods `...` |
| 9 | 1 | Bullet Character | U+2022 | Replace with markdown list `-` |
| 10 | 1 | Bullet Character | U+2022 | Replace with markdown list `-` |
| 11 | 1 | Bullet Character | U+2022 | Replace with markdown list `-` |
| 15 | 12 | Emoji | Various | Remove entirely |
| 15 | 31 | Emoji | Various | Remove entirely |

## Warnings

| Line | Col | Pattern | Character | Fix |
|------|-----|---------|-----------|-----|
| 13 | 41 | Arrow Character | U+2192 `->` | Replace with ASCII arrow `->` |
| 13 | 48 | Arrow Character | U+2192 `->` | Replace with ASCII arrow `->` |
