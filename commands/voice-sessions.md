---
name: voice-sessions
description: "List all voice elicitation interview sessions"
argument-hint: ""
allowed-tools: Read, Bash(python3:*), Bash(source:*), Glob
---

# /sessions — List All Interview Sessions

Display a summary of all mivoca interview sessions stored locally.

## Procedure

1. **List sessions**: Run `bin/mivoca-session list` to get all sessions as JSON.

2. **Display table**: Format as:
   ```
   #  Session ID     State         Writer Type           Q's  Updated
   ──────────────────────────────────────────────────────────────────
   1  a1b2c3d4-...   complete      business_professional  72  2026-04-04
   2  f9e8d7c6-...   paused        creative_literary      32  2026-04-02
   3  11223344-...   in_progress   pending                12  2026-04-01
   ```

3. **Navigation hints**:
   - `complete` sessions: "Run `/voice-profile {id}` to view the voice profile"
   - `paused`/`in_progress`: "Run `/resume {id}` to continue"
   - No sessions: "Run `/voice-interview` to start"

4. **Summary line**: "Total: N sessions (X complete, Y in progress, Z paused)"
