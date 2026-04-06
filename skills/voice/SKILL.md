---
name: voice
description: This skill should be used when the user asks to start a voice interview, elicit writing style, build a voice profile, analyze writing voice, capture writing style, run voice elicitation, understand my writing style, profile my voice, or needs to conduct an adaptive interview that produces a multi-dimensional voice coordinate profile.
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
---

# Voice — Voice Elicitation Interview Engine

Voice is an adaptive voice elicitation interview engine that builds a comprehensive written-voice profile through a structured conversational interview. The engine administers 60-80 questions across 12 thematic modules, adapting its path based on the participant's responses and detected writer type.

## Architecture Overview

- **Question Bank**: JSON question files organized by module in `question-bank/modules/`, validated against `question-bank/schemas/question.schema.json`
- **Branching Logic**: Conditional paths in `question-bank/branching/` that route participants through writer-type-specific question sequences
- **NLP Pipeline**: Text analysis stages in `nlp/` that extract stylistic signals from open-ended and writing-sample responses
- **Scoring Engine**: Dimension scoring in `scoring/` that maps responses to voice profile dimensions with weighted aggregation
- **Agents**: Specialized conductor and analyst agents in `agents/` that orchestrate the interview flow

## Interview Modules

The interview spans 12 modules plus a screening/demographic preamble (SD). Modules cover dimensions such as formality and register, emotional tone, sentence structure, vocabulary preferences, rhetorical patterns, audience awareness, and stylistic identity. Each module contains 4-8 questions with a mix of question types (likert, forced_choice, scenario, open_ended, writing_sample, calibration, etc.) to triangulate self-reported preferences against observed behavior.

## Starting an Interview

1. Generate a UUID session ID.
2. Create the session directory at `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/`.
3. Initialize `state.json` with status `init`, empty response arrays, and module progress tracking.
4. Load the question bank from the project's `question-bank/modules/` directory.
5. Begin with the screening/demographic module (SD) to establish baseline writer type and branching path.
6. Progress through modules in sequence, applying branching rules and format rotation to maintain engagement.

## Resuming an Interview

1. List session directories under `${CLAUDE_PLUGIN_DATA}/sessions/`.
2. Identify sessions with status `paused` or `in_progress` in their `state.json`.
3. Load the selected session's state, including the last answered question, current module, and accumulated responses.
4. Resume from the next unanswered question, preserving all prior scoring and branching decisions.

## Profile Output

Voice produces a dual-output voice profile stored as `profile.json` in the session directory:

- **Self-Report Layer**: Direct preference scores derived from likert, forced_choice, and semantic_differential responses. These capture what the participant believes about their own voice.
- **Computational Analysis Layer**: Scores derived from NLP analysis of open_ended, writing_sample, and process_narration responses. These capture what the participant actually does in practice.
- **Calibration**: Calibration questions cross-reference self-report against behavioral signals to produce a calibration delta — the gap between perceived and actual style. High deltas flag dimensions where the participant's self-image diverges from their practice.

The final profile includes per-dimension scores, a composite writer-type classification, distinctive features, and calibration annotations.

## Session Storage

All session data is stored under `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/`:

- `state.json` — Session state: status, current module, current question index, branching path, timestamps
- `responses.json` — Raw responses keyed by question_id with timestamps
- `scores.json` — Running dimension scores updated after each response
- `profile.json` — Final assembled voice profile (written on completion)
- `writing_samples/` — Collected writing samples for NLP analysis
