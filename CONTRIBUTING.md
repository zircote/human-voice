# Contributing to Human Voice

Thank you for your interest in contributing to the Human Voice plugin.

## Branching Strategy

- **main**: Stable release branch. Do not commit directly to main.
- **develop**: Active development branch. All work starts here.

All pull requests target `develop`. When `develop` is stable and tested, it is merged into `main` as a release.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch from `develop`: `git checkout -b feature/your-feature develop`
4. Run the setup script: `bash scripts/setup.sh`
5. Test locally: `claude --plugin-dir .`

## Development Workflow

### Testing Changes

```bash
# Run scoring tests
python3 -m pytest scoring/tests/ -v

# Test the plugin in current directory
claude --plugin-dir /path/to/human-voice

# Validate character restrictions
node skills/human-voice/scripts/validate-character-restrictions.js docs/

# Test specific commands
/human-voice:voice-review test-content/
/human-voice:voice-fix test-content/ --dry-run
```

### File Structure

| Directory | Purpose |
|-----------|---------|
| `skills/human-voice/` | Core skill and detection patterns |
| `skills/voice/` | Voice elicitation interview skill |
| `commands/` | Slash command definitions |
| `agents/` | Agent configurations (interview, synthesizer, reviewer) |
| `hooks/` | Plugin hooks (SessionStart observer) |
| `bin/` | CLI tools (voice-session, voice-scoring, etc.) |
| `question-bank/` | Interview modules, schemas, scoring config |
| `scoring/src/voice_scoring/` | Self-report scoring engine |
| `nlp/src/voice_nlp/` | NLP stylometric analysis pipeline |
| `lib/` | Core library (session, branching, quality, config) |
| `docs/` | Documentation (Diataxis framework) |
| `.github/agents/` | GitHub Copilot custom agents |
| `.github/workflows/` | CI workflows |

### Working with the Scoring Engine

The scoring pipeline is at `scoring/src/voice_scoring/`. Key files:

- `cli.py`: CLI entry point, metadata discovery, question bank loading
- `self_report.py`: Per-dimension subscale scoring, scoring_map resolution
- `semantic_differential.py`: SD normalization and dimension mapping
- `quality_checks.py`: Post-hoc satisficing detection
- `calibration.py`: Self-report vs NLP observed score calibration
- `profile_builder.py`: Tier-weighted profile merging

When modifying scoring_maps in question bank modules:
- Every scoring_map entry must include a key matching the target dimension name in `dimension-item-mapping.json`
- Use exact match or underscore-separated prefix (e.g., `formality_baseline` matches dimension `formality`)
- Run `python3 -m pytest scoring/tests/ -v` after any scoring_map change

### Working with the NLP Pipeline

The NLP pipeline requires `spacy` and the `en_core_web_sm` model. Install via `scripts/setup.sh` or manually:

```bash
pip install spacy
python3 -m spacy download en_core_web_sm
```

### Working with the Question Bank

Question bank modules are JSON files in `question-bank/modules/`. Each question needs:
- `question_id`: Unique ID (e.g., `M03-Q04`)
- `type`: One of `likert`, `forced_choice`, `select`, `scenario`, `projective`, `calibration`, `open_ended`, `writing_sample`, `process_narration`
- `scoring.scoring_map`: Required for all non-open-ended types if the question is mapped to a dimension in `dimension-item-mapping.json`

See `docs/guides/adding-questions.md` for the full guide.

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

## Voice Development

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
voice-nlp analyze-session --session-dir ${CLAUDE_PLUGIN_DATA}/sessions/{id}/
```

Analysis output files are written as `*.analysis.json` alongside the source writing samples.

### Scoring Engine Architecture

The scoring pipeline follows a linear five-stage flow implemented in `scoring/src/voice_scoring/cli.py`:

1. `run_quality_checks` validates response data for satisficing patterns
2. `normalize_semantic_differentials` converts raw bipolar ratings to dimension scores
3. `score_self_report` computes per-dimension self-report scores using weighted item means
4. `calibrate` compares self-report scores against observed NLP scores (when available)
5. `build_profile` merges all scores into the final voice profile

Each stage is a pure function that accepts data and returns results. The CLI orchestrates the pipeline and handles file I/O.

## Pull Request Guidelines

1. Create a feature branch from `develop` (not main)
2. Make focused, atomic commits
3. Run tests: `python3 -m pytest scoring/tests/ -v`
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Ensure your changes work without optional dependencies (Subcog)
6. Submit a pull request targeting `develop`

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
