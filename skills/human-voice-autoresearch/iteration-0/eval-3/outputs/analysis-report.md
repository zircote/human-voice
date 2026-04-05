# Structural AI Pattern Analysis Report

**File analyzed:** `evals/fixtures/structural-issues.md`
**Date:** 2026-03-19

## Tier 1: Character-Level Patterns

**Result: PASS** -- No character-level violations found. No em dashes, smart quotes, emojis, or special Unicode characters detected.

## Tier 2: Language-Level Patterns

**Result: PASS** -- No AI buzzwords, hedging phrases, filler phrases, or excessive transitions detected. The fixture isolates structural issues cleanly.

## Tier 3: Structural Patterns (PRIMARY FINDINGS)

### 3.1 List Addiction (Lines 6-11, 18-22)

Two sections consist entirely of bullet lists with no connecting prose. The "Introduction" section has 6 bare bullet items; "Key Benefits" has 5. Each item is a vague two-word phrase with no elaboration.

**Lines 6-11:**
```
- Fast execution
- Easy setup
- Clear documentation
- Active community
- Good support
- Regular updates
```

**Fix:** Replace with prose that explains WHY these matter, with specifics. Example: "Setup takes two minutes. The docs cover every endpoint with runnable examples."

### 3.2 Rule of Three Overuse (Lines 26-28)

Three consecutive sentences each deploy the rhetorical triple:
- "faster, simpler, and more reliable"
- "saves time, reduces errors, and improves quality"
- "Learn, practice, and master the technique"

This is a strong AI tell. Real writers occasionally use triples; AI uses them in every paragraph.

**Fix:** Vary the rhythm. Use a single specific claim instead of three vague ones. "Setup dropped from 20 minutes to 2."

### 3.3 "From X to Y" Construction (Lines 30-32)

Three consecutive "From X to Y" sentences:
- "From beginners to experts, everyone can benefit."
- "From setup to deployment, the process is streamlined."
- "From small teams to large enterprises, the tool scales."

This is one of the most recognizable AI structural patterns.

**Fix:** Remove entirely or replace with concrete examples. "A team of three at Acme Corp runs it alongside a 200-person platform org at BigCo."

### 3.4 Monotonous Sentence Structure (Lines 36-38)

Six consecutive sentences with identical structure (Subject "It" + Verb + Adverb):
- "The system processes requests efficiently."
- "It handles errors gracefully."
- "It scales automatically."
- "It logs everything comprehensively."
- "It monitors performance continuously."
- "It alerts teams promptly."

Every sentence is roughly the same length and follows Subject-Verb-Object-Adverb.

**Fix:** Vary sentence length and structure. Mix short statements with longer explanations. Lead with results, not capabilities.

### 3.5 Over-Balanced Perspectives (Lines 42-45)

Artificial balancing where every positive gets an immediate counterweight:
- "The tool is powerful. However, it has a learning curve."
- "On one hand, it saves time. On the other hand, it requires initial investment."
- "While it has advantages, it also has disadvantages."

Real writers pick a position. AI hedges everything into perfect balance.

**Fix:** Take a stance. "The learning curve is steep for the first week. After that, deploys that took an hour take five minutes."

## Tier 4: Voice Patterns

### 4.1 Meta-Commentary

- Title "Why Choose Our Tool" is marketing framing, not content
- "In conclusion" (line 49) is a textbook AI summarization marker

### 4.2 Generic References

Everything refers to "the tool", "the system", "the process" with no proper nouns, no project names, no version numbers.

### 4.3 No Concrete Evidence

Every claim is abstract: "Fast execution", "Speed improvements", "Better reliability". Zero numbers, zero benchmarks, zero examples.

### 4.4 Shallow Insights

Sentences are grammatically correct but contain no information a reader could act on. "Regular updates" tells you nothing. "Biweekly releases since January 2024" does.

## Summary

| Tier | Issues Found | Severity |
|------|-------------|----------|
| Tier 1: Characters | 0 | N/A |
| Tier 2: Language | 0 | N/A |
| Tier 3: Structure | 5 patterns | High |
| Tier 4: Voice | 4 patterns | Medium |

**Overall Assessment:** This file is a textbook example of AI-generated structural patterns. Every section demonstrates at least one structural anti-pattern. The content is grammatically flawless but informationally empty, which is itself a strong AI indicator.

## Structural Review Checklist

- [x] Content over-relies on bullet lists (2 list-only sections)
- [x] Sentence lengths are monotonous (especially lines 36-38)
- [x] "Rule of three" appears in every paragraph of the Overview section
- [x] Perspectives are artificially balanced (Pros and Cons section)
- [x] "From X to Y" constructions present (3 consecutive instances)
- [ ] Paragraphs vary in length (they do not; most are 3-4 lines)
