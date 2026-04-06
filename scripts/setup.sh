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

# 5. Download spaCy model
echo "[5/7] Downloading spaCy en_core_web_sm model ..."
python3 -m spacy download en_core_web_sm
echo ""

# 6. Create ~/.human-voice directory
if [ -d "$HOME/.human-voice" ]; then
    echo "[6/7] ~/.human-voice directory already exists"
else
    echo "[6/7] Creating ~/.human-voice directory ..."
    mkdir -p "$HOME/.human-voice"
fi
echo ""

# 7. Validate JSON files
echo "[7/7] Validating JSON files ..."
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
echo "  Config directory:    ~/.human-voice"
echo "  JSON files:          $JSON_COUNT valid, $JSON_ERRORS errors"
echo ""
echo "Activate the environment with:"
echo "  source .venv/bin/activate"
