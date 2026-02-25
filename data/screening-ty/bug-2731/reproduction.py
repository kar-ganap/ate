"""ty bug #2731: Local reads ignore nonlocal writes.

After calling bump() which increments count via nonlocal, ty still
thinks count is Literal[0]. This makes `assert count == 1` appear
as unreachable, cascading to Never for subsequent code.

All Python type checkers (pyright, pyrefly, mypy) fail on this.
"""

from typing import reveal_type


async def main() -> None:
    count = 0

    async def bump() -> None:
        nonlocal count
        count += 1

    await bump()

    reveal_type(count)  # Expected: int, Actual: Literal[0]
    assert count == 1
    reveal_type(count)  # Expected: Literal[1], Actual: Never (unreachable!)
