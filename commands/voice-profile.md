---
name: voice-profile
description: "View a completed voice profile with example prose"
argument-hint: "[session_id]"
allowed-tools: Read, Bash(python3:*), Bash(source:*), Glob
---

# /voice-profile — View a Completed Voice Profile

Display the full voice profile with dimension scores, calibration, distinctive features, and the user's own writing samples as example prose.

## Procedure

1. **Identify session**: If a session ID argument is provided, use it. Otherwise, find the most recent session with `state` of `complete` via `bin/voice-session list`.

2. **Validate**: Load `state.json` via `bin/voice-session load {session_id}`. If state is not `complete`, inform the user and suggest `/voice-resume`.

3. **Read profile**: Load `{session_dir}/profile.json`.

4. **Display formatted profile**:

   Do NOT load or display interview writing samples. Interview responses are internal data for the scoring and NLP pipelines. The Example Prose section is always generated fresh from the profile configuration to demonstrate what the plugin produces under this profile's rules.

   ```
   ═══════════════════════════════════════════════════
   VOICE PROFILE
   Session:  a1b2c3d4-...
   Writer:   business_professional
   ═══════════════════════════════════════════════════

   Identity: A direct, analytical voice that favors
   precision over warmth. Writes in structured,
   medium-length sentences with minimal hedging.

   ── Gold Standard Dimensions ─────────────────────
   Dimension            Self  Observed  Composite
   ─────────────────────────────────────────────────
   Formality              65       58        62
   Emotional Tone         35       41        38
   Personality            75       67        71
   Complexity             50       60        55
   Audience Awareness     80       76        78
   Authority              74       70        72
   Narrativity            40       48        44
   Humor                  35       25        30

   ── Semantic Differential ────────────────────────
   Formal ●●●●○○○ Casual          (4.2)
   Assertive ●●●●●○○ Tentative    (5.4)
   Direct ●●●●●●○ Diplomatic      (5.8)
   Structured ●●●●●●○ Flowing     (5.6)
   Concrete ●●●●●○○ Abstract      (5.1)

   ── Calibration ─────────────────────────────────
   Overall self-awareness: 0.76
   High awareness: formality, audience_awareness
   Blind spots: complexity, humor
   Aspirational gaps:
     humor: current 30 → desired 50 (Δ20)

   ── Distinctive Features ─────────────────────────
   - High use of em-dashes for parenthetical asides
   - Low hedging frequency (boost-to-hedge ratio: 2.3)
   - Active voice dominance (87% of clauses)
   - Topic-first paragraph structure
   - Preference for Germanic over Latinate vocabulary

   ── Voice Stability ─────────────────────────────
   Stable across contexts:
     formality baseline, sentence length range,
     punctuation habits
   Adapts by context:
     emotional tone, humor level,
     vocabulary sophistication

   ── Example Prose ────────────────────────────────

   SPONTANEOUS (email declining invitation):

     Thanks for thinking of me, but I'm going to
     have to pass on Saturday. I've got a deadline
     Monday that's going to eat the whole weekend.
     Let's find another time — maybe the following
     week works better for both of us.

   REFLECTIVE (place description):

     The library in my college town had this
     particular corner on the second floor where
     the afternoon sun would hit the oak table just
     right. It smelled like old paper and floor wax.
     I spent four years at that table, and most of
     what I know about thinking carefully I learned
     there.

   PROFESSIONAL (decision explanation):

     We decided to sunset the legacy API because
     maintaining two parallel interfaces was costing
     us roughly 30% of the backend team's time. The
     new API covers all the same use cases with
     better documentation and faster response times.

   ═══════════════════════════════════════════════════
   ```

## Display Rules

- **Generated examples (ALWAYS)**: For every profile, regardless of origin, **generate 3-4 prose examples** that demonstrate what writing produced under this profile's rules looks like. Use the dimension scores, mechanics, distinctive features, identity summary, and voice aspirations as constraints. Produce examples across different contexts appropriate to the profile (e.g., a decision email, a code review comment, a postmortem excerpt, a stakeholder explanation, a blog post opening, a meeting decline). The examples prove the profile configuration works — they show the user what the plugin will produce. These are demonstrations of capability, not archive of past writing.
- **Semantic differential**: Show the top 5 most extreme pairs (furthest from 4.0 neutral). Render as a visual scale using filled/empty circles.
- **Dimensions**: Show all 8 gold-standard dimensions with self-report, observed, and composite scores. Flag any with calibration delta > 15 with an asterisk.
- **Calibration**: Show overall self-awareness score, list high-awareness dimensions, blind spots, and aspirational gaps with deltas.
- **Distinctive features**: Show all features as bullet points.
- **Voice stability**: Show stable and adaptive dimensions as comma-separated lists.

## Edge cases
- No `profile.json` anywhere (not published, not in any session dir): suggest `/voice-interview` or `/voice-design`
- Session state is not `complete` but profile.json exists: display the profile (state field may be stale)
- Designed/template profile (no session, no calibration): skip calibration section, generate examples as usual
