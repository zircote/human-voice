---
name: voice-profile
description: "View a completed voice profile"
argument-hint: "[session_id]"
allowed-tools: Read, Bash(python3:*), Bash(source:*), Glob
---

# /profile — View a Completed Voice Profile

Display the full voice profile generated from a completed mivoca interview session.

## Procedure

1. **Identify session**: If a session ID argument is provided, use it. Otherwise, find the most recent session with `state` of `complete` via `bin/mivoca-session list`.

2. **Validate**: Load `state.json` via `bin/mivoca-session load {session_id}`. If state is not `complete`, inform the user and suggest `/voice-resume`.

3. **Read profile**: Load `{session_dir}/profile.json`.

4. **Display formatted profile**:
   ```
   ═══════════════════════════════════════════════
   VOICE PROFILE
   Session:  a1b2c3d4-...
   Writer:   business_professional
   ═══════════════════════════════════════════════

   Identity: A direct, analytical voice that favors
   precision over warmth. Writes in structured,
   medium-length sentences with minimal hedging.

   ── Gold Standard Dimensions ──────────────────
   Dimension            Self  Observed  Composite
   ───────────────────────────────────────────────
   Formality              65       58        62
   Emotional Tone         35       41        38
   Personality            75       67        71
   ...

   ── Calibration ───────────────────────────────
   Overall self-awareness: 0.76
   High awareness: formality, audience_awareness
   Blind spots: complexity, humor

   ── Distinctive Features ──────────────────────
   - High use of em-dashes for parenthetical asides
   - Low hedging frequency (boost-to-hedge ratio: 2.3)
   - Active voice dominance (87% of clauses)
   ```

5. **Edge cases**:
   - No `profile.json` but state is `complete`: report data integrity issue
   - No completed sessions: suggest `/voice-interview`
