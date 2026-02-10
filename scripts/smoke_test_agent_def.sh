#!/bin/bash
# Smoke Test 2: Verify .claude/agents/*.md definitions are loaded by claude -p
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Smoke Test 2: Agent Definition Loading ==="
echo "Working directory: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

if [ ! -f .claude/agents/bug-investigator.md ]; then
    echo "FAIL: .claude/agents/bug-investigator.md not found"
    exit 1
fi
echo "Agent definition exists: .claude/agents/bug-investigator.md"

output=$(claude -p "What is your role? Reply in one sentence." \
    --model haiku \
    --agent bug-investigator \
    --max-turns 1 \
    --output-format json \
    2>/dev/null)

if ! echo "$output" | jq . > /dev/null 2>&1; then
    echo "FAIL: Output is not valid JSON"
    echo "Raw output: $output"
    exit 1
fi
echo "PASS: Valid JSON output"

result=$(echo "$output" | jq -r '.result // "null"')
echo "Result: $result"

if echo "$result" | grep -qi -e "bug" -e "investigat" -e "ruff" -e "linter"; then
    echo "PASS: Agent personality reflected in response"
else
    echo "WARN: Response may not reflect bug-investigator persona"
fi

cost=$(echo "$output" | jq -r '.total_cost_usd // "unknown"')
echo "Cost: \$$cost"

echo ""
echo "=== Smoke Test 2 COMPLETE ==="
