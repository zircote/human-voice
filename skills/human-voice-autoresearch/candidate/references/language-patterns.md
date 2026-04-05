# Language-Level Patterns (Tier 2)

These patterns require human judgment but are strong AI indicators.

## Hedging Phrases (Remove or Rewrite)

| Pattern | Issue | Better Alternative |
|---------|-------|-------------------|
| "It's worth noting that..." | Unnecessary filler | State the point directly |
| "It's important to mention..." | Weakens authority | Just mention it |
| "Generally speaking..." | Vague qualifier | Be specific or omit |
| "In my opinion..." | Redundant (implied) | State the opinion |
| "As a matter of fact..." | Wordy | Use "Actually" or omit |
| "To be honest..." | Implies dishonesty elsewhere | Remove entirely |
| "At the end of the day..." | Cliche | "Ultimately" or rewrite |
| "It goes without saying..." | If true, don't say it | Remove entirely |
| "Arguably..." | Weak commitment | Take a position |
| "To some extent..." | Vague | Be specific about extent |

### Detection Command

```bash
grep -rn -i -E "it's worth noting|it's important to mention|generally speaking|in my opinion|as a matter of fact|to be honest|at the end of the day|it goes without saying|arguably|to some extent" _posts/ content/ _docs/
```

## AI Buzzwords (Replace with Plain Language)

| Word | Issue | Alternatives |
|------|-------|-------------|
| delve | Extremely AI-correlated | explore, examine, dig into, look at |
| realm | Pretentious AI-favorite | area, domain, field, space |
| pivotal | Overused in AI text | critical, key, essential, important |
| harness | Tech buzzword | use, apply, employ |
| revolutionize | Hyperbolic | transform, change, improve |
| seamlessly | Marketing-speak | smoothly, easily, without friction |
| cutting-edge | Cliche | modern, new, advanced, current |
| game-changer | Hyperbolic | significant, impactful, valuable |
| robust | Overused | strong, reliable, solid |
| leverage | Business-speak | use, apply |
| utilize | Formal excess | use |
| facilitate | Bureaucratic | help, enable, allow |
| synergy | Business jargon | combination, collaboration |
| paradigm | Academic pretension | model, approach, framework |
| holistic | Vague buzzword | comprehensive, complete, full |
| ecosystem | Overused tech term | environment, system, platform |
| innovative | Empty adjective | (describe what makes it new) |
| transformative | Vague superlative | (show the transformation) |
| underscore | AI-preferred verb | highlight, emphasize, show |
| illuminate | Pretentious | explain, clarify, show |

### Detection Command

```bash
grep -rn -i -E "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang|robust|leverage|utilize|facilitate|synergy|paradigm|holistic|ecosystem|innovative|transformative|underscore|illuminate" _posts/ content/ _docs/
```

## Filler Phrases (Remove or Simplify)

| Phrase | Replacement |
|--------|-------------|
| "In today's fast-paced world..." | (Remove or be specific) |
| "Due to the fact that..." | "Because" |
| "In order to..." | "To" |
| "For the purpose of..." | "To" or "For" |
| "On a daily basis" | "Daily" |
| "At this point in time" | "Now" or "Currently" |
| "The fact that..." | (Rewrite directly) |
| "It is interesting to note..." | State what's interesting |
| "As we all know..." | Omit or cite source |
| "Needless to say..." | Don't say it |
| "In this article, we will discuss..." | (Start with the content) |
| "As mentioned earlier..." | (Link or remove) |
| "Let's dive in..." | (Just start) |
| "Let's explore..." | (Just start) |
| "Without further ado..." | (Just start) |

### Detection Command

```bash
grep -rn -i -E "in today's fast-paced|due to the fact|in order to|for the purpose of|on a daily basis|at this point in time|the fact that|it is interesting|as we all know|needless to say|in this article|as mentioned earlier|let's dive|let's explore|without further ado" _posts/ content/ _docs/
```

## Excessive Transitions (Use Sparingly)

| Transition | Guidance |
|------------|----------|
| Furthermore | Use only when connection is unclear |
| Moreover | Rarely necessary; often omit |
| Additionally | Use for genuinely additive points |
| In addition to this | Wordy; use "Also" or omit |
| Consequently | Keep only when causation is key |
| Subsequently | Replace with "Then" or reorder |
| Accordingly | Often redundant |
| That being said | Use "However" or omit |
| Having said that | Same as above |

### Detection Command

```bash
grep -rn -i -E "^Furthermore|^Moreover|^Additionally|^In addition|^Consequently|^Subsequently|^Accordingly|That being said|Having said that" _posts/ content/ _docs/
```

## Meta-Commentary Phrases

These phrases describe what the content will do instead of doing it:

| Pattern | Fix |
|---------|-----|
| "In this article, we will..." | Start with the content |
| "This post explores..." | Just explore it |
| "We'll discuss how to..." | Just discuss it |
| "Let me explain..." | Just explain |
| "I'm going to show you..." | Just show |
| "As we've seen..." | (Remove or link) |
| "To summarize..." | Use a heading instead |

### Detection Command

```bash
grep -rn -i -E "in this (article|post|guide)|this post (explores|discusses|covers)|we'll (discuss|explore|look at)|let me explain|I'm going to show|as we've seen|to summarize" _posts/ content/ _docs/
```

## Comprehensive Language Scan

Run all language pattern checks at once:

```bash
# All buzzwords and hedging
grep -rn -i -E \
  "delve|realm|pivotal|harness|revolutionize|seamlessly|cutting-edge|game-chang|robust|leverage|utilize|facilitate|synergy|paradigm|holistic|ecosystem|innovative|transformative|underscore|illuminate|it's worth noting|generally speaking|in order to|due to the fact|in this article|let's dive|let's explore" \
  _posts/ content/ _docs/
```

## Why These Patterns Matter

### Frequency Analysis

Research shows AI models use certain words at statistically anomalous rates:
- "delve" appears 10-50x more frequently in AI text
- "realm" appears 5-20x more frequently
- Em dashes appear 3-5x more frequently

### Reader Perception

Readers subconsciously detect AI patterns even when they can't articulate why. Content heavy in these patterns feels:
- Generic and impersonal
- Marketing-speak or corporate
- Untrustworthy or inauthentic
- Padded or lacking substance
