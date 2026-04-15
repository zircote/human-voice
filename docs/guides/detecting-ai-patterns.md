---
diataxis_type: how-to
diataxis_goal: Detect and fix AI writing patterns in content using the review and fix commands
---

# How to Detect and Fix AI Writing Patterns

The human-voice plugin scans content files for AI-generated writing patterns across four detection tiers. This guide covers how to run scans, interpret results, and auto-fix character-level patterns.

## Prerequisites

- The human-voice plugin installed
- Content files (markdown, text, or mdx) in your project

## Configure detection settings

Run the interactive setup to configure which patterns to detect and which directories to scan:

```
/voice:setup
```

The wizard walks through:

- **Content scope**: Which directories and file extensions to scan
- **Detection tiers**: Which pattern categories to enable
- **Fix behavior**: Whether to default to dry-run mode and whether to back up files
- **Output format**: Verbosity level and output format (markdown or JSON)

You can also edit `${CLAUDE_PLUGIN_DATA}/config.json` directly. See the [Configuration Reference](../reference/configuration.md) for the full config structure.

## Review content for AI patterns

Scan a file or directory:

```
/voice:review docs/
```

Or scan a specific file:

```
/voice:review docs/guides/my-guide.md
```

Without arguments, the command auto-detects standard content directories (`docs/`, `content/`, `_posts/`, `_docs/`).

### The four detection tiers

The review scans for patterns in four tiers, from most concrete to most subjective:

**Tier 1 -- Character patterns**: Unicode characters that AI models substitute for plain ASCII equivalents. These are the most reliably detectable.

| Pattern | Character | Typical replacement |
|---|---|---|
| Em dash | U+2014 | Period, comma, or colon |
| En dash | U+2013 | Hyphen |
| Smart quotes | U+2018, U+2019, U+201C, U+201D | Straight quotes |
| Ellipsis | U+2026 | Three periods |
| Emojis | Various | Removed |

**Tier 2 -- Language patterns**: Word choices and phrases characteristic of AI-generated text.

- **Buzzwords**: "delve", "leverage", "tapestry", "landscape", "robust", "comprehensive"
- **Hedging**: "it's worth noting", "it's important to remember", "arguably"
- **Filler**: "in today's world", "at the end of the day", "when it comes to"
- **Meta-commentary**: "as an AI", "let me explain", "in this article we will explore"

**Tier 3 -- Structural patterns**: Document-level organization habits of AI models.

- **List addiction**: Over-reliance on bulleted and numbered lists where prose fits better
- **Rule of three**: Grouping items in exactly three (three bullet points, three examples)
- **"From X to Y"**: Parallel constructions ("from planning to execution", "from novice to expert")

**Tier 4 -- Voice patterns**: Style and tone markers that suggest AI authorship.

- **Passive voice**: Excessive passive constructions for a formal, detached tone
- **Generic analogies**: Overused metaphors ("like a well-oiled machine", "tip of the iceberg")
- **Perfect grammar**: Unnaturally flawless sentence construction lacking normal imperfections

### Skip specific categories

Use `--ignore` to exclude pattern categories:

```
/voice:review --ignore=emojis,em-dash docs/
```

Valid categories: `emojis`, `em-dash`, `en-dash`, `smart-quotes`, `ellipsis`, `bullet`, `arrow`.

## Auto-fix character patterns

Fix Tier 1 character patterns automatically:

```
/voice:fix docs/
```

Preview changes without modifying files:

```
/voice:fix --dry-run docs/
```

Skip specific categories:

```
/voice:fix --ignore=emojis docs/
```

The fix command handles only Tier 1 (character-level) patterns. Tiers 2-4 require manual review because the correct replacement depends on context.

## Interpret the output

The review command outputs findings grouped by tier:

```
=== Human Voice Review: docs/ ===

Tier 1 - Character Issues: 12
  - docs/guide.md:45 em dash -> comma or period
  - docs/guide.md:78 smart quote -> straight quote

Tier 2 - Language Issues: 3
  - docs/guide.md:23 "it's worth noting" -> remove or rephrase
  - docs/guide.md:56 "delve" -> "examine" or "explore"

Tier 3 - Structural Issues: moderate
  - Rule-of-three pattern detected in 2 sections

Tier 4 - Voice Issues: low
  - Passive voice rate within normal range

Recommendations:
1. Fix 12 character issues with /voice:fix
2. Review 3 language patterns manually
```

Address Tier 1 issues first (automated), then work through Tier 2 manually. Tiers 3 and 4 are subjective assessments that inform revision rather than demanding specific fixes.

## Related documentation

- [Configuration Reference](../reference/configuration.md) for detection settings and thresholds
- [CLI Reference](../reference/cli.md) for full command syntax
- [Getting Started tutorial](../tutorials/getting-started.md) for initial setup
