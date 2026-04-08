---
name: docs
description: Documentation and API reference profile
detection:
  character_patterns:
    enabled: true
    ignore: []
  language_patterns:
    enabled: true
  structural_patterns:
    enabled: false
  voice_patterns:
    enabled: false
strictness: normal
---

# Documentation Voice Profile

Characters and language patterns checked. Structural and voice tiers skipped. Documentation is inherently structured: bullet lists, numbered steps, tables, and consistent formatting are expected, not flaws.

## Tier 2 Guidance: Language Patterns

Flag with documentation context:
- AI buzzwords: flag "delve", "realm", "pivotal" but allow technical terms that overlap (e.g., "leverage" in a finance API is fine)
- Hedging: flag "it's worth noting" and "generally speaking" but allow "typically" and "usually" since docs describe common cases
- Filler: flag all filler ("in order to" -> "to")
- Meta-commentary: flag "in this guide" or "let's explore" but allow "see also" and "refer to" since those are standard doc cross-references

## Tier 3-4: Skipped

Structural patterns (lists, consistent formatting) and voice patterns (some passive voice) are normal in documentation. A doc that says "the function is called with two arguments" (passive) is clearer than forcing active voice.
