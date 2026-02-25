"""ty bug #2480: Missing type narrowing for NoReturn control flow at module scope.

After `if not api_key: exit(1)`, api_key should be narrowed from
str | None to str. This works inside functions but not at module scope.
"""

from typing import reveal_type

data: dict[str, str] = {}
api_key = data.get("api_key")

if not api_key:
    exit(1)

reveal_type(api_key)  # Expected: str, Actual: str | None
