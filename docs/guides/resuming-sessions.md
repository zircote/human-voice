---
diataxis_type: how-to
diataxis_goal: "Pause and resume a voice elicitation interview session"
---

# How to Pause and Resume Interview Sessions

## Pause a session

1. During an active interview, type `pause` as your response to any question. The interview conductor will acknowledge the pause and stop presenting questions.
2. The session state is written to disk immediately. All responses recorded before the pause are preserved in `responses.jsonl`. The session status changes to `paused`.

## Check session state

3. Run `voice-session list` to view all sessions. The output includes status, question count and last updated timestamp for each session.

```bash
voice-session list
```

4. Locate the paused session in the output. Confirm its status shows `paused`.

## Resume a paused session

5. Use the `/voice:resume` slash command in Claude Code. If you have a single paused session, it resumes automatically. If you have multiple paused sessions, the command presents a selection table.

```
/voice:resume
```

6. Alternatively, specify the session ID directly:

```
/voice:resume a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

7. The interview continues from the exact question where you paused. Previously recorded responses remain intact and are not re-asked.

## What happens to recorded responses

All responses are appended to `responses.jsonl` as they are given. Pausing does not discard or modify any existing response data. When the session resumes, the sequencer reads the response log and determines the next unanswered question in the module sequence.

Session state (current module, branch path, quality flags) is stored in `state.json` and restored on resume. The resume operation validates session integrity before continuing.

## Related documentation

- [CLI Reference](../reference/cli.md) for `voice-session` subcommands
- [Getting Started tutorial](../tutorials/getting-started.md) for running a complete session
