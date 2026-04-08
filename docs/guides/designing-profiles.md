---
diataxis_type: how-to
diataxis_goal: Design a voice profile from a description or template without running an interview
---

# How to Design a Voice Profile

You can create a voice profile without running the full interview. The `/voice:design` command generates a complete profile from either a natural-language description or a pre-built template. This is useful for brand voices, fictional characters, or team-standardized styles.

## Prerequisites

- The human-voice plugin installed

## Design from a description

Provide a natural-language description of the voice you want:

```
/voice:design narrator-formal "A warm, narrative voice that uses humor and personal anecdotes. Casual register, short sentences, lots of contractions."
```

The first argument is the profile slug (optional -- the command asks for one if omitted). The remaining text is the voice description.

More examples:

```
/voice:design zircote-brand "Corporate brand voice: professional, authoritative, no humor, active voice, precise vocabulary."
```

```
/voice:design victorian "Victorian narrator: ornate, long multi-clause sentences, formal vocabulary, third-person omniscient."
```

The command generates a complete `profile.json` with:

- All 8 gold-standard dimension scores derived from the description
- Semantic differential values consistent with the description
- Distinctive features, mechanics preferences, and an identity summary
- Origin set to `"designed"`
- Calibration set to `null` (no self-report vs observed comparison possible)

## Design from a template

Start from a pre-built template and optionally customize it:

```
/voice:design --from-template formal-technical
```

### Available templates

| Template | Description |
|---|---|
| `formal-technical` | Technical documentation voice. High formality, precise vocabulary, active voice, structured paragraphs. |
| `casual-conversational` | Informal blog/social voice. Low formality, contractions, short sentences, personal pronouns. |
| `academic-prose` | Scholarly writing voice. High complexity, hedging language, citation-aware, formal register. |
| `brand-corporate` | Corporate communications voice. Professional, authoritative, consistent, audience-aware. |
| `creative-narrative` | Storytelling voice. Variable sentence length, figurative language, emotional range, distinct rhythm. |

Templates are stored as JSON files in `templates/profiles/`. Each template is a minimal `profile.json` with baseline values. The command fills in any missing fields and may ask you to customize dimension scores or mechanics preferences.

The origin for template-based profiles is `"template"`.

## How designed profiles differ from interview-derived ones

Designed profiles lack the empirical grounding of interview-derived profiles:

- **No calibration data**: There are no self-report answers to compare against observed behavior, so the calibration section is null. There are no blind spots or aspirational gaps to report.
- **No writing samples**: The NLP pipeline has no behavioral data to analyze. Dimension scores are based entirely on the description or template, not on observed writing.
- **No confidence scores**: Without measurement agreement between self-report and observation, confidence values are not computed.

Interview-derived profiles produce dual-output scores (self-report and computed) with calibration deltas. Designed profiles produce single-source scores. Both formats are valid voice profiles and work identically with the reviewer agent, Copilot export, and observer protocol.

## After designing a profile

The command stores and activates the profile automatically. Suggested next steps:

View the full profile details:

```
/voice:profiles info {slug}
```

Export the profile to a repository for Copilot:

```
/voice:profiles export {slug} --to-repo ../my-repo
```

Switch to a different active profile:

```
/voice:profiles activate {other-slug}
```

## Related documentation

- [Managing Profiles](managing-profiles.md) for listing, renaming, deleting, and exporting profiles
- [Copilot Integration](copilot-integration.md) for exporting to repositories
- [Getting Started tutorial](../tutorials/getting-started.md) for running an interview instead
- [Configuration Reference](../reference/configuration.md) for profile output paths
