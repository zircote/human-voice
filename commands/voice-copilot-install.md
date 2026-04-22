---
description: Install voice profile(s) into a project's GitHub Copilot configuration
---

# /human-voice:voice-copilot-install

Install one or more human-voice profiles into a target project as GitHub Copilot
custom instructions, prompts, agents, AGENTS.md, and a PR review workflow.

## Arguments

`$ARGUMENTS` — optional CLI args forwarded to `bin/voice-copilot-install`.
Examples:

- `--target /path/to/repo` (default: current working directory)
- `--profile robert-allen` (single profile; default: active profile)
- `--profiles robert-allen,tech-authority --route 'docs/**=tech-authority;**/*.md=robert-allen'`
- `--default robert-allen` (which installed slug is the repo default)
- `--overwrite error|merge|force` (default: `merge` — replaces marker blocks, preserves surrounding content)
- `--dry-run` (print intended writes, touch nothing)
- `--no-workflow`, `--no-prompts`, `--no-agent`, `--no-agents-md`, `--no-redact`

If `$ARGUMENTS` is empty, run with defaults (active profile, install into cwd, merge mode).

## Steps

1. **Show the plan**: Run with `--dry-run` first. Print the list of files that would be written. Ask the user to confirm before proceeding unless they explicitly passed flags indicating they want to proceed immediately.

2. **Run the install**: `bin/voice-copilot-install $ARGUMENTS`. Surface the list of written/skipped files.

3. **Report**: Summarise what was written and point the user at `.github/copilot-instructions.md` as the entry point. If a workflow was written, remind them to commit and push so Copilot code review picks it up on the next PR.

## What gets written

- `.github/copilot-instructions.md` — repo-wide, loaded by Copilot automatically on GitHub.
- `AGENTS.md` at repo root — coding-agent instructions.
- `.github/instructions/human-voice-<slug>.instructions.md` — path-scoped (one per profile; `applyTo` glob drives routing).
- `.github/prompts/voice-{review,fix,draft}.prompt.md` — reusable Copilot Chat slash commands.
- `.github/agents/human-voice-<slug>.agent.md` — Copilot custom agents (one per profile).
- `.github/human-voice/<slug>/profile.json` + `voice-prompt.txt` — redacted profile artefacts.
- `.github/human-voice/scripts/*.js` — bundled validator scripts.
- `.github/workflows/voice-review.yml` — PR workflow that runs validators on changed prose and comments findings.

Repo-wide instructions and AGENTS.md are written inside `<!-- human-voice:start -->` / `<!-- human-voice:end -->` markers, so re-runs are idempotent and never clobber user-added content outside the block.

## Notes

- Profile data is redacted by default before embedding (drops `metadata` and `known_gaps`, trims `calibration` to its summary). Pass `--no-redact` only for private repos.
- The workflow triggers only on pull requests touching `docs/**`, `README*`, `CHANGELOG*`, `CONTRIBUTING*`, and `**/*.{md,mdx}`.
- For multi-profile installs, provide a `--route` spec mapping globs to slugs. The default profile applies to anything not matched by an explicit glob.
