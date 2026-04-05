---
name: voice-status
description: "Show progress of a voice elicitation interview session"
argument-hint: "[session_id]"
allowed-tools: Read, Bash(python3:*), Bash(source:*), Glob
---

# /status — Show Interview Session Progress

Display the current progress of an active or recent mivoca interview session.

## Procedure

1. **Identify session**: If a session ID argument is provided, use it. Otherwise, run `bin/mivoca-session list` and select the most recently updated session.

2. **Load state**: Run `bin/mivoca-session load {session_id}` to get the session state as JSON.

3. **Display progress**:
   ```
   Session:     a1b2c3d4-e5f6-7890-abcd-ef1234567890
   State:       in_progress
   Writer Type: business_professional
   Created:     2026-04-01T14:30:00Z

   Progress:
     Questions answered:  32 / ~68
     Modules completed:   5 / 12
     Current module:      M05 — Narrative & Cognitive Style
     Estimated remaining: ~18 minutes

   Quality:
     Attention checks:    1/1 passed
     Straightlining:      0 flags
     Speed flags:         0
   ```

4. **Handle edge cases**:
   - No sessions: suggest `/voice-interview`
   - State `complete`: suggest `/voice-profile`
   - State `paused`: suggest `/voice-resume`
