---
name: voice-setup
description: Interactive setup for human voice configuration
argument-hint: ""
allowed-tools: Read, Write, Bash(python3:*), Bash(mkdir:*), Glob, AskUserQuestion
---

# Human Voice Setup

Interactive configuration wizard. Creates `${CLAUDE_PLUGIN_DATA}/config.json` — the unified config for both AI pattern detection and voice elicitation.

## Process

1. **Check for existing config**: Read `${CLAUDE_PLUGIN_DATA}/config.json` if it exists. Ask: "Configuration exists. Update or replace?"

2. **Detect project structure**: Scan for content directories (`docs/`, `_posts/`, `content/`, `_docs/`), markdown files, and static site generators.

3. **Gather preferences** via `AskUserQuestion`:

   **Content scope**: Which directories and file extensions to scan.
   
   **Detection tiers**: Which AI pattern tiers to enable (character, language, structural, voice).
   
   **Fix behavior**: Dry-run by default? Backup files?
   
   **Interview defaults**: Override estimated questions, format streak limit, quality thresholds?

4. **Write config**: Run `python3 -c "from lib.config import save_config; import json; save_config(json.loads('{...}'))"` to write `${CLAUDE_PLUGIN_DATA}/config.json` atomically.

5. **Verify**: Run `python3 -m lib.config show` to display the saved config.

6. **Optional initial scan**: Offer to run `/human-voice:voice-review` on detected content.

## Config Structure

The config file is JSON, schema-validated against `question-bank/schemas/config.schema.json`:

```json
{
  "detection": {
    "extensions": [".md", ".mdx", ".txt"],
    "content_directories": ["docs/"],
    "ignore": ["node_modules/", "vendor/"],
    "character_patterns": { "enabled": true, ... },
    "language_patterns": { "enabled": true, ... },
    "structural_patterns": { "enabled": true, ... },
    "voice_patterns": { "enabled": true, ... },
    "fix": { "dry_run_by_default": true, ... },
    "output": { "verbosity": "normal", ... }
  },
  "interview": {
    "session_storage": "${CLAUDE_PLUGIN_DATA}/sessions",
    "estimated_questions": 70,
    "quality": { ... },
    "scoring": { ... },
    "profile": { ... }
  }
}
```

To view current config: `python3 -m lib.config show`
To get a specific value: `python3 -m lib.config get interview.quality.speed_threshold_ms`
To reset to defaults: `python3 -m lib.config reset`

## Output

Report what was configured and suggest next steps:
- `/human-voice:voice-review` to scan content
- `/human-voice:voice-interview` to start a voice elicitation session
