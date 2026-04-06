---
name: voice-profiles
description: "List, activate, delete, rename, and export voice profiles"
argument-hint: "[list|activate|delete|rename|info|export|set-override] [args]"
allowed-tools: Read, Write, Bash(python3:*), Bash(source:*), Glob, AskUserQuestion
---

# /voice-profiles — Manage Voice Profiles

Manage multiple named voice profiles. Each profile is a complete voice characterization (dimensions, calibration, distinctive features, mechanics) that can be activated, exported to repos, or assigned to directories.

## Subcommands

### list (default)

Show all registered profiles with active marker, origin, and tags.

```
bin/voice-profiles list
```

Display as a table:
```
  * robert-allen          interview    personal, default
    zircote-brand         designed     corporate, brand
    narrator-formal       template     fictional, narrator
```

The `*` marks the currently active profile.

### activate {slug}

Set a profile as active. This copies its `profile.json` and `voice-prompt.txt` to the top-level data directory, making it the profile used by hooks, agents, and all voice commands.

```
bin/voice-profiles activate zircote-brand
```

### info {slug}

Show full details for a profile: all dimension scores, calibration, distinctive features, mechanics, identity summary, and **example prose**.

```
bin/voice-profiles info robert-allen
```

Display the same formatted output as `/voice-profile` but for any named profile, not just the active one.

Always **generate 3-4 prose examples** from the profile's dimension scores, mechanics, distinctive features, and identity summary. These demonstrate what writing produced under this profile's rules looks like — they prove the configuration works. Choose contexts appropriate to the profile (decision email, code review, postmortem, stakeholder explanation, blog opening, etc.).

### delete {slug}

Delete a profile permanently. Cannot delete the currently active profile — activate a different one first.

```
bin/voice-profiles delete narrator-formal
```

Confirm with `AskUserQuestion` before deleting.

### rename {old-slug} {new-slug}

Rename a profile. Updates the registry, directory, and any directory overrides that reference it.

```
bin/voice-profiles rename old-name new-name
```

### export {slug} [--to-repo path]

Export a profile as a markdown voice guide to a repository's `.github/voice-profiles/` directory for GitHub Copilot consumption.

```
bin/voice-profiles export robert-allen --to-repo ../zircote.github.io
```

This writes `{repo}/.github/voice-profiles/{slug}.md` with the full voice prompt text.

### set-override {pattern} {slug}

Assign a profile to activate automatically when working in directories matching the glob pattern.

```
bin/voice-profiles set-override "/Users/me/Projects/novel/*" narrator-formal
```

### remove-override {pattern}

Remove a directory override.

```
bin/voice-profiles remove-override "/Users/me/Projects/novel/*"
```

## Examples

```
/voice-profiles                     # list all profiles
/voice-profiles list                # same
/voice-profiles activate zircote    # switch active profile
/voice-profiles info robert-allen   # view profile details
/voice-profiles export robert-allen --to-repo ../my-blog
/voice-profiles set-override "/path/to/repo/*" zircote-brand
```
