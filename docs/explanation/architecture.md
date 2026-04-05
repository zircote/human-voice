---
diataxis_type: explanation
diataxis_topic: Mivoca system architecture, design rationale, and research basis
---

# Understanding the Mivoca Architecture

Mivoca is built on a counterintuitive premise: the features of writing that best distinguish one writer from another are precisely the features that writers cannot describe about themselves. This document explains why the system is designed the way it is, what trade-offs were made, and how the research literature shaped every major architectural decision.

This is not a guide to using Mivoca or a reference for its data schemas. It is a place to develop a deeper understanding of the system's reasoning --- the "why" behind each component and the connections between them.

## The Conscious/Unconscious Divide

The founding problem Mivoca addresses is a gap in how we understand writing voice. Ask a writer to describe their style, and they will talk about things like tone, audience, and maybe formality. They will rarely mention their ratio of function words to content words, their characteristic distribution of sentence lengths, or their preference for particular character-level n-gram patterns. Yet these unconscious features --- function word distributions (CS-020), character n-grams (CS-021), punctuation rhythms --- are among the most powerful discriminators in computational stylistics. They are what make one writer's prose statistically distinguishable from another's.

This is not a minor inconvenience; it is a structural problem. Across 98 research findings drawn from computational stylistics, psycholinguistics, and survey methodology, a consistent pattern emerges: **self-report reliability correlates inversely with discrimination power** (LT-003). The features a writer can most accurately report --- "I write formally" or "I use humor" --- tend to be the least distinctive across a population of writers. The features that make a writer's voice truly unique --- their unconscious lexical and syntactic habits --- are invisible to introspection.

This creates a dilemma for any system that wants to capture writing voice. Pure self-report misses the most distinctive features. Pure computational analysis misses the writer's conscious intentions, preferences, and aspirations. Mivoca exists because neither approach alone is sufficient, and a thoughtful combination of both requires an architecture designed around the boundary between what writers know and what they do not.

## Dual-Output Architecture

Given the conscious/unconscious divide, Mivoca could have taken the simpler path: blend self-report and computational scores into a single number per dimension and present that. Many psychometric instruments do exactly this. Mivoca deliberately does not.

The system produces two independent profiles for every writer: a **self-reported profile** (what the writer believes about their voice) and a **computationally observed profile** (what their writing actually exhibits). The research basis for keeping these separate is the low implicit-explicit correlation. Across the style dimensions Mivoca measures, the correlation between what writers say and what they do ranges from roughly r=0.14 to r=0.27 (EM-002). This is not measurement error --- it reflects a genuine divergence between conscious preference and unconscious habit.

Both profiles are independently valid. The self-report profile captures something real: how the writer thinks about their craft, what they value, what they aspire to. A writer who reports high formality may be someone who cares deeply about register even if their unedited prose occasionally drifts casual. The observed profile captures something equally real: the statistical fingerprint of how they actually write when they are not thinking about it.

Collapsing these two views into a single number would destroy information. It would obscure the cases where they agree (the writer knows their voice) and the cases where they diverge (the writer has a blind spot or an aspiration). The dual-output design preserves both signals so that the calibration layer can make sense of the gap.

## The Calibration Model

The distance between the self-reported and observed profiles is where much of Mivoca's value lives. In a simpler system, a large gap between what someone says and what they do would be treated as noise --- evidence that one measurement is wrong. Mivoca treats this gap as a **signal**.

The calibration layer classifies the delta between self-report and observation for each dimension into three categories:

- **High self-awareness** (delta of 10 points or fewer): The writer accurately perceives this aspect of their voice. They know what they do and can describe it. This is common for high-visibility features like overall tone and formality.

- **Blind spots** (delta exceeding 25 points): The writer's self-perception diverges substantially from their observed behavior. They may believe they write concisely when their prose is actually expansive, or they may think they are informal when their language patterns are quite structured. These blind spots are not failures --- they are valuable diagnostic information. They show where coaching, editing, or self-awareness exercises would have the highest impact.

- **Aspirational gaps**: A specific subtype of divergence where the self-report score is notably higher than the observed score. The writer aspires to a quality --- say, narrative sophistication or emotional restraint --- that they do not yet consistently demonstrate. This is distinct from a blind spot because the directionality matters: the writer knows where they want to go, they just have not arrived yet.

The analogy is a vocal coach working with a singer. The singer can describe their desired sound (self-report), and the coach can analyze recordings of their actual singing (observation). Neither alone is the full picture. The gap between them is the coaching opportunity.

During the session itself, the self-perception divergence trigger fires whenever the absolute difference between self-reported and projective scores exceeds 25 points on any dimension, injecting a calibration question immediately. This is not just post-hoc analysis; the system actively probes divergence in real time.

## Tier-Weighted Merging

When Mivoca does need to produce a single composite score per dimension --- for applications that require one number rather than two --- it cannot simply average the self-report and observed scores equally. The reason is that different voice dimensions have fundamentally different self-reportability characteristics.

The tier system, grounded in the research findings, assigns each dimension a self-reportability level:

**Tier 1 (high self-reportability)** covers dimensions like formality, emotional tone, audience awareness, narrativity, and humor. Writers generally know whether they write formally or casually, whether they lean emotional or analytical. For these dimensions, the self-report signal is strong, so the merging weights favor it: 0.7 for self-report, 0.3 for observation. The observed score still contributes --- it provides a reality check --- but the writer's own assessment is trusted as the primary signal.

**Tier 2 (moderate self-reportability)** covers personality, complexity, and authority. Writers have partial insight into these dimensions but are less reliable. A writer may believe they project strong authority without realizing their hedging language undermines it. For Tier 2, the weights are balanced equally: 0.5 and 0.5.

**Tier 3 (low self-reportability)** would cover features where the computational signal is substantially more reliable, weighting it at 0.7 against 0.3 for self-report. **Tier 4 (not self-reportable)** covers features like function word distributions and character n-grams --- features writers simply cannot introspect on. For these, the observed score is used exclusively, with a weight of 1.0.

The alternative --- uniform weighting across all dimensions --- was considered and rejected. It would mean trusting a writer's self-report about their function word usage (which they cannot perceive) as much as their self-report about their formality preference (which they can). The tier system encodes the empirically established limits of self-knowledge.

The integration formula for dimensions that include semantic differential ratings blends module item means with normalized semantic differential means at a 0.7/0.3 ratio, a separate weighting layer that operates within the self-report channel before the tier-based merge with observed scores.

## Adaptive Branching

The question bank contains over 120 items across 12 modules plus a semantic differential section. At an estimated 30-60 seconds per item, administering every question to every writer would require 60-120 minutes. Research on survey methodology is unambiguous: sessions exceeding 25 minutes lose roughly three times as many respondents as shorter sessions (SM-008). Satisficing --- the tendency to give minimally acceptable rather than thoughtful answers --- increases sharply after the 20-minute mark.

Mivoca's branching system addresses this by dividing modules into two categories: **core modules** that every writer receives (M01, M02, M03, M04, M09, M12, and the semantic differential section) and **branch-activated modules** that are administered only when relevant (M05, M06, M07, M08, M10, M11).

Branch selection happens during the orientation phase based on screening questions in M01. The system evaluates the writer's context --- creative/literary, business/professional, academic/technical, or personal/journalistic --- and activates a subset of three additional modules relevant to that context. A fiction writer gets narrativity (M05), authority/register (M08), and writing process (M10). A business writer gets audience awareness (M07), authority/register (M08), and contextual adaptation (M11). This reduces the typical session to 60-80 items administered over approximately 35 minutes.

The branching is declarative, not imperative. Routes are defined in static JSON with conditions evaluated in a fixed order; the first matching branch wins, with a default fallback. This design was chosen over a rule engine or decision tree library because the branching logic is simple enough that declarative data is more maintainable, more auditable, and less likely to harbor subtle bugs than procedural code.

Beyond primary routes, the deep-dive trigger system can inject additional questions mid-session when specific patterns are detected: extreme scores on a semantic differential pair, high narrativity tendencies, or divergence between self-report and projective responses. These triggers are capped at 5 per session with a 3-minute time budget, preventing the adaptive system from inadvertently recreating the length problem it was designed to solve.

An engagement detector monitors response timing. When three or more consecutive responses fall below the minimum expected time threshold --- suggesting the writer is rushing or satisficing --- the system injects an engagement reset before continuing. This is a direct application of survey methodology research (SM-003) on maintaining response quality in longer instruments.

## Question Type Diversity

Mivoca uses eight distinct question types: **select** (single-choice), **select_multiple**, **forced_choice** (binary or ternary), **likert** (scaled agreement), **scenario** (behavioral vignette), **projective** (indirect elicitation), **open_ended** (free text), and **writing_sample** (compositional prompt). There is also the **semantic_differential** section, which uses bipolar adjective pairs on a 7-point scale.

The rationale for this diversity traces directly to the self-reportability tier system. Tier 1 features work well with direct questioning --- Likert scales, select menus, semantic differentials. A writer can tell you how formal they are, and a straightforward scale captures it. But as you move toward Tier 2 and Tier 3, direct questioning becomes less reliable. A writer cannot accurately rate their own authority stance on a 1-7 scale because they lack the introspective access to do so reliably.

For these harder-to-self-report dimensions, Mivoca uses indirect techniques. **Scenario questions** present a writing situation and ask what the writer would do, revealing preferences through simulated behavior rather than abstract self-assessment. **Projective questions** --- adapted from projective techniques in psychology --- ask writers to react to or evaluate someone else's writing, which surfaces attitudes they might not articulate about their own practice. The M02 module, for example, includes a projective item where the writer evaluates voice samples, and their evaluative criteria reveal their own values.

Format alternation also serves a pragmatic purpose: combating survey fatigue. Research on questionnaire design (SM-012) shows that monotonous formats --- page after page of Likert scales --- increase satisficing and decrease thoughtful engagement. Alternating between question types creates novelty that maintains attention. The module sequence is designed so that cognitively demanding formats (scenarios, open-ended, writing samples) are interspersed with lighter formats (select, forced choice), with explicit engagement reset points between phases.

## The NLP Pipeline

The computational observation side of Mivoca's dual-output architecture is implemented as a stateless NLP pipeline. When a writer provides a writing sample, the pipeline analyzes it and produces a structured feature vector. This pipeline is the system's "ear" --- it listens to the writing the way a trained stylometrist would, but systematically and at scale.

The pipeline operates in five stages that correspond to the stylometric feature hierarchy established in the research literature:

1. **Lexical analysis**: Vocabulary richness, word frequency distributions, type-token ratios, and lexical sophistication. These features capture what words the writer chooses (CS-005).

2. **Syntactic analysis**: Sentence structure, clause embedding depth, dependency parse patterns, and grammatical complexity. These features capture how the writer constructs sentences (CS-011).

3. **Character-level analysis**: Character n-gram distributions, punctuation patterns, and orthographic habits. These are among the most powerful authorship discriminators precisely because they are below the threshold of conscious control (CS-021).

4. **Discourse-level analysis**: Paragraph structure, cohesion markers, rhetorical move patterns, and information density distribution. These capture how the writer organizes ideas across spans of text.

5. **Pragmatic analysis**: Hedging, stance markers, evidentiality, and reader-orientation signals. These capture the writer's relationship to their claims and their audience.

Each stage produces features that map directly to the self-reportability tier system. Lexical and syntactic features from stages 1-2 correspond roughly to Tier 2-3 dimensions. Character-level features from stage 3 are firmly Tier 4 --- the writer has no awareness of their character n-gram distribution. Discourse and pragmatic features from stages 4-5 span Tiers 2-3.

The pipeline is implemented in Python using spaCy for core NLP and is deliberately stateless: text goes in, JSON comes out. It has no knowledge of the session, the writer's identity, or their self-report responses. This isolation is architectural --- it ensures the observed profile is genuinely independent of the self-reported profile, which is a prerequisite for the calibration model to be meaningful.

## Component Architecture

Mivoca is divided into six major components, each with a distinct concern and execution model:

**The Interview Conductor** is an LLM agent that manages the conversational interface. It presents questions naturally, handles branching decisions, monitors engagement quality, and manages session flow. It is the only component that interacts directly with the writer. The conductor is stateful within a session but does not perform scoring or analysis --- it delegates those responsibilities downstream.

**The Question Bank** is a collection of static JSON files defining all questions, modules, branching routes, deep-dive triggers, scoring weights, and dimension mappings. It is pure data with no behavior. This separation means the question content can be reviewed, validated, and revised by domain experts without touching any code. The schemas enforce structural consistency across all 120+ items.

**The Session State** layer manages persistence: the current position in the module sequence, the branch path taken, quality flags, and the append-only response log. It uses atomic writes (write-to-temp-then-rename) to prevent corruption from interrupted sessions. Sessions can be paused and resumed because all state is externalized to disk rather than held in agent memory.

**The NLP Pipeline** performs computational writing analysis. As discussed above, it is stateless and isolated. It is invoked via shell commands, receives text, and produces JSON. This boundary exists because NLP processing has fundamentally different execution characteristics from the rest of the system --- it is CPU-intensive, benefits from batch processing, and depends on a separate technology stack (Python, spaCy, statistical models).

**The Scoring Engine** transforms raw responses into dimension scores for the self-report profile. It applies the scoring weights, integrates semantic differential ratings, handles missing items, and runs the attention check validations. Like the NLP pipeline, it is a Python process invoked via shell, maintaining a clear boundary between the conversational agent and the psychometric computation.

**The Profile Synthesizer** is a second LLM agent that performs the final merge. It reads self-report scores and observed features, applies the tier-weighted merging algorithm, computes calibration data, identifies distinctive features by comparison to population norms, and generates the natural-language identity summary. This is implemented as an agent rather than a script because the identity summary requires the kind of nuanced language generation that statistical code does poorly --- translating "subordinate_clause_ratio z=2.1" into "unusually complex sentence structures with deeply nested clauses" is a language task.

The boundaries between these components are not arbitrary. Each one corresponds to a different execution model (conversational agent, static data, file I/O, CPU-intensive NLP, psychometric computation, language generation), a different rate of change (question content changes frequently, schemas change rarely, the NLP pipeline evolves with research), and a different expertise domain (survey design, data engineering, computational linguistics, psychometrics, natural language generation). Merging any two of these components would create coupling between concerns that change for different reasons and are maintained by different kinds of expertise.

---

## Further Reading

- **Tutorials**: [Getting started with a voice elicitation session](../tutorial/) --- walk through your first session from start to finished profile
- **How-to guides**: [How to resume a paused session](../how-to/), [How to interpret calibration results](../how-to/) --- task-oriented instructions for specific goals
- **Reference**: [Question bank schema reference](../reference/), [Voice profile schema reference](../reference/), [Scoring weights reference](../reference/) --- precise specifications for all data formats and configuration
