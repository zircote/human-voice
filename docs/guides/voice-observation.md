---
title: Voice Observation
diataxis_type: how-to
diataxis_goal: Understand how the passive voice observer works and how to check for voice drift over time
---

# Continuous Voice Observation

The voice observer protocol runs passively during every Claude Code session. It watches for content you author and silently compares your writing against your voice profile. No manual setup is required beyond having a completed profile at `~/.human-voice/voice-prompt.txt`.

## How It Works

A SessionStart hook loads the voice profile and observer protocol at the beginning of every session. Claude reads both files silently and follows the observation rules throughout the session.

When you write prose (emails, blog posts, documentation, drafts), the observer compares your writing against the profile dimensions: formality, emotional tone, sentence structure, vocabulary, hedging patterns, humor, and mechanics (contractions, Oxford comma, punctuation style).

The observer does not interrupt your work. It accumulates observations silently.

## What Gets Observed

The observer distinguishes three types of text:

1. **Your writing**: Text you composed, drafted, or typed. This is the signal. Indicators: you said "I wrote this," the text emerged through conversation drafting, or you are clearly authoring content.

2. **Pasted/external text**: Content from other sources that you presented for review. This is ignored. Indicators: you said "review this," the text is quoted, or it appeared as a large block with no prior drafting context.

3. **AI-generated text**: Content Claude wrote. Tracked separately as "AI compliance" (does Claude match your profile?). Not mixed with your voice observations.

When uncertain, the observer does not record the text. Missing a sample is better than recording someone else's voice.

## Checking for Drift

Run the drift report:

```
/human-voice:voice-drift
```

The report shows:
- **Confirmed patterns**: Your writing matches the profile as expected
- **Drift detected**: Your writing consistently diverges from the profile on specific dimensions
- **New patterns**: Voice characteristics observed that are not in the profile

## Where Observations Are Stored

Observations are stored in Atlatl memory under the `voice-observations` namespace. They persist across sessions. The observer captures a memory only when it has identified 5 or more consistent observations showing the same divergent pattern.

To view raw observations:

```
recall_memories(query="voice drift observed pattern", namespace="voice-observations")
```

## When to Re-Interview

- **No drift**: Profile is accurate. No action needed.
- **Moderate drift** (1-2 dimensions): Consider a targeted supplemental interview covering the drifting modules.
- **Significant drift** (3+ dimensions): The profile may no longer represent your current voice. Run `/human-voice:voice-interview` for a full re-interview.

## Disabling the Observer

The observer is controlled by the SessionStart hook in `hooks/hooks.json`. To disable it, remove or rename the hooks file. The observer reads `~/.human-voice/observer-protocol.md`; deleting that file also disables observation while keeping the voice profile active for content generation.
