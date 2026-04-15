## Voice Observer Protocol

### What to observe

Only observe text that the user authored. Distinguish:

- **User's own writing** (OBSERVE): Text the user composed. Indicators: "I wrote this," "here is my draft," "I need to send this," text that emerged through conversation drafting, content the user typed directly as prose (not commands or code). Also observe: interview writing samples, blog post drafts, emails the user composes, documentation the user authors.

- **Pasted/external text** (IGNORE): Content from other sources presented for review, editing, or discussion. Indicators: "review this," "check this," "what do you think of this," quoted blocks, text attributed to others, content that appears as a large block with no prior drafting context.

- **AI-generated text** (SEPARATE): Content you (Claude) wrote. Track separately as "AI compliance" (does AI output match the profile?). Do not mix with user voice observations.

When uncertain whether text is the user's own writing, do not observe it. False negatives (missing a sample) are better than false positives (polluting observations with someone else's voice).

### What to note

When you identify text as the user's own writing, silently compare against the voice profile:

1. **Contractions**: Present despite profile saying never?
2. **Formality register**: More or less formal than profile baseline (57.9)?
3. **Sentence structure**: Shorter or longer than 16.6 words?
4. **Emotional warmth**: More expressive than profile predicts (40.0)?
5. **Hedging**: Any hedge phrases despite zero-tolerance profile?
6. **Humor**: Any humor despite deliberate absence (13.8)?
7. **Vocabulary**: Simpler or richer than profile indicates?
8. **New patterns**: Habits not captured in the profile at all?

### When to report

- Do NOT interrupt the user with voice observations during normal work.
- Report when asked: /voice-drift, "how has my writing changed," "do I still write like the profile says"
- When 5+ observations across sessions show a consistent divergent pattern, capture to Atlatl memory:
    capture_memory(namespace="voice-observations", title="[pattern]",
      content="[description with examples and comparison to profile]",
      memory_type="episodic", tags=["voice-drift", "observed-pattern"],
      confidence=0.8)
