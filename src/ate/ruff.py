"""Ruff integration: pin, build, check, and test."""

from __future__ import annotations

import subprocess
from pathlib import Path

RUFF_TAG = "0.14.14"
RUFF_REPO = "https://github.com/astral-sh/ruff.git"


def get_ruff_binary(ruff_dir: Path) -> Path:
    """Return path to the debug-built ruff binary."""
    return ruff_dir / "target" / "debug" / "ruff"


def build_ruff(ruff_dir: Path) -> None:
    """Build Ruff from source with cargo."""
    result = subprocess.run(
        ["cargo", "build"],
        cwd=ruff_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = f"cargo build failed (exit {result.returncode}): {result.stderr}"
        raise RuntimeError(msg)


def get_ruff_version(ruff_dir: Path) -> str:
    """Get the version string from the built ruff binary."""
    binary = get_ruff_binary(ruff_dir)
    result = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = f"Failed to get ruff version: {result.stderr}"
        raise RuntimeError(msg)
    # Output is "ruff X.Y.Z\n"
    return result.stdout.strip().split()[-1]


def run_ruff_check(
    ruff_dir: Path,
    target_file: Path,
    rules: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ruff check on a target file using the built binary."""
    binary = get_ruff_binary(ruff_dir)
    cmd: list[str] = [str(binary), "check", str(target_file)]
    if rules:
        cmd.extend(["--select", ",".join(rules)])
    return subprocess.run(cmd, capture_output=True, text=True)


def run_cargo_test(
    ruff_dir: Path,
    test_filter: str | None = None,
    package: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run cargo test in the Ruff repo."""
    cmd = ["cargo", "test"]
    if test_filter:
        cmd.append(test_filter)
    if package:
        cmd.extend(["--package", package])
    return subprocess.run(cmd, cwd=ruff_dir, capture_output=True, text=True)
