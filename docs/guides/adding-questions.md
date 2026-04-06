---
diataxis_type: how-to
diataxis_goal: Add new questions, modules, or branching rules to the voice question bank
---

# Adding Questions to the Question Bank

## How to add a question to an existing module

1. Open the module file in `question-bank/modules/`. Files follow the pattern `Mxx-<slug>.json` (e.g., `M02-voice-personality.json`).

2. Append a new question object to the top-level JSON array. Every question requires these fields:

    ```json
    {
      "question_id": "M02-Q11",
      "module_id": "M02",
      "module_name": "Voice Personality & Values",
      "text": "Your question text here.",
      "type": "forced_choice",
      "metadata": {
        "self_reportability_tier": 2,
        "estimated_seconds": 20,
        "format_category": "forced_choice"
      }
    }
    ```

3. Set `question_id` using the pattern `Mxx-Qnn` where `xx` is the module number and `nn` is the next sequential question number within that module. For sub-questions, append a lowercase letter (e.g., `M02-Q11a`). Semantic differential questions use `SD-nn`.

4. Set `type` to one of the allowed values: `likert`, `forced_choice`, `semantic_differential`, `scenario`, `open_ended`, `projective`, `writing_sample`, `calibration`, `select`, `select_multiple`, `behavioral`, `process_narration`.

5. If the question type requires response options (`likert`, `forced_choice`, `select`, `select_multiple`, `semantic_differential`), add an `options` array with at least two entries, each containing `value` and `label`:

    ```json
    "options": [
      { "value": "clarity", "label": "Being clear and easily understood" },
      { "value": "authenticity", "label": "Sounding genuine and true to myself" }
    ]
    ```

6. If the question feeds into scoring, add a `scoring` block:

    ```json
    "scoring": {
      "dimensions": ["voice_values", "communication_priority"],
      "weights": { "voice_values": 0.9, "communication_priority": 0.8 },
      "scoring_map": {
        "clarity": { "voice_values": 3, "communication_priority": 5 },
        "authenticity": { "voice_values": 5, "communication_priority": 3 }
      }
    }
    ```

    Weight values range from 0 to 1. Scoring map keys must match option `value` fields exactly.

7. If you want to add optional metadata, include any of these fields inside `metadata`:

    - `finding_refs` -- array of research finding reference IDs (e.g., `["PL-001", "EF-003"]`)
    - `bias_mitigation` -- description of the bias mitigation strategy applied
    - `branching.required_branches` -- writer type branches required for this question to appear (use `["*"]` for all)
    - `branching.excluded_branches` -- writer type branches for which this question is skipped
    - `position.module_sequence` -- ordinal position within the module
    - `position.funnel_stage` -- one of `screening`, `general`, `core`, `deep_dive`, `wrap_up`

8. If the question should trigger a conditional follow-up, add a `follow_up` block:

    ```json
    "follow_up": {
      "condition": "some_value",
      "question_id": "M02-Q11a"
    }
    ```

    The condition can be a string, number, or boolean that matches a response value.

## How to create a new module

1. Choose a module ID. Use the next available `Mxx` number (check existing files in `question-bank/modules/`).

2. Create the module file as `question-bank/modules/Mxx-<descriptive-slug>.json`. The filename prefix before the first letter-bearing hyphen segment must match the module ID. For example, module `M13` becomes `M13-my-new-module.json`.

3. Structure the file as a JSON array of question objects:

    ```json
    [
      {
        "question_id": "M13-Q01",
        "module_id": "M13",
        "module_name": "My New Module",
        "text": "First question text.",
        "type": "likert",
        "options": [ ... ],
        "metadata": {
          "self_reportability_tier": 1,
          "estimated_seconds": 15,
          "format_category": "likert",
          "position": { "module_sequence": 1, "funnel_stage": "core" }
        }
      }
    ]
    ```

4. Register the module in `question-bank/branching/module-sequence.json`. Add the module ID to the appropriate phase's `modules` array:

    ```json
    {
      "phase": 4,
      "name": "Contextual",
      "modules": ["M07", "M08", "M13"]
    }
    ```

5. Decide whether the module is core or branch-activated. Add the module ID to either the `core_modules` or `branch_activated_modules` array at the bottom of `module-sequence.json`. Core modules are always administered; branch-activated modules can be skipped based on the respondent's writer type path.

6. If you need an engagement reset before or after the module, add an entry to the phase's `engagement_reset_points` array:

    ```json
    {
      "position": "after_M13",
      "type": "engagement_reset",
      "description": "Reset between M13 and next module"
    }
    ```

7. Update the `total_estimated_minutes` field in `module-sequence.json` to account for the new module's expected duration.

## How to add a deep-dive trigger

1. Open `question-bank/branching/deep-dive-triggers.json`.

2. Add a new key under `triggers` with a descriptive name:

    ```json
    "high_precision_drive": {
      "source_module": "M09",
      "condition": {
        "metric": "precision_score",
        "operator": ">",
        "threshold": 80
      },
      "injected_items": ["M09-DD01", "M09-DD02"],
      "description": "When precision score exceeds 80, inject deep-dive items probing precision preferences",
      "injection_point": "after_M09"
    }
    ```

3. The `condition` object supports these fields:

    - `metric` -- the score or measurement to evaluate
    - `operator` -- comparison operator: `>`, `>=`, `<`, `<=`, `==`
    - `threshold` -- numeric threshold value
    - For semantic differential triggers, also include `sd_pair` naming the pair
    - For cross-score comparisons, include `comparison`, and `operands` array

4. Set `injection_point` to control when the deep-dive questions appear:

    - `after_Mxx` -- inject after the named module completes
    - `immediate` -- inject immediately when the condition fires

5. If you want the trigger to apply only to specific dimensions, add `applies_to_dimensions` (use `"all"` for all dimensions).

6. Create the deep-dive question items (e.g., `M09-DD01`) in the source module's JSON file following the standard question format. Use the `DD` infix in the question ID to distinguish deep-dive items from standard questions.

7. Check the `notes` section at the bottom of `deep-dive-triggers.json` for session constraints:

    - `max_deep_dives_per_session` caps total deep-dive injections (currently 5)
    - `deep_dive_time_budget_minutes` caps total deep-dive time (currently 3 minutes)
    - `injection_priority` defines processing order when multiple triggers fire simultaneously

## How to map questions to scoring dimensions

### Update dimension-item-mapping.json

1. Open `question-bank/scoring/dimension-item-mapping.json`.

2. Find the target dimension under `gold_standard_dimensions` or `gap_dimensions`.

3. Add the new question ID to the dimension's `contributing_items` object, under the appropriate module key:

    ```json
    "formality": {
      "contributing_items": {
        "M03": ["M03-Q01", "M03-Q02", "M03-Q03", "M03-Q04", "M03-Q05", "M03-Q06", "M03-Q07"],
        "SD": ["formal_casual", "accessible_specialized"]
      },
      "total_items": 9,
      "min_items_for_score": 5
    }
    ```

4. Update `total_items` to reflect the new count.

5. If you are introducing a new dimension, add a new key under the appropriate section (`gold_standard_dimensions` for primary output dimensions, `gap_dimensions` for supplementary dimensions). Include `contributing_items`, `total_items`, `min_items_for_score`, and `description`.

6. If the new dimension uses semantic differential pairs, also add the pair name to the `semantic_differential_pairs` array at the bottom of the file.

### Update scoring-weights.json

1. Open `question-bank/scoring/scoring-weights.json`.

2. Under `dimension_weights`, find the target dimension and add the new question ID with its weight:

    ```json
    "formality": {
      "items": {
        "M03-Q01": 1.0,
        "M03-Q07": 1.0
      },
      "sd_pairs": { ... },
      "self_reportability_tier": 1
    }
    ```

    Items carry equal weight (1.0) by default. Adjust only if the item should contribute more or less than standard items.

3. If you are adding a new dimension, create a new key under `dimension_weights` with its `items`, `sd_pairs` (if applicable), and `self_reportability_tier`. The tier determines how self-report vs. projective items are weighted in the integration formula.

4. The integration formula for final dimension scores is: `dimension_score = (0.7 * module_items_mean) + (0.3 * sd_normalized_mean)`. These weights are configured in the `integration_formula` section. If the new dimension has no semantic differential component, the full score comes from module items alone.

## How to validate changes

1. Run the validation script from the repository root:

    ```bash
    ./scripts/validate-question-bank.sh
    ```

    This checks:
    - All module JSON files parse correctly
    - Each question's `module_id` matches its filename prefix
    - No duplicate `question_id` values exist across modules

2. The script outputs a summary table showing each module file, its module ID, question count, and status. A successful run ends with `All validations passed.`

3. To additionally check JSON Schema compliance, validate individual module files against the schema:

    ```bash
    # Using ajv-cli
    npx ajv validate -s question-bank/schemas/question.schema.json \
                     -d "question-bank/modules/M02-voice-personality.json" \
                     --spec=draft2020 --all-errors

    # Using check-jsonschema
    check-jsonschema --schemafile question-bank/schemas/question.schema.json \
                     question-bank/modules/M02-voice-personality.json
    ```

4. Verify cross-file consistency manually:

    - Every question ID referenced in `dimension-item-mapping.json` exists in a module file
    - Every question ID referenced in `scoring-weights.json` exists in a module file
    - Every module ID in `module-sequence.json` has a corresponding module file
    - Deep-dive trigger `injected_items` reference valid question IDs

## How to add a new question type

1. **Update the schema.** In `question-bank/schemas/question.schema.json`, add the new type to the `type` property's `enum` array:

    ```json
    "enum": [
      "likert",
      "forced_choice",
      ...
      "your_new_type"
    ]
    ```

2. **Define option requirements.** If the new type requires response options, no schema change is needed -- the `options` array is already optional. If the new type requires a specific option structure different from `{value, label}`, you will need to extend the `options` item schema or add conditional validation using `if`/`then` blocks.

3. **Update the renderer.** The interview engine's renderer must know how to present the new type. Add a rendering handler that maps the type string to the appropriate UI component. See the existing renderer implementations for the pattern.

4. **Update scoring.** If the new type produces responses that score differently from existing types:

    - Define how response values map to numeric scores in each question's `scoring.scoring_map`
    - If the type produces multi-valued or structured responses (unlike a single selection), update the scoring engine to handle the new response shape

5. **Add questions using the new type.** Follow the standard process in "How to add a question to an existing module" above, setting `type` to your new type string.

6. **Update format rotation.** Set `metadata.format_category` on questions using the new type. The engine uses this to prevent consecutive questions of the same format. Choose a category name that matches the type or groups it with similar formats.

## Verification

After making changes, confirm the following:

- [ ] `./scripts/validate-question-bank.sh` exits with `All validations passed.`
- [ ] JSON Schema validation passes for every modified module file
- [ ] New question IDs follow the `Mxx-Qnn` pattern and are unique across all modules
- [ ] Every question referenced in `dimension-item-mapping.json` and `scoring-weights.json` exists in a module file
- [ ] Every module referenced in `module-sequence.json` has a corresponding file in `question-bank/modules/`
- [ ] Deep-dive trigger `injected_items` reference question IDs that exist
- [ ] `total_items` counts in `dimension-item-mapping.json` are accurate
- [ ] `total_estimated_minutes` in `module-sequence.json` reflects any added module time

## Troubleshooting

**`PARSE ERROR` from validation script**
: The module file contains invalid JSON. Run `python3 -m json.tool question-bank/modules/Mxx-slug.json` to locate the syntax error.

**`MODULE MISMATCH` from validation script**
: A question's `module_id` does not match the filename prefix. The filename `M03-formality-register.json` expects all questions to have `"module_id": "M03"`.

**`DUPLICATE ID` from validation script**
: Two questions share the same `question_id`. Search across all module files for the ID and rename one of them.

**Schema validation fails on `question_id` pattern**
: The ID must match `^(M\d{2}-[A-Z]{1,2}\d{2}[a-z]?|SD-\d{2})$`. Common mistakes: lowercase module prefix, missing hyphen, three-digit question number. Valid: `M02-Q01`, `M02-Q01a`, `SD-01`. Invalid: `m02-Q01`, `M02Q01`, `M02-Q001`.

**Schema validation fails on `metadata` required fields**
: Every question must include `self_reportability_tier` (integer 1-4), `estimated_seconds` (integer >= 1), and `format_category` (string) in its `metadata` block.

**Deep-dive trigger does not fire**
: Check that the `source_module` matches the module where the condition metric is calculated. Verify the `operator` and `threshold` values. Check session limits in the `notes` section -- the trigger may be suppressed by `max_deep_dives_per_session` or `deep_dive_time_budget_minutes`.

**New module not appearing in the interview**
: Confirm the module ID is listed in the correct phase in `module-sequence.json` and appears in either `core_modules` or `branch_activated_modules`. If branch-activated, verify the respondent's writer type path includes the required branch.

---

See [question.schema.json](../../question-bank/schemas/question.schema.json) for full schema reference. See the explanation docs for design rationale behind the module structure, scoring integration formula, and self-reportability tiers.
