---
name: default
description: General-purpose balanced voice profile
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
strictness: normal
---

# Default Voice Profile

Balanced detection across all four tiers. Suitable for most content types.

## Tier 2 Guidance: Language Patterns

Flag these with normal thresholds:
- AI buzzwords (delve, realm, pivotal, harness, revolutionize, seamlessly)
- Hedging phrases ("it's worth noting", "generally speaking")
- Filler phrases ("in order to", "due to the fact")
- Meta-commentary ("in this article", "let's dive in")

A single common transition word is fine. Flag clusters of 3+ AI indicators in one section.

## Tier 3 Guidance: Structural Patterns

Check for:
- List addiction: flag when prose would work better
- Rule of three overuse: flag when it appears in every paragraph
- "From X to Y" constructions
- Monotonous sentence length

Lists in reference material or configuration docs are fine.

## Tier 4 Guidance: Voice Patterns

Check for:
- Passive voice overuse (some passive is natural)
- Generic analogies ("like a Swiss Army knife")
- Meta-commentary openings
- Well-formed sentences that say nothing specific
