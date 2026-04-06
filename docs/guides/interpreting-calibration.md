---
diataxis_type: how-to
diataxis_goal: "Interpret scoring results and calibration data from a completed voice profile session"
---

# How to Interpret Calibration Results

## Prerequisites

- A completed Voice session with scoring results in `scores/self-report.json`
- Familiarity with the [Dimensions Reference](../reference/dimensions.md)

## Open the scoring output

1. Locate your session directory. Run `voice-session list` to find the session ID.
2. Open `${CLAUDE_PLUGIN_DATA}/sessions/{session_id}/scores/self-report.json` in a text editor or pipe it through `python3 -m json.tool` for formatted output.

## Read the self_report_scores section

The `self_report_scores` object contains one entry per voice dimension. Each entry has a numeric score on a 0-100 scale.

- **0-25**: Low expression of that dimension
- **26-50**: Below-average expression
- **51-75**: Above-average expression
- **76-100**: Strong expression of that dimension

Scores are derived from weighted item means across all questions that contribute to a given dimension. The weights are defined in `question-bank/scoring/scoring-weights.json`.

## Read the semantic_differentials section

The `semantic_differentials` object contains normalized scores for bipolar adjective pairs (e.g., formal-informal, emotional-analytical). These scores range from 1.0 to 7.0, where 1.0 represents the left pole and 7.0 represents the right pole of each pair.

## Understand the calibration section

The `calibration` object is present only when observed NLP scores exist (i.e., when writing samples were analyzed). It contains per-dimension comparisons between what the writer reported and what their writing exhibited.

Each dimension entry in the calibration report includes:

| Field | Description |
|---|---|
| `self_report` | The self-report score (0-100) |
| `observed` | The computationally observed score (0-100) |
| `delta` | The absolute difference between self-report and observed scores |
| `awareness_level` | Classification of the delta: "high_awareness", "moderate_awareness", or "blind_spot" |

### Interpret awareness levels

3. Check the `awareness_level` field for each dimension:
   - **high_awareness** (delta of 10 or fewer): The writer accurately perceives this aspect of their voice. No action needed.
   - **moderate_awareness** (delta between 11 and 25): The writer has partial insight. Review the direction of the gap to determine whether the writer overestimates or underestimates.
   - **blind_spot** (delta exceeding 25): The writer's self-perception diverges substantially from observed behavior. This is the highest-value diagnostic information in the profile.

### Interpret the SD cross-validation blend

4. When both self-report and observed scores are available, the system produces a blended composite score per dimension. The blend ratio is 0.7 (self-report) and 0.3 (observed) for Tier 1 dimensions (high self-reportability), 0.5/0.5 for Tier 2, and 0.3/0.7 for Tier 3. Tier assignments are documented in the [Dimensions Reference](../reference/dimensions.md).

## Check the quality section

5. Review the `quality` object at the top level of the scoring output. A `pass` value of `true` indicates all quality checks passed. When `pass` is `false`, review the quality flags:
   - `too_fast_count`: Number of responses below the minimum expected time
   - `straightlining_detected`: Whether the writer gave identical scale responses in sequence
   - `attention_check_failures`: Number of failed attention checks

## Identify skipped items

6. Check for a `skipped_items` field in each dimension's scoring entry. This field lists question IDs that were not answered, either because the writer skipped them or because adaptive branching excluded them. A high skip count for a dimension reduces confidence in that dimension's score.

## Decide whether to re-interview

Re-interview when any of the following conditions apply:

- Item coverage for a key dimension falls below 50% (too many skipped items to produce a reliable score)
- The quality section reports `pass: false` with multiple flags active
- SD (semantic differential) cross-validation shows divergence exceeding 30 points on more than three dimensions, suggesting the writer may have been performing rather than responding naturally
- The writer requests a re-interview after reviewing their profile

To start a new session, run `voice-session create` and begin the interview again with `/voice:interview`.

## Related documentation

- [CLI Reference](../reference/cli.md) for scoring command options
- [Dimensions Reference](../reference/dimensions.md) for dimension definitions and tier assignments
- [Architecture explanation](../explanation/architecture.md) for the design rationale behind dual-output scoring
