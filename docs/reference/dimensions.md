---
diataxis_type: reference
diataxis_describes: Voice profile dimensions, scoring tiers, and semantic differential pairs
---

# Dimensions Reference

The voice profile measures writing voice across 8 gold standard dimensions, 10 gap dimensions, and 20 semantic differential pairs. Dimension scores range from 0-100. Semantic differential ratings range from 1.0-7.0.

Configuration files:

- `question-bank/scoring/dimension-item-mapping.json` -- item-to-dimension mappings
- `question-bank/scoring/scoring-weights.json` -- per-item weights and integration formula
- `question-bank/modules/SD-semantic-differential.json` -- semantic differential items

---

## Gold Standard Dimensions

The 8 core voice dimensions are measured with triangulated self-report and behavioral observation. Each produces a composite score blending self-report and observed values, weighted by confidence.

| Dimension | Description | Contributing Modules | SD Pairs | Total Items | Min Items | Tier |
|---|---|---|---|---|---|---|
| `formality` | Degree of formal vs. informal register | M03 (6 items) | `formal_casual`, `accessible_specialized` | 8 | 5 | 1 |
| `emotional_tone` | Emotional valence and intensity, from reserved to expressive | M04 (6 items) | `emotional_analytical`, `warm_detached` | 8 | 5 | 1 |
| `personality` | Degree to which the writer's personality emerges through prose | M02 (5 items), M11 (3 items) | `personal_impersonal`, `earnest_ironic` | 10 | 6 | 2 |
| `complexity` | Syntactic and conceptual complexity | M06 (5 items) | `elaborate_minimalist`, `concise_expansive` | 7 | 4 | 2 |
| `audience_awareness` | Degree of adaptation to and addressing the audience | M07 (5 items) | _(none)_ | 5 | 3 | 1 |
| `authority` | Level of authoritative, expert, or confident voice | M08 (4 items), M02 (2 items) | `assertive_tentative`, `authoritative_collaborative` | 8 | 5 | 2 |
| `narrativity` | Tendency toward narrative and storytelling | M05 (5 items) | `narrative_expository` | 6 | 4 | 1 |
| `humor` | Use of humor, wit, irony, and playfulness | M04 (2 items), M02 (2 items) | `serious_playful` | 5 | 3 | 1 |

### Contributing Items

#### formality

| Source | Items |
|---|---|
| M03 | M03-Q01, M03-Q02, M03-Q03, M03-Q04, M03-Q05, M03-Q06 |
| SD | formal_casual, accessible_specialized |

#### emotional_tone

| Source | Items |
|---|---|
| M04 | M04-Q01, M04-Q02, M04-Q03, M04-Q04, M04-Q05, M04-Q06 |
| SD | emotional_analytical, warm_detached |

#### personality

| Source | Items |
|---|---|
| M02 | M02-Q01, M02-Q02, M02-Q03, M02-Q04, M02-Q05 |
| M11 | M11-Q01, M11-Q02, M11-Q03 |
| SD | personal_impersonal, earnest_ironic |

#### complexity

| Source | Items |
|---|---|
| M06 | M06-Q01, M06-Q02, M06-Q03, M06-Q04, M06-Q05 |
| SD | elaborate_minimalist, concise_expansive |

#### audience_awareness

| Source | Items |
|---|---|
| M07 | M07-Q01, M07-Q02, M07-Q03, M07-Q04, M07-Q05 |

#### authority

| Source | Items |
|---|---|
| M08 | M08-Q01, M08-Q02, M08-Q03, M08-Q04 |
| M02 | M02-Q06, M02-Q07 |
| SD | assertive_tentative, authoritative_collaborative |

#### narrativity

| Source | Items |
|---|---|
| M05 | M05-Q01, M05-Q02, M05-Q03, M05-Q04, M05-Q05 |
| SD | narrative_expository |

#### humor

| Source | Items |
|---|---|
| M04 | M04-Q07, M04-Q08 |
| M02 | M02-Q08, M02-Q09 |
| SD | serious_playful |

---

## Gap Dimensions

Secondary voice dimensions that extend the profile beyond the 8 gold-standard measures. Each is scored 0-100 with a `source` field indicating measurement origin (`self_report`, `observed`, or `both`).

| Dimension | Description | Contributing Items | Min Items |
|---|---|---|---|
| `precision` | Attention to grammatical precision, word choice exactness, and mechanical correctness | M09-Q01, M09-Q02, M09-Q03, M09-Q04, M09-Q05 | 3 |
| `revision_orientation` | Approach to revision and editing in the writing process | M10-Q01, M10-Q02, M10-Q03, M10-Q04 | 2 |
| `contextual_flexibility` | Ability and willingness to shift voice across different writing contexts | M11-Q04, M11-Q05, M11-Q06 | 2 |
| `risk_tolerance` | Willingness to take creative risks and experiment with unconventional voice choices | M02-Q10, M05-Q04 | 1 |
| `self_awareness` | Metacognitive awareness of one's own writing voice and its effects | M12-Q01, M12-Q02, M12-Q03 | 2 |
| `consistency` | Consistency of voice across writing sessions and pieces | M12-Q04, M12-Q05 | 1 |
| `influence_absorption` | Tendency to absorb and integrate influences from other writers | M02-Q03, M10-Q03 | 1 |
| `vocabulary_range` | Breadth and register range of vocabulary usage | M06-Q02, M09-Q03 | 1 |
| `sentence_rhythm` | Characteristic sentence length patterns and rhythmic variation | M06-Q04, M09-Q06 | 1 |
| `genre_awareness` | Awareness of and adherence to genre-specific voice conventions | M07-Q04, M08-Q03 | 1 |

---

## Semantic Differential Pairs

20 bipolar adjective pairs rated on a 7-point scale (1.0 = first pole, 4.0 = neutral, 7.0 = second pole). All pairs are presented to all writer types.

| ID | Pole 1 (1) | Pole 2 (7) | Mapped Dimensions | Weights | Tier |
|---|---|---|---|---|---|
| SD-01 | Formal | Casual | formality | formality: 1.0 | 1 |
| SD-02 | Serious | Playful | humor | humor: 1.0 | 1 |
| SD-03 | Elaborate | Minimalist | complexity | complexity: 1.0 | 2 |
| SD-04 | Assertive | Tentative | authority | authority: 1.0 | 2 |
| SD-05 | Warm | Detached | emotional_tone | emotional_tone: 1.0 | 1 |
| SD-06 | Concrete | Abstract | complexity, narrativity | complexity: 0.5, narrativity: 0.5 | 2 |
| SD-07 | Structured | Flowing | complexity | complexity: 1.0 | 2 |
| SD-08 | Direct | Diplomatic | authority, audience_awareness | authority: 0.5, audience_awareness: 0.5 | 2 |
| SD-09 | Accessible | Specialized | formality, audience_awareness | formality: 0.5, audience_awareness: 0.5 | 1 |
| SD-10 | Emotional | Analytical | emotional_tone, narrativity | emotional_tone: 0.5, narrativity: 0.5 | 1 |
| SD-11 | Authoritative | Collaborative | authority | authority: 1.0 | 2 |
| SD-12 | Conventional | Experimental | personality | personality: 1.0 | 2 |
| SD-13 | Precise | Evocative | personality, complexity | personality: 0.5, complexity: 0.5 | 2 |
| SD-14 | Concise | Expansive | complexity | complexity: 1.0 | 1 |
| SD-15 | Personal | Impersonal | personality, formality | personality: 0.5, formality: 0.5 | 1 |
| SD-16 | Earnest | Ironic | humor, personality | humor: 0.5, personality: 0.5 | 2 |
| SD-17 | Careful | Bold | authority, personality | authority: 0.5, personality: 0.5 | 2 |
| SD-18 | Narrative | Expository | narrativity | narrativity: 1.0 | 2 |
| SD-19 | Inclusive | Exclusive | audience_awareness | audience_awareness: 1.0 | 1 |
| SD-20 | Spontaneous | Deliberate | personality | personality: 1.0 | 2 |

### SD Normalization

Semantic differential scores are normalized from the 1-7 scale to 0-100 before integration:

```
normalized = ((raw - 1) / 6) * 100
```

---

## Self-Reportability Tiers

Self-reportability tiers indicate how accurately participants can self-assess a dimension. The tier determines how self-report data is weighted relative to observed (behavioral/computational) data.

| Tier | Label | Reliability | Description |
|---|---|---|---|
| 1 | High | High | Respondents can accurately self-assess. Self-report items are weighted at full value. |
| 2 | Moderate | Moderate | Respondents have partial insight. Projective and behavioral items are weighted more heavily when available. |
| 3 | Low | Low | Limited self-awareness on this dimension. Behavioral observation is the primary data source. |
| 4 | Very Low | Very low | Self-report is unreliable. Measurement relies entirely on observational and computational methods. |

### Tier Assignments

| Tier | Dimensions |
|---|---|
| 1 (High) | formality, emotional_tone, audience_awareness, narrativity, humor |
| 2 (Moderate) | personality, complexity, authority |

Tiers 3 and 4 are not assigned to any gold standard dimension in the current question bank but are used for individual question items where indirect measurement is required.

---

## Scoring Integration Formula

The final dimension score combines module item scores and semantic differential scores using a weighted blend:

```
dimension_score = (0.7 * module_items_mean) + (0.3 * sd_normalized_mean)
```

| Component | Weight | Description |
|---|---|---|
| `module_items_mean` | 0.70 | Mean across all answered module items for the dimension. Missing items are excluded (not zero-filled), provided `min_items_for_score` is met. |
| `sd_normalized_mean` | 0.30 | Mean of normalized semantic differential scores (1-7 mapped to 0-100) for pairs assigned to the dimension. |

All items within a dimension carry equal weight (1.0) unless otherwise specified in `scoring-weights.json`. This reflects the psychometric design where each item was calibrated to contribute equally to its target dimension.

### Tier 2 Adjustment

For Tier 2 (moderate self-reportability) dimensions, projective item scores are preferred when self-report and projective scores diverge significantly. The `self_perception_divergence` deep-dive trigger (defined in `deep-dive-triggers.json`) detects this condition and injects additional measurement items.

---

## Computational Validators

The NLP pipeline (`voice-nlp`) produces observed scores that serve as computational validators for self-report data. The mapping from writing analysis features to gold standard dimensions:

| Dimension | Key NLP Features |
|---|---|
| formality | `formality_f_score`, `latinate_germanic_ratio`, `contractions_per_100_words` |
| emotional_tone | `liwc_equivalent.emotional_tone`, `positive_emotion_pct`, `negative_emotion_pct` |
| personality | `liwc_equivalent.authenticity`, `first_person_singular_pct`, `self_mention_count` |
| complexity | `flesch_kincaid_grade`, `mean_sentence_length`, `dependent_clause_ratio`, `mtld` |
| audience_awareness | `liwc_equivalent.clout`, `second_person_pct`, `engagement_markers` |
| authority | `liwc_equivalent.clout`, `hedge_boost_ratio`, `active_voice_ratio` |
| narrativity | `liwc_equivalent.analytical_thinking` (inverse), `temporal_connective_density`, `referential_cohesion` |
| humor | Requires manual/LLM evaluation; no direct NLP proxy. |

### Calibration

When both self-report and observed scores are available, the scoring engine (`voice-scoring score`) produces a calibration report comparing the two. Dimensions where self-report and observed scores diverge by more than a threshold are flagged as blind spots or aspirational gaps in the voice profile's `calibration` section.
