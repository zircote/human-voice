---
diataxis_type: reference
diataxis_describes: "Environment variables, CLI flags, directory layout, session structure, and file formats"
---

# Configuration Reference

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `MIVOCA_QUESTION_BANK` | Path to the question-bank directory containing scoring metadata and module definitions. Overrides automatic parent-walk discovery. The `--metadata-dir` CLI flag takes precedence over this variable. | _(none)_ |

## CLI Flags

| Flag | Command | Purpose |
|---|---|---|
| `--session-dir PATH` | `mivoca-scoring score`, `mivoca-nlp analyze-session`, `mivoca-quality check-session` | Path to a session directory. Required for all session-scoped operations. |
| `--metadata-dir PATH` | `mivoca-scoring score` | Path to question-bank directory containing scoring metadata. Overrides automatic discovery and the `MIVOCA_QUESTION_BANK` environment variable. |
| `--model NAME` | `mivoca-nlp` | spaCy language model to use. Defaults to `en_core_web_sm`. |

## Directory Layout

### Home directory: `~/.human-voice/`

| Path | Type | Description |
|---|---|---|
| `config.json` | File | Global Mivoca configuration. |
| `sessions/` | Directory | Contains all session directories, keyed by UUID. |
| `question-bank/` | Directory | Default location for question bank data. Used as a fallback during metadata discovery. |
| `profile.json` | File | The most recently completed voice profile. |
| `voice-prompt.txt` | File | Generated voice prompt derived from the completed profile. |

### Session directory: `~/.human-voice/sessions/{session_id}/`

| Path | Type | Description |
|---|---|---|
| `state.json` | File | Session state: status, current module, branch path, quality flags, timestamps. |
| `responses.jsonl` | File | Append-only log of all responses. One JSON object per line. |
| `writing-samples/` | Directory | Writing sample files collected during the interview. Each sample is a JSON file. NLP analysis output files use the suffix `.analysis.json`. |
| `scores/` | Directory | Scoring output directory. |
| `scores/self-report.json` | File | Full scoring pipeline output: quality checks, semantic differentials, dimension scores, calibration report, merged profile. |
| `scores/observed.json` | File | Aggregated NLP observation scores. Written by the scoring engine when writing sample analyses are available. |
| `metadata/` | Directory | Optional session-local scoring metadata. Searched before shared question-bank directories. |
| `questions.json` | File | Optional session-local copy of the question bank. If present, the scoring engine uses this instead of loading from question-bank module files. |

## File Formats

### responses.jsonl

JSON Lines format. Each line is a JSON object representing one response.

```json
{"question_id": "M01-Q01", "module_id": "M01", "response": "formal", "duration_ms": 4200, "timestamp": "2026-04-04T14:30:00Z"}
```

Fields vary by question type. Common fields: `question_id`, `module_id`, `response`, `duration_ms`, `timestamp`.

### state.json

JSON object containing session state.

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "state": "in_progress",
  "previous_state": null,
  "writer_type": "business_professional",
  "branch_path": "business",
  "current_module": "M03",
  "current_question_index": 4,
  "modules_completed": ["M01", "M02"],
  "questions_answered": 22,
  "quality_flags": {},
  "created_at": "2026-04-04T14:00:00Z",
  "updated_at": "2026-04-04T14:30:00Z"
}
```

### scores/self-report.json

JSON object containing the full scoring pipeline output. See the [CLI Reference](cli.md) `mivoca-scoring score` output section for field descriptions.

### Writing sample files

JSON objects in `writing-samples/`. Each file contains a `raw_text`, `text`, or `content` field with the writing sample text. NLP analysis output is written alongside the source as `{filename}.analysis.json` and conforms to the `writing-analysis.schema.json` schema documented in the [Schema Reference](schemas.md#writing-analysis).

## Metadata Discovery Order

When the scoring engine needs question-bank metadata files (`dimension-item-mapping.json`, `scoring-weights.json`), it searches the following locations in order and uses the first match:

1. Explicit `--metadata-dir` flag value
2. `MIVOCA_QUESTION_BANK` environment variable
3. Session-local `metadata/` subdirectory, then the session directory itself
4. Parent directory walk from the session directory (up to 5 levels), looking for `question-bank/`
5. `~/.human-voice/question-bank/`

## Related documentation

- [CLI Reference](cli.md) for command syntax and output formats
- [Schema Reference](schemas.md) for JSON Schema definitions
- [Dimensions Reference](dimensions.md) for voice dimension definitions
