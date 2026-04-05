---
diataxis_type: how-to
diataxis_goal: "Provide better writing samples during a voice elicitation interview"
---

# How to Provide Better Writing Samples

## Which questions ask for writing samples

The following questions prompt you to produce a writing sample during the interview:

| Question ID | Module | Prompt Summary |
|---|---|---|
| M01-Q10 | Orientation | Baseline writing sample |
| M02-Q11 | Voice Personality | Personality-revealing writing |
| M03-Q08 | Emotional Tone | Emotionally characteristic writing |
| M04-Q04 | Complexity | Technical or complex writing |
| M04-Q12 | Complexity | Extended complexity sample |
| M05-Q08 | Narrativity | Narrative writing sample |
| M12-WS01 | Writing Samples | Unconstrained writing sample 1 |
| M12-WS02 | Writing Samples | Unconstrained writing sample 2 |
| M12-WS03 | Writing Samples | Unconstrained writing sample 3 |
| M12-WS04 | Writing Samples | Unconstrained writing sample 4 |

Not all questions appear in every session. Adaptive branching determines which modules are active based on your writer type.

## What the NLP pipeline measures

The pipeline analyzes four categories of features from your writing samples:

1. **Lexical diversity**: Vocabulary richness, type-token ratio, hapax legomena ratio, word frequency distributions. These features capture the range and specificity of your word choices.

2. **Syntactic complexity**: Sentence length distribution, clause embedding depth, dependency parse patterns, subordination ratio. These features capture how you construct sentences.

3. **Pragmatic markers**: Hedging frequency, stance markers, evidentiality signals, reader-orientation cues. These features capture your relationship to your claims and your audience.

4. **Discourse cohesion**: Paragraph structure, transition patterns, information density distribution, rhetorical move sequences. These features capture how you organize ideas across spans of text.

## Tips for natural writing

5. Write as you normally would. The pipeline measures your natural habits, not your performance under observation. Attempting to write differently than usual degrades the accuracy of the observed profile.

6. Shorter samples are acceptable. A 100-word paragraph written naturally is more valuable than a 500-word essay written self-consciously. The pipeline extracts features from samples as short as 50 words.

7. Do not edit extensively. First-draft writing reveals more about unconscious style patterns than polished prose. Light corrections for typos are fine. Restructuring or rewriting defeats the purpose.

8. Choose familiar topics. Writing about something you know well produces more natural prose than writing about an unfamiliar subject. The topic itself does not affect scoring; only the style features matter.

9. Use your typical register. If you normally write formally, write formally. If you normally write casually, write casually. The system measures what you do, not what you think you should do.

## Related documentation

- [Dimensions Reference](../reference/dimensions.md) for the full list of measured dimensions
- [Architecture explanation](../explanation/architecture.md) for the design rationale behind dual-output observation
- [Interpreting calibration results](interpreting-calibration.md) for understanding how NLP scores compare to self-report scores
