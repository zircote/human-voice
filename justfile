# human-voice plugin development justfile

set dotenv-load := false

venv := ".venv/bin"
python := venv / "python3"
pip := venv / "pip"
pytest := venv / "pytest"

# list available recipes
default:
    @just --list

# ---------- setup ----------

# create venv and install all packages
setup:
    test -d .venv || python3 -m venv .venv
    {{ pip }} install -e ".[all,dev]"
    {{ pip }} install -e "./nlp[dev]"
    {{ pip }} install -e "./scoring[dev]"
    {{ python }} -m spacy download en_core_web_sm
    mkdir -p ~/.human-voice

# install packages only (skip spacy model)
install:
    {{ pip }} install -e ".[all,dev]"
    {{ pip }} install -e "./nlp[dev]"
    {{ pip }} install -e "./scoring[dev]"

# ---------- test ----------

# run all tests
test: test-lib test-scoring test-nlp

# run lib tests
test-lib:
    {{ pytest }} tests/ --ignore=tests/test_integration.py -q

# run scoring tests
test-scoring:
    {{ pytest }} scoring/tests/ -q

# run nlp tests
test-nlp:
    {{ pytest }} nlp/tests/ -q

# run integration tests (requires spacy)
test-integration:
    {{ pytest }} tests/test_integration.py -q

# run all tests with coverage
test-cov:
    {{ pytest }} tests/ scoring/tests/ nlp/tests/ --ignore=tests/test_integration.py --cov=lib --cov=scoring/src --cov=nlp/src --cov-report=term-missing -q

# ---------- validate ----------

# validate question bank JSON
validate-questions:
    bash scripts/validate-question-bank.sh

# validate all JSON schemas
validate-json:
    {{ python }} -c "import json, pathlib, sys; files = list(pathlib.Path('question-bank').rglob('*.json')); errs = [f for f in files if not (lambda p: (json.load(open(p)), True)[1])(f)]; print(f'{len(files)} valid') if not errs else (print('\n'.join(f'ERROR: {e}' for e in errs)), sys.exit(1))"

# validate character restrictions in docs
validate-chars path="docs/":
    node skills/human-voice/scripts/validate-character-restrictions.js {{ path }}

# run all validations
validate: validate-questions validate-json

# ---------- build ----------

# build self-contained Cowork plugin (.plugin)
bundle:
    rm -f human-voice.plugin
    zip -r human-voice.plugin \
        .claude-plugin/ \
        skills/ \
        commands/ \
        agents/ \
        hooks/ \
        bin/ \
        lib/ \
        question-bank/ \
        scoring/src/ scoring/pyproject.toml \
        nlp/src/ nlp/pyproject.toml \
        templates/ \
        CONNECTORS.md \
        pyproject.toml \
        LICENSE \
        README.md \
        -x "*.DS_Store" \
        -x "*/__pycache__/*" \
        -x "*/evals/*"
    @ls -lh human-voice.plugin
    @echo "Files: $(unzip -l human-voice.plugin | tail -1 | awk '{print $2}')"

# build full archive with all source (for Claude Code --plugin-dir)
archive:
    rm -f human-voice-full.zip
    git ls-files | grep -v '\.venv/' | grep -v '__pycache__' | grep -v '\.skill$' | grep -v '\.plugin$' | grep -v '\.jpg$' | grep -v '\.png$' | zip human-voice-full.zip -@
    @ls -lh human-voice-full.zip

# verify bundle integrity
bundle-check: bundle
    #!/usr/bin/env bash
    set -euo pipefail
    echo "=== Bundle Checks ==="
    # No stale mivoca references
    if unzip -p human-voice.plugin | grep -qi mivoca; then
        echo "FAIL: stale mivoca references in bundle content"
        exit 1
    fi
    echo "  [ok] No mivoca references"
    # No binary/image files in bundle
    BINARIES=$(unzip -l human-voice.plugin | awk '{print $NF}' | grep -E '\.(jpg|png|gif|skill|zip)$' || true)
    if [ -n "$BINARIES" ]; then
        echo "FAIL: unexpected binary files in bundle:"
        echo "$BINARIES"
        exit 1
    fi
    echo "  [ok] No unexpected binary files"
    # Frontmatter validates
    TMP=$(mktemp -d)
    unzip -q human-voice.plugin -d "$TMP"
    ERRORS=0
    for f in "$TMP"/commands/*.md "$TMP"/agents/*.md "$TMP"/skills/*/SKILL.md; do
        [ -f "$f" ] || continue
        python3 -c "import yaml,sys;c=open(sys.argv[1]).read();e=c.index('---',3) if c.startswith('---') else -1;yaml.safe_load(c[3:e]) if e>0 else None" "$f" 2>/dev/null || { echo "FAIL: bad frontmatter in ${f#$TMP/}"; ERRORS=1; }
    done
    rm -rf "$TMP"
    if [ "$ERRORS" -eq 1 ]; then exit 1; fi
    echo "  [ok] All frontmatter valid"
    echo "=== Bundle OK ==="

# ---------- lint ----------

# check for mivoca remnants in source
check-rename:
    @grep -r "mivoca" --include="*.py" --include="*.md" --include="*.json" --include="*.toml" --include="*.sh" --include="*.txt" --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.git . && echo "ERROR: mivoca references found" && exit 1 || echo "No mivoca references"

# ---------- clean ----------

# remove build artifacts
clean:
    rm -f human-voice.plugin
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

# remove venv and all artifacts
clean-all: clean
    rm -rf .venv

# ---------- plugin ----------

# test plugin loads correctly
plugin-test:
    claude --plugin-dir . --print-plugin-state 2>&1 || claude --plugin-dir . -p "exit" 2>&1 | head -20

# ---------- data ----------

# migrate ~/.human-voice data to CLAUDE_PLUGIN_DATA and create symlinks
migrate:
    #!/usr/bin/env bash
    set -euo pipefail
    LEGACY="$HOME/.human-voice"
    # Always target the human-voice plugin data dir (not the current session's env)
    PERSONAL_DATA="$HOME/.claude-personal/plugins/data/human-voice-zircote"
    SHARED_DATA="$HOME/.claude/plugins/data/human-voice-zircote"
    # Pick the target: personal > shared
    if [ -d "$PERSONAL_DATA" ] || [ -L "$PERSONAL_DATA" ]; then
        TARGET="$PERSONAL_DATA"
    elif [ -d "$SHARED_DATA" ] || [ -L "$SHARED_DATA" ]; then
        TARGET="$SHARED_DATA"
    else
        # Create under personal by default
        TARGET="$PERSONAL_DATA"
    fi
    echo "Target data dir: $TARGET"
    mkdir -p "$TARGET"
    # Migrate legacy data if it exists and isn't already a symlink
    if [ -d "$LEGACY" ] && [ ! -L "$LEGACY" ]; then
        echo "Migrating $LEGACY -> $TARGET"
        for item in "$LEGACY"/*; do
            name=$(basename "$item")
            dest="$TARGET/$name"
            if [ -e "$dest" ]; then
                echo "  skip: $name (already exists in target)"
            else
                cp -a "$item" "$dest"
                echo "  copied: $name"
            fi
        done
        # Replace legacy dir with symlink
        mv "$LEGACY" "${LEGACY}.bak"
        ln -s "$TARGET" "$LEGACY"
        echo "Created symlink: $LEGACY -> $TARGET"
        echo "Backup at: ${LEGACY}.bak"
    elif [ -L "$LEGACY" ]; then
        echo "$LEGACY is already a symlink -> $(readlink "$LEGACY")"
    else
        echo "No legacy data at $LEGACY"
        ln -sf "$TARGET" "$LEGACY"
        echo "Created symlink: $LEGACY -> $TARGET"
    fi
    # Cross-link personal <-> shared so both scopes see the same data
    if [ "$TARGET" = "$PERSONAL_DATA" ] && [ ! -e "$SHARED_DATA" ]; then
        mkdir -p "$(dirname "$SHARED_DATA")"
        ln -sf "$PERSONAL_DATA" "$SHARED_DATA"
        echo "Linked: $SHARED_DATA -> $PERSONAL_DATA"
    elif [ "$TARGET" = "$SHARED_DATA" ] && [ ! -e "$PERSONAL_DATA" ]; then
        mkdir -p "$(dirname "$PERSONAL_DATA")"
        ln -sf "$SHARED_DATA" "$PERSONAL_DATA"
        echo "Linked: $PERSONAL_DATA -> $SHARED_DATA"
    fi
    echo "Done. All scopes share: $TARGET"

# show data directory status
data-status:
    #!/usr/bin/env bash
    echo "CLAUDE_PLUGIN_DATA=${CLAUDE_PLUGIN_DATA:-NOT SET}"
    for d in "$HOME/.human-voice" "$HOME/.claude-personal/plugins/data/human-voice-zircote" "$HOME/.claude/plugins/data/human-voice-zircote"; do
        if [ -L "$d" ]; then
            echo "  $d -> $(readlink "$d") (symlink)"
        elif [ -d "$d" ]; then
            count=$(find "$d" -maxdepth 1 -not -name "$(basename "$d")" | wc -l | tr -d ' ')
            echo "  $d ($count items)"
        else
            echo "  $d (not found)"
        fi
    done

# ---------- session tools ----------

# list interview sessions
sessions:
    {{ python }} -m lib.session list

# show config
config:
    {{ python }} -m lib.config show

# reset config to defaults
config-reset:
    {{ python }} -m lib.config reset

# ---------- profile management ----------

# list all voice profiles
profiles:
    {{ python }} -m lib.profile_registry list

# activate a voice profile
profile-activate slug:
    {{ python }} -m lib.profile_registry activate {{ slug }}

# show profile details
profile-info slug:
    {{ python }} -m lib.profile_registry info {{ slug }}

# export profile to a repo for Copilot
profile-export slug repo:
    {{ python }} -m lib.profile_registry export {{ slug }} --to-repo {{ repo }}

# set directory override
profile-override pattern slug:
    {{ python }} -m lib.profile_registry set-override {{ pattern }} {{ slug }}

# migrate single profile to multi-profile registry
profile-migrate:
    {{ python }} -m lib.profile_registry migrate
