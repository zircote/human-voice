---
name: academic
description: Academic and research writing profile tolerating passive voice
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

# Academic Voice Profile

All tiers checked with adjustments for academic conventions. Passive voice is tolerated (it's standard in research writing). Hedging gets extra scrutiny because academic AI text hedges everything instead of making precise claims with confidence intervals.

## Tier 2 Guidance: Language Patterns

Academic-calibrated language checks:
- Flag AI buzzwords: "delve", "realm", "pivotal" are not academic vocabulary
- Hedging gets special treatment:
  - Flag vague hedges: "it's worth noting", "generally speaking", "arguably"
  - Allow precise hedges: "p < 0.05", "with 95% confidence", "in 7 of 10 trials"
  - Flag hedging that avoids commitment: "this may suggest" should be "this suggests" or "our data does not support"
- Flag filler: academic writing should be tight
- Flag meta-commentary: "in this paper we will discuss" should be cut; let the abstract handle framing

## Tier 3 Guidance: Structural Patterns

Academic-specific structural checks:
- Flag list addiction: academic writing should use prose for arguments
- Allow numbered lists for methodology steps or enumerated findings
- Flag rule-of-three: academic arguments should have as many points as the evidence supports, not three because it sounds nice
- Flag monotonous sentence length: even academic writing benefits from varied rhythm

## Tier 4 Guidance: Voice Patterns

Academic-adjusted voice checks:
- Passive voice: **tolerated**. "The samples were analyzed" is standard. Only flag passive that obscures agency when agency matters ("mistakes were made")
- Flag generic analogies: academic writing should use precise comparisons to prior work, not pop analogies
- Flag vague claims: "significantly improved" must have numbers; "widely used" must cite adoption data
- Allow measured tone: academic writing doesn't need to "hook" readers like a blog post
- Flag false modesty: "our humble contribution" reads as AI; state what the contribution is
