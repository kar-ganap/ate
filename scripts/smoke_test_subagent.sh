#!/bin/bash
# Smoke Test 1: Verify claude -p can use tools against a codebase and return JSON
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Smoke Test 1: Subagent (claude -p with tool use) ==="
echo "Working directory: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

output=$(claude -p "Read the file pyproject.toml in the current directory and tell me the project name. Reply with just the name, nothing else." \
    --model haiku \
    --max-turns 3 \
    --output-format json \
    --allowedTools "Read,Grep,Glob" \
    2>/dev/null)

if ! echo "$output" | jq . > /dev/null 2>&1; then
    echo "FAIL: Output is not valid JSON"
    echo "Raw output: $output"
    exit 1
fi
echo "PASS: Valid JSON output"

result=$(echo "$output" | jq -r '.result // "null"')
echo "Result: $result"
if echo "$result" | grep -qi "agent-teams-eval"; then
    echo "PASS: Correct project name found (tool use worked)"
else
    echo "WARN: Expected 'agent-teams-eval' in result"
fi

num_turns=$(echo "$output" | jq -r '.num_turns // "unknown"')
echo "Turns: $num_turns (max 3)"

cost=$(echo "$output" | jq -r '.total_cost_usd // "unknown"')
echo "Cost: \$$cost"

session_id=$(echo "$output" | jq -r '.session_id // "unknown"')
echo "Session: $session_id"

echo ""
echo "=== Smoke Test 1 COMPLETE ==="
