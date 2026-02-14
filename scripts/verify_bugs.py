"""Verify all 8 primary bugs reproduce against pinned Ruff build."""

from __future__ import annotations

import sys
from pathlib import Path

from ate.scoring.reproduction import REPRO_CASES, run_repro

RUFF_DIR = Path(__file__).parent.parent / "data" / "ruff"
RUFF_BINARY = RUFF_DIR / "target" / "debug" / "ruff"


def main() -> None:
    if not RUFF_BINARY.exists():
        print(f"ERROR: Ruff binary not found at {RUFF_BINARY}")
        print("Run 'ate ruff pin' and 'ate ruff build' first.")
        sys.exit(1)

    print(f"Verifying 8 bugs against {RUFF_BINARY}")
    print("=" * 70)

    passed = 0
    failed = 0
    for bug_id, case in REPRO_CASES.items():
        reproduced, details = run_repro(bug_id, RUFF_DIR)
        status = "REPRODUCED" if reproduced else "NOT REPRODUCED"
        icon = "+" if reproduced else "-"
        print(f"  [{icon}] #{case.bug_id} {case.title}")
        print(f"      {status}: {details}")
        if reproduced:
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"Reproduced: {passed}/8  |  Not reproduced: {failed}/8")

    if failed > 0:
        print("\nWARN: Some bugs did not reproduce. Check if they were fixed")
        print("before v0.14.14, or swap from backup list.")
        sys.exit(1)


if __name__ == "__main__":
    main()
