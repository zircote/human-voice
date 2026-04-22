---
diataxis_type: reference
diataxis_describes: "Environment variables, CLI flags, directory layout, session structure, and file formats"
---

# Configuration Reference

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `VOICE_QUESTION_BANK` | Path to the question-bank directory containing scoring metadata and module definitions. Overrides automatic parent-walk discovery. The `--metadata-dir` CLI flag takes precedence over this variable. Legacy name `MIVOCA_QUESTION_BANK` is also accepted as a fallback. | _(none)_ |
| `CLAUDE_PLUGIN_DATA` | Root data directory for the plugin. Honoured only when the path is recognised as this plugin's data dir (basename contains `human-voice`, or the directory contains a `.human-voice-plugin` marker / `voice-prompt.txt`). If set but unrecognised — e.g. leaked from another plugin in the same session — the value is ignored and resolution falls back to `~/.human-voice`. | _(none)_ |
| `HUMAN_VOICE_DATA_DIR` | Plugin-scoped override for the data directory. Takes precedence over `CLAUDE_PLUGIN_DATA`. Use this to force a specific path regardless of runtime-supplied values. | _(none)_ |

## CLI Flags

| Flag | Command | Purpose |
|---|---|---|
| `--session-dir PATH` | `voice-scoring score`, `voice-nlp analyze-session`, `voice-quality check-session` | Path to a session directory. Required for all session-scoped operations. |
| `--metadata-dir PATH` | `voice-scoring score` | Path to question-bank directory containing scoring metadata. Overrides automatic discovery and the `VOICE_QUESTION_BANK` environment variable. |
| `--model NAME` | `voice-nlp` | spaCy language model to use. Defaults to `en_core_web_sm`. |

## Directory Layout

### Home directory: `${CLAUDE_PLUGIN_DATA}/`

| Path | Type | Description |
|---|---|---|
| `config.json` | File | Global Voice configuration. |
| `sessions/` | Directory | Contains all session directories, keyed by UUID. |
| `question-bank/` | Directory | Default location for question bank data. Used as a fallback during metadata discovery. |
| `profile.json` | File | The most recently completed voice profile. |
| `voice-prompt.txt` | File | Generated voice prompt derived from the completed profile. |

### Session directory: `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/`

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

JSON object containing the full scoring pipeline output. See the [CLI Reference](cli.md) `voice-scoring score` output section for field descriptions.

### Writing sample files

JSON objects in `writing-samples/`. Each file contains a `raw_text`, `text`, or `content` field with the writing sample text. NLP analysis output is written alongside the source as `{filename}.analysis.json` and conforms to the `writing-analysis.schema.json` schema documented in the [Schema Reference](schemas.md#writing-analysis).

## Metadata Discovery Order

When the scoring engine needs question-bank metadata files (`dimension-item-mapping.json`, `scoring-weights.json`), it searches the following locations in order and uses the first match. For each candidate, the engine also checks a `scoring/` subdirectory.

1. Session-local `metadata/` subdirectory, then the session directory itself
2. Explicit `--metadata-dir` flag value
3. `VOICE_QUESTION_BANK` environment variable (legacy `MIVOCA_QUESTION_BANK` also accepted)
4. Parent directory walk from the session directory (up to 5 levels), looking for `question-bank/`
5. `~/.human-voice/question-bank/`

## Data Directory Resolution

The plugin resolves its data directory as follows:

1. If `CLAUDE_PLUGIN_DATA` is set (the Claude Code runtime sets this automatically), use that path
2. Otherwise, fall back to `~/.human-voice`

On first run, if data exists in `~/.human-voice` but `CLAUDE_PLUGIN_DATA` points elsewhere, the plugin migrates files from the legacy location automatically.

## config.json Structure

The configuration file lives at `${CLAUDE_PLUGIN_DATA}/config.json`. The file is JSON, validated against `question-bank/schemas/config.schema.json`. Partial configs are supported: any missing keys are filled from the built-in defaults via deep merge.

You can view the effective config at any time:

```bash
python3 -m lib.config show          # print full effective config
python3 -m lib.config get KEY_PATH  # get a specific value by dot path
python3 -m lib.config reset         # reset to defaults
```

### detection

| Key | Type | Default | Description |
|---|---|---|---|
| `extensions` | array of string | `[".md", ".mdx", ".txt"]` | File extensions to scan for AI patterns. Include the leading dot. |
| `content_directories` | array of string | `[]` | Directories to scan. Empty means scan the working directory recursively. |
| `ignore` | array of string | `[]` | Glob patterns for files and directories to exclude (e.g., `node_modules/**`). |

### detection.character_patterns

Each key is a boolean toggle. Set to `false` to skip that pattern category.

| Key | Default | Description |
|---|---|---|
| `em_dash` | `true` | Detect em dash (U+2014) characters. |
| `en_dash` | `true` | Detect en dash (U+2013) characters. |
| `smart_quotes` | `true` | Detect curly/smart quote characters. |
| `ellipsis` | `true` | Detect Unicode horizontal ellipsis (U+2026). |
| `emojis` | `true` | Detect emoji characters. |

### detection.language_patterns

| Key | Default | Description |
|---|---|---|
| `buzzwords` | `true` | Detect AI-favored buzzwords (delve, leverage, tapestry, etc.). |
| `hedging` | `true` | Detect excessive hedging language. |
| `filler` | `true` | Detect filler phrases that pad AI text. |
| `meta_commentary` | `true` | Detect self-referential meta-commentary. |

### detection.structural_patterns

| Key | Default | Description |
|---|---|---|
| `list_addiction` | `true` | Detect over-reliance on lists where prose fits better. |
| `rule_of_three` | `true` | Detect the AI tendency to group items in threes. |
| `from_x_to_y` | `true` | Detect "from X to Y" parallel constructions. |

### detection.voice_patterns

| Key | Default | Description |
|---|---|---|
| `passive_voice` | `true` | Detect excessive passive voice. |
| `generic_analogies` | `true` | Detect overused generic metaphors. |
| `perfect_grammar` | `true` | Detect unnaturally flawless grammar. |

### detection.fix

| Key | Type | Default | Description |
|---|---|---|---|
| `dry_run_by_default` | boolean | `true` | Preview changes without modifying files unless `--apply` is passed. |
| `backup_files` | boolean | `false` | Create `.bak` copies before applying fixes. |
| `report_format` | string | `"normal"` | Detail level: `"minimal"`, `"normal"`, or `"detailed"`. |

### detection.output

| Key | Type | Default | Description |
|---|---|---|---|
| `verbosity` | string | `"normal"` | Output verbosity: `"minimal"`, `"normal"`, or `"detailed"`. |
| `format` | string | `"markdown"` | Output format: `"markdown"` or `"json"`. |
| `show_line_numbers` | boolean | `true` | Include line numbers in scan output. |
| `max_results_per_tier` | integer | `50` | Maximum findings reported per detection tier. |

### interview

| Key | Type | Default | Description |
|---|---|---|---|
| `session_storage` | string | `"$CLAUDE_PLUGIN_DATA/sessions"` | Directory for session state persistence. |
| `total_estimated_minutes` | integer | `35` | Estimated interview duration in minutes. |
| `estimated_questions` | integer | `70` | Target question count for a complete session. |
| `format_streak_limit` | integer | `5` | Max consecutive same-format questions before a forced format change. |
| `default_branch` | string | `"personal_journalistic"` | Initial writer-type branch. One of: `creative_literary`, `business_professional`, `academic_technical`, `personal_journalistic`. |

### interview.quality

| Key | Type | Default | Description |
|---|---|---|---|
| `straightlining_threshold` | integer | `5` | Consecutive identical scale responses before flagging. |
| `speed_threshold_ms` | integer | `2000` | Minimum response time (ms) for speed-rushing detection. |
| `speed_exempt_below_seconds` | integer | `5` | Questions with expected time below this are exempt from speed checks. |
| `speed_applies_above_seconds` | integer | `10` | Speed checks apply only to questions with expected time above this. |
| `alternation_threshold` | integer | `4` | Consecutive alternating extreme values before flagging. |
| `alternation_extreme_values` | array | `[1, 7]` | Scale endpoints considered extreme for alternation detection. |
| `engagement_reset_min_flags` | integer | `2` | Quality flags needed to trigger an engagement reset. |
| `engagement_reset_max_per_session` | integer | `3` | Maximum engagement resets per session. |
| `session_invalid_threshold` | integer | `8` | Total flags that trigger automatic session invalidation. |
| `confidence_penalty_per_flag` | number | `0.05` | Confidence reduction per quality flag. |

### interview.attention_checks

| Key | Type | Default | Description |
|---|---|---|---|
| `min_checks_passed` | integer | `2` | Minimum attention checks that must pass for session validity. |
| `confidence_penalty_per_failure` | number | `0.1` | Confidence reduction per failed attention check. |

### interview.scoring

| Key | Type | Default | Description |
|---|---|---|---|
| `dimension_sd_weight` | number | `0.7` | Weight of the semantic differential score in each dimension composite. |
| `sd_normalized_weight` | number | `0.3` | Weight of the normalized SD component. Should sum to 1.0 with `dimension_sd_weight`. |
| `min_cronbach_alpha` | number | `0.60` | Minimum Cronbach's alpha for internal consistency. Dimensions below this are flagged as unreliable. |
| `reliability_tiers.tier_1` | array | `["formality", "directness", "conciseness", "enthusiasm", "technical_density"]` | Dimensions with highest item redundancy and expected reliability. |
| `reliability_tiers.tier_2` | array | `["humor", "warmth", "hedging", "figurative_language", "sentence_complexity"]` | Dimensions with fewer redundant items. |

### interview.elicitation

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `true` | Master toggle for adaptive probing. |
| `max_probes_per_question` | integer | `2` | Maximum follow-up probes per question. |
| `eligible_types` | array | `["open_ended", "writing_sample", "process_narration", "scenario", "projective"]` | Question types eligible for probing. |
| `min_words_open_ended` | integer | `15` | Minimum word count for open-ended responses. |
| `min_words_writing_sample` | integer | `40` | Minimum word count for writing samples. |
| `min_words_scenario` | integer | `20` | Minimum word count for scenario responses. |
| `vagueness_indicators` | array | `["I don't know", "not sure", "it depends", "maybe", "I guess", "hard to say", "no preference"]` | Phrases that trigger probing in eligible types. |

### interview.deep_dives

| Key | Type | Default | Description |
|---|---|---|---|
| `max_per_session` | integer | `5` | Maximum deep-dive sequences per session. Set to 0 to disable. |
| `time_budget_minutes` | integer | `3` | Time budget per deep-dive sequence. |

### interview.profile

| Key | Type | Default | Description |
|---|---|---|---|
| `publish_to` | string | `"$CLAUDE_PLUGIN_DATA/profile.json"` | Path where the completed voice profile JSON is written. |
| `injection_to` | string | `"$CLAUDE_PLUGIN_DATA/voice-prompt.txt"` | Path where the voice prompt injection text is written. |
| `profiles_dir` | string | `"$CLAUDE_PLUGIN_DATA/profiles"` | Directory where named profiles are stored by the profile registry. |
| `population_means` | object | _(see below)_ | Population baseline statistics for z-score computation. |

#### population_means defaults

| Dimension | Mean | SD |
|---|---|---|
| `formality_f_score` | 55.0 | 10.0 |
| `flesch_kincaid_grade` | 10.0 | 3.0 |
| `liwc_clout` | 55.0 | 18.0 |
| `liwc_analytical` | 50.0 | 20.0 |
| `liwc_emotional_tone` | 50.0 | 20.0 |
| `avg_sentence_length` | 18.0 | 5.0 |
| `type_token_ratio` | 0.65 | 0.10 |
| `hedge_word_rate` | 0.02 | 0.01 |
| `passive_voice_rate` | 0.08 | 0.05 |
| `contraction_rate` | 0.04 | 0.03 |

## Related documentation

- [CLI Reference](cli.md) for command syntax and output formats
- [Schema Reference](schemas.md) for JSON Schema definitions
- [Dimensions Reference](dimensions.md) for voice dimension definitions
