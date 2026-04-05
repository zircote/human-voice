#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODULES_DIR="$REPO_ROOT/question-bank/modules"

echo "=== Question Bank Validation ==="
echo ""

python3 - "$MODULES_DIR" <<'PYEOF'
import json
import os
import sys
from pathlib import Path

modules_dir = Path(sys.argv[1])
if not modules_dir.is_dir():
    print(f"ERROR: Modules directory not found: {modules_dir}", file=sys.stderr)
    sys.exit(1)

json_files = sorted(modules_dir.glob("*.json"))
if not json_files:
    print("ERROR: No JSON files found in modules directory", file=sys.stderr)
    sys.exit(1)

all_question_ids = []
module_data = []
errors = []

for json_file in json_files:
    filename_stem = json_file.stem  # e.g., "M01-writing-identity"
    # Extract module prefix: everything before the first hyphen that is followed by a letter
    # For "M01-writing-identity" -> "M01", for "SD-semantic-differential" -> "SD"
    parts = filename_stem.split("-")
    expected_module_id = parts[0]

    # 1. Check valid JSON
    try:
        with open(json_file) as f:
            questions = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"PARSE ERROR: {json_file.name}: {e}")
        module_data.append((json_file.name, expected_module_id, 0, "PARSE ERROR"))
        continue

    if not isinstance(questions, list):
        errors.append(f"FORMAT ERROR: {json_file.name}: Expected a JSON array at top level")
        module_data.append((json_file.name, expected_module_id, 0, "FORMAT ERROR"))
        continue

    question_count = len(questions)
    file_question_ids = []

    for q in questions:
        qid = q.get("question_id", "<missing>")
        mid = q.get("module_id", "<missing>")
        file_question_ids.append(qid)
        all_question_ids.append((qid, json_file.name))

        # 2. Verify module_id matches filename
        if mid != expected_module_id:
            errors.append(
                f"MODULE MISMATCH: {json_file.name}: question {qid} has "
                f"module_id '{mid}', expected '{expected_module_id}'"
            )

    module_data.append((json_file.name, expected_module_id, question_count, "OK"))

# 3. Check for duplicate question_ids across all modules
seen_ids = {}
for qid, fname in all_question_ids:
    if qid in seen_ids:
        errors.append(
            f"DUPLICATE ID: '{qid}' appears in both {seen_ids[qid]} and {fname}"
        )
    else:
        seen_ids[qid] = fname

# Print summary table
print(f"{'File':<45} {'Module':<8} {'Questions':>9}  {'Status'}")
print("-" * 80)
total_questions = 0
for fname, mid, count, status in module_data:
    print(f"{fname:<45} {mid:<8} {count:>9}  {status}")
    total_questions += count
print("-" * 80)
print(f"{'TOTAL':<45} {'':<8} {total_questions:>9}")
print()

# Print unique question IDs count
print(f"Unique question IDs: {len(seen_ids)}")
print(f"Total modules:       {len(json_files)}")
print()

# Print errors
if errors:
    print(f"ERRORS ({len(errors)}):")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("All validations passed.")
PYEOF
