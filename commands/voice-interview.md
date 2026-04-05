---
name: voice-interview
description: "Start a new voice elicitation interview session"
argument-hint: ""
allowed-tools: Read, Write, Bash(python3:*), Bash(source:*), Glob, AskUserQuestion, Agent
---

# /interview — Start a New Voice Elicitation Interview

Start a new mivoca voice elicitation interview session.

## Procedure

1. **Create session**: Run `bin/mivoca-session create` to generate a new session. This creates `~/.human-voice/sessions/{session_id}/` with `state.json` and `responses.jsonl`.

2. **Load question bank**: Read question bank modules from `question-bank/modules/` to verify they are present.

3. **Launch interview conductor**: Spawn the `interview-conductor` agent with the session ID. The conductor:
   - Presents questions conversationally using `AskUserQuestion`
   - Records each response via `bin/mivoca-session` (appends to `responses.jsonl` with timing)
   - Updates `state.json` after each response (increments `questions_answered`, advances `current_module` and `current_question_index`)
   - Evaluates branching logic via `bin/mivoca-branching` after screening questions
   - Tracks format streak and injects engagement resets per `bin/mivoca-sequencer`
   - Monitors quality flags via `bin/mivoca-quality`
   - Handles pause requests (sets state to `paused`)
   - On completion: runs `bin/mivoca-nlp analyze-session`, then `bin/mivoca-scoring score`, then spawns `profile-synthesizer` agent

## Session States

```
init → screening → branching → in_progress → writing_samples → scoring → analyzing → generating → complete
                                    ↕
                                  paused
```

## Output

Report the session ID and begin the interview with the first question from M01.
