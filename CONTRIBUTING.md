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
/human-voice:voice-review test-content/
/human-voice:voice-fix test-content/ --dry-run
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

## Mivoca Development

### Running Scoring Tests

The scoring engine has a dedicated test suite under `scoring/tests/`. Run all tests with:

```bash
python3 -m pytest scoring/tests/ -v
```

Individual test modules cover calibration, profile building and self-report scoring. The `conftest.py` file provides shared fixtures for session data and question bank metadata.

### Working with the Question Bank

Question bank modules are JSON files in `question-bank/modules/` following the naming pattern `Mxx-<slug>.json` (e.g., `M02-voice-personality.json`). Each file contains an array of question definition objects.

Requirements for question definitions:

- Every question must have a unique `question_id` matching the pattern `Mxx-Qyy`
- Questions that contribute to dimension scoring must include a `scoring_map` object mapping response values to numeric scores
- Dimension keys in `scoring_map` must match keys defined in `question-bank/scoring/dimension-item-mapping.json`
- See the [Adding Questions guide](docs/guides/adding-questions.md) for step-by-step instructions

### NLP Pipeline Development

The NLP pipeline depends on spaCy and the `en_core_web_sm` language model. Install dependencies:

```bash
pip install spacy
python3 -m spacy download en_core_web_sm
```

Run NLP analysis on a session:

```bash
mivoca-nlp analyze-session --session-dir ~/.human-voice/sessions/{id}/
```

Analysis output files are written as `*.analysis.json` alongside the source writing samples.

### Scoring Engine Architecture

The scoring pipeline follows a linear five-stage flow implemented in `scoring/src/mivoca_scoring/cli.py`:

1. `run_quality_checks` validates response data for satisficing patterns
2. `normalize_semantic_differentials` converts raw bipolar ratings to dimension scores
3. `score_self_report` computes per-dimension self-report scores using weighted item means
4. `calibrate` compares self-report scores against observed NLP scores (when available)
5. `build_profile` merges all scores into the final voice profile

Each stage is a pure function that accepts data and returns results. The CLI orchestrates the pipeline and handles file I/O.

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
