---
name: lenient
description: Relaxed profile for drafts, internal notes, and READMEs
detection:
  character_patterns:
    enabled: true
    ignore:
      - emojis
      - arrow
  language_patterns:
    enabled: false
  structural_patterns:
    enabled: false
  voice_patterns:
    enabled: false
strictness: lenient
---

# Lenient Voice Profile

Character-level cleanup only. Skips emojis and arrow characters. No language, structural, or voice analysis. Use for internal notes, rough drafts, README files, and content where polish matters less than getting the information down.

## Tier 2-4: Skipped

Language, structural, and voice tiers are disabled. Only obvious character-level issues (em dashes, smart quotes, en dashes, ellipsis, bullet characters) are flagged because these cause rendering issues regardless of content quality.

Emojis and arrows are allowed since they're often intentional in informal content.
