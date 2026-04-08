---
name: strict
description: Maximum strictness for published content
detection:
  character_patterns:
    enabled: true
    ignore: []
  language_patterns:
    enabled: true
  structural_patterns:
    enabled: true
  voice_patterns:
    enabled: true
strictness: strict
---

# Strict Voice Profile

Flag everything. No tolerance for AI patterns. Use for content that will be published, read by a wide audience, or represents your brand.

## Tier 2 Guidance: Language Patterns

Zero tolerance. Flag every instance of:
- Any AI buzzword, even in isolation
- Any hedging phrase, even mild ones ("arguably", "it could be said")
- Any filler ("in order to" should always be "to")
- Any meta-commentary or self-referential framing
- Excessive transitions (furthermore, moreover, additionally): flag if more than one per section

Demand concrete replacements for every flagged phrase.

## Tier 3 Guidance: Structural Patterns

Flag aggressively:
- Any bullet list longer than 5 items that could be prose
- Any rule-of-three construction
- Any "from X to Y" framing
- Sections where all sentences are within 5 words of each other in length
- Over-balanced perspectives ("on one hand... on the other")

## Tier 4 Guidance: Voice Patterns

Flag aggressively:
- Every passive voice construction (suggest active rewording)
- Every generic analogy or comparison
- Every opening that doesn't hook the reader immediately
- Every claim without a specific number, date, or example
- Every sentence that could apply to any product/project (not specific enough)
