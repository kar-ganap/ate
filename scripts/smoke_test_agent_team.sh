#!/bin/bash
# Smoke Test 3: Verify agent teams can be spawned
# NOTE: This test is INTERACTIVE — it cannot be fully automated.
# Run manually and observe the results.
set -euo pipefail

echo "=== Smoke Test: Agent Team Formation ==="
echo ""
echo "This test is INTERACTIVE. It will launch Claude Code with agent teams enabled."
echo "You will need to:"
echo "  1. Ask Claude to create a team with 2 teammates"
echo "  2. Verify teammates appear (Shift+Down to cycle in in-process mode)"
echo "  3. Ask the lead to clean up the team"
echo "  4. Exit with Ctrl+C or /exit"
echo ""

# Check env var
if [ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" != "1" ]; then
    echo "Setting CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
    export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
fi

echo "Suggested prompt:"
echo '  "Create a minimal team with 2 teammates. Teammate 1: Analyst.'
echo '   Teammate 2: Reviewer. Have them each say hello, then clean up the team."'
echo ""
read -p "Press Enter to launch Claude Code with agent teams enabled..."

CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude

echo ""
echo "=== Manual Verification Checklist ==="
echo "[ ] Did the team form? (teammates appeared)"
echo "[ ] Did teammates communicate? (messages visible)"
echo "[ ] Did cleanup succeed? (team dissolved)"
echo ""

# Check if team directories were created
if [ -d ~/.claude/teams ]; then
    team_count=$(ls -1 ~/.claude/teams 2>/dev/null | wc -l | tr -d ' ')
    echo "INFO: Found $team_count team directory(ies) in ~/.claude/teams/"
else
    echo "INFO: No ~/.claude/teams/ directory found (may have been cleaned up)"
fi

echo ""
echo "Record results in docs/phases/phase-1-plan.md under 'Smoke Test Results'"
