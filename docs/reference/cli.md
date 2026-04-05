---
diataxis_type: reference
diataxis_describes: CLI commands and bin/ executables
---

# CLI Reference

All CLI commands output JSON to stdout. Errors are written to stderr as JSON objects with an `error` key. Exit code `0` indicates success; non-zero indicates failure.

Session data is stored under `~/.human-voice/sessions/{session_id}/`.

## bin/ Executables

Each executable is a thin bash wrapper that delegates to a Python module via the project virtualenv (`.venv/bin/python3`), falling back to system `python3`.

---

### mivoca-session

Session lifecycle management. Delegates to `lib.session`.

#### Subcommands

| Subcommand | Arguments | Description |
|---|---|---|
| `create` | _(none)_ | Create a new session. Generates a UUID, creates the on-disk directory structure, and initializes `state.json` and `responses.jsonl`. |
| `load` | `SESSION_ID` | Load session state by UUID. Returns the full `state.json` contents. |
| `list` | _(none)_ | List all sessions with summary fields: `id`, `state`, `writer_type`, `questions_answered`, `created_at`, `updated_at`. Sorted by `updated_at` descending. |
| `pause` | `SESSION_ID` | Pause a session. Stores the current state in `previous_state` and sets `state` to `"paused"`. Idempotent if already paused. |
| `resume` | `SESSION_ID` | Resume a paused session. Restores `state` from `previous_state`. Raises an error if the session is not paused. |

#### Output Format

All subcommands return JSON. `create`, `load`, `pause`, and `resume` return the session state object. `list` returns an array of summary objects.

#### Example

```bash
mivoca-session create
# {"session_id": "a1b2c3d4-...", "state": "init", ...}

mivoca-session load a1b2c3d4-e5f6-7890-abcd-ef1234567890
# {"session_id": "a1b2c3d4-...", "state": "in_progress", ...}

mivoca-session list
# [{"id": "a1b2c3d4-...", "state": "paused", ...}, ...]

mivoca-session pause a1b2c3d4-e5f6-7890-abcd-ef1234567890
mivoca-session resume a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

### mivoca-branching

Interview routing evaluator. Delegates to `lib.branching`.

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `evaluate-route` | `--responses JSON` | Determine the writer-type branch from screening responses. Accepts a JSON object mapping question IDs to response values, or a JSON array of `{question_id, response}` objects. |
| `module-sequence` | `--writer-type TYPE` | Return the ordered module sequence for a writer type. Each entry includes `module_id`, `phase`, `is_core`, and `is_active`. |
| `check-triggers` | `--module ID --state PATH --responses PATH` | Check deep-dive triggers for a module. `--state` is a path to a JSON file with session state metrics. `--responses` is a path to a JSONL file of response records. |

#### Output Format

`evaluate-route` returns: `{writer_type, branch_path, activated_modules, description}`.

`module-sequence` returns an array of `{module_id, phase, is_core, is_active}` objects.

`check-triggers` returns `{"triggered": false}` if no trigger fires, or `{triggered, trigger_id, inject_questions, purpose}` if a trigger fires.

#### Example

```bash
mivoca-branching evaluate-route \
  --responses '{"M01-Q05": "business", "M01-Q10": 5}'

mivoca-branching module-sequence --writer-type business_professional

mivoca-branching check-triggers \
  --module M03 \
  --state ~/.human-voice/sessions/abc123/state.json \
  --responses ~/.human-voice/sessions/abc123/responses.jsonl
```

---

### mivoca-sequencer

Question sequencing engine. Delegates to `lib.sequencer`.

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `next-question` | `--state PATH --responses PATH` | Determine the next question to present. `--state` is a path to `state.json`. `--responses` is a path to `responses.jsonl`. |
| `active-modules` | `--writer-type TYPE` | List the ordered active module IDs for a writer type. |

#### Output Format

`next-question` returns:

| Field | Type | Description |
|---|---|---|
| `question` | object or null | The question object to present, or null for non-question actions. |
| `action` | string | One of: `present_question`, `module_transition`, `engagement_reset`, `deep_dive`, `interview_complete`. |
| `module_id` | string | Module the question belongs to. |
| `transition_message` | string or null | Message for module transitions. |
| `progress` | object | `{answered, estimated_remaining, percent}`. |

`active-modules` returns a JSON array of module ID strings.

#### Example

```bash
mivoca-sequencer next-question \
  --state ~/.human-voice/sessions/abc123/state.json \
  --responses ~/.human-voice/sessions/abc123/responses.jsonl

mivoca-sequencer active-modules --writer-type academic_technical
```

---

### mivoca-quality

Satisficing and quality detection. Delegates to `lib.quality`.

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `check-response` | `--response JSON --recent JSON --question JSON` | Check a single response for quality issues. `--response` is a JSON string of the current response. `--recent` is a JSON array of recent responses. `--question` is a JSON string of the question definition. |
| `check-session` | `--session-dir PATH` | Generate a quality report for a complete session. PATH is a session directory (e.g., `~/.human-voice/sessions/{id}/`). |

#### Output Format

`check-response` returns:

| Field | Type | Description |
|---|---|---|
| `flags` | object | `{too_fast, straightlining, alternation}` -- all booleans. |
| `flag_count` | integer | Number of active flags. |
| `needs_engagement_reset` | boolean | True when 2 or more flags are active. |
| `details` | string or null | Human-readable description of detected issues. |

`check-session` returns a comprehensive quality report including attention check results.

#### Quality Detection Thresholds

| Check | Condition |
|---|---|
| Too-fast response | `duration_ms < 2000` for questions with `estimated_seconds > 10` |
| Straightlining | 5 or more consecutive identical scale values |
| Alternation | 4 or more alternating extreme values (1, 7, 1, 7...) |
| Engagement reset | 2 or more concurrent quality flags |

#### Example

```bash
mivoca-quality check-response \
  --response '{"value": 3, "duration_ms": 800, "question_type": "likert_scale"}' \
  --recent '[...]' \
  --question '{"estimated_seconds": 15}'

mivoca-quality check-session \
  --session-dir ~/.human-voice/sessions/a1b2c3d4/
```

---

### mivoca-nlp

Stylometric NLP analysis pipeline. Delegates to `mivoca_nlp`.

#### Global Options

| Option | Default | Description |
|---|---|---|
| `--model` | `en_core_web_sm` | spaCy language model to use. |

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `analyze` | `--input PATH [--output PATH]` | Analyze a single writing sample JSON file. Input must contain a `raw_text`, `text`, or `content` field. Output defaults to `{input}.analysis.json`. |
| `analyze-session` | `--session-dir PATH` | Analyze all writing sample JSON files in a session's `writing-samples/` subdirectory. Skips files ending in `.analysis.json`. |

#### Output Format

Each analysis produces a JSON file conforming to `writing-analysis.schema.json`. See [Schemas Reference](schemas.md#writing-analysis) for field details.

#### Example

```bash
mivoca-nlp analyze \
  --input ~/.human-voice/sessions/abc123/writing-samples/sample-01.json \
  --output analysis.json

mivoca-nlp analyze-session \
  --session-dir ~/.human-voice/sessions/abc123/
```

---

### mivoca-scoring

Scoring engine. Delegates to `mivoca_scoring`.

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `score` | `--session-dir PATH [--metadata-dir PATH]` | Run the full scoring pipeline on a session directory. Reads `responses.jsonl` and question-bank metadata. |

#### Options

| Option | Required | Description |
|---|---|---|
| `--session-dir PATH` | Yes | Path to the session directory containing `responses.jsonl`. |
| `--metadata-dir PATH` | No | Path to a question-bank directory containing scoring metadata (`dimension-item-mapping.json`, `scoring-weights.json`). Overrides automatic discovery. |

#### Environment Variables

| Variable | Description |
|---|---|
| `MIVOCA_QUESTION_BANK` | Path to the question-bank directory. Serves the same purpose as `--metadata-dir`. The explicit flag takes precedence over this variable. |

#### Metadata Discovery Order

The scoring engine locates question-bank metadata files in the following order. It uses the first directory that contains the required files.

1. Explicit `--metadata-dir` flag value
2. `MIVOCA_QUESTION_BANK` environment variable
3. Session-local `metadata/` subdirectory
4. Parent directory walk from the session directory (up to 5 levels), looking for a `question-bank/` directory
5. Well-known fallback: `~/.human-voice/question-bank/`

#### Pipeline Stages

1. Quality checks on response data
2. Semantic differential normalization
3. Self-report dimension scoring
4. Calibration (if observed NLP scores are available in `scores/observed.json`)
5. Profile assembly

#### Output

Writes results to `{session-dir}/scores/self-report.json` containing:

| Field | Type | Description |
|---|---|---|
| `version` | string | Scoring engine version. |
| `quality` | object | Quality check results. |
| `semantic_differentials` | object | Normalized semantic differential scores. |
| `self_report_scores` | object | Per-dimension self-report scores. |
| `calibration` | object or null | Calibration report (present only if observed scores exist). |
| `profile` | object | Merged voice profile. |

#### Example

```bash
mivoca-scoring score \
  --session-dir ~/.human-voice/sessions/a1b2c3d4/
```

---

## Slash Commands

Slash commands are Claude Code custom commands defined in `commands/`. They orchestrate multi-step interview workflows using the bin/ executables and direct file operations.

### /mivoca:interview

Start a new voice elicitation interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion, Agent |
| **Creates** | Session directory at `~/.human-voice/sessions/{session_id}/` |
| **Initializes** | `state.json`, `responses.json`, `scores.json` |
| **Behavior** | Creates a new session directory, then begins an interactive voice elicitation interview. Questions are presented one at a time in conversational format. The participant types responses directly and may type `pause` at any time to suspend the session. On completion, scoring results are written to the session's `scores/` directory. |

### /mivoca:resume

Resume a paused or interrupted interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion, Agent |
| **Arguments** | Optional session ID (prompts for selection if omitted) |
| **Behavior** | Scans `~/.human-voice/sessions/` for sessions with status `paused` or `in_progress`, presents a selection table, validates session integrity, then resumes the interview conductor from the exact pause point. |

### /mivoca:status

Display progress and status of an interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Arguments** | Optional session ID (defaults to most recently updated) |
| **Output** | Session metadata, questions answered vs. estimated total, modules completed, current position, estimated time remaining, and provisional dimension scores. |

### /mivoca:profile

View a completed voice profile.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Arguments** | Optional session ID (defaults to most recent completed session) |
| **Requires** | Session status `complete` and `profile.json` present |
| **Output** | Formatted display of writer type, dimension scores (self-report, computed, delta), calibration summary, distinctive features, and recommendations. |

### /mivoca:sessions

List all interview sessions.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Output** | Table of all sessions with session ID, status, writer type, questions answered, modules completed, and last updated date. Sorted by most recently active first. |
