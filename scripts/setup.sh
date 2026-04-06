#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== voice setup ==="
echo "Repository root: $REPO_ROOT"
echo ""

# 1. Create virtual environment if it doesn't exist
if [ -d ".venv" ]; then
    echo "[1/7] Virtual environment already exists at .venv"
else
    echo "[1/7] Creating virtual environment at .venv ..."
    python3 -m venv .venv
fi

# Activate the virtual environment
# shellcheck disable=SC1091
source .venv/bin/activate
echo "      Using Python: $(python3 --version) at $(which python3)"
echo ""

# 2. Install root package with all extras
echo "[2/7] Installing voice root package with [all,dev] extras ..."
pip install -e ".[all,dev]"
echo ""

# 3. Install NLP sub-package
echo "[3/7] Installing voice-nlp package with [dev] extras ..."
pip install -e "./nlp[dev]"
echo ""

# 4. Install scoring sub-package
echo "[4/7] Installing voice-scoring package with [dev] extras ..."
pip install -e "./scoring[dev]"
echo ""

# 5. Download spaCy model into plugin data directory
DATA_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.human-voice}"
mkdir -p "$DATA_DIR/models"
echo "[5/8] Downloading spaCy en_core_web_sm model to $DATA_DIR/models ..."
python3 -m spacy download en_core_web_sm
# Link model into data dir for portability
SPACY_MODEL=$(python3 -c "import spacy; print(spacy.util.get_package_path('en_core_web_sm'))" 2>/dev/null || true)
if [ -n "$SPACY_MODEL" ] && [ -d "$SPACY_MODEL" ]; then
    ln -sf "$SPACY_MODEL" "$DATA_DIR/models/en_core_web_sm"
    echo "      Linked model: $DATA_DIR/models/en_core_web_sm -> $SPACY_MODEL"
fi
echo ""

# 6. Create plugin data directory
if [ -d "$DATA_DIR" ]; then
    echo "[6/8] Data directory already exists at $DATA_DIR"
else
    echo "[6/8] Creating data directory at $DATA_DIR ..."
    mkdir -p "$DATA_DIR"
fi

# 7. Migrate legacy data if needed
if [ -d "$HOME/.human-voice" ] && [ ! -L "$HOME/.human-voice" ] && [ "$DATA_DIR" != "$HOME/.human-voice" ]; then
    echo "[7/8] Migrating legacy data from ~/.human-voice ..."
    python3 -c "from lib.config import migrate_legacy_data; print('Migrated' if migrate_legacy_data() else 'Nothing to migrate')"
else
    echo "[7/8] No legacy migration needed"
fi
echo ""

# 8. Validate JSON files
echo "[8/8] Validating JSON files ..."
JSON_COUNT=0
JSON_ERRORS=0
while IFS= read -r -d '' jsonfile; do
    if python3 -c "import json, sys; json.load(open(sys.argv[1]))" "$jsonfile" 2>/dev/null; then
        JSON_COUNT=$((JSON_COUNT + 1))
    else
        echo "      ERROR: Invalid JSON: $jsonfile"
        JSON_ERRORS=$((JSON_ERRORS + 1))
    fi
done < <(find "$REPO_ROOT/question-bank" -name '*.json' -print0 2>/dev/null || true)
echo "      Validated $JSON_COUNT JSON files, $JSON_ERRORS errors"
echo ""

# Summary
echo "=== Setup complete ==="
echo "  Virtual environment: .venv"
echo "  Packages installed:  voice, voice-nlp, voice-scoring"
echo "  spaCy model:         en_core_web_sm"
echo "  Config directory:    $DATA_DIR"
echo "  JSON files:          $JSON_COUNT valid, $JSON_ERRORS errors"
echo ""
echo "Activate the environment with:"
echo "  source .venv/bin/activate"
