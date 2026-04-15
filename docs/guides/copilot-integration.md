---
title: Copilot Integration
diataxis_type: how-to
diataxis_goal: Export voice profiles to a repository for use by GitHub Copilot and CI validation
---

# Integrating with GitHub Copilot

This guide covers how to export voice profiles to a repository so GitHub Copilot applies them automatically during content generation and review.

## Prerequisites

- At least one voice profile stored in the registry (from an interview, design, or template)
- The human-voice plugin installed
- GitHub Copilot enabled on the target repository

## Install profiles to a repository

Use the `voice-profiles install` command to export one or more profiles into a repository. This generates a single `.github/copilot-instructions.md` file containing all specified profiles with routing logic.

```bash
bin/voice-profiles install robert-allen zircote-brand --to-repo ../my-repo
```

Or use the slash command:

```
/voice:profiles export robert-allen --to-repo ../my-repo
```

The command writes the profiles inside marker-delimited sections:

```markdown
<!-- voice-profiles:start -->
# Voice Instructions
...profile content...
<!-- voice-profiles:end -->
```

If `copilot-instructions.md` already exists, the command replaces only the content between the markers. Non-voice content in the file is preserved.

## Set a default profile

When installing multiple profiles, specify which one Copilot should use by default:

```bash
bin/voice-profiles install robert-allen zircote-brand \
  --to-repo ../my-repo \
  --default robert-allen
```

If you omit `--default`, the first slug in the list is the default.

## Select profiles with labels

Copilot uses the default profile unless a different one is specified. You can select a profile three ways:

1. **Issue/PR label**: Add a label `voice:{slug}` to the issue or pull request (e.g., `voice:zircote-brand`)
2. **Issue/PR body**: Include `voice: {slug}` in the description text
3. **Direct instruction**: Tell Copilot "use the zircote-brand voice profile" in the prompt

The generated `copilot-instructions.md` includes a routing table showing all installed profiles and when to use each one.

## Update profiles after re-interview

Run the install command again with the same slugs. The marker-delimited section is replaced with the updated profiles. Non-voice content outside the markers is untouched.

```bash
bin/voice-profiles install robert-allen zircote-brand --to-repo ../my-repo
```

## Automatic cleanup

The install command removes stale artifacts from previous export formats:

- `.github/voice-profile.md` (old single-file export) is deleted
- `.github/voice-profiles/` directory (old per-file export) is removed

No manual cleanup is needed when upgrading from older export formats.

## Use the voice reviewer agent

The repository includes a custom Copilot agent at `.github/agents/voice-reviewer.agent.md`. This agent reviews content files against the voice profile rules.

1. Open a content file in your editor
2. Open GitHub Copilot Chat
3. Select the "voice-reviewer" agent from the agent dropdown
4. Ask it to review the current file: "Review this content for voice compliance"

The agent checks for restricted characters, contractions, Oxford comma usage, AI writing anti-patterns, and voice profile deviations. It is editorial only -- it does not conduct interviews, run scoring, or execute CLI tools.

## CI validation

The workflow at `.github/workflows/voice-validation.yml` runs automatically on pull requests that modify content files. It validates:

1. **Character restrictions**: Scans markdown files in `docs/`, `content/`, `src/content/`, and `_docs/` for restricted characters
2. **Contractions**: Checks changed files for contraction usage (hard failure)
3. **Oxford comma**: Checks changed files for Oxford comma patterns (warning only)

### Workflow trigger paths

The workflow triggers on PRs that change files matching:

- `docs/**/*.md`
- `content/**/*.md`
- `src/content/**/*.md`
- `_docs/**/*.md`
- `README.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`

### Interpreting CI results

- **Character restriction failures**: The validation script lists each violation with file path, line number, and the restricted character found. Replace the character according to the substitution table in the voice profile.
- **Contraction failures**: The check lists each contraction found with file and line number. Expand each contraction to its full form.
- **Oxford comma warnings**: Flagged for manual review. Not all matches are true Oxford commas. Review each match in context.

## Related documentation

- [Managing Profiles](managing-profiles.md) for full profile registry operations
- [CLI Reference](../reference/cli.md) for `voice-profiles` command syntax
- [Configuration Reference](../reference/configuration.md) for plugin settings
