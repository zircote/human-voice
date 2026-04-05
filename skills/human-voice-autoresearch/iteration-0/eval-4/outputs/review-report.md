# Human Voice Review Report

**File reviewed:** `skills/human-voice-autoresearch/candidate/evals/fixtures/voice-issues.md`
**Date:** 2026-03-19

## Tier 1: Character-Level Patterns

**Result: PASS** -- No character-level violations detected. No em dashes, smart quotes, emojis, or special Unicode characters found.

## Tier 2: Language-Level Patterns

**Result: FAIL** -- AI buzzwords and filler detected.

| Line | Pattern | Category |
|------|---------|----------|
| 13 | "streamlining" | AI buzzword |
| 14 | "cognitive load" | AI buzzword / jargon |
| 15 | "facilitates" | AI buzzword |
| 15 | "optimal performance" | AI buzzword |
| 15 | "development lifecycle" | AI buzzword / jargon |

Lines 13-15 contain a dense cluster of AI-typical corporate language that says nothing specific.

## Tier 3: Structural Patterns

**Result: FAIL** -- Multiple structural issues found.

- **Monotonous sentence structure (lines 6-8):** Five consecutive passive-voice sentences of similar length and pattern: "The X was Y." Reads like a machine-generated list of events.
- **List of three analogies (lines 10-11):** Three generic analogies in a row ("Swiss Army knife," "GPS," "bridge") follow the AI "rule of three" pattern exactly.
- **Perfect grammar with shallow insights (lines 13-15):** Well-formed sentences with buzzwords but zero concrete information. No numbers, no specifics, no real claim.
- **Hedging paragraph (lines 20-22):** The entire closing paragraph hedges every possible claim with "may potentially," "some users," "certain situations," "somewhat better," "many cases," "depending on." This is a hallmark AI pattern of avoiding any definitive statement.

## Tier 4: Voice and Style

**Result: FAIL** -- Multiple voice issues found.

| Line(s) | Issue | Category |
|----------|-------|----------|
| 1-2 | "In this tutorial, we will discuss" -- meta-commentary opening that tells the reader what the article will do instead of doing it | Meta-commentary |
| 2 | "Let's explore the various options available" -- more meta-commentary with no substance | Meta-commentary |
| 6-8 | Five sentences all in passive voice: "was implemented," "were run," "was completed," "was discovered," "was applied" | Passive voice overuse |
| 10-11 | "Like a Swiss Army knife for developers," "Think of it as a GPS for your codebase," "Consider it a bridge between frontend and backend" | Generic analogies |
| 13-15 | Vague corporate language with no specifics. What tool? What workflows? How much improvement? | Perfect grammar, shallow insight |
| 17-18 | "We're thrilled to announce," "exciting new feature," "You're going to love," "How amazing is that?" -- excessive enthusiasm with no substance | Artificial enthusiasm / hype |
| 20-22 | Every claim is hedged: "may potentially," "some users," "certain situations," "somewhat better," "many cases," "depending on" | Excessive hedging |

## Summary

The file contains zero character-level issues but is heavily affected by voice and style problems across all other tiers:

- **0** character violations (Tier 1)
- **5** language-level buzzword/jargon instances (Tier 2)
- **4** structural pattern issues (Tier 3)
- **7** voice and style issues (Tier 4)

Every paragraph in this file exhibits at least one AI writing anti-pattern. The content reads as a textbook example of AI-generated prose: meta-commentary openings, passive voice chains, generic analogies, buzzword-laden filler, artificial enthusiasm, and pervasive hedging.

## Recommended Fixes

1. **Lines 1-2:** Remove meta-commentary. Start with the actual content: what authentication is being set up and why.
2. **Lines 6-8:** Rewrite in active voice with specific subjects: "The team implemented OAuth2 login. CI runs tests on every push. We deployed to staging on Tuesday."
3. **Lines 10-11:** Replace generic analogies with concrete descriptions of what the tool actually does.
4. **Lines 13-15:** Replace buzzwords with specifics: name the tool, state actual performance numbers, describe the real workflow improvement.
5. **Lines 17-18:** Remove hype. State what the feature does and why it matters, without exclamation marks or enthusiasm markers.
6. **Lines 20-22:** Pick a position. State what the approach does, for whom, with what tradeoff. Drop the hedging.
