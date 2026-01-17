# Contributing to Human Voice

Thank you for your interest in contributing to the Human Voice plugin.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Install dependencies: `npm install`
4. Test locally: `claude --plugin-dir .`

## Development Workflow

### Testing Changes

Run the plugin locally against your changes:

```bash
# Test the plugin in current directory
claude --plugin-dir /path/to/human-voice

# Test specific commands
/human-voice:review test-content/
/human-voice:fix test-content/ --dry-run
```

### File Structure

| Directory | Purpose |
|-----------|---------|
| `skills/human-voice/` | Core skill and detection patterns |
| `skills/human-voice/scripts/` | Node.js validation/fix scripts |
| `skills/human-voice/references/` | Pattern documentation |
| `commands/` | Slash command definitions |
| `agents/` | Agent configurations |

### Adding Detection Patterns

1. Identify the pattern tier (character, language, structural, voice)
2. Add documentation to appropriate `references/*.md` file
3. Update `SKILL.md` if the pattern affects the workflow
4. Add before/after examples to `examples/before-after.md`

### Modifying Commands

Commands are markdown files in `commands/` with YAML frontmatter:

```yaml
---
name: command-name
description: What the command does
allowed-tools:
  - Read
  - Write
  - Glob
---
```

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Make focused, atomic commits
3. Update `CHANGELOG.md` under `[Unreleased]`
4. Ensure your changes work without optional dependencies (Subcog)
5. Submit a pull request with a clear description

### Commit Messages

Use conventional commit format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions or changes

### Changelog Entry

Add your changes to `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- **[Component]**: Description of new feature

### Fixed
- **[Component]**: Description of bug fix
```

## Code of Conduct

Be respectful and constructive. Focus on the work, not the person.

## Questions?

Open an issue for questions or discussion.
