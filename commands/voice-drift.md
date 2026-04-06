---
name: voice-drift
description: Report observed voice patterns and drift from the voice profile. Shows how the user's actual writing compares to their profiled voice over time.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Voice Drift Report

Generate a drift report comparing accumulated voice observations against the current profile.

## Procedure

1. **Recall observations**: Search Atlatl memory for voice observations:
   ```
   recall_memories(query="voice drift observed pattern writing", namespace="voice-observations", mode="hybrid")
   ```

2. **Load profile**: Read `${CLAUDE_PLUGIN_DATA}/profile.json` for current dimension scores. Extract the score for each dimension from the `dimensions` object. Do not use hardcoded values; every user's profile is different.

3. **Compare**: For each observation, compare against the dimension scores loaded from the profile in step 2. Cover all gold standard dimensions (formality, emotional_tone, personality, complexity, audience_awareness, authority, narrativity, humor) and all gap dimensions that have scores. Also compare mechanics observations (contractions, Oxford comma, punctuation style) against the `mechanics` section of the profile.

4. **Report** in three sections:

   **Confirmed patterns**: Observations that align with the profile. The user writes as the profile predicts.

   **Drift detected**: Observations that consistently diverge from the profile. Include the dimension name, the profile score, the observed tendency, the direction of drift (warmer, more formal, shorter sentences, etc.), and the number of observations supporting the pattern.

   **New patterns**: Voice characteristics observed that are not captured in the current profile at all.

5. **Recommend**:
   - If no drift: "Profile remains accurate. No action needed."
   - If moderate drift (1-2 dimensions): "Consider updating the profile for [dimensions]. A targeted re-interview of [modules] would refine the scores."
   - If significant drift (3+ dimensions): "The profile may no longer represent your current voice. Consider a full re-interview with /voice-interview."

6. **If no observations exist**: "No voice observations have been recorded yet. The observer protocol accumulates observations silently as you write during Claude Code sessions. Continue working and check back after you have authored several pieces of content."
