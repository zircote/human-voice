---
name: voice-interview
description: "Start a new voice elicitation interview session"
argument-hint: ""
allowed-tools: Read, Write, Bash(python3:*), Bash(source:*), Glob, AskUserQuestion, Agent
---

# /interview — Start a New Voice Elicitation Interview

Start a new mivoca voice elicitation interview session.

## Procedure

1. **Create session**: Run `bin/mivoca-session create` to generate a new session. This creates `~/.human-voice/sessions/{session_id}/` with `state.json` and `responses.jsonl`. Capture the session_id and session_dir path from the output.

2. **Load question bank**: Verify question bank modules exist in `question-bank/modules/`.

3. **Launch interview conductor**: Spawn the `interview-conductor` agent with this prompt:

   > You are conducting a new mivoca voice elicitation interview.
   >
   > Session ID: {session_id}
   > Session directory: {session_dir}
   > Project root: {project_root}
   >
   > Run the FULL interview loop as described in your instructions. Use `bin/mivoca-sequencer next-question` to get each question, present it via AskUserQuestion, record the response, update state, and loop. Do NOT exit after a single question — continue the loop until the interview is complete or the user pauses.
   >
   > Start by getting the first question from the sequencer and presenting it.

   **IMPORTANT**: The agent must stay alive for the entire interview. It loops through all ~70 questions in a single agent session. It only exits when:
   - The sequencer returns `action: "interview_complete"`
   - The user requests a pause

## Session States

```
init → screening → branching → in_progress → writing_samples → scoring → analyzing → generating → complete
                                    ↕
                                  paused
```

## Output

Report the session ID and begin the interview with the first question from M01.
