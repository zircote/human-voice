---
name: marketing
description: Marketing copy profile flagging hype and demanding proof
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

# Marketing Voice Profile

Everything on, strict mode, with extra attention to hype words and unsubstantiated claims. Marketing copy is where AI-generated text does the most reputational damage: readers have learned to pattern-match "revolutionize your workflow" as AI slop.

## Tier 2 Guidance: Language Patterns

Standard buzzwords plus marketing-specific additions:
- Flag all standard AI buzzwords
- Additionally flag superlatives without evidence: "best-in-class", "world-class", "industry-leading", "unmatched", "unparalleled"
- Flag hype verbs: "revolutionize", "transform", "supercharge", "turbocharge", "unlock", "empower"
- Flag empty modifiers: "robust", "powerful", "comprehensive", "seamless", "intuitive"
- Every claim needs a number: "fast" needs "50ms", "reliable" needs "99.9% uptime", "popular" needs "10,000 users"
- Flag hedging: marketing should commit to claims or drop them

## Tier 3 Guidance: Structural Patterns

Marketing-specific structural checks:
- Flag feature lists without benefit explanations: each feature needs a "so that..."
- Flag identical paragraph structures: if every paragraph is "Feature. Benefit. Call to action.", restructure
- Flag rule-of-three: it reads as a template, not genuine communication
- Allow short punchy sections: marketing copy can use more whitespace and shorter paragraphs than other formats

## Tier 4 Guidance: Voice Patterns

Marketing-specific voice checks:
- Flag passive voice: "your workflow is improved" should be "you ship faster"
- Flag false enthusiasm that lacks substance: "we're excited to announce" needs to follow with something genuinely noteworthy
- Flag generic comparisons: "unlike other solutions" must name the alternatives
- Demand social proof: customer quotes, usage numbers, case study references
- Flag "we" without personality: generic "we believe" statements need specifics about what the team actually did
