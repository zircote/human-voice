---
name: voice-resume
description: "Resume a paused voice elicitation interview session"
argument-hint: "[session_id]"
allowed-tools: Read, Write, Bash(python3:*), Bash(source:*), Glob, AskUserQuestion, Agent
---

# /resume — Resume a Paused Interview Session

Resume a previously paused voice interview session.

## Procedure

1. **List sessions**: Run `bin/voice-session list` to get all sessions as JSON.

2. **Filter resumable**: Show sessions with `state` of `paused` or `in_progress`. If a session ID was provided as an argument, use that directly. If no resumable sessions exist, suggest `/voice-interview`.

3. **Present choices**: If multiple resumable sessions, display a table and use `AskUserQuestion`:
   ```
   #  Session ID     State         Module  Questions  Updated
   1  a1b2c3d4-...   paused        M03     18/~70     2026-04-01
   2  e5f6g7h8-...   in_progress   M07     42/~70     2026-03-28
   ```

4. **Resume session**: Run `bin/voice-session resume {session_id}` to restore state.

5. **Launch conductor**: Spawn the `interview-conductor` agent with this prompt:

   > You are resuming a paused voice elicitation interview.
   >
   > Session ID: {session_id}
   > Session directory: {session_dir}
   > Project root: {project_root}
   >
   > Load state.json, recap progress conversationally to the user, then run the FULL interview loop. Use `bin/voice-sequencer next-question` to get each question, present it via AskUserQuestion, record the response, update state, and loop. Do NOT exit after a single question — continue until the interview is complete or the user pauses again.

## Output

Confirm which session was resumed, show progress, then present the next question.
