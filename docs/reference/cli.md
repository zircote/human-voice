---
diataxis_type: reference
diataxis_describes: CLI commands and bin/ executables
---

# CLI Reference

All CLI commands output JSON to stdout. Errors are written to stderr as JSON objects with an `error` key. Exit code `0` indicates success; non-zero indicates failure.

Session data is stored under `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/`.

## bin/ Executables

Each executable is a thin bash wrapper that delegates to a Python module via the project virtualenv (`.venv/bin/python3`), falling back to system `python3`.

---

### voice-session

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
voice-session create
# {"session_id": "a1b2c3d4-...", "state": "init", ...}

voice-session load a1b2c3d4-e5f6-7890-abcd-ef1234567890
# {"session_id": "a1b2c3d4-...", "state": "in_progress", ...}

voice-session list
# [{"id": "a1b2c3d4-...", "state": "paused", ...}, ...]

voice-session pause a1b2c3d4-e5f6-7890-abcd-ef1234567890
voice-session resume a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

### voice-branching

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
voice-branching evaluate-route \
  --responses '{"M01-Q05": "business", "M01-Q10": 5}'

voice-branching module-sequence --writer-type business_professional

voice-branching check-triggers \
  --module M03 \
  --state ${CLAUDE_PLUGIN_DATA}/sessions/abc123/state.json \
  --responses ${CLAUDE_PLUGIN_DATA}/sessions/abc123/responses.jsonl
```

---

### voice-sequencer

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
voice-sequencer next-question \
  --state ${CLAUDE_PLUGIN_DATA}/sessions/abc123/state.json \
  --responses ${CLAUDE_PLUGIN_DATA}/sessions/abc123/responses.jsonl

voice-sequencer active-modules --writer-type academic_technical
```

---

### voice-quality

Satisficing and quality detection. Delegates to `lib.quality`.

#### Subcommands

| Subcommand | Options | Description |
|---|---|---|
| `check-response` | `--response JSON --recent JSON --question JSON` | Check a single response for quality issues. `--response` is a JSON string of the current response. `--recent` is a JSON array of recent responses. `--question` is a JSON string of the question definition. |
| `check-session` | `--session-dir PATH` | Generate a quality report for a complete session. PATH is a session directory (e.g., `${CLAUDE_PLUGIN_DATA}/sessions/{id}/`). |

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
voice-quality check-response \
  --response '{"value": 3, "duration_ms": 800, "question_type": "likert_scale"}' \
  --recent '[...]' \
  --question '{"estimated_seconds": 15}'

voice-quality check-session \
  --session-dir ${CLAUDE_PLUGIN_DATA}/sessions/a1b2c3d4/
```

---

### voice-nlp

Stylometric NLP analysis pipeline. Delegates to `voice_nlp`.

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
voice-nlp analyze \
  --input ${CLAUDE_PLUGIN_DATA}/sessions/abc123/writing-samples/sample-01.json \
  --output analysis.json

voice-nlp analyze-session \
  --session-dir ${CLAUDE_PLUGIN_DATA}/sessions/abc123/
```

---

### voice-scoring

Scoring engine. Delegates to `voice_scoring`.

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
| `VOICE_QUESTION_BANK` | Path to the question-bank directory. Serves the same purpose as `--metadata-dir`. The explicit flag takes precedence over this variable. Legacy name `MIVOCA_QUESTION_BANK` is also accepted as a fallback. |

#### Metadata Discovery Order

The scoring engine locates question-bank metadata files in the following order. It uses the first directory that contains the required files. For each candidate, the engine also checks a `scoring/` subdirectory.

1. Session-local `metadata/` subdirectory, then the session directory itself
2. Explicit `--metadata-dir` flag value
3. `VOICE_QUESTION_BANK` environment variable (legacy `MIVOCA_QUESTION_BANK` also accepted)
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
voice-scoring score \
  --session-dir ${CLAUDE_PLUGIN_DATA}/sessions/a1b2c3d4/
```

---

### voice-profiles

Profile registry management. Delegates to `lib.profile_registry`.

#### Subcommands

| Subcommand | Arguments | Description |
|---|---|---|
| `list` | _(none)_ | List all registered profiles with active marker, origin, and tags. |
| `activate` | `SLUG` | Set a profile as the active profile. Copies its `profile.json` and `voice-prompt.txt` to the top-level data directory. |
| `info` | `SLUG` | Show full registry entry for a profile (JSON output). |
| `delete` | `SLUG` | Delete a profile permanently. Cannot delete the currently active profile. |
| `install` | `SLUG [SLUG...] --to-repo PATH [--default SLUG]` | Install one or more profiles into a repository as `.github/copilot-instructions.md` with marker-delimited sections and profile routing logic. |
| `export` | `SLUG --to-repo PATH` | Install a single profile to a repo (alias for `install` with one slug). |
| `set-override` | `PATTERN SLUG` | Assign a profile to activate automatically when working in directories matching the glob pattern. |
| `remove-override` | `PATTERN` | Remove a directory override. |
| `migrate` | _(none)_ | Migrate a single top-level profile into the multi-profile registry. |

#### Example

```bash
voice-profiles list
#  * robert-allen         interview    personal, default
#    zircote-brand        designed     corporate, brand

voice-profiles activate zircote-brand
voice-profiles install robert-allen zircote-brand --to-repo ../my-repo --default robert-allen
voice-profiles set-override "/Users/me/Projects/novel/*" narrator-formal
voice-profiles remove-override "/Users/me/Projects/novel/*"
voice-profiles migrate
```

---

## Slash Commands

Slash commands are Claude Code custom commands defined in `commands/`. They orchestrate multi-step interview workflows using the bin/ executables and direct file operations.

### /voice:interview

Start a new voice elicitation interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion, Agent |
| **Creates** | Session directory at `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/` |
| **Initializes** | `state.json`, `responses.json`, `scores.json` |
| **Behavior** | Creates a new session directory, then begins an interactive voice elicitation interview. Questions are presented one at a time in conversational format. The participant types responses directly and may type `pause` at any time to suspend the session. On completion, scoring results are written to the session's `scores/` directory. |

### /voice:resume

Resume a paused or interrupted interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion, Agent |
| **Arguments** | Optional session ID (prompts for selection if omitted) |
| **Behavior** | Scans `${CLAUDE_PLUGIN_DATA}/sessions/` for sessions with status `paused` or `in_progress`, presents a selection table, validates session integrity, then resumes the interview conductor from the exact pause point. |

### /voice:status

Display progress and status of an interview session.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Arguments** | Optional session ID (defaults to most recently updated) |
| **Output** | Session metadata, questions answered vs. estimated total, modules completed, current position, estimated time remaining, and provisional dimension scores. |

### /voice:profile

View a completed voice profile.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Arguments** | Optional session ID (defaults to most recent completed session) |
| **Requires** | Session status `complete` and `profile.json` present |
| **Output** | Formatted display of writer type, dimension scores (self-report, computed, delta), calibration summary, distinctive features, and recommendations. |

### /voice:sessions

List all interview sessions.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash, Glob |
| **Output** | Table of all sessions with session ID, status, writer type, questions answered, modules completed, and last updated date. Sorted by most recently active first. |

### /voice:setup

Interactive setup wizard for human-voice configuration.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion |
| **Creates** | `${CLAUDE_PLUGIN_DATA}/config.json` |
| **Behavior** | Detects project structure (content directories, file extensions, static site generators), gathers preferences through interactive questions (detection tiers, fix behavior, interview defaults), writes the unified config file, and verifies it. Optionally offers an initial content scan. |

### /voice:review

Review content for AI writing patterns.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Glob, Grep, Bash |
| **Arguments** | Optional path (file or directory); `--ignore=categories` to skip specific pattern types |
| **Behavior** | Runs a multi-tier analysis: (1) character-level detection via the validation script, (2) language pattern scan for buzzwords, hedging, and meta-commentary, (3) structural pattern assessment, (4) voice pattern assessment. Reports findings by tier with line numbers, replacements, and priority recommendations. |

### /voice:fix

Auto-fix AI character patterns in content files.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Bash |
| **Arguments** | Optional path; `--dry-run` to preview; `--ignore=categories` to skip pattern types |
| **Behavior** | Replaces Tier 1 character-level AI patterns (em dashes, smart quotes, ellipsis, emojis) with human-typical equivalents. Runs in dry-run mode first when `--dry-run` is specified or when unsure. Reports summary of changes and suggests `/voice:review` for comprehensive analysis. Does not fix language, structural, or voice patterns (manual review required). |

### /voice:drift

Report observed voice patterns and drift from the active profile.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Glob, Grep, Bash |
| **Requires** | A completed voice profile and accumulated voice observations in Atlatl memory |
| **Output** | Three sections: confirmed patterns (writing matches profile), drift detected (consistent divergence on specific dimensions), and new patterns (characteristics not in the profile). Includes re-interview recommendations based on drift severity. |

### /voice:design

Design a voice profile from a description or template without running an interview.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion |
| **Arguments** | Optional slug; natural-language description or `--from-template {name}` |
| **Templates** | `formal-technical`, `casual-conversational`, `academic-prose`, `brand-corporate`, `creative-narrative` |
| **Behavior** | Generates a complete profile.json from either a natural-language voice description or a starter template. Stores the profile in the registry and activates it. Designed profiles have no calibration data (no self-report vs observed comparison). Origin is `"designed"` or `"template"`. |

### /voice:profiles

Manage multiple named voice profiles.

| Aspect | Detail |
|---|---|
| **Tools used** | Read, Write, Bash, Glob, AskUserQuestion |
| **Subcommands** | `list` (default), `activate {slug}`, `info {slug}`, `delete {slug}`, `rename {old} {new}`, `export {slug} --to-repo path`, `set-override {pattern} {slug}`, `remove-override {pattern}` |
| **Behavior** | Lists all registered profiles with active marker, activates profiles (copies to top-level data directory), shows full profile details with example prose, deletes/renames profiles, exports to repositories for Copilot consumption, and manages directory-based overrides for automatic profile switching. |
