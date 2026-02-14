"""Score persistence: save and load score models as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def save_scores(scores: list[BaseModel], output_path: Path) -> Path:
    """Save a list of Pydantic score models to JSON."""
    data = [s.model_dump() for s in scores]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path


def load_scores(scores_path: Path, model_class: type[T]) -> list[T]:
    """Load scores from JSON file, returning typed model instances."""
    if not scores_path.exists():
        return []
    data = json.loads(scores_path.read_text())
    return [model_class.model_validate(item) for item in data]
