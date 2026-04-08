---
name: changelog
description: Release notes and changelog profile with minimal detection
detection:
  character_patterns:
    enabled: true
    ignore:
      - emojis
      - arrow
      - bullet
      - ellipsis
  language_patterns:
    enabled: false
  structural_patterns:
    enabled: false
  voice_patterns:
    enabled: false
strictness: lenient
---

# Changelog Voice Profile

Minimal detection. Changelogs and release notes are inherently list-heavy, structured, and formulaic. That's fine: their job is to communicate what changed, not to entertain. Only flag characters that cause rendering problems.

## What Gets Checked

- Em dashes (U+2014): replace with colon or comma
- En dashes (U+2013): replace with hyphen
- Smart quotes: replace with straight quotes

## What Gets Skipped

- Emojis: often used intentionally in changelogs (ship emoji for releases, etc.)
- Arrows: used for "before -> after" descriptions
- Bullets: changelogs are lists by definition
- Ellipsis: not a concern in this format
- All language, structural, and voice patterns: changelogs have their own conventions
