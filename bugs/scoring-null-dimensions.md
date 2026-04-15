# Bug: Scorer returns null scores for all dimensions

## Summary

`voice-scoring score` completes without error (after metadata is found) but returns null scores for every dimension. Two root causes combine to produce this failure.

## Environment

- human-voice 0.3.0 (plugin cache)
- Python 3.14
- Session: `b5738aed-1feb-4dbc-954c-6e804f675159`
- macOS, sessions stored at `~/.human-voice/sessions/`

## Root Cause 1: Metadata file discovery fails from default session path

**File**: `scoring/src/voice_scoring/cli.py`, lines 50-65

`_load_metadata()` walks up 5 parent directories from the session directory looking for a `question-bank/` directory. When sessions are stored at the default location (`~/.human-voice/sessions/{session_id}/`), the walk visits:

```
~/.human-voice/sessions/{id}/  (start)
~/.human-voice/sessions/       (parent 1)
~/.human-voice/                (parent 2)
~/                             (parent 3)
/Users/                        (parent 4)
/                              (parent 5)
```

None of these contain `question-bank/`. The plugin's `question-bank/` lives at the plugin cache path (`~/.claude/plugins/cache/zircote/human-voice/0.3.0/question-bank/`) or the source repo, neither of which is reachable by walking up from the session directory.

**Result**: Hard exit with `ERROR: required metadata file 'dimension-item-mapping.json' not found.`

**Workaround applied**: Symlinked `~/.human-voice/question-bank` to plugin cache. This does not fix the issue because the walker checks parents of the session dir, not `~/.human-voice/` directly. A second symlink or copy into `~/.human-voice/sessions/question-bank/` would work but is fragile.

### Fix

Add the config-derived or well-known plugin paths to the candidate list. Options:

1. Read `~/.human-voice/config.json` to find the plugin base directory, then append `{base}/question-bank/scoring/` to candidates.
2. Check `~/.human-voice/question-bank/` as a fallback (two levels up from sessions/{id}/ already lands at `~/.human-voice/`, so this should work if the walker depth is increased by 1 or the starting candidates include `session_dir.parent.parent`).
3. Accept a `--metadata-dir` CLI flag as an explicit override.
4. Bundle the metadata files into the session directory at creation time (`voice-session create` copies them).

Option 4 is the most robust: it makes sessions self-contained and eliminates the discovery problem entirely.

## Root Cause 2: Response value extraction does not match response schema

**File**: `scoring/src/voice_scoring/self_report.py`, lines 171-185 and 226-233

`_infer_question_type()` checks for top-level keys: `scale_value`, `semantic_differential_value`, `selected_options`, `raw_text`, or `value`.

`score_self_report()` extracts the raw value via:
```python
raw_value = resp.get("scale_value") or resp.get("semantic_differential_value") or resp.get("value")
```

The actual response records written by `voice-session` and the interview conductor use a nested structure:

```json
{
  "question_id": "M03-Q01",
  "answer": {
    "value": 3,
    "raw": "3"
  },
  "elapsed_seconds": 8,
  "timestamp": "2026-04-05T02:35:00Z"
}
```

The scorer looks for `resp["value"]` but the value lives at `resp["answer"]["value"]`. Since the top-level `value` key does not exist, `raw_value` is None, `normalize_response()` returns None, and no items contribute to any dimension. All dimensions score as null.

### Fix

In `_build_response_lookup()` or `score_self_report()`, unwrap the `answer` envelope:

```python
def _build_response_lookup(responses):
    lookup = {}
    for r in responses:
        qid = r.get("question_id")
        if qid:
            # Flatten answer envelope into top-level for scorer compatibility
            answer = r.get("answer", {})
            flat = {**r, **answer}  # answer keys (value, raw) promoted to top level
            lookup[qid] = flat
    return lookup
```

Additionally, `_infer_question_type()` falls back to checking `isinstance(v, (int, float))` for the `value` key, but many forced-choice and select responses store string values (e.g., `"technical"`, `"keep"`, `"avoid"`). These string values need to be mapped to their ordinal position using the question's `scoring_map` from the module JSON. Without loading the question bank modules, the scorer cannot convert categorical answers to numeric scores.

### Suggested approach

1. At session creation or scoring time, load all question bank modules and build a `{question_id: question_definition}` lookup.
2. Use each question's `type`, `options`, and `scoring_map` to:
   - Determine the question type (instead of inferring from response shape)
   - Map categorical `value` strings to their numeric score via `scoring_map`
3. This eliminates both the type inference problem and the categorical-to-numeric conversion problem.

The `questions.json` path (line 175 of cli.py) exists for this purpose but is never populated by `voice-session create`.

## Impact

Every session scored with the default configuration produces a profile with 100% null dimension scores. The profile synthesizer must fall back to manual synthesis from raw interview data, which works but defeats the purpose of the automated scoring pipeline.

## Steps to Reproduce

```bash
# 1. Create a session (default storage)
bin/voice-session create

# 2. Record responses through interview conductor (any responses)

# 3. Attempt scoring
bin/voice-scoring score --session-dir ~/.human-voice/sessions/{session_id}
# ERROR: required metadata file 'dimension-item-mapping.json' not found.

# 4. Symlink metadata workaround
ln -s /path/to/plugin/question-bank ~/.human-voice/sessions/question-bank

# 5. Re-run scoring
bin/voice-scoring score --session-dir ~/.human-voice/sessions/{session_id}
# Scores written, but all dimensions are null
```

## Priority

High. This is the primary output pipeline and it produces no usable scores.
