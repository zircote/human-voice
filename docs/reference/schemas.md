---
diataxis_type: reference
diataxis_describes: JSON schemas for questions, responses, sessions, profiles, and writing analysis
---

# Schema Reference

All schemas use JSON Schema Draft 2020-12. Schema files are located in `question-bank/schemas/`.

| Schema | File | ID |
|---|---|---|
| [Configuration](#configuration) | `config.schema.json` | `https://human-voice.zircote.com/schemas/config.schema.json` |
| [Question](#question) | `question.schema.json` | `https://voice.zircote.com/schemas/question.schema.json` |
| [Response](#response) | `response.schema.json` | `https://voice.zircote.com/schemas/response.schema.json` |
| [Session State](#session-state) | `session-state.schema.json` | `https://voice.zircote.com/schemas/session-state.schema.json` |
| [Voice Profile](#voice-profile) | `voice-profile.schema.json` | `https://voice.zircote.com/schemas/voice-profile.schema.json` |
| [Writing Analysis](#writing-analysis) | `writing-analysis.schema.json` | `https://voice.zircote.com/schemas/writing-analysis.schema.json` |

---

## Configuration

Defines the unified configuration for the human-voice plugin, covering AI writing pattern detection settings and voice elicitation interview settings. Stored at `$CLAUDE_PLUGIN_DATA/config.json`.

The schema contains two top-level sections:

- **detection**: File scanning scope, pattern toggles for character/language/structural/voice patterns, fix behavior, and output formatting
- **interview**: Session parameters, quality monitoring thresholds, scoring algorithm weights, adaptive elicitation settings, deep-dive limits, and profile output paths

See the [Configuration Reference](configuration.md#configjson-structure) for a full key-by-key breakdown with defaults and descriptions.

---

## Question

Defines a single question in the voice elicitation interview engine. Each question belongs to a module and carries scoring rules, branching metadata, and sequencing constraints.

### Required Fields

| Field | Type | Constraints | Description |
|---|---|---|---|
| `question_id` | string | Pattern: `^(M\d{2}-[A-Z]{1,2}\d{2}[a-z]?\|SD-\d{2})$` | Unique identifier. Standard modules use `Mxx-Qnn`; semantic differential uses `SD-nn`. |
| `module_id` | string | Pattern: `^(M\d{2}\|SD)$` | Parent module identifier. |
| `module_name` | string | minLength: 1 | Human-readable module name. |
| `text` | string | minLength: 1 | Question text presented to the participant. |
| `type` | string | enum | Response format type. See [Question Types](#question-types). |
| `metadata` | object | | Sequencing, bias, and timing metadata. See [Question Metadata](#question-metadata). |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `options` | array of `{value, label}` | Response options for closed-ended types. Minimum 2 items. `value` is string or number; `label` is a display string. |
| `follow_up` | object | Conditional follow-up: `{condition, question_id}`. Triggers when the response matches `condition`. |
| `scoring` | object | Dimension scoring configuration. See [Scoring](#question-scoring). |

### Question Types

| Type | Description |
|---|---|
| `likert` | Likert scale rating |
| `forced_choice` | Binary or constrained choice |
| `semantic_differential` | Bipolar adjective pair on a 7-point scale |
| `scenario` | Situational judgment / scenario-based |
| `open_ended` | Free-text response |
| `projective` | Indirect/projective measurement |
| `writing_sample` | Extended writing prompt |
| `calibration` | Self-assessment calibration |
| `select` | Single-select from options |
| `select_multiple` | Multi-select from options |
| `behavioral` | Behavioral observation prompt |
| `process_narration` | Think-aloud process narration |

### Question Metadata

| Field | Type | Required | Description |
|---|---|---|---|
| `self_reportability_tier` | integer | yes | Tier 1-4. See [Dimensions Reference](dimensions.md#self-reportability-tiers). |
| `estimated_seconds` | integer | yes | Estimated response time in seconds. |
| `format_category` | string | yes | Category label for format rotation tracking. |
| `finding_refs` | array of string | no | Research finding references. |
| `bias_mitigation` | string | no | Bias mitigation strategy description. |
| `branching` | object | no | `{required_branches, excluded_branches}` -- arrays of writer type strings. `["*"]` means all branches. |
| `position` | object | no | `{module_sequence, funnel_stage}`. Funnel stages: `screening`, `core`, `deep_dive`, `wrap_up`. |

### Question Scoring

| Field | Type | Description |
|---|---|---|
| `dimensions` | array of string | Dimension keys this question contributes to. |
| `weights` | object | Dimension-keyed weights (0-1) for relative contribution. |
| `scoring_map` | object | Maps response values to numeric scores per dimension. |

### Example

```json
{
  "question_id": "M03-Q01",
  "module_id": "M03",
  "module_name": "Formality & Register",
  "text": "How would you describe your typical writing tone?",
  "type": "likert",
  "options": [
    {"value": 1, "label": "Very informal"},
    {"value": 7, "label": "Very formal"}
  ],
  "scoring": {
    "dimensions": ["formality"],
    "weights": {"formality": 1.0},
    "scoring_map": {"1": {"formality": 1}, "7": {"formality": 7}}
  },
  "metadata": {
    "self_reportability_tier": 1,
    "estimated_seconds": 15,
    "format_category": "likert"
  }
}
```

---

## Response

Captures a single participant response during a voice elicitation session. Includes the answer, timing telemetry, and quality flags.

### Required Fields

| Field | Type | Constraints | Description |
|---|---|---|---|
| `response_id` | string | uuid | Unique response identifier. |
| `session_id` | string | uuid | Parent session identifier. |
| `question_id` | string | | Matches a `question_id` in the question bank. |
| `timestamp` | string | date-time | ISO-8601 submission timestamp. |
| `value` | string, number, or null | | Primary response value. Type depends on question type. Null if skipped. |
| `timing` | object | | Timing telemetry. See [Timing](#response-timing). |
| `quality_flags` | object | | Automated quality indicators. See [Quality Flags](#response-quality-flags). |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `raw_text` | string or null | Free-text content for open-ended, writing sample, and process narration questions. |
| `selected_options` | array of string or null | Selected option values for select/select_multiple types. |
| `scale_value` | number or null | Numeric scale position for Likert and rating-scale responses. |
| `semantic_differential_value` | number or null | Position on semantic differential scale (1.0-7.0). |

### Response Timing

| Field | Type | Description |
|---|---|---|
| `displayed_at` | string (date-time) | When the question was first displayed. |
| `first_interaction_at` | string (date-time) | First participant interaction (click, keypress). |
| `submitted_at` | string (date-time) | When the response was submitted. |
| `duration_ms` | integer (min: 0) | Total time from display to submission in milliseconds. |

### Response Quality Flags

| Field | Type | Description |
|---|---|---|
| `too_fast` | boolean | Response duration below minimum threshold for the question type. |
| `straightline_sequence` | integer (min: 0) | Count of consecutive identical responses ending with this one. |
| `changed_answer` | boolean | Participant changed their initial selection before submitting. |

---

## Session State

Represents the complete state of an interview session at any point in time. Enables pause/resume and adaptive interview flow.

### Required Fields

| Field | Type | Constraints | Description |
|---|---|---|---|
| `session_id` | string | uuid | Session identifier. |
| `created_at` | string | date-time | Session creation timestamp. |
| `updated_at` | string | date-time | Most recent state update. |
| `state` | string | enum | Current session phase. See [Session States](#session-states). |
| `writer_type` | string or null | enum or null | Determined writer type. Null until branching completes. |
| `branch_path` | array of string | | Ordered branching decisions. |
| `current_module` | string or null | | Currently active module ID. Null between modules. |
| `current_question_index` | integer | min: 0 | Zero-based index within the active module. |
| `questions_answered` | integer | min: 0 | Total questions answered. |
| `questions_remaining_estimate` | integer | min: 0 | Estimated remaining questions. |
| `elapsed_seconds` | number | min: 0 | Total elapsed time, excluding paused time. |
| `format_streak` | object | | `{current_type: string, count: integer}` for monotony prevention. |
| `quality_flags` | object | | Aggregated quality metrics. See [Session Quality Flags](#session-quality-flags). |
| `module_progress` | object | | Module ID to status mapping. Values: `pending`, `in_progress`, `complete`, `skipped`. |
| `deep_dives_triggered` | array of string | | Deep dive identifiers that have been triggered. |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `deep_dive_return` | object or null | Bookmark for returning after a deep dive: `{module: string, question_index: integer}`. |
| `previous_state` | string or null | Stored state value before pausing, used by resume. |

### Session States

| State | Description |
|---|---|
| `init` | Session created, interview not yet started. |
| `screening` | Administering screening/demographic questions. |
| `branching` | Evaluating writer-type routing. |
| `in_progress` | Core interview underway. |
| `deep_dive` | Administering injected deep-dive questions. |
| `engagement_reset` | Engagement reset intervention active. |
| `writing_samples` | Collecting writing samples. |
| `paused` | Session paused by participant. |
| `interview_complete` | All questions administered. |
| `scoring` | Running scoring pipeline. |
| `analyzing` | Running NLP analysis. |
| `generating` | Generating voice profile. |
| `complete` | Profile generated, session finished. |

### Writer Types

| Value | Description |
|---|---|
| `creative_literary` | Creative and literary writing focus. |
| `business_professional` | Business and professional writing focus. |
| `academic_technical` | Academic and technical writing focus. |
| `personal_journalistic` | Personal and journalistic writing focus (default). |

### Session Quality Flags

| Field | Type | Description |
|---|---|---|
| `straightline_count` | integer | Total straightlining-flagged responses. |
| `too_fast_count` | integer | Total too-fast-flagged responses. |
| `attention_checks_passed` | integer | Attention checks answered correctly. |
| `attention_checks_total` | integer | Total attention checks presented. |
| `engagement_resets_triggered` | integer | Engagement reset interventions activated. |

---

## Voice Profile

The primary output artifact. A comprehensive, quantified representation of a writer's voice across gold-standard dimensions, gap dimensions, semantic differentials, calibration data, and distinctive features.

Schema version identifier: `voice-profile/v1`.

### Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | const `"voice-profile/v1"` | Schema version. |
| `profile_id` | string (uuid) | Unique profile identifier. |
| `created_at` | string (date-time) | Generation timestamp. |
| `version` | string | Semantic version (e.g., `"1.0.0"`). Pattern: `^\d+\.\d+\.\d+$`. |
| `session_id` | string (uuid) | Source session identifier. |
| `identity_summary` | string | Natural-language voice identity summary. |
| `writer_type` | string | Writer type that guided interview branching. |
| `gold_standard_dimensions` | object | 8 core dimensions. See [Gold Standard Dimensions](dimensions.md#gold-standard-dimensions). |
| `gap_dimensions` | object | Secondary dimensions keyed by name. Each: `{score: 0-100, source: "self_report"\|"observed"\|"both"}`. |
| `semantic_differential` | object | 20 bipolar pair ratings. Keys are hyphenated pair identifiers; values are 1.0-7.0. |
| `calibration` | object | Self-awareness calibration data. See [Calibration](#profile-calibration). |
| `distinctive_features` | array of string | Noteworthy voice characteristics. |
| `voice_stability_map` | object | `{stable_across_contexts: [string], adapts_by_context: [string]}`. |
| `writing_sample_analysis` | object | Aggregate NLP statistics: `{sample_count, total_words}` plus additional computed metrics. |
| `metadata` | object | Session and quality metadata. See [Profile Metadata](#profile-metadata). |

### Gold Standard Dimension Object

Each of the 8 gold standard dimensions has the following structure:

| Field | Type | Range | Description |
|---|---|---|---|
| `score` | integer | 0-100 | Composite score blending self-report and observed, weighted by confidence. |
| `self_report` | integer | 0-100 | Score from participant's self-reported responses. |
| `observed` | integer | 0-100 | Score from behavioral observation and writing sample analysis. |
| `confidence` | number | 0-1 | Confidence in the composite score. Influenced by self-reportability tier, response quality, and measurement agreement. |

### Profile Calibration

| Field | Type | Description |
|---|---|---|
| `overall_self_awareness` | number (0-1) | Aggregate self-awareness score. |
| `high_awareness_dimensions` | array of string | Dimensions where self-report closely matches observed. |
| `blind_spots` | array of string | Dimensions where self-report diverges significantly from observed. |
| `aspirational_gaps` | array of object | Each: `{dimension, current: 0-100, desired: 0-100, delta}`. |

### Profile Metadata

| Field | Type | Description |
|---|---|---|
| `questions_answered` | integer | Total questions answered. |
| `modules_completed` | integer | Modules fully completed. |
| `duration_seconds` | number | Total session duration. |
| `branch_path` | array of string | Branching path through the adaptive interview. |
| `attention_check_pass` | boolean | Whether minimum attention check threshold was met. |
| `satisficing_flags` | integer | Total satisficing indicators detected. |

---

## Writing Analysis

Output of the NLP analysis pipeline for a single writing sample. Contains lexical, syntactic, pragmatic, discourse, and formatting features along with readability scores and LIWC-equivalent psycholinguistic markers.

### Required Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `sample_id` | string (uuid) | Analysis identifier. |
| `session_id` | string (uuid) | Parent session. |
| `prompt_id` | string | Eliciting prompt identifier. |
| `prompt_type` | string | One of: `spontaneous`, `reflective`, `professional`, `creative`. |
| `raw_text` | string | Original unmodified writing sample. |
| `word_count` | integer | Total words. |
| `sentence_count` | integer | Total sentences. |

### Lexical Features

| Field | Type | Range | Description |
|---|---|---|---|
| `mtld` | number | 0+ | Measure of Textual Lexical Diversity. Higher = more diverse. |
| `mattr_window_50` | number | 0-1 | Moving Average Type-Token Ratio (50-word window). |
| `hapax_ratio` | number | 0-1 | Proportion of words appearing exactly once. |
| `avg_word_length_chars` | number | 0+ | Average word length in characters. |
| `avg_word_length_syllables` | number | 0+ | Average word length in syllables. |
| `latinate_germanic_ratio` | number | 0+ | Ratio of Latinate to Germanic-origin words. Higher = more formal. |
| `vocabulary_sophistication` | number | 0+ | Proportion of low-frequency words. |

### Syntactic Features

| Field | Type | Range | Description |
|---|---|---|---|
| `mean_sentence_length` | number | 0+ | Average words per sentence. |
| `sentence_length_sd` | number | 0+ | Standard deviation of sentence lengths. |
| `mean_clause_length` | number | 0+ | Average words per clause. |
| `clauses_per_sentence` | number | 0+ | Average clauses per sentence. |
| `dependent_clause_ratio` | number | 0-1 | Proportion of dependent (subordinate) clauses. |
| `complex_t_unit_ratio` | number | 0-1 | Proportion of T-units containing dependent clauses. |
| `complex_nominal_per_t_unit` | number | 0+ | Complex nominals per T-unit. |
| `active_voice_ratio` | number | 0-1 | Proportion of active-voice clauses. |
| `left_branching_ratio` | number | 0-1 | Proportion of left-branching (front-loaded modifier) sentences. |

### Pragmatic Features

| Field | Type | Description |
|---|---|---|
| `hedge_count` | integer | Hedging expressions ("perhaps", "might", "somewhat"). |
| `boost_count` | integer | Boosting expressions ("clearly", "obviously", "certainly"). |
| `hedge_boost_ratio` | number | Ratio of hedges to boosters. >1 = cautious; <1 = confident. |
| `self_mention_count` | integer | First-person references. |
| `engagement_markers` | integer | Reader-engagement devices. |
| `attitude_markers` | integer | Explicit attitude expressions. |

### LIWC-Equivalent Markers

| Field | Type | Range | Description |
|---|---|---|---|
| `analytical_thinking` | number | 0-100 | Formal, logical thinking patterns. |
| `clout` | number | 0-100 | Social status and confidence. |
| `authenticity` | number | 0-100 | Honest, personal, disclosing language. |
| `emotional_tone` | number | 0-100 | Negative (0) to positive (100); 50 = neutral. |
| `first_person_singular_pct` | number | 0-100 | Percentage of I/me/my words. |
| `first_person_plural_pct` | number | 0-100 | Percentage of we/us/our words. |
| `second_person_pct` | number | 0-100 | Percentage of you/your words. |
| `positive_emotion_pct` | number | 0-100 | Positive emotion word percentage. |
| `negative_emotion_pct` | number | 0-100 | Negative emotion word percentage. |
| `cognitive_process_pct` | number | 0-100 | Cognitive process word percentage. |

### Formatting Features

| Field | Type | Description |
|---|---|---|
| `semicolons_per_100_words` | number | Semicolon frequency per 100 words. |
| `em_dashes_per_100_words` | number | Em dash frequency per 100 words. |
| `exclamation_marks` | integer | Total exclamation marks. |
| `question_marks` | integer | Total question marks. |
| `parenthetical_asides` | integer | Parenthetical expression count. |
| `contractions_per_100_words` | number | Contraction frequency per 100 words. Higher = more informal. |
| `avg_paragraph_length_words` | number | Average words per paragraph. |

### Discourse Features

| Field | Type | Range | Description |
|---|---|---|---|
| `causal_connective_density` | number | 0+ | Causal connectives (because, therefore) per 100 words. |
| `additive_connective_density` | number | 0+ | Additive connectives (and, also, moreover) per 100 words. |
| `adversative_connective_density` | number | 0+ | Adversative connectives (but, however) per 100 words. |
| `temporal_connective_density` | number | 0+ | Temporal connectives (then, before, after) per 100 words. |
| `referential_cohesion` | number | 0-1 | Referential overlap between adjacent sentences. |
| `propositional_idea_density` | number | 0+ | Propositions per sentence. |

### Readability Scores

| Field | Type | Description |
|---|---|---|
| `formality_f_score` | number | Heylighen & Dewaele F-score. Typical range: -100 to 100. |
| `flesch_kincaid_grade` | number | U.S. school grade level. |
| `flesch_reading_ease` | number | Higher = easier text. |
| `gunning_fog` | number | Years of formal education needed. |
