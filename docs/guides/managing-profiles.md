---
diataxis_type: how-to
diataxis_goal: Manage multiple named voice profiles using the profile registry
---

# How to Manage Voice Profiles

The profile registry stores multiple named voice profiles. Each profile is a complete voice characterization (dimensions, calibration, distinctive features, mechanics) that you can activate, export, or assign to directories.

## Prerequisites

- The human-voice plugin installed
- At least one profile created (via interview, design, or template)

## List all profiles

View all registered profiles with their active status, origin, and tags.

Using the slash command:

```
/voice:profiles list
```

Using the bin executable:

```bash
bin/voice-profiles list
```

Output:

```
  * robert-allen          interview    personal, default
    zircote-brand         designed     corporate, brand
    narrator-formal       template     fictional, narrator
```

The `*` marks the currently active profile.

## Activate a profile

Set a profile as active. This copies its `profile.json` and `voice-prompt.txt` to the top-level data directory, making it the profile used by hooks, agents, and all voice commands.

```
/voice:profiles activate zircote-brand
```

Or:

```bash
bin/voice-profiles activate zircote-brand
```

## View profile details

Show full details for a profile, including dimension scores, calibration, distinctive features, mechanics, and identity summary.

```
/voice:profiles info robert-allen
```

## Delete a profile

Remove a profile permanently. You cannot delete the currently active profile -- activate a different one first.

```
/voice:profiles delete narrator-formal
```

The slash command prompts for confirmation before deleting.

## Rename a profile

Change a profile's slug. This updates the registry, the profile directory, and any directory overrides that reference the old name.

```bash
bin/voice-profiles rename old-name new-name
```

Or:

```
/voice:profiles rename old-name new-name
```

Slug requirements: lowercase letters, numbers, and hyphens. Must be 2-48 characters, start and end with a letter or number.

## Set directory overrides

Assign a profile to activate automatically when working in directories matching a glob pattern. This is useful when different repositories require different voices.

```bash
bin/voice-profiles set-override "/Users/me/Projects/novel/*" narrator-formal
```

When you open a Claude Code session in a matching directory, the override profile activates automatically.

To remove an override:

```bash
bin/voice-profiles remove-override "/Users/me/Projects/novel/*"
```

## Export profiles to a repository

Install one or more profiles into a repository for GitHub Copilot consumption. This writes a `.github/copilot-instructions.md` file with marker-delimited profile sections and routing logic.

```bash
bin/voice-profiles install robert-allen zircote-brand --to-repo ../my-repo --default robert-allen
```

For single-profile export:

```bash
bin/voice-profiles export robert-allen --to-repo ../my-repo
```

See the [Copilot Integration guide](copilot-integration.md) for details on profile selection labels and CI validation.

## Migrate from single-profile format

If you have an existing top-level `profile.json` from before the multi-profile system, migrate it into the registry:

```bash
bin/voice-profiles migrate
```

This creates a named profile from the existing `profile.json`, derives a slug from the profile metadata, and registers it as the active profile. The original top-level files remain as copies of the active profile for backward compatibility.

## Related documentation

- [CLI Reference](../reference/cli.md) for full `voice-profiles` command syntax
- [Copilot Integration](copilot-integration.md) for exporting to repositories
- [Designing Profiles](designing-profiles.md) for creating profiles without an interview
- [Getting Started tutorial](../tutorials/getting-started.md) for running your first interview
