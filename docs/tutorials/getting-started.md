---
diataxis_type: tutorial
diataxis_learning_goals:
  - Set up voice and its dependencies
  - Run a complete voice elicitation interview
  - View and interpret a voice profile
---

# Getting Started with Voice

In this tutorial, we will set up voice, run a voice elicitation interview from start to finish, and view the resulting voice profile. By the end, we will have a multi-dimensional map of our writing voice based on both self-reported preferences and computationally observed features.

The full interview takes 30--45 minutes. We can pause and resume at any point, so there is no need to complete it in one sitting.

## Prerequisites

Before we begin, we need the following installed on our machine:

- **Python 3.10 or later** -- verify with `python3 --version`
- **Git** -- verify with `git --version`
- **Claude Code** -- the voice interview engine runs as a Claude Code agent

## Step 1: Clone and set up the project

First, we will clone the repository and run the setup script.

```bash
git clone https://github.com/zircote/human-voice.git
cd human-voice
```

Now run the setup script, which creates a virtual environment, installs all dependencies, downloads the spaCy language model, and validates the question bank:

```bash
bash scripts/setup.sh
```

We should see output that progresses through seven steps:

```
=== voice setup ===
Repository root: /path/to/voice

[1/7] Creating virtual environment at .venv ...
      Using Python: Python 3.12.4 at /path/to/voice/.venv/bin/python3

[2/7] Installing voice root package with [all,dev] extras ...
[3/7] Installing voice-nlp package with [dev] extras ...
[4/7] Installing voice-scoring package with [dev] extras ...
[5/7] Downloading spaCy en_core_web_sm model ...
[6/7] Creating ${CLAUDE_PLUGIN_DATA} directory ...
[7/7] Validating JSON files ...
      Validated 14 JSON files, 0 errors

=== Setup complete ===
  Virtual environment: .venv
  Packages installed:  voice, voice-nlp, voice-scoring
  spaCy model:         en_core_web_sm
  Config directory:    ${CLAUDE_PLUGIN_DATA}
  JSON files:          14 valid, 0 errors
```

The important things to confirm: zero JSON errors, all three packages installed, and the `${CLAUDE_PLUGIN_DATA}` config directory created.

We have completed the setup. Our environment is ready for interviews.

## Step 2: Start an interview

With Claude Code open in the voice project directory, we start a new voice elicitation session:

```
/voice:interview
```

Voice creates a unique session, initializes its state files, and loads the question bank. We will see a confirmation like this:

```
Session created: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Session directory: ${CLAUDE_PLUGIN_DATA}/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/

Beginning voice elicitation interview...
```

The interview begins immediately with the first question.

We have started our first interview session. The session ID is saved automatically -- we will use it later to check progress and view our profile.

## Step 3: Answer the screening questions (M01)

The interview opens with Module 01: Writing Identity & Context. These initial questions establish who we are as a writer. The conductor presents them conversationally, one at a time.

The first question asks about our primary writing role:

```
How would you describe your primary role as a writer?

1) Professional communicator (emails, reports, proposals)
2) Creative writer (fiction, poetry, essays)
3) Academic or researcher
4) Technical writer (documentation, specifications)
5) Casual or personal writer (social media, blogs, journals)
6) A mix of several roles
```

We type our answer (a number or the label) and press Enter. The conductor records our response, updates our session state, and moves to the next question.

The second question asks about writing frequency:

```
What types of writing do you do most frequently? Select all that apply.

1) Emails and business correspondence
2) Reports and analyses
3) Social media posts
4) Blog posts or articles
5) Creative writing (stories, poetry)
6) Academic papers or research
7) Technical documentation
8) Personal journals or notes
9) Marketing and promotional copy
```

We can select multiple options by listing numbers separated by commas (e.g., `1, 4, 7`).

The third question shifts to a reflective forced-choice format:

```
When you think about your writing, which statement best describes
how you feel about having a distinct 'voice'?

1) I have a strong sense of my writing voice and it stays consistent
2) My voice shifts depending on what I'm writing and who I'm writing for
3) I'm still figuring out what my writing voice is
```

Notice how the question format changes -- selections, multi-selects, and forced choices are interleaved to keep the experience varied. This is by design; voice rotates formats to prevent monotony.

We continue answering through the remaining M01 questions, which cover our audience, writing evolution, and a brief reflective prompt. There are 10 questions in this module.

We have completed the screening module. Voice now knows enough about our writing context to route us into the right interview path.

## Step 4: Experience the branching

After the screening questions, voice classifies our writer type and selects a branching path. Based on our answers about writing role, audience, and context, the system routes us into one of four paths:

- **Creative/Literary** -- for fiction, poetry, and creative nonfiction writers
- **Business/Professional** -- for corporate, marketing, and business writers
- **Academic/Technical** -- for researchers, scientists, and technical writers
- **Personal/Journalistic** -- for bloggers, journalists, and personal writers

The conductor acknowledges the routing naturally:

```
Based on your responses, it looks like your writing lives primarily in
a professional/business context. I'll tailor some of the upcoming
questions to explore that space more deeply.

Let's move into the next section...
```

Each path activates a different combination of deep-dive modules while sharing common core modules. We do not need to do anything special here -- the branching happens automatically. We simply continue answering questions as they are presented.

The interview now adapts to our specific writing context. The questions ahead will be more relevant to the kind of writing we actually do.

## Step 5: Work through the core modules

After branching, the interview moves through Phases 2 through 5. The conductor guides us through modules covering:

- Voice personality and style preferences
- Formality and register
- Emotional expression and tone
- Sentence structure and complexity
- Audience adaptation
- Rhetorical patterns
- Writing process and mechanics

The question formats continue to vary. We will encounter Likert scales:

```
On a scale of 1 to 7, where 1 means "highly structured and planned"
and 7 means "completely spontaneous and free-flowing," how would you
describe your typical writing process?
```

Semantic differentials:

```
Between "Formal" and "Casual," where would you place your default
writing style on a 1-7 scale?

1 ---- 2 ---- 3 ---- 4 ---- 5 ---- 6 ---- 7
Formal                Neutral               Casual
```

And open-ended reflections:

```
Think of a time when you had to write something outside your comfort
zone. What was the situation, and how did you approach it?
```

There is no wrong answer to any of these questions. The goal is an honest picture of how we write, not an idealized version.

We are making steady progress through the interview. Each module builds a richer picture of our voice dimensions.

## Step 6: Provide writing samples (M12)

In the final phase, voice asks us to produce short writing samples. These are the most valuable part of the interview -- they provide behavioral data that the NLP pipeline analyzes computationally, independent of our self-reported preferences.

The conductor sets up the writing sample section:

```
We're entering the final section. I'll give you a few short writing
prompts. Write naturally -- there's no right or wrong style here.
These samples help calibrate what you told me earlier against how
you actually write.
```

The first prompt:

```
Please write a short passage on the following topic:

"Draft a brief email declining a social invitation."

Write naturally in whatever style comes to you. Aim for a few
sentences to a short paragraph.
```

We write the email in our own voice. The conductor then presents additional prompts -- describing a meaningful place, explaining a recent decision, and optionally writing a story opening.

After the writing samples, a calibration question asks us to reflect on the accuracy of our earlier answers:

```
How well do your answers capture your actual vs. idealized style?

1) Mostly idealized -- I described who I want to be, not who I am
2) Somewhat idealized
3) Slightly idealized
4) A fair mix of actual and aspirational
5) Mostly accurate
6) Very accurate
7) Highly accurate -- this is genuinely how I write
```

We are nearly done. The writing samples and calibration data give voice the signal it needs to compare what we said against what we do.

## Step 7: Check progress mid-interview

At any point during the interview, we can check our progress without leaving the session. Run:

```
/voice:status
```

This displays a summary of where we stand:

```
Session:    a1b2c3d4-e5f6-7890-abcd-ef1234567890
Status:     in_progress
Created:    2026-04-04T14:30:00Z
Updated:    2026-04-04T15:02:00Z
Writer Type: business_professional (detected at M01)

Progress:
  Questions answered:  32 / ~68
  Modules completed:   5 / 12  [SD, M01, M02, M03, M04]
  Current module:      M05 — Vocabulary & Word Choice
  Current question:    M05-A03

Estimated Time Remaining: ~18 minutes

Dimension Scores (provisional):
  Formality:        7.2 / 10
  Emotional Tone:   4.8 / 10
  Sentence Length:   6.1 / 10
  ...
```

The status report shows completed modules, our detected writer type, provisional dimension scores, and an estimated time remaining based on our pace so far.

We can check progress as often as we like. It is a read-only operation that does not affect the interview.

## Step 8: Pause and resume the interview

If we need to step away, we can pause at any question by typing:

```
pause
```

The conductor saves our full session state and confirms:

```
Session paused. Your progress has been saved.

Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Progress:   42 / ~68 questions answered
Module:     M07 — Audience Adaptation

To resume later, run: /voice:resume
```

When we return, we resume exactly where we left off:

```
/voice:resume
```

The conductor loads our saved state and picks up naturally:

```
Welcome back -- you're in Section 7 of 12, about 15 minutes remaining
based on your pace so far.

Let's continue where we left off...
```

All previous responses, branching decisions, and scores are preserved. We do not lose any progress.

Our session state is durable. We can pause and resume across days or even weeks without any data loss.

## Step 9: View our voice profile

Once we have answered all questions and provided writing samples, the interview completes automatically. Voice runs the scoring engine and NLP pipeline, then generates our voice profile.

To view the finished profile:

```
/voice:profile
```

The output is a comprehensive voice profile:

```
═══════════════════════════════════════════════════
MIVOCA VOICE PROFILE
Session:  a1b2c3d4-e5f6-7890-abcd-ef1234567890
Completed: 2026-04-04T16:45:00Z
═══════════════════════════════════════════════════

Writer Type: Analytical Explainer

── Dimension Scores ──────────────────────────────

Dimension               Self-Report  Computed  Delta
─────────────────────────────────────────────────────
Formality & Register       7.2         6.8      0.4
Emotional Tone             4.8         5.3     -0.5
Sentence Structure         6.1         6.4     -0.3
Vocabulary Complexity      8.0         7.1      0.9 *
Rhetorical Patterns        5.5         5.2      0.3
Audience Adaptation        6.7         6.9     -0.2
Pacing & Rhythm            5.0         4.6      0.4
Figurative Language        3.2         3.8     -0.6
Precision vs Ambiguity     8.4         7.9      0.5
Humor & Wit                4.1         4.5     -0.4
Persuasion Style           5.8         5.6      0.2
Identity & Authenticity    7.0         7.3     -0.3

* High calibration delta — self-perception diverges
  from observed practice on this dimension.

── Calibration Summary ───────────────────────────

Overall calibration accuracy: 82%
Dimensions with high delta (>0.8): Vocabulary Complexity
Self-awareness strength: Formality, Audience Adaptation
Blind spots: Vocabulary Complexity, Figurative Language

── Distinctive Features ──────────────────────────

- Favors parallel structure in explanatory passages
- Defaults to active voice with occasional strategic passive
- Uses technical vocabulary but explains terms inline
- Sentence length varies by context: short for emphasis,
  long for nuance
- Low use of hedging language; high assertion confidence

── Recommendations ───────────────────────────────

Based on the calibration delta for Vocabulary Complexity,
consider that your writing may use slightly less complex
vocabulary than you believe. This is not a weakness — it
suggests strong audience awareness in practice.
```

We now have a complete voice profile. This is the primary output of the voice interview.

## Step 10: Interpret the output

The voice profile has four sections worth understanding at a high level.

**Dimension Scores** show 12 voice dimensions, each scored on a 1--10 scale. Every dimension has two scores:

- **Self-Report** -- derived from our interview answers (what we said about our writing)
- **Computed** -- derived from NLP analysis of our writing samples (what we actually did)

**Delta** is the gap between self-report and computed scores. A small delta means our self-perception matches our practice. A high delta (marked with `*`) means there is a meaningful divergence worth paying attention to.

**Calibration Summary** distills the deltas into an overall accuracy percentage. It highlights dimensions where we have strong self-awareness and dimensions where we have blind spots.

**Distinctive Features** lists specific, observable patterns found in our writing samples -- sentence structure preferences, voice tendencies, vocabulary habits, and rhetorical patterns.

For a deeper understanding of what each dimension measures and how calibration works, see the [explanation docs](../explanation/).

## What we have accomplished

In this tutorial, we:

- Installed voice and verified all dependencies
- Started a voice elicitation interview session
- Answered screening questions and saw the adaptive branching in action
- Worked through multiple question formats across core modules
- Provided writing samples for computational analysis
- Checked progress mid-interview with `/voice:status`
- Paused and resumed the interview without losing progress
- Viewed a completed voice profile with dual self-report and computed scores
- Understood the basics of dimension scores, deltas, and calibration

## Next steps

- **Customize your interview experience** -- see the [how-to guides](../guides/) for pausing strategies, providing better writing samples, and re-running specific modules
- **Understand voice dimensions in depth** -- read the [explanation docs](../explanation/) for the research foundation behind each dimension and how calibration accuracy is calculated
- **Work with profile data programmatically** -- consult the [reference docs](../reference/) for the `profile.json` schema and scoring engine API
