#!/usr/bin/env bash
# screen_bug.sh — Screen a single candidate bug for Round 2
#
# Usage: ./scripts/screen_bug.sh <bug_id>
#
# Checks:
#   1. Issue is still open (gh issue view)
#   2. No competing PRs (gh pr list --search)
#   3. Creates screening directory structure
#
# After running this script, manually run a 30-min Claude session
# and record results in data/screening/bug-<id>/metadata.json

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <bug_id>"
    exit 1
fi

BUG_ID="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SCREEN_DIR="$PROJECT_DIR/data/screening/bug-$BUG_ID"

echo "=== Screening Bug #$BUG_ID ==="
echo

# 1. Check issue status
echo "--- Issue Status ---"
if ! gh issue view "$BUG_ID" --repo astral-sh/ruff --json state,title,labels 2>/dev/null; then
    echo "ERROR: Could not fetch issue #$BUG_ID"
    exit 1
fi
echo

# 2. Check for competing PRs
echo "--- Competing PRs ---"
PR_COUNT=$(gh pr list --repo astral-sh/ruff --search "$BUG_ID" --json number --jq 'length' 2>/dev/null || echo "0")
if [ "$PR_COUNT" -gt 0 ]; then
    echo "WARNING: Found $PR_COUNT PR(s) mentioning #$BUG_ID:"
    gh pr list --repo astral-sh/ruff --search "$BUG_ID" --json number,title,state --jq '.[] | "  #\(.number) [\(.state)] \(.title)"'
else
    echo "  No competing PRs found."
fi
echo

# 3. Create screening directory
mkdir -p "$SCREEN_DIR"

# Create metadata template if it doesn't exist
if [ ! -f "$SCREEN_DIR/metadata.json" ]; then
    cat > "$SCREEN_DIR/metadata.json" << METAEOF
{
  "bug_id": $BUG_ID,
  "screening_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "pending",
  "time_minutes": null,
  "dead_ends": 0,
  "fix_produced": false,
  "fix_correct": null,
  "notes": ""
}
METAEOF
    echo "Created: $SCREEN_DIR/metadata.json"
fi

# Create notes template if it doesn't exist
if [ ! -f "$SCREEN_DIR/notes.md" ]; then
    cat > "$SCREEN_DIR/notes.md" << NOTESEOF
# Screening: Bug #$BUG_ID

## Reproduction
<!-- Does the bug reproduce against latest Ruff main? -->

## Claude Session
<!-- 30-min hard limit. Record observations. -->
- Started:
- Ended:
- Dead ends:

## Verdict
<!-- KEEP / MAYBE / DROP -->
NOTESEOF
    echo "Created: $SCREEN_DIR/notes.md"
fi

echo
echo "Next steps:"
echo "  1. Write reproduction case at: $SCREEN_DIR/reproduction.py"
echo "  2. Run a 30-min Claude session (Treatment 0b style)"
echo "  3. Update $SCREEN_DIR/metadata.json with results"
echo "  4. Update config/screening_candidates.yaml status"
