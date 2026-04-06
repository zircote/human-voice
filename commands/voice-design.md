---
name: voice-design
description: "Design a voice profile from a description or template without running an interview"
argument-hint: "[slug] [description or --from-template name]"
allowed-tools: Read, Write, Bash(python3:*), Glob, AskUserQuestion
---

# /voice-design — Design a Voice Profile

Create a complete voice profile without running an interview. Two modes: describe a voice character in natural language, or start from a pre-built template.

## Procedure

1. **Parse arguments**: Extract the slug and either a description or `--from-template {name}`.

2. **From description** (default):
   - The user provides a natural-language description of the voice character. Examples:
     - `"A warm, narrative voice that uses humor and personal anecdotes. Casual register, short sentences, lots of contractions."`
     - `"Corporate brand voice: professional, authoritative, no humor, active voice, precise vocabulary."`
     - `"Victorian narrator: ornate, long multi-clause sentences, formal vocabulary, third-person omniscient."`
   - Generate a complete `profile.json` conforming to `question-bank/schemas/voice-profile.schema.json`:
     - Set `session_id` to `null` (no interview session)
     - Set all 8 gold-standard dimensions with plausible scores derived from the description
     - Set semantic differential values consistent with the description
     - Generate distinctive features, mechanics preferences, and an identity summary
     - Set calibration to `null` (no self-report vs observed comparison possible)
   - The origin is `"designed"`.

3. **From template** (`--from-template {name}`):
   - Load the template from `templates/profiles/{name}.json`
   - Available templates: `formal-technical`, `casual-conversational`, `academic-prose`, `brand-corporate`, `creative-narrative`
   - Optionally ask the user to customize dimension scores or mechanics via `AskUserQuestion`
   - The origin is `"template"`.

4. **Name the profile**:
   - If a slug was provided as the first argument, use it.
   - Otherwise, ask via `AskUserQuestion`: "What slug would you like for this profile? (e.g., 'narrator-formal', 'brand-zircote')"

5. **Store and activate**:
   - Run: `python3 -c "from lib.profile_registry import store_profile, activate_profile; import json; store_profile('{slug}', json.load(open('/tmp/designed-profile.json')), '{display_name}', origin='{origin}'); activate_profile('{slug}')"`
   - Or write the profile directly and call the registry functions.

6. **Confirm**: Show the identity summary and top dimension scores. Offer to export to a repo with `/voice-profiles export`.

## Template Format

Templates are minimal profile.json files with placeholder values. The LLM fills in any missing fields and adjusts scores based on user customization.

## Output

Report the slug, identity summary, and suggest next steps:
- `/voice-profiles info {slug}` to see full details
- `/voice-profiles activate {slug}` if not auto-activated
- `/voice-profiles export {slug} --to-repo .` to install for Copilot
