"""Integration test fixtures — auto-skip if Ruff not built or cargo unavailable."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

RUFF_DIR = Path(__file__).parent.parent.parent / "data" / "ruff"
RUFF_BINARY = RUFF_DIR / "target" / "debug" / "ruff"

skip_no_ruff = pytest.mark.skipif(
    not RUFF_BINARY.exists(),
    reason="Ruff not built — run 'ate ruff pin && ate ruff build' first",
)

skip_no_cargo = pytest.mark.skipif(
    shutil.which("cargo") is None,
    reason="cargo not found — install Rust toolchain",
)
