# Structural Patterns (Tier 3)

These patterns require manual review but are strong AI indicators.

## Pattern: List Addiction

AI formats everything as bullet lists even when prose is more natural.

### AI Pattern (Avoid)

```markdown
The tool has several benefits:
- Fast execution
- Easy setup
- Clear documentation
- Active community
```

### Human Pattern (Prefer)

```markdown
The tool runs fast, sets up in minutes, and has documentation
that actually answers your questions. The community on Discord
responds within hours, not days.
```

### When Lists Work

Lists are appropriate for:
- Step-by-step instructions
- Reference material (API parameters, configuration options)
- Checklists
- Items that are genuinely parallel and unrelated

Lists are inappropriate for:
- Describing features (use prose)
- Making arguments (use paragraphs)
- Comparing options (use prose or tables)
- Any content where narrative flow matters

## Pattern: Rule of Three Overuse

AI over-applies rhetorical threes, making content predictable.

### AI Pattern (Predictable)

```markdown
This approach is faster, simpler, and more reliable.
It saves time, reduces errors, and improves quality.
Learn, practice, and master the technique.
```

Every paragraph has exactly three items. Readers notice this rhythm.

### Human Pattern (Varied)

```markdown
This approach cuts deployment time in half. It also eliminated
the three most common error types we tracked last quarter.
```

### Fixing Rule of Three

- Use two items sometimes
- Use four items occasionally
- Vary paragraph structure
- Let the content determine the count, not a formula

## Pattern: "From X to Y" Construction

AI loves this construction for false inclusivity.

### AI Pattern

```markdown
From beginners to experts, everyone can benefit.
From setup to deployment, the process is streamlined.
From small teams to large enterprises, the tool scales.
```

### Human Pattern

```markdown
Beginners pick it up in a day. Experts appreciate not
having to fight the tool.
```

### Why This Matters

"From X to Y" is vague and non-committal. It claims universal applicability without evidence. Human writing makes specific claims about specific audiences.

## Pattern: Monotonous Sentence Structure

AI writes sentences of similar length and structure.

### AI Pattern

```markdown
The system processes requests efficiently. It handles
errors gracefully. It scales automatically. It logs
everything comprehensively.
```

All sentences are 4-6 words, all start with "It" or "The", all have the same rhythm.

### Human Pattern

```markdown
Request processing is fast. Errors don't crash it. And
when traffic spikes hit, I've watched it spin up new
instances without any intervention. The logs are verbose,
sometimes annoyingly so, but I'd rather have too much
information than not enough.
```

### Sentence Variety Checklist

- [ ] Mix short sentences (3-5 words) with longer ones (15-25 words)
- [ ] Vary sentence starters (don't start 3+ sentences with "The")
- [ ] Include at least one question or exclamation where appropriate
- [ ] Use fragments occasionally for emphasis
- [ ] Vary paragraph length (some 2 sentences, some 5+)

## Pattern: Over-Balanced Perspectives

AI hedges every statement with "on the other hand."

### AI Pattern

```markdown
The tool is powerful. However, it has a learning curve.
On one hand, it saves time. On the other hand, it requires
initial investment. While it has advantages, it also has
disadvantages.
```

Every positive gets a negative. No clear recommendation emerges.

### Human Pattern

```markdown
The tool is powerful but the documentation assumes you
already know concepts it never explains. Expect to spend
a weekend getting oriented. After that, you'll wonder
how you lived without it.
```

### Taking a Position

Human writing:
- States opinions clearly
- Acknowledges tradeoffs without false balance
- Makes recommendations
- Doesn't hedge every claim

## Pattern: Predictable Headers

AI uses generic, formulaic headers.

### AI Pattern

```markdown
## Introduction
## Overview
## Key Features
## Benefits
## Use Cases
## Conclusion
```

### Human Pattern

```markdown
## Why I switched from X to Y
## Setup in 5 minutes
## The three features I actually use
## When this tool is wrong for you
## What I'd change
```

### Better Headers

- Be specific to the content
- Use questions when appropriate
- Include numbers or specifics
- Avoid generic labels

## Structural Review Checklist

Apply this checklist during content review:

- [ ] Content doesn't over-rely on bullet lists
- [ ] Sentence lengths vary naturally (mix 5-word and 20-word sentences)
- [ ] No "rule of three" in every paragraph
- [ ] Perspectives aren't artificially balanced
- [ ] No "From X to Y" constructions
- [ ] Paragraphs vary in length (2-7 sentences)
- [ ] Headers are specific, not generic
- [ ] Lists are used for genuinely list-appropriate content
- [ ] At least some sentences start with words other than "The" or "It"
- [ ] Content flows as narrative, not disconnected points

## Detection Heuristics

### List Ratio

Count bullet points vs paragraphs. If bullets > paragraphs, review for list addiction.

```bash
# Count bullet points
grep -c "^- " file.md

# Count paragraphs (blank-line separated blocks)
grep -c "^$" file.md
```

### Sentence Length Variance

Healthy writing has high variance. AI writing has low variance.

### "From X to Y" Detection

```bash
grep -rn -i "from .* to .*," _posts/ content/ _docs/
```

## Examples of Transformation

### Example 1: List to Prose

**Before:**
```markdown
Key benefits:
- Faster deployment
- Reduced errors
- Better monitoring
- Lower costs
```

**After:**
```markdown
Deployment dropped from 45 minutes to 3. The error rate in
production fell by 80% in the first month. And we finally
have monitoring that tells us what's actually broken instead
of just that something is broken.
```

### Example 2: Adding Variance

**Before:**
```markdown
The API is fast. The documentation is clear. The support
team is responsive. The pricing is reasonable.
```

**After:**
```markdown
Fast API. Clear docs. Support responds within hours, not days.
At $50/month, it's cheaper than the engineering time we were
burning on our homebrew solution.
```
