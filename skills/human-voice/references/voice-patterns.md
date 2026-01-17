# Voice and Style Patterns (Tier 4)

These patterns require careful review and judgment to identify and fix.

## Issue: Passive Voice Overuse

AI defaults to passive voice, which weakens writing and obscures agency.

### AI Pattern

```markdown
The feature was implemented by the team.
The tests were run automatically.
The deployment was completed successfully.
The bug was discovered during review.
```

### Human Pattern

```markdown
The team shipped the feature.
Tests run automatically.
Deployment finished.
Review caught the bug.
```

### Detection

Look for "was/were + past participle" constructions:

```bash
grep -rn -i -E "was (implemented|completed|discovered|created|built|designed|developed|deployed|fixed)" _posts/ content/ _docs/
```

### When Passive Voice Works

Passive voice is appropriate when:
- The agent is unknown: "The code was committed at 3am"
- The agent is irrelevant: "The server was upgraded to v2.0"
- Emphasizing the action: "The data was encrypted before transmission"

## Issue: Generic Analogies

AI uses tired analogies that don't illuminate.

### AI Pattern

```markdown
It's like a Swiss Army knife for developers.
Think of it as a GPS for your codebase.
Consider it a bridge between frontend and backend.
It's the duct tape of software engineering.
```

### Human Pattern (Specific)

```markdown
I use it like I use grep: constantly, almost unconsciously,
for problems I'd otherwise solve with manual inspection.
```

### Fixing Generic Analogies

- Use analogies specific to your experience
- Or skip the analogy and describe what it actually does
- If you can't think of a fresh analogy, just explain directly

## Issue: Meta-Commentary

AI narrates what it's about to do instead of doing it.

### Patterns to Remove Entirely

```markdown
In this article, we will discuss...
As mentioned earlier...
As we have seen...
Let's explore...
Let's dive in...
Without further ado...
To summarize what we've covered...
In conclusion...
```

### Fix

Start with the content. End when you're done. Don't announce what you're doing.

**Before:**
```markdown
In this tutorial, we're going to explore how to set up
authentication. Let's dive in!
```

**After:**
```markdown
Authentication setup takes three steps: install the SDK,
configure your provider, and add the middleware.
```

## Issue: Perfect Grammar with Shallow Insights

Well-formed sentences that say nothing specific.

### AI Pattern

```markdown
This tool significantly improves developer productivity
by streamlining common workflows and reducing cognitive load.
```

Every word is correct, but there's no actual information.

### Human Pattern

```markdown
I used to spend 20 minutes setting up test environments.
Now it's two commands and 30 seconds.
```

### Recognizing Shallow Insights

Ask: "What specific fact did I learn?" If the answer is vague or nothing, rewrite with specifics.

Red flags:
- Adjectives without evidence: "significantly improves"
- Vague nouns: "workflows", "productivity", "experience"
- Missing numbers: "faster", "better", "easier" without metrics

## Issue: False Enthusiasm

AI adds exclamation marks and enthusiasm that feel forced.

### AI Pattern

```markdown
This is an exciting development!
We're thrilled to announce!
You're going to love this feature!
How amazing is that?
```

### Human Pattern

```markdown
Version 2.0 ships Monday.
The new feature cuts build time by 40%.
It works. Finally.
```

### Fix

- Remove exclamation marks (use at most 1 per document)
- Delete "exciting", "thrilled", "amazing", "incredible"
- Let the facts create excitement

## Issue: Hedging Everything

AI qualifies every statement to avoid being wrong.

### AI Pattern

```markdown
This approach may potentially help some users in certain
situations achieve somewhat better results in many cases.
```

### Human Pattern

```markdown
This approach works for teams under 10 people. Larger
teams should look at X instead.
```

### Fix

- Make specific claims
- Acknowledge limitations directly
- Don't hedge the core message

## Voice Review Checklist

Apply during content review:

- [ ] Opening hooks the reader (no meta-commentary)
- [ ] Specific examples replace generic claims
- [ ] Personal experience or perspective included
- [ ] Honest about tradeoffs and limitations
- [ ] Varied rhythm (short and long sentences)
- [ ] No excessive hedging or qualifiers
- [ ] Active voice predominates (>70% of sentences)
- [ ] Numbers and specifics over vague claims
- [ ] No false enthusiasm or forced excitement
- [ ] Analogies are fresh or absent (not generic)
- [ ] No "In conclusion" or "To summarize"
- [ ] Reader learns specific facts, not vague impressions

## The "Read Aloud" Test

Read the content aloud. Human writing has natural rhythm; AI writing sounds robotic.

Signs of robotic writing:
- Every sentence feels the same length
- No natural pauses or emphasis points
- Feels like reading a list even in prose form
- No personality or voice comes through
- Could have been written about any topic

Signs of human writing:
- Varied pace and rhythm
- Some sentences punch, others flow
- Personality comes through
- Specific to this topic and author
- Sounds like someone talking

## Before/After Transformations

### Technical Documentation

**Before (AI):**
```markdown
The installation process is designed to be seamless and
user-friendly. By leveraging modern package management
solutions, users can effortlessly set up the tool in a
matter of minutes. It's important to note that the
following prerequisites should be in place before proceeding.
```

**After (Human):**
```markdown
Installation takes about two minutes. You need Node.js 18+
and npm or pnpm.
```

### Product Description

**Before (AI):**
```markdown
swagger-php is a robust, cutting-edge library that enables
developers to seamlessly generate OpenAPI documentation from
their PHP codebase. This revolutionary tool transforms the
way teams approach API documentation, providing a holistic
solution that bridges the gap between code and documentation.
```

**After (Human):**
```markdown
swagger-php generates OpenAPI documentation from PHP annotations.
Write `@OA\Get` in your controller, run the command, get valid
OpenAPI JSON. Your Swagger UI stays in sync with your code.
```

### Blog Opening

**Before (AI):**
```markdown
In today's fast-paced world of software development, it's worth
noting that AI coding assistants have revolutionized the way
developers approach their daily tasks. This paradigm shift has
enabled teams to harness cutting-edge technology to streamline
workflows seamlessly. In this article, we will delve into the
pivotal role these tools play in modern development.
```

**After (Human):**
```markdown
I was skeptical about AI coding assistants until Claude saved me
three hours on a refactoring task I'd been dreading. Now I use
one every day, though not for the reasons most marketing material
suggests.
```

## Advanced: Voice Consistency

Human writers have consistent voice. AI voice varies or feels generic.

### Develop Voice Markers

Identify 3-5 phrases or patterns that characterize your authentic voice:
- Sentence starters you naturally use
- Expressions or turns of phrase
- Your typical paragraph length
- How you handle transitions
- Your approach to humor or seriousness

### Apply Consistently

Once identified, consciously apply these markers when editing AI-generated content to match your voice.
