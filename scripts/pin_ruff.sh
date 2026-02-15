#!/bin/bash
# Pin Ruff to v0.14.14 for the experiment
set -euo pipefail

RUFF_DIR="data/ruff"
RUFF_TAG="0.15.1"
RUFF_REPO="https://github.com/astral-sh/ruff.git"

if [ -d "$RUFF_DIR/.git" ]; then
    echo "Ruff already cloned at $RUFF_DIR"
    echo "Checking out tag $RUFF_TAG..."
    git -C "$RUFF_DIR" checkout "tags/$RUFF_TAG" --quiet
else
    # Remove .gitkeep if present (empty dir placeholder)
    if [ -d "$RUFF_DIR" ]; then
        rm -rf "$RUFF_DIR"
    fi
    echo "Cloning Ruff (shallow, single tag)..."
    git clone --depth 1 --branch "$RUFF_TAG" "$RUFF_REPO" "$RUFF_DIR"
fi

echo "Pinned to Ruff $RUFF_TAG"
git -C "$RUFF_DIR" log --oneline -1
